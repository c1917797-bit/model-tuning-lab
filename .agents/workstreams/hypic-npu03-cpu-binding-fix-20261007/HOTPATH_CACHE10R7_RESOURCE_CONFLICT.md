# cache10r7 full HYPIC arm — actual NPU3 collision before health

- Target: chicaihong01/ma; original full HYPIC protocol on physical NPU0–3, 127 samples and 2048-token output. Foreign Docker device mappings alone did not block launch.
- The first launch (`exec-000000000000151d`) exited before creating a root because the campaign allowlist only reached r6. The r7 campaign and artifact mapping were added, 35 offline tests passed, then the sole real controller `exec-0000000000001523` launched after an actual-idle probe.
- Artifact root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r7-full-hypic`.
- At `2026-10-08T16:28:11.364038Z` and `16:28:13.042499Z`, the startup guard observed foreign PID `1482057` on physical NPU3. The PID belonged to container `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`; probe errors were empty.
- The guard stopped before health and scoring: `0/127`. This is environment/isolation-invalid, **not** a HYPIC quality or algorithm verdict. Do not reuse or pair this root.
- Exact owned container `ddd9dbff746a437b5cb27d5c03b806d57833cd7c099a163a952e7168f4e3240a` was removed. Stop receipt confirms owned NPUs and port 8223 released. It reports `lane_available=false` solely because the foreign NPU3 process was still present. The foreign container was not modified.

Immutable raw-artifact SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `contract.json` | `89490d2b45967cffe3296242e16292f61004a58005f50e6fab13e7893545fa48` |
| `arm-result.json` | `746b15ad1fdbc3ccbd26622f122ab248702b66368d043e8b04d23996488546ea` |
| `hypic-only/lane-guard.json` | `d0edf3ed3216b43819c5b1215e6005ebb687b9e2ea2b151d1cbcb6411cbe2952` |
| `hypic-only/service-stop.json` | `9ea958e1656b6be13bb63aa485adaf558a94c1d85c6afbca740bc6b5f2972a94` |

cache10r6 and r7 both began after physical NPU0–3 were idle, but a real foreign worker appeared during service startup. More immediate retries under the same shared scheduling conditions would repeat invalid work. A long exclusive window for physical NPU0–3 is needed for the full matched protocol; do not treat passive mappings as a conflict, and do not stop the foreign workload without authorization.
