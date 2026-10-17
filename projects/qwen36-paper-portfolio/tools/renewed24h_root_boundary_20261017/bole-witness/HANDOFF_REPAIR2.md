# BOLE131 repair2 — exact contextmanager identity only

Original131 and131R1 source/actual failures remain unchanged and available as
historical template bytes. No native algorithm, three-node tree, numeric bound,
input131/C1, component source, deadline3600/cleanup180 or resource budget changes.

Actual131R1 loaded weights and passed the FA patch gate, then failed because
inspect.getsourcefile(context_adapter.enter) correctly names stdlib contextlib,
while model_smoke incorrectly used its basename as an own-file key. This is a
source-adapter fault, not a model/kernel numerical verdict.

Only this reviewed context_adapter.enter is accepted. The module records its
actual wrapper and generator identities at import. Adapter checks exact own and
actual Python3.12.13 stdlib Ref3, compiled full-source factory/helper and generator
code objects, module/qualname, actual globals, defaults, no extra wrapper layer,
and the single func closure cell's identity. It never calls inspect.unwrap and
does not accept arbitrary contextmanager functions. Source failures include
expected and actual source/module/qualname. Publish remains an ordinary exact
worker_bootstrap.py function check, not basename dispatch.

The complete actual enter generator body is unchanged; only identity anchors
are added after its definition. model_smoke has a callable install_sources
frontdoor using explicit known own-file keys and the exact stdlib runtime pin.

Four new controls cover actual stdlib wrapper plus full actual enter body,
wrong wrapper, closure mutation, generator-code mutation and factory mutation.
A fresh -I process executes the complete actual model_smoke.install to the
first native-group boundary, asserting no vllm_ascend/torch_npu import occurs.
This is CPU source plumbing, not an actual native group or backend execution.
Original38 controls remain, aggregate42. New source/outputs are repair2 only.

Adjacent guards were checked: get_forward_context/is_forward_context_available,
get_attention_context, loaded Attention/AscendAttention forward, GDN core,
worker.load_model, proposer._propose, MTP/target compute_logits and CPU table
getter have no equivalent contextmanager decoration. Native context constructor
is checked by its exact module source rather than this mistaken function gate.
Existing source-bound CANN/native framework guards remain unchanged.

MAIN only: exact copy/Add deployment, bind actual component receipts, source
audit, actual same-image CPU42, then fresh original TP4 model admission. Missing
or wrong stdlib pin, source closure, unknown decoration or runtime path refuses.
No current model/NPU PASS is claimed; scheduler/performance/task still false.
