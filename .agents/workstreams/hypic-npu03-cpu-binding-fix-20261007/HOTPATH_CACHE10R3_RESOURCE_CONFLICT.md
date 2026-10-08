# cache10r3 original-protocol quality attempt: real NPU3 collision

Decision: **environment/isolation invalid**, not a HYPIC algorithm or
model-quality result. The full HYPIC-only LongBench-v2 127-sample,
three-repeat, 2048-output, c8 arm produced 0 completed samples and 0 scored
rows. Do not launch a matching baseline for this rejected root.

- Controller: AWMCP exec-000000000000147b, exit 1, target
  chicaihong01/ma; work branch commit at launch
  1b6dd816c138b6f61b8de0926e65ddaecb6e3fc7.
- Immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r3-full-hypic.
- At launch, physical NPU0–3 and port 8223 were idle. Other containers'
  device mappings were deliberately not treated as usage.
- Owned service ID:
  86e8b26af066f94959418e6de5e4351c4ec87b0ca9af06331f5d1ccdbf4c3948.
  Its physical NPU0–3 worker PIDs were 641320–641323.
- The owned service became ready at 2026-10-08 15:09:28 UTC. The first
  continuous guard sample at 15:09:30 recorded a foreign PID 672924 on
  physical NPU3. Its cgroup identified container
  efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6,
  named cannbench_ds. This is actual occupancy, unlike a passive mapping.
  The guard had no probe error.
- Guard receipt SHA256:
  4ee35d98eadbeda8344d8b14f747865a9f2e3587606f48243b1559dc9740d6db.
  Arm-result SHA256:
  75fa7b0586cd6af3633e591d6c51c5f4786910bce7c31d53e4207a872f267b34.
- The controller stopped and removed only its exact owned container.
  service-stop.json proves container_removed, owned_npus_released and
  port_released true. It also records the foreign PID and
  lane_available false at cleanup. Stop receipt SHA256:
  a264fd7c7e13cdc4c56ecc72ad4c7f3cb9cf0b0573c7405fd223abd8368629d1.
  Later read-only inspection found the owned container absent and port free.

This failure proves why idle-at-launch alone cannot guarantee a long
uninterrupted TP4 experiment when another container intermittently runs
real kernels on the same physical devices. Keep the full rejected root for
audit. Do not retry into the same root, reinterpret the absence of scored
requests as a quality score, alter cannbench_ds, or use NPU4–7. Continue
offline acceptance work and obtain a sustained clean NPU0–3 window before
a new full original-protocol paired attempt. The optional split protocol
remains unapproved.
