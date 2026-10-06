# MAIN-owned real-service preparation (not executed by preparer)

This NEW tools/service/ layer leaves the 7 compiled files, frozen native probe,
and existing plugin byte-for-byte unchanged. This is P1 eager/prefix-off screening,
not final 10% acceptance. MAIN alone may execute these commands after kernel gate
PASS, fresh physical4–7 inspection, physical/logical mapping proof and source/CLI
review. Do not run while DAMP TP4 or any overlapping job is active. No auto-retry.
A same-eager control cannot replace final common-optimized dense, graph-service
coverage, three repeated pairs or LongBench-v2/GSM8K task accuracy.

## Source-bound actual seams

MAIN no-load snapshot receipt4a4e548e300339a0d28fbd71068ca803ad026325a5cf1c0fce1b8d7ee7261177:
gdn d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816;
Qwen alias copier21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3;
runner94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968;
CachedRequestStatecaeeb20f5010d74663c45f9419237191e3c0a149f4c7aa25bc1b73b1112d67ae.
Runner2294–2322 establishes the real forward context before _model_forward;
4699–4714 partitions Mamba state into contiguous views. Qwen alias copier207–208
copies donor function objects onto the actual receiver, not inheritance lookup.

MAIN completion snapshot receipt84354f4d55c6a444722d2f11271c49fd4f3f99eb7394c1c2954d0ab367544af6:
protocol93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c;
servingc67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7.
return_token_ids explicitly exposes per-chunk delta tokens and initial prompt IDs;
serving363–414 returns actual output.token_ids,451–474 emits final usage then[DONE].
TTFT is client submission (includes queue) to first nonempty token-ID delta receipt;
TPOT is first-to-last delta receipt /1023. Coalesced tokens share the delta receipt
timestamp; these are serving/client metrics, never per-kernel/device timings.
Throughput is40960 output tokens divided by earliest submission→latest[DONE].

## Evidence observer, lifecycle and budget

Both arms enable the SAME additional metadata observer. It does not wrap any GDN
core (candidate live_bindings requires the exact frozen function), alter arguments,
copy NPU tensor values to CPU, synchronize or capture graphs. It checks actual48
receiver bindings, FP32 local[N,12,128,128] state, real request prompt fingerprint,
parent dispatch and stable base/aux storage metadata on every real turn.
The frozen candidate wrapper itself asserts all48 core visits on every successful
turn, checks actual slots/owners, rejects active alias/migration/restore, and resets
aux after native full prefill. P1 mixed decode still materializes selected slots
and uses native core; the observer's expected counts are matched to native
aux_materialized_for_fallback records. No P2 mixed acceleration is claimed.
Dense proof is actual48 binding/native network, NOT a newly hooked per-core trace.

Observer CPU pre/post bookkeeping times and prior JSON I/O are reported; last
turn JSON-write time is not included in the diagnostic lower bound. All observer
and client raw-I/O overhead remains inside the matched throughput wall. Do not
compare this measured service to a dense arm without the observer. Before final
acceptance quantify/disable common diagnostic overhead symmetrically and prove
dispatch separately; these instrumented P1 numbers alone are not final acceptance.

Aux119296B/layer/slot,48 layers. Total10658488320B/rank is equal:
dense native10658488320; candidate native8053063680+aux reserve2605424640.
Actual candidate slots must<=455 before allocation. Never increase budget on fail.
Prefix cache off, mamba-cache none, eager, no chunking/speculation/CP/mm/prompt
embeds. Existing lifecycle rejection is retained, not silently dense fallback.

## Preconditions and unique stage plan

Host result root /cache/cch/qwen36-kvbuffer-parallel-20261006 is mounted RW at
/kvbuffer-results, canonical repo same absolute path RO, /cache/efim/Qwen3.6-27B
RO at /models/Qwen3.6-27B; preserve original CANN paths. MAIN inspect exact image
660ce23a..., nonprivileged container physically4–7->logical0–3, fresh idle/PIDs/UDA,
RAM/disk, actual SoC and native ABI. Stop-retain ONLY this stage's exact owned
container/ID in MAIN finally. No preparer Docker launcher or device action exists.

