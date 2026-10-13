# Current-source screen pair — 2026-10-13

Source4429e35177979c874bf053ab29789e4773f39b22; frozen image/Qwen3.6-27B
TP4 physical0–3; input32768/shared16384/fixed output1024/c16/40 requests.
Candidate immutable root:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-current4429-performance-20261013-hypic-only-screen

Terminal06:10:03UTC valid=true. Controller02a3 expired afterward; not a failure.
Independent audit02ab exit0 checks40/40 fixed rows,42 unique IDs,40/40
explicit-boundary joins and four-worker hot proofs, source identity,164 clean
isolation samples and exact owned release. Baseline02a1 likewise independently
valid. Neither root is rerun or changed.

Metric | Baseline | HYPIC
--- | ---: | ---:
Weighted TPOT ms/token | 75.61811296 | 58.33108782
TPOT P95 ms/token | 112.48249252 | 78.25055296
TTFT P95 ms | 88505.27276 | 45021.40591
Output tokens/s | 100.64426347 | 134.47501979
Measured duration s | 406.97798950 | 304.59188677

Single-pair weighted TPOT reduction22.860958%, TTFT P95 reduction49.131386%,
throughput increase33.614192%. Not the three-round aggregate; no quality pass.
r19 REJECT_OR_QUALIFY/deployment false remains.

Candidate hashes:
result f263c1122102ccb993ddd720de077aab5307572178908a0675a977692fcaf68e
performance eccee3883fa985fb363f2e209ba76f5582f45de1909e39cef0e342835d815e47
contract b7647c70d1373a6d539a608fee633e3b116dfa43bb9197d98402f3b4e9114e95
evidence af5c19fd2d5b1ba7378eceed04392387a3af1998aba6aae4e9073e50583e7519

Fresh admission02ad: prior phases valid,physical0–3/8223 idle,new repeat2 root
absent,source clean,cache free121625956352bytes. Forced-direct launch02af starts
hypic-only/repeat2; no other runtime changes. Next no-cache/repeat2,
no-cache/repeat3,hypic-only/repeat3 then independent aggregate.
Deadline08:47:14UTC unchanged; no remote auth retries or main-sync claim.

