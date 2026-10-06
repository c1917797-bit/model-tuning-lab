# Removable HYPIC runtime delivery

The pinned HYPIC source is already a vllm.general_plugins package. Its
entry point is hypic_vllm_ascend:register; the sole treatment switch is
VLLM_ASCEND_HYPIC_ENABLE=1. The entry point returns without patching when
the switch is 0. This supported plugin route expresses the HYPIC treatment
directly, so an additional sitecustomize monkeypatch would create a second
activation path and confound attribution.

The controller pins the official image digest, copies the source tree from a
read-only mount into ephemeral /opt/hypic, then runs
python3 -m pip install --no-deps -e /opt/hypic inside each experiment
container. The official image and host framework files are unchanged.
Baseline and treatment use the same copied plugin source and serve command;
only the enable switch differs. The source commit, package-tree diff, benchmark
hash, evaluator hash and container inspect records are saved in
environment-and-container-snapshot.txt.

The treatment emits plugin_build_active and per-worker HYPIC evidence into
hypic-only/hypic-evidence.jsonl. The first full performance run requires the
verified hot path. A successful disabled-control request and absence of HYPIC
activation markers in no-cache/hypic-evidence.jsonl are required before an
accepted decision.

Rollback: stop the owned treatment container, switch
VLLM_ASCEND_HYPIC_ENABLE=0, restart the same pinned source in a new
experiment container, complete a real request, and verify that treatment
markers disappear. Uninstall by removing only the experiment container and
its ephemeral /opt/hypic copy; no official image or framework repair is
needed. Finally verify physical NPU0-3 have no owned process. These steps
must be executed and recorded before an accepted final decision.

Historical 0-3 performance artifacts used --max-num-seqs 32; this experiment
uses 16. Historical Qwen3.6 quality artifacts cap output at 1024; this
experiment caps at 2048. Neither historical baseline satisfies the new
baseline contract. Once the new 0-3 baseline is frozen, candidate iterations
reuse it if the contract and individual run checks still pass.
