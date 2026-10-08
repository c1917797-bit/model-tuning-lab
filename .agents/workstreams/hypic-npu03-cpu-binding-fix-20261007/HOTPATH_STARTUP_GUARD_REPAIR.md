# Physical NPU0–3 startup guard repair (prospective)

cache10r3 and cache10r4 both began with idle physical NPU0–3 and later
encountered actual foreign NPU processes. cache10r4 spent about seven
minutes loading before its scoring-phase guard rejected a foreign PID at
0/127 completed samples. This is an isolation/control-plane failure;
neither root is a HYPIC quality or algorithm verdict.

For the next fresh original-protocol attempt, the same 10-second guard
starts immediately after exact owned-container creation, before model
loading. During loading it recognizes only PIDs whose live cgroup matches
the exact owned container ID; other actual NPU0–3 PIDs and probe errors
fail closed. The service-health loop checks the guard at each poll, so a
collision can terminate during loading rather than waiting for service
readiness. After health, four proven worker PIDs are added to the guard.
The existing scored-request guard continues unchanged.

The exact-owned cleanup path now supports a pre-health abort: capture
the running container's host PIDs with `docker top`, stop/remove only that
container, verify those PIDs are absent from NPU0–3 and port 8223 is free,
write a stop receipt with `service_reached_health=false`, and separately
report whether the shared lane is still occupied. If PID capture fails,
the release proof is marked false rather than silently claiming success.

The proposed cache10r5 keeps the frozen model/source/weight/dataset,
TP4 physical0–3, cpuset, service flags, explicit segment boundaries,
2048 max output, c8, 127×3 samples, and 3584 MiB/10-segment cache. It
changes only admission/isolation monitoring and unique artifact identity.
Offline regression includes exact-owner cgroup exemption, foreign PID
capture, startup-loop fail-fast, and pre-health exact-owned cleanup.
No NPU result or model-quality pass is claimed for this repair yet.
