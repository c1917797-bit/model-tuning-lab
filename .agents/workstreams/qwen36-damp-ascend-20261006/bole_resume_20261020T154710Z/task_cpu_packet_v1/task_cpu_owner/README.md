# Finite same-image CPU software owner

Prepared default-OFF MAIN controller for the frozen task_decoder_scorer packet. No remote host, Docker/container, tokenizer, model, generated code or NPU execution occurred during this preparation. The local16 pure tests pass. The original task packet remains byte-exact; its manifest SHA256 is `f687ad69fa0226fe72565e8ed356b65244a475c570259c865e6b3cf68fcda851`.

The execution is strictly serial:

1. An8GiB, one-CPU145, same-image Devices[] container runs the frozen38 software controls (including9 default-OFF/help checks), restores all1319 existing GSM token lists by exact12-token insertion proof, decodes all15,525 actual task prompts with the original tokenizer, and verifies complete official source/gold/template coverage. It prepares the fixed HE public source/suite/input stage. Stop-retain completes before the next phase.
2. A separate2GiB, one-CPU145, uid65534/runc/network-none/Devices[]/read-only HE container runs only the known official HumanEval/0 canonical solution, deliberate failure and infinite-loop controls through the unchanged official evaluator. It has only3 exact read-only public mounts, minimal env-i, no capabilities/privileges, private scratch and FD/file/PID limits. No task model output enters this sandbox. Stop-retain completes before the next phase.
3. A fresh8GiB CPU145 Devices[] container independently reruns actual tokenizer/full provenance checks and the frozen result reader over the real HE CID/create/wait/inspect/logs/rows. It must report all1319/164/14042 input coverage and correct/wrong/timeout discrimination, with no task score. It is then stopped-retained.

MAIN must run this after its4CPU NPU model phase is fully stopped-retained. The original025 protected0..3 boundary, actual4..7 idle/FD checks, summed7CPU host/daemon ancestor admission (root166 plus original guest allocation/reserve2), disk32GiB output cap plus8.5GiB reserve, host512MiB, ordinary RAM reserve8GiB, source/image checks and exact owned cleanup remain active. Additional CPU-only monitoring rejects any running container declaring target4..7, including a model still in CPU startup before NPU FDs appear. Running CPU phases are sampled every5seconds; this is sampled exclusion, while MAIN's serial scheduling supplies the no-overlap operation guarantee. Nothing stops or signals a foreign/model worker.

The whole phase is3600seconds with one cumulative180-second cleanup lane; child limits are1450/90/1450 and reserve the original cleanup time. Original helpers keep their registered technical cutoff; the separately supplied new CPU authority must admit the full3600 seconds and cannot exceed that horizon. Historical task sources/deadlines are never changed or invoked via old main/source admission.

The narrow new profile changes are explicit and restored by object identity after cleanup:

- Registered private output globals point only to this new output root.
- `safety_host.MEM` is32→8GiB for CPU-only resource admission. Original CPU create/inspect already fixes8GiB; no model profile can be created in this namespace. Initial ordinary RAM floor is8GiB guest +8GiB reserve +0.5GiB host. Original disk reserves remain independent.
- Original CPU create/inspect still execute; an outer wrapper explicitly adds `--runtime runc`, rejects every non-CPU profile/device flag, and verifies the actual runtime. This avoids assuming the daemon's default runtime. It does not modify the original files/image.
- Frozen HE create argv remains unchanged. Before start, after strict full-CID/image/source/config inspection, MAIN performs a separately captured `docker update --cpuset-cpus 145` on that exact stopped owned CID. The actual update and CPU/cgroup are checked. No fabricated create argv/projection is passed to the frozen reader.

Actual host/guest PID+start+UID mappings, inspected image/CID, oneCPU145 ancestor view, actual memory ancestry, namespace interpreter binary bytes and source/input before/after are captured. HE resolves the frozen env-i PATH inside its pinned actual namespace and compares the loaded binary with that first executable; it does not guess the default Python from the host. CPU children use the original explicit Python3.12.13 path and original full namespace binary verifier. Success is published only after the module/function/output globals are restored. OOM/time/resource/source failures remain failures, while exact ownership inspection retains safe stop authority.

Only the seven tokenizer files are mounted read-only under `/models/Qwen3.6-27B`; checkpoint weights are neither mounted nor rehashed. Complete old input arrays are streamed for whole-byte hashes on the host and decoded/read only inside the8GiB CPU container. Official source/data/token-list/license and small metadata refs are exact. No runner, vLLM or NPU bootstrap import is used; the frozen decoder may import CPU Torch utilities but forbids accelerator/inference modules and device FDs. There is no model/HTTP workload dispatch in this controller.

## Preparation

Use a fresh private `python3 -I -B prepare_owner.py --prepare` process. Required arguments are:

- `--G1-source-ref`, `--G1-owner-ref`, `--G1-bundle-ref`, `--G1-independent-ref`: exact actual successful repair-v2 qualification Refs. Original release receipts are reopened; this is a helper/platform basis, not task/model admission.
- `--authority-ref`: MAIN's separately recorded current CPU authority, with start/cutoff epochs covering the finite phase.
- `--rendered-inputs-ref`: exact actual011 metadata Ref. The new task source derives unchanged original metadata/renderer/package Refs from it.
- `--packet-root`: frozen task_decoder_scorer directory.
- `--new-root`: absent ordinary new source leaf. The builder copies the7 owner files and all frozen packet bytes, and creates a NEW unbound task source and OWNER_INPUTS.json. It leaves the original packet untouched.
- `--output-root`: absent `/opt/host/vnf/austinov/run-bole-task-cpu-...` leaf. The builder does not create it or a container.

Ref arguments are JSON objects `{path,bytes,sha256}` (original025 Ref2 inputs are accepted only by the compatibility IO helper where required). Preparation prints the exact OWNER_INPUTS Ref. It hashes source/input/tokenizer files only and is separate from resource/device execution admission.

## Audit and finite execution

`python3 -I -B <new-root>/cpu_host.py --source-audit --inputs-ref <OWNER_INPUTS Ref JSON>` checks the complete exact readset and prints resources_admitted=false.

MAIN then launches a fresh private process with `BOLE_TASK_CPU_MAIN_ENABLE=1`, `python3 -I -B <new-root>/cpu_host.py --execute --inputs-ref <OWNER_INPUTS Ref JSON>`. The controller rechecks authority/source/basis, pins root CPU166, applies the original host AS/Go-child wrapper, and admits only the serial CPU phases above. Actual Docker operations are all through the original host/025 controller helpers; HE has a dedicated strict profile and reuses the same calls/resources/joint cleanup. No existing source/image/runtime checkout is patched; no container is deleted; every owned artifact is retained.

The actual output RESULT.json and exit0 together are required. `source_image_CPU_owner_software_controls_verified` can become true only from completed actual children, full frozen independent reader, all exact owned releases, unchanged source/input readsets and completed inverse. Its meaning is CPU software qualification only. `model_ready`, `task_score_produced`, `formal_accuracy_accepted`, `performance_ready`, `HTTP_executed`, `model_executed`, `NPU` stay false. The frozen component report's `CPU_same_image_owner_join_accepted=false` is preserved; the new outer owner supplies a separate actual same-image/Devices[] lifecycle proof rather than editing that report.

All required small helper sources were available for design; actual execution still reads the exact original paths declared by the qualified G1/025 metadata. If an actual source path/CPU/ancestor/cgroup/profile differs, execution fails with retained evidence. No pass is assumed from local controls.
