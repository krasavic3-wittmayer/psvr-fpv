# FPV simulator integration

Status: **not started.** This is step 9 of the game plan (optional,
after milestone 1 and after step 7's refresh-rate result are known).

Will document, for one named simulator: how to force it fullscreen on
the PSVR output, and how `psvr-display fpv` fits into the launch
sequence (`--lock/--free`, `--size`, `--distance` passthrough to the
cinematic screen).

Open question carried from the main risk list: on this machine the sim
likely needs to render on the dGPU (`__NV_PRIME_RENDER_OFFLOAD=1` or
equivalent) while the PSVR output is driven by the iGPU. Measure the
added latency before treating any sim as usable.
