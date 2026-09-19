# Display verification

Status: steps 1-6 of the game plan run and confirmed on hardware
(2026-09-19). **Milestone 1 complete.**

## Machine

MSI Cyborg 15 A12V — Intel iGPU + Nvidia dGPU, no MUX switch (assumed).
HDMI port is physically wired to the iGPU; the dGPU renders and hands
frames to the iGPU for scanout (PRIME reverse offload). See "Known risks"
below.

## Procedure

```
xrandr --listproviders                 # confirm PSVR connector is under the Intel provider
drm_info                                # or: cat /sys/class/drm/*/status
edid-decode < /sys/class/drm/card*-HDMI-*/edid
```

## Results (this machine, 2026-09-19)

- Connector: `HDMI-1` (DRM `card1-HDMI-A-1`) — same card as `eDP-1`, the
  laptop's built-in panel. Confirms the HDMI port is wired to the Intel
  iGPU, not the Nvidia dGPU, on this MSI Cyborg 15 A12V (no MUX switch).
- `xrandr` mode list once connected: `1920x1080` at `60.00 / 50.00 / 59.94
  / 24.00 / 23.98` Hz — matches the spec's predicted EDID (VIC 16 native
  plus 50/24 Hz) exactly.
- `psvr-display probe`: `bcdDevice=0x0107` — matches the 2016 wiki dump.
- `psvr-display on` confirmed via `0xF0` status poll, exit 0. USB-only
  power-on works; video required a separate `xrandr --output HDMI-1
  --auto` before the headset showed anything but a "no HDMI" indicator.

- Mode switching (step 4), confirmed visually on hardware:
  - `psvr-display mode --mode cinematic`: floating screen. This is the
    PU's power-on default — sending it again from an already-cinematic
    state is a visible no-op, as expected.
  - `psvr-display mode --mode vr`: raw edge-to-edge split, left half of
    the 1920x1080 frame to the left eye, right half to the right eye,
    no overlap. Confirms Known Problem #9 exactly — correct behaviour
    for a plain 2D frame in VR mode, not a bug. Needs Mode B's SBS
    renderer (`psvr-sbs`, step 10) to look like a duplicated view.
  - `psvr-display off`: screen goes dark, PU stays enumerated on USB
    (kernel driver released/reattached cleanly, not unplugged).

## EDID (step 5, `edid-decode` on this machine)

```
Manufacturer: SNY
Model: 27140 (0x6a04)          <- spec/wiki predicted "b403" — DIFFERENT
Made in: week 38 of 2017        <- spec/wiki predicted week 48/2014 — DIFFERENT
Display Product Name: 'SIE  HMD *08'
Native mode: 1920x1080@60, VIC 16, 148.5 MHz — CONFIRMED
Also advertised: 1080p50 (VIC31), 1080i50/60 (VIC5/20), 1080p24 (VIC32),
                 720p50/60 (VIC4/19), 480p (VIC1/2/3), 576p (VIC17/18)
Max TMDS clock: 150 MHz         <- CONFIRMED, matches spec exactly
No 90/120 Hz mode advertised    <- CONFIRMED, matches spec exactly
```

The model code and manufacture date differ from the PSVRFramework wiki's
2016 dump. `bcdDevice` (`0x0107`) still matches, so USB-level firmware is
the same generation, but this specific PU's EDID reports a 2017
manufacture week — plausibly a CUH-ZVR2 unit (the second hardware
revision, Known Problem #6) rather than the ZVR1 the wiki documented.
Doesn't change anything about the protocol or the video-routing
behaviour — everything else in the EDID matches the spec's predictions
exactly — but it's worth having on record for anyone chasing the 90/120
Hz question later, since firmware/hardware-revision differences are
exactly the kind of thing that could explain a result diverging from
what's documented.

## Test image (step 6, `assets/testpattern-1920x1080.png`)

Displayed fullscreen via `feh --fullscreen` (mirrored `eDP-1`/`HDMI-1`,
both at `+0+0`). In VR mode: left eye shows the left-half content (blue
background, "L" label), right eye shows the right-half content (red
background, "R" label) — correctly mapped, not swapped. Confirms the
panel's left/right halves correspond to the naive left-half-of-frame /
right-half-of-frame split, which matters for building `psvr-sbs` (step
10) correctly later.

## Known risks / findings

- **PU disconnects from USB entirely if no HDMI signal arrives within
  roughly 90s of power-on.** Observed via `dmesg`: PU enumerates, sits
  idle with no video, then `USB disconnect` at ~95s uptime-relative. Not
  documented in OpenHMD, Monado, psvrd or the wiki. Practical
  consequence: `psvr-display on` (or `fpv`) must be followed promptly by
  activating the HDMI output, not run standalone with video set up later.
  `fpv` (step 8) should likely drive the xrandr activation itself, or at
  minimum the docs must say to run them back-to-back.
- Optimus/PRIME copy per frame may add latency; expect to measure, not assume.
- EDID declares max TMDS clock 150 MHz — relevant once step 7 (90/120 Hz) starts.
