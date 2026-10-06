// Test-only: never register this namespace as a serving or vendor operator.
#include <torch/library.h>
#include "ops.h"
TORCH_LIBRARY(qwen36_damp_reference, m) {
    m.def("decode(Tensor q, Tensor k, Tensor v, Tensor g, Tensor beta, Tensor state_selected, Tensor pk, Tensor pv, Tensor inv_pv, Tensor sr) -> (Tensor, Tensor, Tensor)");
}
TORCH_LIBRARY_IMPL(qwen36_damp_reference, PrivateUse1, m) {
    m.impl("decode", TORCH_FN(qwen36_damp_reference::decode));
}
TORCH_LIBRARY_IMPL(qwen36_damp_reference, Meta, m) {
    m.impl("decode", TORCH_FN(qwen36_damp_reference::meta));
}