Before loading model MAIN runs exact-image no-device CLI --help and verifies all
listed arguments and both general-plugin inventories. Required plugins:
ascend,ascend_kv_connector,ascend_model,ascend_model_loader,kvbuffer_parallel,
kvbuffer_service; never candidate-only whitelist, never profiling plugin.
Launch verifies frozen source/model/completion/library hashes, actual CLI remains
an explicit MAIN preflight gate. Existing successful build/Meta is not this gate.

All NEW paths must not exist: host p1-service-pair-v1, both parent identity JSON,
dense/candidate arm directories and paired.json. Main can choose a NEW version
if any name exists; no overwrite, restart or rerun of previous failed outputs.
The following container paths are a plan, not executed commands.

Parent-created identity per arm schema kvbp.service-identity/v1:
image_id; physical_devices[4,5,6,7]; logical_to_physical{"0":4,"1":5,"2":6,"3":7};
fresh_idle_verified/nonprivileged/source_canary_passed true; preflight_utc with UTC zone and age<=600s at launch;
evidence object containing actual raw device/mount/source/CLI paths and SHA256;
native_gate_sha256 = actual p1-native-matrix-v1/report.json SHA;
arm dense/candidate; port8246; common exactly contract.COMMON;
common_total_budget_bytes10658488320. This tool NEVER creates successful identity.
Use fresh source canary and idle check before EACH arm, not an old receipt.

1. MAIN executes launch with stdout/stderr in a NEW durable log and retains exact
process/container ownership. It is a foreground server; MAIN waits /health then
runs bench from a separate controlled exec. Fresh prepare-only directories can
check manifests without loading weights, but do not reuse them for live launch.

ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/service/launch.py --arm dense --identity /kvbuffer-results/p1-service-pair-v1/dense-identity.json --native-gate /kvbuffer-results/p1-native-matrix-v1/report.json --output-dir /kvbuffer-results/p1-service-pair-v1/dense --port 8246

2. ONLY after healthy dense service:
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/service/bench.py --arm-dir /kvbuffer-results/p1-service-pair-v1/dense --port 8246 --output-dir /kvbuffer-results/p1-service-pair-v1/dense/client

3. MAIN exact owned stop-retain; wait fresh no-PIDs4–7 and port free. New candidate
arm process/container, same image/settings/port/client/observer; no simultaneous
dense+candidate sharing. Parent observer source fresh proof:
ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/service/launch.py --arm candidate --identity /kvbuffer-results/p1-service-pair-v1/candidate-identity.json --native-gate /kvbuffer-results/p1-native-matrix-v1/report.json --output-dir /kvbuffer-results/p1-service-pair-v1/candidate --port 8246

4. ONLY after healthy candidate:
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/service/bench.py --arm-dir /kvbuffer-results/p1-service-pair-v1/candidate --port 8246 --output-dir /kvbuffer-results/p1-service-pair-v1/candidate/client

5. Stop-retain owned stage; validate:
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/service/compare.py --dense-arm /kvbuffer-results/p1-service-pair-v1/dense --candidate-arm /kvbuffer-results/p1-service-pair-v1/candidate --dense-client /kvbuffer-results/p1-service-pair-v1/dense/client --candidate-client /kvbuffer-results/p1-service-pair-v1/candidate/client --output /kvbuffer-results/p1-service-pair-v1/paired.json

Formal workload shape40 req/C16/input32768/shared prefix16384/output1024 (40960
total) is implemented, but still one SCREEN pair with raw token-ID prompts
(no chat template; no thinking mode enabled). This is NOT final task accuracy.
Final quality uses real GSM8K/LongBench-v2 chat with thinking explicitly disabled,
normalEOS/max2048 and acceptance loss<=1% per user's updated direction, paired
same-stack dense. No calibration/final-test mixing. No accuracy run here.

## Remaining real gates

No preparer service/NPU execution. Actual entrypoint import/CLI, real first
candidate48/cache state, native-oracle matrix, same-eager model lifecycle and
40/C16 pair all need MAIN execution after current DAMP stops. Graph service is
unsupported; mixed native fallback may eliminate benefit. If kernel/admission
fails preserve raw failure and diagnose once with new evidence, no silent fallback.
This preparation does not start a paper timer or predict a successful gain.
