# Display verification

Status: **not yet run on hardware.** This is step 5 of the game plan —
fill in after connecting the PU and running the commands below.

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

## To fill in

- [ ] Connector name (e.g. `HDMI-1`, `HDMI-A-2`)
- [ ] DRM provider owning that connector (Intel iGPU, confirmed or not)
- [ ] Decoded EDID: manufacturer/model/monitor name match `SNY` / `b403` / `SCEI`?
- [ ] Native mode confirmed: `1920x1080@60`, VIC 16
- [ ] `bcdDevice` from `psvr-display probe` (expect `0x0107`; note if different)

## Known risks going in

- Optimus/PRIME copy per frame may add latency; expect to measure, not assume.
- EDID declares max TMDS clock 150 MHz — relevant once step 7 (90/120 Hz) starts.
