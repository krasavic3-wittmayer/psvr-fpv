# psvr-sbs

Side-by-side compositor for PSVR VR mode. Duplicates whatever's on a
chosen screen region into both eyes, so a monoscopic FPV sim looks like
a duplicated view instead of VR mode's raw left-half/right-half split
of a plain 2D frame (see `../docs/display.md`, step 6).

Optional, separate from `psvr-display` — see Spec 9/10 in
`../psvr-display-spec.md` for why this is its own small C program
instead of Python.

## Build

```
make
```

Needs `libx11`, `libxrandr`, `libxext` (MIT-SHM) development packages.

## Usage

Put the PU in VR mode first (`psvr-display mode --mode vr`) and make
sure `HDMI-1` (or whatever your PSVR output is named) is active at
exactly 1920x1080.

Your source — the sim's rendering — must be exactly 960x1080, with no
scaling done by this program (see the project's step 10 discussion for
why: simplest, lowest-latency V1).

```
./psvr-sbs --source-output NAME [--target-output HDMI-1] [--fps 90]
./psvr-sbs --source-geometry X,Y [--target-output HDMI-1] [--fps 90]
```

- `--source-output NAME` — a RandR monitor (`xrandr --listmonitors`)
  showing the sim. Works for a real second output, or a virtual one
  carved out with `xrandr --setmonitor NAME 960x1080+X+Y OUTPUT`.
  **Caution:** don't `--setmonitor` your primary/laptop output (`eDP-1`)
  while your desktop is live — see "Known issues" below.
- `--source-geometry X,Y` — reads a 960x1080 region straight off the
  root window at that position instead, no RandR monitor involved.
  Position a plain 960x1080 window there (e.g. your sim, windowed) and
  point this at its top-left corner. The safer option.

Ctrl-C to stop.

## How it works

Each frame: `XShmGetImage` reads the source region into a shared-memory
buffer, then two `XShmPutImage` calls write it into both halves of a
fullscreen `override_redirect` window on the target output. No GLX, no
compositing extension, no distortion correction — see the top-of-file
comment in `main.c` for the full reasoning and for **why this doesn't
use plain `XCopyArea`**, which silently produces solid black on this
driver stack (worth reading if you're modifying this).

## Known issues

- **Don't use `xrandr --setmonitor` on a live desktop's primary output
  as the source.** During development, redefining `eDP-1`'s RandR
  monitor while the desktop was running was followed by a hard system
  freeze requiring a reboot — correlation, not proven causation (a
  second freeze that looked similar turned out to be unrelated, an
  accidentally-killed IDE), but not disproven either. `--source-geometry`
  avoids touching any live output's monitor definition entirely and is
  the tested, working path.
- No scaling: source must be exactly 960x1080. Feed it a mismatched
  size and you get incorrect output, not an error.
- No barrel/pincushion pre-distortion. The lenses will show some
  distortion; whether that matters enough to build the shader is
  unmeasured.
