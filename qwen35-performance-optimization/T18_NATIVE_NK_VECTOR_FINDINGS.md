# T18 native-NK vector reductions: device evidence and bounded closure

Date: 2026-09-11. Branch-local, uncommitted. No service promotion.

## What actually executed

Pinned image: sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
Physical NPU0 only, NPU0-3 full-lifetime cooperative lock, >=48 GiB host
available and active-device reservation checks. No custom OPP or runtime SO;
Triton/cache files are isolated per output root. External NPU4-7 work untouched.

Initial attempt:
`/cache/austinov/qwen35-t18-nk-vector-20260911-01/gateup-screen-20260911T1002Z`.
BN1 numerical check passed. BN4 full K8192 padded block failed compiler UB
planning: 1835008 bits required, 1572864 available. No timings; BN8 not reached.

Successor r2:
`/cache/austinov/qwen35-t18-nk-vector-r2-20260911/gateup-screen-20260911T1006Z`.
Full-K BN1/2 and chunked BN4/8 BK1024 all compile and pass numerical plus
graph replay. The K loop bounds live storage without changing the logical
matrix-vector product. Eight offline contracts pass in the pinned image.

R2 profile:
`/cache/austinov/qwen35-t18-nk-vector-r2-20260911/gateup-profile-20260911T1008Z`.
Graph IDs 2/3/4/5 map in captured order to BN1-full, BN2-full, BN4-BK1024,
BN8-BK1024. BN8 mean AIV time 103.480 us includes overlapping vector 73.636,
MTE2 57.663, scalar 13.146, MTE3 4.508 us. This is diagnostic attribution,
not a sum of independently removable costs or accepted performance timing.

Profile-grounded r3:
`/cache/austinov/qwen35-t18-nk-vector-r3-20260911/gateup-screen-20260911T1011Z`.
Two new configurations BN16/BK512 and BN32/BK256 keep BN*BK=8192 while
reducing the final reduction length and logical output-block count. Both
compile and pass numerical/graph checks. Prior BN8 is diagnostic control,
not a reopened final candidate. Eight offline contracts pass.

## Scope of numerical evidence

One K5120 N8704 normal-distribution BF16 matrix and BF16 vector, seed1024.
Every output compared with CPU FP64 computation rounded to BF16, tolerance
0.005 + 0.005*abs(reference), reject nonfinite. Six distinct compiled configs
passed eager and NPUGraph checks. Multiple seeds, production activation
distributions, tail shapes and full model quality remain untested. Do not
turn this canary into an all-357 or general precision guarantee.

## Non-profiler performance screen

Each value is the median of three per-repeat medians, each with twenty raw
NPU-event samples. All variants use NPUGraph. Cold follows a synchronized,
distinct 512 MiB weight-reading MatMul before each sample; this is a defined
eviction protocol, not proof of the full-model hardware cache-miss state.

| Round | Variant | Hot us | Cold us |
|---|---|---:|---:|
| r2 | stock native NK | 75.070 | 149.760 |
| r2 | full BN1 | 421.780 | 416.570 |
| r2 | full BN2 | 229.770 | 234.760 |
| r2 | BN4 BK1024 | 143.650 | 161.320 |
| r2 | BN8 BK1024 | 115.920 | 165.810 |
| r3 | stock native NK | 61.320 | 138.470 |
| r3 | BN8 BK1024 | 101.650 | 150.010 |
| r3 | BN16 BK512 | 96.260 | 150.590 |
| r3 | BN32 BK256 | 90.910 | 146.790 |

Compare only within the same round. Controls varied across rounds; the r3
last repeat also shifted, with BN16/32 near equal to NK rather than clearly
slower. Their first two repeats are slower and none clears the registered
>=10% cold-weight operator progression screen. This threshold is NOT the
service's corrected >=10% TPOT and >=20% TTFT acceptance target.

R2 stores 720 raw samples; r3 stores 600. KN layout controls are retained in
the raw records; they do not justify a weight-layout win in these screens.

## Decision and provenance

Stop this configuration family before service integration. Do not expand to
the full matrix or all-357 for unchanged bytes. This closes tested tilings,
not every possible native NK or GEMV design.

R2 VALIDATED_SCREEN_DECISION.json SHA256:
dd249d7782bab75dd7ffc4dda244781a8b312dbd55c21c2d76bef405adeead82.
R3 VALIDATED_SCREEN_DECISION.json SHA256:
91907db33c40ad82a9efd15be4e95974ebe929178395c3a6ece7c1f465289d5c.
Both are under the respective external r2/r3 roots named above.
The evaluator validates raw sample counts, finiteness, repeats, numerical
markers, exact harness hash, graph mode and cleanup; it rejects profiled
timings and never grants service promotion. Its device-free tests cover
missing/duplicate cells, NaN/Inf, wrong medians and mixed timing modes.

## Next admission, not an implemented successor

Use exact T16 exclusive budget and actual input layouts to assess a different
memory-transfer or pipeline mechanism before generating another operator.
Do not keep scanning BN/BK. Source admission also found the referenced
TLA BlockGemv AIC calls TileMmad with L1XAlignHelper::M_ALIGNED rather than
simply passing M=1. A class name or absent disableGemv assignment alone is
insufficient native-M1 proof; inspect the resolved helper/launch and device
trace. A compute-only improvement cannot be advertised as removal of the
whole weight-transfer bottleneck.

Keep T16 TTFT evidence, T17 negative results and current source snapshots.
No commit/push, framework or image mutation, network changes, or final goal
attainment is claimed. Resume from these records, not the old resource blocker.
