/*
 * psvr-sbs — side-by-side compositor for PSVR VR mode.
 *
 * Takes whatever is currently shown on a chosen X11 output (the game's
 * monitor) and duplicates it into both halves of a fullscreen window on
 * the PSVR's HDMI output, so a monoscopic FPV sim looks like a duplicated
 * view instead of VR mode's raw left-half/right-half split (see
 * docs/display.md, step 6).
 *
 * Deliberately simple: no GLX, no compositing extension, no barrel
 * distortion. Each frame reads the source region with XShmGetImage and
 * writes it into both halves of the destination window with two
 * XShmPutImage calls. That's enough to satisfy step 10's success
 * criterion (a source appears duplicated in both eyes with correct
 * geometry); distortion and a lower-latency GPU-texture path are future
 * work if this turns out too slow or too blurry to be usable.
 *
 * Why XShmGetImage/XShmPutImage and not plain XCopyArea: XCopyArea is a
 * drawable-to-drawable blit limited to the classic X rendering model. On
 * this machine's driver stack (Intel iGPU, DRI3/Present), a client
 * window's actual rendered content is presented straight to the scanout
 * buffer and never lands in anything XCopyArea can read back from the
 * root window — copying from root silently produces solid black, no X
 * error, nothing in the logs. XShmGetImage asks the server to actually
 * rasterize the requested screen region (the same mechanism screenshot
 * tools like `scrot` use), which does see it correctly. Verified by
 * direct experiment: an XCopyArea-based version produced black, an
 * XGetImage/XPutImage-based version worked, and XShm is that same
 * mechanism with a shared-memory buffer instead of round-tripping full
 * frames through the X11 wire protocol every frame.
 *
 * Source output must be exactly 960x1080 and target exactly 1920x1080 —
 * no scaling step, by design (see the project's step 10 discussion).
 */

#define _DEFAULT_SOURCE
#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>
#include <X11/extensions/Xrandr.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>

#define EYE_WIDTH 960
#define EYE_HEIGHT 1080
#define FRAME_WIDTH 1920
#define FRAME_HEIGHT 1080

static volatile sig_atomic_t g_stop = 0;

static void handle_signal(int sig) {
    (void)sig;
    g_stop = 1;
}

typedef struct {
    int x, y, width, height;
} OutputGeometry;

/*
 * Looked up via RandR *monitors*, not raw outputs. Every connected output
 * gets an auto-named monitor for free (so "HDMI-1" as a target still just
 * works), but this also picks up virtual monitors created with
 * `xrandr --setmonitor NAME WxH+X+Y OUTPUT` — a named sub-rectangle of an
 * existing output's desktop, no separate physical resolution required.
 * That matters here: a laptop's internal panel (eDP) generally rejects a
 * non-native custom mode, so carving 960x1080 out of its normal desktop
 * with --setmonitor is the practical way to get a source region, instead
 * of forcing the panel itself to a mode it may not actually support.
 */
static int find_output_geometry(Display *dpy, Window root, const char *name, OutputGeometry *out) {
    int nmonitors = 0;
    XRRMonitorInfo *monitors = XRRGetMonitors(dpy, root, True, &nmonitors);
    if (!monitors) {
        fprintf(stderr, "error: XRRGetMonitors failed\n");
        return -1;
    }

    int found = 0;
    for (int i = 0; i < nmonitors && !found; i++) {
        char *mon_name = XGetAtomName(dpy, monitors[i].name);
        if (mon_name && strcmp(mon_name, name) == 0) {
            out->x = monitors[i].x;
            out->y = monitors[i].y;
            out->width = monitors[i].width;
            out->height = monitors[i].height;
            found = 1;
        }
        if (mon_name) XFree(mon_name);
    }

    XRRFreeMonitors(monitors);

    if (!found) {
        fprintf(stderr, "error: monitor '%s' not found (see: xrandr --listmonitors)\n", name);
        return -1;
    }
    return 0;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "usage: %s (--source-output NAME | --source-geometry X,Y) [--target-output NAME] [--fps N]\n\n"
        "  --source-output NAME    RandR monitor showing the sim (`xrandr --listmonitors`),\n"
        "                          must be exactly %dx%d. Picks up both real outputs and\n"
        "                          virtual ones made with `xrandr --setmonitor`.\n"
        "  --source-geometry X,Y   Read a %dx%d region straight off the root window at X,Y\n"
        "                          instead — no RandR monitor lookup, so it can't touch a\n"
        "                          live output's monitor definition. Position a plain\n"
        "                          %dx%d window there and point this at its top-left corner.\n"
        "  --target-output NAME    PSVR's output, must be exactly %dx%d (default: HDMI-1)\n"
        "  --fps N                 composite loop rate (default: 90)\n",
        prog, EYE_WIDTH, EYE_HEIGHT, EYE_WIDTH, EYE_HEIGHT, EYE_WIDTH, EYE_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT);
}

