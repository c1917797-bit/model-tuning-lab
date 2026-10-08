# cache10r4 original-protocol quality attempt: actual 0–3 lane intrusion

Decision: **environment/isolation invalid**, not a HYPIC algorithm, performance,
or model-quality verdict. The candidate arm completed 0/127 LongBench-v2
samples and 0 scored rows. Do not launch a matching no-cache baseline for
this rejected root, reuse its rows, or retry into the same directory.

- User clarified that passive foreign Docker mappings do not block use of
  idle physical NPU0–3. The preflight found all 127 expected samples, the
  frozen source/weight/dataset identity, idle actual NPU0–3 processes, and
  free port 8223. It did not require empty foreign mappings.
- AWMCP direct chicaihong01/ma controller `exec-00000000000014c4` ran the
  unchanged original full-arm protocol with a unique `cache10r4` identity:
  2048 max output, 3 scored repeats, c8, TP4 physical0–3,
  gpu-memory-utilization 0.85, material cache 3584 MiB/10 segments.
  Immutable raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r4-full-hypic`.
- The exact owned service `b8d790f9b03e2b168de20aefec3d0aa94df3df12bc0a88e9321984c53cc552ad`
  became ready at 2026-10-08 15:46:20 UTC. During loading, a read-only
  snapshot at 15:44 showed extra actual NPU0/1 Python processes; a live
  cgroup read confirmed one on NPU1 belonged to `cannbench_ds`. This
  startup overlap is a caveat, not merely a device mapping.
- The continuous scoring guard took 13 samples and twice found foreign
  PID 1072000 on physical NPU0 at 15:47:15 UTC, with no probe errors.
  At exact owned-service cleanup, another real foreign PID 1078676 was
  on physical NPU2. The guard captured no reliable cgroup ownership for
  those transient PIDs, so do not attribute them to a named container.
- Guard SHA256:
  `d1e18d197653845919fe545679e0008e9acf858d430dd618303e10f471e7e1c3`.
  Arm-result SHA256:
  `1753f249cb185221baddb197022b7a6a8456e1da93f5d64923367a842d8baa5c`.
  Service-stop SHA256:
  `e8543c3e382e7f2bbae6aa1ffe280de67d341da87a5774dc86b0d7a7c32cb03f`.
  The stop receipt reports container removed, owned NPU workers released,
  and port 8223 released. A subsequent `docker inspect` found no owned
  container and `ss` found no listener on the port.

This repeats cache10r3's environmental failure despite correct permission
to start when the cards were idle. The missing ingredient is sustained
exclusive *actual* use during a long TP4 arm; no foreign mapping is itself
a veto. Continue productive offline verification and watch actual NPU PIDs.
Do not stop/modify `cannbench_ds` or touch NPU4–7. A later attempt needs
a fresh unique root and must retain the original protocol and isolation
checks; HYPIC success or failure remains undetermined.
