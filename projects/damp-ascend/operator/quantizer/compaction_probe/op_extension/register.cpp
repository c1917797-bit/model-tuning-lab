// SPDX-License-Identifier: Apache-2.0
#include <torch/library.h>
#include "ops.h"
namespace {
void meta_check(const at::Tensor& a,const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    TORCH_CHECK(a.scalar_type()==at::kInt && x.scalar_type()==at::kInt &&
        s.scalar_type()==at::kInt && n.scalar_type()==at::kInt &&
        a.dim()==1 && x.sizes()==a.sizes() && s.sizes()==a.sizes() &&
        n.sizes()==a.sizes() && a.is_contiguous() && x.is_contiguous() &&
        s.is_contiguous() && n.is_contiguous(),"four equal INT32 contiguous vectors");
    TORCH_CHECK(a.numel()==64 || a.numel()==448 || a.numel()==896,"N64/448/896 only");
}
void prepare_meta(const at::Tensor& a,const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    meta_check(a,x,s,n); // shapes/dtypes ONLY; never value/device/upload proof
}
damp_compaction_extension::Outputs compact_meta(
    const at::Tensor& a,const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    meta_check(a,x,s,n);
    return {at::empty({a.numel()+16},a.options()),at::empty({a.numel()+16},a.options()),
            at::empty({a.numel()+16},a.options()),at::empty({a.numel()+16},a.options())};
}
}
TORCH_LIBRARY(qwen36_damp_compaction_probe,m) {
    m.def("prepare(Tensor accepted, Tensor x_bits, Tensor scale_bits, Tensor magnitude) -> ()");
    m.def("compact(Tensor accepted, Tensor x_bits, Tensor scale_bits, Tensor magnitude) -> (Tensor, Tensor, Tensor, Tensor)");
}
TORCH_LIBRARY_IMPL(qwen36_damp_compaction_probe,PrivateUse1,m) {
    m.impl("prepare",TORCH_FN(damp_compaction_extension::prepare));
    m.impl("compact",TORCH_FN(damp_compaction_extension::compact));
}
TORCH_LIBRARY_IMPL(qwen36_damp_compaction_probe,Meta,m) {
    m.impl("prepare",TORCH_FN(prepare_meta)); m.impl("compact",TORCH_FN(compact_meta));
}