int main(int argc, char **argv) {
    const char *source_name = NULL;
    const char *target_name = "HDMI-1";
    int fps = 90;
    int have_source_geometry = 0;
    int source_geom_x = 0, source_geom_y = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--source-output") == 0 && i + 1 < argc) {
            source_name = argv[++i];
        } else if (strcmp(argv[i], "--source-geometry") == 0 && i + 1 < argc) {
            if (sscanf(argv[++i], "%d,%d", &source_geom_x, &source_geom_y) != 2) {
                fprintf(stderr, "error: --source-geometry wants X,Y (e.g. 100,100)\n");
                return 2;
            }
            have_source_geometry = 1;
        } else if (strcmp(argv[i], "--target-output") == 0 && i + 1 < argc) {
            target_name = argv[++i];
        } else if (strcmp(argv[i], "--fps") == 0 && i + 1 < argc) {
            fps = atoi(argv[++i]);
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if ((!source_name && !have_source_geometry) || (source_name && have_source_geometry) || fps <= 0) {
        usage(argv[0]);
        return 2;
    }

    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr, "error: cannot open X display\n");
        return 1;
    }

    int screen = DefaultScreen(dpy);
    Window root = RootWindow(dpy, screen);

    int rr_event_base, rr_error_base;
    if (!XRRQueryExtension(dpy, &rr_event_base, &rr_error_base)) {
        fprintf(stderr, "error: XRandR extension not available\n");
        return 1;
    }

    OutputGeometry src, dst;
    if (have_source_geometry) {
        src.x = source_geom_x;
        src.y = source_geom_y;
        src.width = EYE_WIDTH;
        src.height = EYE_HEIGHT;
    } else if (find_output_geometry(dpy, root, source_name, &src) != 0) {
        return 1;
    }
    if (find_output_geometry(dpy, root, target_name, &dst) != 0) return 1;

    if (src.width != EYE_WIDTH || src.height != EYE_HEIGHT) {
        fprintf(stderr, "error: source '%s' is %dx%d, expected exactly %dx%d\n",
                have_source_geometry ? "(geometry)" : source_name, src.width, src.height, EYE_WIDTH, EYE_HEIGHT);
        return 1;
    }
    if (dst.width != FRAME_WIDTH || dst.height != FRAME_HEIGHT) {
        fprintf(stderr, "error: target output '%s' is %dx%d, expected exactly %dx%d\n",
                target_name, dst.width, dst.height, FRAME_WIDTH, FRAME_HEIGHT);
        return 1;
    }

    if (!XShmQueryExtension(dpy)) {
        fprintf(stderr, "error: MIT-SHM extension not available\n");
        return 1;
    }

    XSetWindowAttributes attrs;
    memset(&attrs, 0, sizeof(attrs));
    attrs.override_redirect = True;
    attrs.background_pixel = BlackPixel(dpy, screen);

    Window win = XCreateWindow(
        dpy, root, dst.x, dst.y, FRAME_WIDTH, FRAME_HEIGHT, 0,
        CopyFromParent, InputOutput, CopyFromParent,
        CWOverrideRedirect | CWBackPixel, &attrs);

    XStoreName(dpy, win, "psvr-sbs");
    XMapRaised(dpy, win);
    XFlush(dpy);

    GC gc = XCreateGC(dpy, win, 0, NULL);

    XShmSegmentInfo shminfo;
    memset(&shminfo, 0, sizeof(shminfo));
    XImage *ximg = XShmCreateImage(dpy, DefaultVisual(dpy, screen), DefaultDepth(dpy, screen),
                                    ZPixmap, NULL, &shminfo, EYE_WIDTH, EYE_HEIGHT);
    if (!ximg) {
        fprintf(stderr, "error: XShmCreateImage failed\n");
        return 1;
    }

    shminfo.shmid = shmget(IPC_PRIVATE, (size_t)ximg->bytes_per_line * ximg->height, IPC_CREAT | 0600);
    if (shminfo.shmid < 0) {
        perror("shmget");
        return 1;
    }
    shminfo.shmaddr = ximg->data = shmat(shminfo.shmid, NULL, 0);
    shminfo.readOnly = False;

    if (!XShmAttach(dpy, &shminfo)) {
        fprintf(stderr, "error: XShmAttach failed\n");
        return 1;
    }
    XSync(dpy, False);
    shmctl(shminfo.shmid, IPC_RMID, NULL); /* safe once attached; segment lives until detach */

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    fprintf(stderr, "psvr-sbs: %s (%dx%d+%d+%d) -> %s (%dx%d+%d+%d), %d fps. Ctrl-C to stop.\n",
            have_source_geometry ? "(geometry)" : source_name, src.width, src.height, src.x, src.y,
            target_name, dst.width, dst.height, dst.x, dst.y, fps);

    long frame_us = 1000000L / fps;

    while (!g_stop) {
        if (!XShmGetImage(dpy, root, ximg, src.x, src.y, AllPlanes)) {
            fprintf(stderr, "warning: XShmGetImage failed, skipping frame\n");
            usleep(frame_us);
            continue;
        }
        XShmPutImage(dpy, win, gc, ximg, 0, 0, 0, 0, EYE_WIDTH, EYE_HEIGHT, False);
        XShmPutImage(dpy, win, gc, ximg, 0, 0, EYE_WIDTH, 0, EYE_WIDTH, EYE_HEIGHT, False);
        XSync(dpy, False); /* both Puts must finish reading ximg before the next Get overwrites it */
        usleep(frame_us);
    }

    fprintf(stderr, "psvr-sbs: stopping\n");
    XShmDetach(dpy, &shminfo);
    XDestroyImage(ximg);
    shmdt(shminfo.shmaddr);
    XFreeGC(dpy, gc);
    XDestroyWindow(dpy, win);
    XCloseDisplay(dpy);
    return 0;
}
