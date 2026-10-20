# Native AR owner repair v2: source-only Devices[] preflight

This is a new isolated repair of `native_ar_owner` v1. V1 and every frozen
native AR observer/reader remain unchanged. No host, Docker, Git, NPU or actual
target-image execution was performed for this repair.

MAIN reported that an earlier V4 Devices[] import of the same native Ascend
worker/runner stack aborted in C++ SOC setup; V5 consequently used exact-source
compile/native-parser checks and deferred real instance guards to actual NPU
load. The v1 preflight's `installed('runner')` directly imports the identical
`vllm_ascend.worker.model_runner_v1` module, so the risk applies. This repair does
not claim to independently reproduce that abort or establish a safe alternative
import order. The known dangerous import is removed. The supplied current
`g1_review_v2/preflight114.py` is4903 bytes / SHA256
`dd350e30348d56f1b0ec0cf9c9ca4a794374f7574ec5797c6423bf407e12ba07`.
Its report explicitly sets `registry_class_imported=False`,
`model_config_constructed=False`, and says actual ModelConfig/QwenMTP class and
weights load is still required. Its safe parser/registry route does not import
the native runner class; it supplies direct source support for that separation.

Only `ar_sameimage_preflight.py` changes. The six controller/common/builder/
snapshot/consumer sources are exact v1 bytes. The repaired preflight:

- Reopens all exact host/installed source refs, actual G1 complete pass, guest
  model files, private plugin metadata and all18 cold default/help cases.
- Resolves the private bootstrap file with top-level `find_spec`, without
  executing its module or invoking the plugin.
- Parses and compiles every exact installed runtime source without `exec`.
- Checks the single actual runner source declaration of
  `@torch.inference_mode()` on `NPUModelRunner.sample_tokens` by AST only.
- Imports no Torch, torch_npu, Triton, vllm or vllm_ascend module; a final
  sys.modules check rejects any such import.
- Reports runtime wrapper/closure and actual instance checks **unexercised**.

The frozen actual native observer still requires original instance/class
method identity, exact Torch `_contextlib` wrapper source, original runner
`__wrapped__` identity, `inspect.getclosurevars`, the real
`torch.inference_mode` context factory and every native loaded runner/model/FA
guard. Those checks execute only during its real after-load callback inside
MAIN's actual admitted TP4 run. No CPU AST declaration is promoted into their
success.

Use this directory's unchanged `prepare_native_owner.py` in place of the v1
builder, with the same explicit actual G1/model/initial-profile refs and new
AR/control/output leaves. It copies the repaired preflight into the new control
source closure, so the owner/readset references its actual new bytes. Do not
rewrite an already bound v1 source/input ticket. The owner invokes the same
preflight filename and unchanged generic `source_preflight_pass` contract.
All original finite controller/resource/window/cleanup/ownership, initial-only
metadata join, private inverse and mathematical observer/consumer behavior are
unchanged.

Six pure local tests and eight default/help CLIs pass. The source-only decorator
test uses the actual G1 runner bytes/SHA256. A local text-transport copy contains
one extra final LF; the test reconstructs bytes only after matching the complete
actual bound258160-byte SHA256, and does not modify that read-only copy.
The original observer hash and its deferred runtime guard source are checked.
Actual same-image source preflight, real load/instance/closure guards and paired
native numerical/token qualification remain unexecuted. No model/task/perf/E2E
success is claimed; common plugin effects remain pending.
