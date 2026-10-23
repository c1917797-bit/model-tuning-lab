# BACKUP B: MXR / Good Enough solve seam

Finite source-only successor, not ready for devices. This packet does not modify
old sources, renew an old ticket, install a model plugin, or claim paper success.
Current overall cutoff remains2026-10-24T07:35:53Z; MAIN owns physical4–7.
The selected next experiment uses only physical6→logical0, not protected0–3.

## Actual path and evidence

Current native2k SOURCE_BOUND records gdn.py SHA d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816.
Copied native chunk.py/solve_tril.py have SHA6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5 /
2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0.
chunk.py67–80 builds FP32 KKT A then calls its module-global solve_tril,
requesting k.dtype (BF16 here). Existing official vLLM-Ascend already supplies
Triton16x16 solve plus64x64 merge. MXR must replace that actual imported binding;
changing another module or claiming an all-fallback run would not test it.
Decode uses the native recurrent path: this is a prefill/TTFT opportunity, not
a demonstrated TPOT improvement.

Saved real four-rank native profile (Oct14) has48 solve+merge calls per rank.
It used32768/prefix16384/C16 and outputs256; not current2k/fixed1024 acceptance
and not a critical-path or10% throughput upper bound:
 /cache/cch/qwen36-paper-portfolio-synthesis-20260920/new48h-dense-profile-20261014-002/service/independent-diagnostic.json

MXR official MegaGDN PTO revision d357fd38608f99ddf9b9fb2d217b2e731ecd3a72 and
compiled tri_inverse_jit_MEMORY_BASE.so (SHA1a518ef0603d266d3d62218d0a30a97e14618a7657faf6ab586f417ca59267af)
already exist. Official FP16 input differs from service FP32 A; existing
mixed/residual adapter and actual saved2048 inputs must be reused and validated,
not replaced with another FP16 toy test.
The actual125 three-frame native-relative output/state gates passed for original
saved candidate and third-residual variants; independent canonical gates were
not all satisfied. This is limited evidence, not full48 or model qualification.

Good Enough (arXiv2606.06034v1) candidate at
 /cache/cch/qwen36-paper-preparation-20261007/lowbit/good-enough-gdn-controlled-new48h-v1-008/candidate.py
is Eq11+right Eq13 N3/S11 FP32 (9matmul/tile),948B,
SHA0a864c53c187f786f4e04b2fbdf31d0ffbf871372937b1007ea2ebce1ab31f8d.
Official author implementation remains unverified; this is a paper-derived local
implementation, not an author-code claim. Its actual008 matrix raw passed324
FP32 NPU dispatch checks, but the old owner failed cleanup attribution and its
independent full-chain recovery still needs exact receipts. GE003 grouped
fullGDN preparation has no actual SOURCE_BOUND/COMMANDS and needs prerequisites.
Neither route has accepted end-to-end performance or task accuracy evidence.

## Shortest selected successor: repair actual MXR48 harness failure

Actual failed owner:
 /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-mxr-event-single6-owned-main-RENEW24H_MXR48_S0_NPU_001/RESULT.json
548216B SHAebb755d08ac9bf2f5897928cc78f9d3f84a52cf4e3c042d49a621b8d2e53128f.
Actual matrix stderr2894B SHA081cf586cdabed3090be5354e4fb239d35ca75ceeca0ab96f3bcc77a5e559c4a
proves nested process-group initialization, BEFORE candidate/native arithmetic.

event_probe creates outer WORLD/PCP; full_bridge→two_arm→unchanged125.execute
enters original native_pcp_context, which correctly rejects existing groups.
native_identity.capture only verifies active callable provenance and needs no
outer group. The renderer removes ONLY redundant outer create/destroy, retains
the initial cold-group guard and changes outer cleanup to VERIFY all per-frame
original contexts actually released. Each original execute still owns real
HCCL PCP1 and its original finally; no borrowed group or weakened fixture guard.

    python -I -B render_context_owner.py --check

The source check proves exact before/after/inverse, unchanged downstream hashes,
zero outer group create/destroy calls, mutated-source and double-apply rejection.
It does not run Torch, original suites, containers, process groups or devices.

## Exact future run contract (MAIN binding required, do not run old owner)

Re-use the existing MAIN-owned singleton event lifecycle only AFTER deriving a
NEW source identity and MAIN current-window authority/plan. Do not execute the
old expired event_contract.py START/CUT/AUTHORITY_REF. Existing source hashes,
input lineage, library identity, cold native-callable checks, finite budget and
stop/retain checks must remain fully validated in the new packet.

Input: existing source-bound rank0 complete48 model captures,2048tokens,
Q/K H4 D128, V H12 D128, same original BF16 inputs/FP32 gates and states.
First shard only: original rows0..11. saved_candidate/native each run original
full GDN; same A/G and saved candidate full B/output/state bitwise anchor.
Independent references remain original inverse FP64 and separately source-derived
canonical GDN; this repair changes neither oracle nor its metrics.
Native-relative pass cannot replace canonical evidence or task accuracy.

Future child (argv exact interface; Refs MUST be real MAIN bindings):
 python -I -B NEW_SOURCE/event_probe_entry.py --execute
   --source-ref NEW_SOURCE_REF_JSON --plan-ref NEW_PLAN_REF_JSON
   --output /opt/host/vnf/austinov/run-mxr48-context-owner-20261023-v1/physical6/numeric

MAIN creates no existing path: use that unique root only if fresh, otherwise
choose a new experiment identity, never overwrite. Source audit/default-OFF and
same-image existing97 controls precede the actual child. Physical6 only,
owner phase600s, compute child300s, cleanup90s, shard raw432MiB plus metadata
inside existing512MiB evidence allocation; keep original CPU/cgroup/RAM/HBM/
diskreserve and exact owner retain/release gates. This source repair itself
does not create any such admission or extend any budget.

Judgment: context/ABI failure means current implementation not tested; numeric
disagreement is current adapter/reference attribution; pass qualifies only that
actual12-case shard. Next three shards, TP4 worker call proof, fixed1024
dense/candidate pairs and final task accuracy remain pending. No paper-wide no-go.

Ready count from this packet:0. Missing: MAIN new source+authority+input plan,
whole closure/source audit, same-image97, fresh resources, actual shard NPU and
independent consumed/release proof. The finite next experiment is now specified
and the exact proven blocking code seam is repaired reversibly.
