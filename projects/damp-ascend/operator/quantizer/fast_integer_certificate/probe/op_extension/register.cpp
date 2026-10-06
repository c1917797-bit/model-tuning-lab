// SPDX-License-Identifier: Apache-2.0
#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"
namespace {
void check_meta(const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    TORCH_CHECK(x.device().is_meta() && s.device()==x.device() && n.device()==x.device(),
                "Meta device mismatch");
    TORCH_CHECK(x.scalar_type()==at::kInt && s.scalar_type()==at::kInt &&
                n.scalar_type()==at::kInt && x.dim()==1 && x.sizes()==s.sizes() &&
                x.sizes()==n.sizes(),"three equal-shape INT32 Meta vectors required");
    TORCH_CHECK(x.is_contiguous() && s.is_contiguous() && n.is_contiguous() &&
                x.storage_offset()%8==0 && s.storage_offset()%8==0 &&
                n.storage_offset()%8==0,"Meta contiguous32B element offsets required");
    TORCH_CHECK(x.numel()==64 || x.numel()==896,"probe accepts N64 or896 only");
}
void prepare_meta(const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    check_meta(x,s,n);
}
damp_integer_probe_extension::Outputs certify_meta(
    const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    check_meta(x,s,n);
    return {at::empty({x.numel()+16},x.options()),at::empty({x.numel()+16},x.options()),
            at::empty({x.numel()+16},x.options()),at::empty({x.numel()+16},x.options()),
            at::empty({x.numel()+16},x.options()),at::empty({x.numel()+16},x.options()),
            at::empty({x.numel()+16},x.options())};
}
TORCH_LIBRARY_FRAGMENT(qwen36_damp_integer_probe,m) {
    m.def("prepare(Tensor x_bits, Tensor scale_bits, Tensor proposal_magnitude) -> ()");
    m.def("certify_bits(Tensor x_bits, Tensor scale_bits, Tensor proposal_magnitude) -> "
          "(Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor)");
}
TORCH_LIBRARY_IMPL(qwen36_damp_integer_probe,PrivateUse1,m) {
    m.impl("prepare",TORCH_FN(damp_integer_probe_extension::prepare));
    m.impl("certify_bits",TORCH_FN(damp_integer_probe_extension::certify_bits));
}
TORCH_LIBRARY_IMPL(qwen36_damp_integer_probe,Meta,m) {
    m.impl("prepare",&prepare_meta); m.impl("certify_bits",&certify_meta);
}
}

