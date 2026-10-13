# Current 4429e35 descriptive performance — frozen prospective plan

User explicitly authorized three same-source paired performance rounds after
r19 LongBench rejection. This is NOT a quality pass, deployment approval,
new algorithm, observer experiment, or new full-quality run.

Source: /cache/cch/hypic_vllm_ascend-hotproof-20261008,
4429e35177979c874bf053ab29789e4773f39b22, clean checkout, unchanged image.
Use existing matched service and benchmark primitives, hash-pinned by
current_source_performance_20261013.py; do not edit frozen helpers or old roots.
Legacy r13 schema names are reused record FORMATS only, never r13 identities.
New campaign: current4429-performance-20261013. Each new root is exclusive.

Protocol: physical NPU0–3, TP4, CPU112–191, CPU binding disabled, context41984,
memory0.85, material cache3584MiB/10 segments. Input32768/shared prefix16384,
explicit boundaries[16384,32768], output exactly1024, concurrency16,
40 measured plus2 concurrent one-token warm requests. Temperature0,seed0,
ignoreEOS. The max2048 quality protocol remains unchanged and already terminal.

Frozen order: no-cache/screen, hypic-only/screen, hypic-only/repeat2,
no-cache/repeat2, no-cache/repeat3, hypic-only/repeat3.
Each phase is independently audited before the next. No performance gain
threshold is an admission gate: the purpose is descriptive measurement.
Report all40 requests per arm/round; report four-worker hot coverage separately,
never remove cold/unproven rows to inflate speed.

Entry: fresh ma resolution, loaded host-development, forced direct target proof,
actual physical0–3 idle and8223 free, new root absent, exact source identity.
Continuous existing guard records foreign processes; stop only exact owned
service on contamination and preserve invalid evidence. No foreign mutations,
no physical4–7. Passive device mappings are not occupancy.
No automatic retries or resumption of any completed/partial root.

Independent audit:40 fixed1024 rows,42 unique IDs, recomputed TPOT/TTFT/throughput,
actual mounted source hash, four physical workers/PID namespace relation,
continuous isolation, exact owned container/port release, one-switch paired
configuration. Aggregate medians/three paired deltas and full per-round metrics.
Quality remains REJECT_OR_QUALIFY (227/381 versus219/381), deployment false.
R19 audit SHA256:
40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b.

Target six phases~90–120min if continuously idle; inspect after each stage.
Fixed overall deadline2026-10-13T08:47:14Z remains; do not reset it.
No new starts after deadline. Failures/blockers are reported, not converted
into success or hidden by retries. Runtime performance does not retroactively
repair r19 quality or all29 Skills. Unchanged origin credentials are not retried.

