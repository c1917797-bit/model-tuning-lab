# Standalone collective replay host controller preparation

`replay_host.py` is default OFF and now contains the actual one-shot host lifecycle. No Docker/container/NPU operation has been executed by this preparation. MAIN must inspect its source, provide the exact input packet, independently provide a real same-image Devices=[] software receipt and its source/admission review, then choose the actual launch. No MAIN approval file is authored here.

Reuse is deliberately narrow. The controller uses existing `native_ar_fsum_oracle_v1/ar_owner_common.py` for checked Ref/loading and `ar_saved_namespace.py:open_namespace` for the fresh private runtime. The base source manifest must be one whose exact inherited controller dependencies match that adapter. Actual pure source API execution with V4 frozen source passed in operation exec-0000000000000800; all subprocess calls and Torch imports were tripwired. It built the real S.create_argv in memory and confirmed network none, read-only rootfs, 32GiB, 4CPU and physical4–7 mappings without creating an output directory or container.

The inherited `DENSE090_EXTERNAL_OUTPUT_ENABLE=1` remains an explicit host launch prerequisite. The first source API attempt exec-00000000000007fc rejected its absence; the valid successor supplied the existing flag. The old sources were unchanged. Output root must be a new `/opt/host/vnf/austinov/run-bole-native-ar-collective-replay-...` name to fit the existing private adapter's exact prefix, with owned leaf `dense`. This name is compatibility with an existing host adapter; it does not make the WORLD replay group a vLLM TP group.

No resource safety function is copied or edited. The actual original `S.Controller.observe/resources/create_owned/inspect/cleanup`, `S.fd_holders/device_map`, `H.Joint`, protected0–3 comparison, exact owner CID/image/labels, read-only rootfs, capped Docker logging and stop-retain release checks run unchanged. The model-sized32GiB memory/32GiB workspace admission and independent8.5GiB Docker/output disk reserve stay in force. The replay adds a stricter sole64MiB output cap; it does not lower those reserves.

MAIN lock uses the exact existing `MAIN_ADMISSION.lock`, nonblocking flock held through create, request, stop, release, log freezing and RESULT persistence. No existing container is reused. Container network is none; standard torchrun uses `--standalone --nnodes=1 --nproc-per-node=4 --local-addr=127.0.0.1`. The local-addr option must pass the actual pinned torchrun parser in same-image preflight. The fresh container mounts only driver, exact worker/input/raw/source Ref files and its own writable output, with the original runtime cache alias. It does not mount model weights or broad old result trees.

The controller has a tighter600s phase including180s cleanup reserve, wholly inside the inherited current authority. It does not reset the original authority. The worker timeout is180s per group operation. MAIN's outer operation/unit must allow bounded cleanup and preserve a nonzero process exit. SIGTERM/SIGINT enter the own-only cleanup path.

The default variant requires the image not to set HCCL_DETERMINISTIC and adds no such variable. The deterministic variant starts another new owner with exactly `HCCL_DETERMINISTIC=true` passed to docker exec before Python. Worker runtime evidence decides the actual getter/flag values. An absent setting does not mean deterministic behavior is false. This replay uses its own WORLD group, not production vLLM's actual TP process group. HCCL kernel identity, communicator construction and stream topology may differ; standalone results remain diagnostic.

MAIN controller input schema `bole.collective-replay-controller-input/v1` contains exactly:

- `controller_ref`, `common_ref`, `namespace_ref`, `base_source_ref`, `authority_ref`;
- `replay_manifest_ref`, `replay_worker_ref`, `variant`;
- `output_root`, fresh `owner_name` matching `bole-collective-[a-z0-9-]{1,50}`;
- `lock_path` equal to the existing workstream MAIN_ADMISSION.lock;
- `image` equal to SHA660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1;
- `phase_seconds:600`, `cleanup_seconds:180`, `output_cap_bytes:67108864`;
- `same_image_software_ref` pointing to actual later source-qualified same-image software evidence.

The referenced authority has the original `start_epoch`, `cutoff_epoch`, `phase_seconds:3600`, `cleanup_seconds:180` expected by existing namespace.

Actual MAIN review schema is `bole.collective-replay-main-review/v1`, with exact controller and input Ref joins, `approved:true`, `NPU_executed:false`, and the actual same-image software Ref. The latter schema `bole.collective-replay-sameimage-software/v1` binds image, worker/controller Refs, `passed:true`, `devices:[]`, `NPU:false`. These are required consumers, not claims that such evidence already exists.

CLI modes:

```text
python3 -B replay_host.py
python3 -B replay_host.py --source-audit --inputs-ref '<actual Ref3>'
DENSE090_EXTERNAL_OUTPUT_ENABLE=1 python3 -B replay_host.py --execute --inputs-ref '<actual Ref3>' --review-ref '<actual MAIN Ref3>'
```

Raw stdout/stderr and actual exit remain retained even if a worker refuses its rank/environment contract before that worker's own try/finally. Log Refs are frozen only after termination. A timed-out/failed arm triggers exact own stop-retain, retains first error and stderr, marks incomplete and never promotes a diagnostic into numerical/performance/task acceptance.

Pure controls are available in test_replay_host.py. Actual same-image/API and both NPU replay results are recorded in ../../COLLECTIVE_CAUSAL_CHECKPOINT_20261022T210000Z.md; none qualifies whole-model performance or task accuracy.
