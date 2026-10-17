# Repair2: preserve complete compilation context in software fixture

Original repair1 actual same-image119 observed118PASS/1ERROR; no NPU. Its
underlying_body failure belongs to the test fixture, not a proven active native
binding failure. Original source/result remain unchanged. Production validator,
including its entire underlying_body gate, is byte-identical repair1.

Local Python3.12.14 reproduces the exact refusal without Torch/backend. The
fixture rebuilt a ClassDef containing selected methods but omitted module
imports. Python3.12's compiler uses import binding context: full-source forward
has LOAD_GLOBAL(NULL+torch/triton) then LOAD_ATTR, while the extracted-class AST
uses LOAD_GLOBAL followed by method-form LOAD_ATTR(NULL|self+...). The code
byte arrays differ at triton.cdiv108/109 and torch.zeros119, and KW_NAMES source
positions differ. Python3.9 emitted equal code and did not expose the fixture
defect. No relaxed code equivalence or source-position masking is introduced.

The fixture now obtains forward's CodeType from the exact complete source
compile already used by production native_code, then constructs a FunctionType
using the explicit software module globals. No imports, hardware constructor,
Tensor, HAL or source body is executed. The real producer's non310p copy
assignment still executes unchanged. On3.12 the old extracted-body mismatch is
explicitly asserted, while the full body equals expected. All original negative
target/receiver/module/globals/body/wrapper/source cases remain and must reject.

Only fixture and new output/owner/source identities change. Original plain,
known-copy validator, bounded pre-failure diagnostics, four actual forwards,
numeric/calibration/independent gates, resources and UTC window remain.119
same-image controls and real NPU capture are still required; this source-only
preparation does not claim them passed. No original FAIL becomes PASS.
