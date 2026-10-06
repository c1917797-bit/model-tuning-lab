# Parent-owned next one-shot NPU commands (not executed)

Status: BUILT + LOAD/META / NPU-UNVERIFIED. MAIN completed the NO-device
build-p1-v1 and meta-p1-v1 stages; their existing output roots MUST NOT be rerun
or overwritten. Preparer performed no build, Docker/NPU start or Git mutation.
Actual receipt/library/source hashes are recorded in README and PROVENANCE.

Only NEW launch identity, NPU output and service paths below must be fresh; stop if they exist. The parent must first inspect physical4–7,
all NPU processes, exact container device/mount declarations, RAM and free disk,
source hashes and image ID. No preparer launcher starts Docker/NPU/build.

Already built by MAIN with repo RO and external results RW, image
sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
Historical build-p1-v1 (DO NOT rerun in this existing directory):
cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/operator -B /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1 -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
cmake --build /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1 -j2

Build receipt SHA25db2cee4f6e6020e476b2c92e15fa8321655bd22e371e35c4d27b0db16dd0d4.
Library SHA0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b.
Actual load/schema and positive Meta B1/B16 passed; report SHA
2765f4bbcbf1d935e260b4d6cfa3b5401257aaf125fca0ae4c149193566dc727.
Meta negatives not implemented, physical_nd_proven=false, graph_proven=false,
npu_executed=false. These are not numerical or device-lifecycle results.

NEXT NPU stage is one native-oracle matrix, not a repeated build/Meta stage.
Parent must map host /cache/cch/qwen36-kvbuffer-parallel-20261006 to
/kvbuffer-results RW and canonical repository at its same absolute path RO,
preserve the original image CANN/PYTHONPATH, and record actual mapping/SoC.
Read and hash the four contract.SOURCES in the fresh exact-image process;
confirm native operator/keyword-only schema after the canary, not by Meta.
An old stopped-container audit is not fresh load/ABI/idle proof.

Read-only path review found host p1-launch-v1.json and p1-native-matrix-v1 absent
in preparer LGW exec0289; this is a snapshot, never authorization to reuse them.
Immediately before launch, MAIN must fail if either path now exists:
host /cache/cch/qwen36-kvbuffer-parallel-20261006/p1-launch-v1.json
host /cache/cch/qwen36-kvbuffer-parallel-20261006/p1-native-matrix-v1
Probe itself additionally requires a nonexistent output under /kvbuffer-results.
Never run while the owned DAMP TP4 capture or any conflicting NPU job is active.

Before native oracle, compute actual .so SHA and create an external JSON receipt:
schema kvbp.launch-identity/v1; image_id (frozen PROVENANCE/contract);
physical_devices [4]; logical_to_physical {"0":4}; fresh_idle_verified true;
nonprivileged true; library_sha256 0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b; full parent device/mount/source
evidence paths+hashes, no invented successful source-lock.
Receipt /kvbuffer-results/p1-launch-v1.json is created once by MAIN after fresh preflight.
The following is the UNIQUE candidate NPU command for this frozen artifact; no retries.
Probe container maps ONLY physical4
to logical0. Do not reuse old KVBuffer containers or old result directories.

ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/native_oracle_probe.py --library /kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so --identity /kvbuffer-results/p1-launch-v1.json --output-dir /kvbuffer-results/p1-native-matrix-v1

After numerical PASS and parent source/API review, one fresh eager model-native
off/on lifecycle pair on ONLY physical4–7 -> logical0–3. Use same mandatory
Ascend platform/model/loader plugins on both; candidate additionally
kvbuffer_parallel. Do not set VLLM_PLUGINS to candidate only.
Do not start E2E until per-rank actual48 receiver proof and full coverage pass.

Proposed COMMON total KV+aux budget10658488320 bytes/rank; dense native
KV10658488320, candidate native8053063680 plus reserved auxiliary2605424640.
This permits at most455 native state slots. Parent must check actual pool
geometry BEFORE acceptance; >455 is a budget FAIL, not permission to increase.
This is a preregistered fair total-budget screen, NOT the historic v5 configuration
or reused108.996204 baseline.

COMMON server args:
vllm serve /models/Qwen3.6-27B --tensor-parallel-size 4 --data-parallel-size 1 --trust-remote-code --max-model-len 40960 --max-num-batched-tokens 40960 --max-num-seqs 16 --no-enable-prefix-caching --mamba-cache-mode none --no-enable-chunked-prefill --enforce-eager --port PARENT_NEW_EXCLUSIVE_PORT
dense adds --kv-cache-memory-bytes 10658488320 and QWEN36_KVBP_ENABLE=0
candidate adds --kv-cache-memory-bytes 8053063680 and:
QWEN36_KVBP_ENABLE=1
QWEN36_KVBP_LIBRARY=/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so
QWEN36_KVBP_LIBRARY_SHA256=0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b
QWEN36_KVBP_AUX_BUDGET_BYTES=2605424640
QWEN36_KVBP_TOTAL_BUDGET_BYTES=10658488320
QWEN36_KVBP_MODEL_CONFIG=/models/Qwen3.6-27B/config.json
QWEN36_KVBP_AUDIT=/kvbuffer-results/p1-service-v1/candidate/evidence.jsonl
PYTHONPATH append only this NEW plugin directory.

Parent must confirm exact installed CLI/config names and entrypoint inventory
with a no-device check; these commands are a reviewed draft, not a launch receipt.
Formal E2E request harness must validate40/40 successes and exactly40960 output
tokens by usage/token IDs (not chunk counts); queue-included TTFT/first-token
definition/TPOT semantics must match dense. Fixed input32768, shared prefix16384,
1024 outputs, C16, temperature0 seed0 thinkingoff; profiler disabled. Keep both
full logs and receipts. Stop-retain only the exact owned container in finally.
No broad kill, retry, old-result overwrite or claims from kernel microtime.
