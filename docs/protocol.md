# PSVR1 Processing Unit — USB control protocol

Confidence levels: **confirmed** (read in source + cross-checked against a
second source), **reported** (single source, not independently verified),
**unknown** (must be tested on hardware).

## USB identity

```
idVendor  0x054c   idProduct  0x09af   bcdDevice  0x0107 (2016 dump; log this per device)
```

Interface 5, "PS VR Control" (HID): endpoint `0x84` interrupt IN, `0x04`
interrupt OUT, 64 bytes each. This is the only interface this project
touches. Interface 4, "PS VR Sensor", carries the IMU stream and is not
used. Detaching the kernel driver from any interface other than 5 will
break PSVR audio.

## Packet format

`[0] register · [1] sub-register (send 0x00) · [2] 0xAA magic · [3] payload length (4|8|16)`,
then the payload. Written whole to endpoint `0x04` as an interrupt transfer.

| Action | Bytes | Confidence |
| --- | --- | --- |
| Headset on | `17 00 AA 04 01 00 00 00` | confirmed x3 |
| Headset off | `17 00 AA 04 00 00 00 00` | confirmed x3 |
| VR mode on | `23 00 AA 04 01 00 00 00` | confirmed x3 |
| Cinematic mode (VR mode off) | `23 00 AA 04 00 00 00 00` | confirmed x3 |
| PU power off | `13 00 AA 04 01 00 00 00` | reported (psvrd, pyPSVR) |
| Recentre cinematic screen | `1B 00 AA 04 00 00 00 00` | reported (pyPSVR) |
| Cinematic screen settings | `21 00 AA 10` + 16 bytes | reported, field meanings provisional |

`0x21` payload: byte 0 = `0x00` locked / `0x40` free, byte 1 size 26-100
(default 52), byte 2 distance 20-50 (default 35), byte 3 "mist" 1-40
(default 20), byte 10 brightness 1-32 (default 20), byte 12 social-screen
resolution 0-4, rest zero. Out-of-range values produce a device-side
"Bad sidetone value" error report; `protocol.py` validates before sending.

**Contradiction found in the wild:** OpenHMD's `psvr_power_on` sends
`17 76 AA 04 01 00 00 00` — byte 1 is `0x76`, where Monado and this project
send `0x00`. Both are reported to work; byte 1 appears ignored for
command `0x17`.

## Status report 0xF0

20 bytes, sent unsolicited on `0x84`. Skip the 4-byte header.

```
byte 4   status bitfield
  bit 0  powered on
  bit 1  HMD worn
  bit 2  cinematic mode active
  bit 4  headphones connected
  bit 5  mic muted
byte 5   volume
byte 8   display-on time, minutes
```

Monado's `psvr_device.h` also tracks a separate VR-mode on/off value; its
exact byte offset within this packet was **not** determined from any
source examined. `device.py` currently confirms VR-mode-on by the inverse
of the cinematic-mode bit — treat as a proxy, not a confirmed field, until
verified against a hardware log.

## Timing

No fixed delays are documented anywhere. Pattern copied from Monado's
`control_power_and_wait()` / `control_vrmode_and_wait()`: send, then poll
for a status report every 1 ms, up to 5000 iterations (~5s timeout). No
periodic keepalive is required — confirmed by its absence in OpenHMD,
Monado and psvrd alike; the PU holds its mode until told otherwise or
unplugged.

## Sources

| Source | Used for |
| --- | --- |
| [PSVRFramework wiki — USB Interfaces](https://github.com/gusmanb/PSVRFramework/wiki/USB-Interfaces) | descriptor dump, interface roles, endpoints |
| [PSVRFramework wiki — Video routing and EDIDs](https://github.com/gusmanb/PSVRFramework/wiki/Video-routing-and-EDIDs) | EDID, cinematic vs VR mode behaviour |
| [PSVRFramework wiki — USB Command Response Format](https://github.com/gusmanb/PSVRFramework/wiki/PSVR-Control:--USB-Command-Response-Format) | 4-byte header layout, error reports |
| [OpenHMD `drv_psvr`](https://github.com/OpenHMD/OpenHMD/blob/master/src/drv_psvr/psvr.c) | command constants, interface numbers, the `0x76` anomaly |
| Monado `drv_psvr` (via [`shinyquagsire23/monado`](https://github.com/shinyquagsire23/monado) mirror) | init order, status polling, `0xF0` bitfield |
| [psvrd](https://github.com/ronsaldo/psvrd) | libusb approach, endpoint numbers, MIT licence |
| [pyPSVR](https://github.com/mungewell/pyPSVR) | `0x21` field ranges, PyUSB precedent — facts only, code not reused (GPL-2.0) |

## Licensing note

Protocol bytes are facts about a device, not copyrightable expression.
This file and `protocol.py` were written from these facts, not copied
from any project's source. pyPSVR (GPL-2.0) and PSVRFramework (AGPL-3.0)
code specifically was not reused anywhere in this repository.
