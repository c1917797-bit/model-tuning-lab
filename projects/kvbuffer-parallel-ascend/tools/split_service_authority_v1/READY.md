# KVBuffer split → kernel prerequisite bridge (default OFF)

NEW stdlib-only report/consumer ABI bridge. No Docker, Torch, library loading,
NPU, automatic retry, Git or KVBuffer24h timer. All37 frozen KVBuffer files
remain unchanged. Actual split reports do not exist at preparation time;
build-p1-v1/meta-p1-v1 are no-device identities, not NPU correctness.

## Exact API and provenance

validator.validate_complete(b1,b16,source_manifest,read_bytes,enabled=False,
testing=False) is the explicit NEW consumer. read_bytes defaults to host
Path.read_bytes. MAIN must audit any image→host snapshot alias separately.

Each run dictionary has exactly report,identity,operation,stdout,stderr,child
(raw Ref{path,sha256}), peer_id,operation_id,command,args,cwd,producer_sources
{absoluteSource:SHA}. MAIN's externally supplied exact command/argv/cwd/peer/
opid are compared to the ORIGINAL authoritative AWMCP record. a_exec and
operation_get actual record shapes are supported; outer ok cannot hide exit1.
Original stdout must contain one MAIN_KVBUFFER_SPLIT_CHILD JSON marker binding
report/identity/child Refs. Old runner DOES NOT emit this marker/sidecar:
a reviewed real MAIN launch/observer adapter remains PENDING.

NEW child schema kvbp.split-child-execution/v1:
report/identity Refs; evidence_kind=actual-main-execution;
execution{command,args,cwd,exit_code,error,cancelled,timed_out,stdoutRef,stderrRef}
from the original actual Docker Popen; image_identity_path,image_output_dir;
producer_sources equal MAIN's expected real source pins; original
container_inspect Ref; device_proof Ref; native_library Ref.
Host Docker and image Python identities are different. The inner runner flags
after the real runner boundary must identify true B1/card5 or B16/card6.
No fake padded batch, reconstructed Python host outcome or self-ready boolean.

Container inspect must be the actual one-container list/fullID/image,
nonprivileged, memory/swap8GiB, only physical5 or6 (never0–3).
MAIN external device schema kvbp.split-main-device-binding/v1:
container_id,image_id,physical_devices,logical_to_physical,same_process_pid,
preflight_utc,evidence_kind,raw_refs exactly canary/mapping/host_processes/cgroup.
identity.evidence must bind the same device_proof/container_inspect Refs.
MAIN actually produces and reviews these raw bytes; the bridge binds provenance
and parses inspect, but does not itself interpret arbitrary canary/npu-smi/
cgroup formats or manufacture physical proof. Missing metadata is a preparation
gap, not an algorithm failure. Historical freshness is checked against actual
report creation, not against the present time when reviewing completed evidence.

Mapped native binary must match actual same-image stopped snapshot SHA
eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a.
Merely printing a schema or passing Meta cannot substitute for this binding.
SOURCE_MANIFEST pins all37 existing KVBuffer files, actual build/Meta/candidate
SO and three NEW sources, no self-hash recursion. Future launcher/observer
sources are explicitly missing and must arrive through producer_sources.

## Checks and restricted result

Exactly8 unique B1/B16×eager0/graph0/1/2 cases,1280 ordered changing steps:
finite output/complete/per-head .00303/2e-6/2e-6; every guard/input/slot/base/log
flag; exact active schedule/reset slots64/112 zero-based; independently replayed
cap16 flush counts; maxima; each raw checkpoint name/hash/size/passed cleanup.
Any original failure/nonterminal/cancel/timeout/pending or retained failed raw
rejects. Both jobs must have distinct operations/containers/reports and matching
native code/schema. Original stdout/stderr/report/identity/source/sidecar Refs
are preserved in the result, never rewritten into fake old single-process PASS.

Passed raw tensor payloads were lawfully deleted by the frozen producer after
hashing. The bridge cannot recover/reanalyse them and never claims it did.
Original save-error masking still needs a thin execution-shim repair; this
validator cannot reinterpret historical failures. Failed artifacts remain raw
and outside Git. No write/delete/retry occurs during validation.

Output schema kvbp.split-kernel-prerequisite/v1:
actual checked inputs → checked_actual_split_kernel_prerequisite;
service_ready/model_lifecycle/other_batches/matched_E2E/task_accuracy allFalse.
testing=True is API-only software mode → synthetic_contract_pass,npu_verifiedFalse;
there is no CLI switch promoting synthetic fixtures to actual evidence.

Old service launch still rejects the NEW schema. After real split PASS, MAIN
may explicitly wire this API into a NEW thin service entrypoint; that wiring
is PENDING, as are trueT2–15/cache lifecycle/nativeOFF/ONstate/output/formalE2E/
task quality. Kernel prerequisite is not permission to start model service.

## Software and default-OFF CLI

Only source/stdlib execution, after MAIN review:

    /usr/bin/python3 -B -m unittest discover -s /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_service_authority_v1 -p test_validator.py -v
    /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_service_authority_v1/validator.py
    /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_service_authority_v1/validator.py --help

Tests read actual existing frozen artifact/source/snapshot bytes but create
producer-shaped operations/reports/inspect/proofs ONLY in memory and explicitly
synthetic. No subprocess/device loads or filesystem fixture writes.

Future evidence-only CLI; these example files are not real/verified reports:

    /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_service_authority_v1/validator.py --enable --inputs /cache/cch/qwen36-kvbuffer-parallel-20261006/REAL_MAIN_TWO_SPLIT_INPUTS.json --output /cache/cch/qwen36-kvbuffer-parallel-20261006/NEW_KERNEL_PREREQUISITE.json

Without --enable the CLI is OFF/no admission. Enabled validates all raw inputs
before exclusive-create output. Missing/failed evidence retains original Python
error in stderr and writes no PASS; MAIN retains raw inputs/stderr separately.
