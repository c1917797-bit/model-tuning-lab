# cache10r5: prospective startup guard caught a real competing NPU task

Decision: **environment/isolation invalid**, not a HYPIC algorithm or
quality verdict. The fresh original-protocol HYPIC-only full arm completed
0/127 LongBench-v2 samples and 0 scored rows. Do not pair it with a
no-cache baseline or reuse its root for another attempt.

- At 2026-10-08 15:56:54 UTC, physical NPU0–3 had no actual process;
  a first launch was rejected during preflight because a real process
  appeared before any root/container was created. After a fresh read-only
  check again found 0–3 idle, the second launch proceeded as AWMCP
  `exec-00000000000014ee` at 15:58:37 UTC. Passive foreign Docker
  mappings were ignored as the user directed.
- Exact owned container:
  `54dad9c627f40097c97fb6a43f8aed8a4df8d6d9937895ce0e56dae47dbeea69`.
  Immutable raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r5-full-hypic`.
  The model never reached service health; this is a startup, not scoring,
  collision.
- The prospective guard sampled the loading interval 14 times. At
  15:59:47 and 15:59:48 UTC it recorded PID 1206204 on physical NPU2,
  live cgroup container ID
  `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`
  (`cannbench_ds` from the earlier exact Docker inspection). There were
  no probe errors. The ID differs from our exact owned container.
- The controller exited 1 after about 135 seconds. Guard SHA256:
  `e38d1e80b0e20ab85fe8d856030392896401122fcfa187dda0f31282f1b89d35`.
  Arm-result SHA256:
  `91761a2fc2df538a5e7e561f1b75a9c38173e84e39a2d1ac6dcec3624d9b0c2c`.
  Pre-health service-stop SHA256:
  `3497295f411bfdda92c7450fed0c1bbb9a80e6bdb52a47158effd9fcf3c91372`.
  The stop receipt says `service_reached_health=false`, exact container
  removed, owned NPU processes released, port 8223 released, and no
  pre-health process-capture error. No foreign container was changed.

This is the first live evidence that the repaired guard can stop a
startup collision before paying the previous seven-minute service-load
cost, while preserving exact-owned cleanup. It does **not** validate the
full 2048-token quality ruler, HYPIC hot-path activation, or matched
performance. The competing workload continued to launch real NPU0–3
processes after cleanup, so a momentary idle snapshot alone is not a
reasonable trigger for another costly full attempt. Continue offline
Skill acceptance and resume with a fresh unique original-protocol root
when actual physical NPU0–3 use is sustainably clear. NPU4–7 remain out
of scope.
