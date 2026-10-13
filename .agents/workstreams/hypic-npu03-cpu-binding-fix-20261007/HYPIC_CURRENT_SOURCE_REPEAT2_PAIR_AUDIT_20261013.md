# Current4429 second paired performance round — independently valid

Protocol frozen in HYPIC_CURRENT_SOURCE_PERFORMANCE_PLAN_20261013.md:
physical0–3,TP4,input32768/shared16384,fixed1024 output,c16,40 measured
requests plus2 one-token warmups per arm. Identical runtime source4429e35.

| Metric | no-cache | HYPIC | Change |
| --- | ---: | ---: | ---: |
| Weighted TPOT ms | 74.74103170674458 | 58.41951318548415 | -21.8374274% |
| TTFT P95 ms | 89404.3560900027 | 45016.32172000245 | -49.6486260% |
| Output tokens/s | 102.17587149636084 | 134.63074501363513 | +31.7637355% |

Baseline controller02bc exit0,released07:05:56UTC; independent audit02c3 exit0.
40 rows/42 IDs,172 clean guard samples,source and exact owned release verified.
Baseline root /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-current4429-performance-20261013-no-cache-repeat2
Result SHA256 428d8440b6d03919e65016206583c07fd3c8ce7a528a2fc5cb2f8c22e7019f5d
Performance SHA256 545a4fddfa86f926b9662e3bbe15c012d09a1e7c6d6f8ab784ba494f3ef29dc6
Contract SHA256 29c4e3d96eeebe4ba9432089848c82c95204cbc0c4e2dd878ba6d0495a8fcd78

Candidate independent audit02b9 exit0,40/40 four-worker hot proof,162 clean
samples and exact release; hashes in HYPIC_CURRENT_SOURCE_REPEAT2_CANDIDATE_AUDIT_20261013.md.
All requests retained. This is round2,not the three-round aggregate.
The r19 quality REJECT_OR_QUALIFY remains; no deployment or29-Skill acceptance.

After fresh direct admission02c4,baseline repeat3 controller02c5 launched.
Deadline2026-10-13T08:47:14Z unchanged; app automation absent, not recreated.

