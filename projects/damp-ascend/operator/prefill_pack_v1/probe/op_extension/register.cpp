// SPDX-License-Identifier: Apache-2.0
#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"
namespace {
void check_meta(const at::Tensor& x,const at::Tensor& s,const at::Tensor& p) {
    TORCH_CHECK(x.device().is_meta() && s.device()==x.device() && p.device()==x.device(),
                "Meta device mismatch");
    TORCH_CHECK(x.scalar_type()==at::kInt && s.scalar_type()==at::kInt &&
                p.scalar_type()==at::kInt && x.dim()==1 && x.sizes()==s.sizes() &&
                x.sizes()==p.sizes(),"three equal-shape INT32 Meta raw-bit vectors required");
    TORCH_CHECK(x.is_contiguous() && s.is_contiguous() && p.is_contiguous() &&
                x.storage_offset()%8==0 && s.storage_offset()%8==0 &&
                p.storage_offset()%8==0,"Meta contiguous32B element offsets required");
    TORCH_CHECK(x.numel()==64 || x.numel()==896,"probe accepts N64 or896 only");
}
void prepare_meta(const at::Tensor& x,const at::Tensor& s,const at::Tensor& p,bool useCandidate) {
    check_meta(x,s,p);
}
damp_prefill_float_probe_extension::Outputs divide_meta(
    const at::Tensor& x,const at::Tensor& s,const at::Tensor& p,bool useCandidate) {
    check_meta(x,s,p);
    return {at::empty({x.numel()+16},x.options()),at::empty({x.numel()+16},x.options()),
            at::empty({x.numel()+16},x.options()),at::empty({x.numel()+16},x.options())};
}
TORCH_LIBRARY_FRAGMENT(qwen36_damp_prefill_float_probe,m) {
    m.def("prepare(Tensor x_bits, Tensor sr_bits, Tensor proposal_bits, bool use_candidate=False) -> ()");
    m.def("divide_bits(Tensor x_bits, Tensor sr_bits, Tensor proposal_bits, bool use_candidate=False) -> "
          "(Tensor, Tensor, Tensor, Tensor)");
}
TORCH_LIBRARY_IMPL(qwen36_damp_prefill_float_probe,PrivateUse1,m) {
    m.impl("prepare",TORCH_FN(damp_prefill_float_probe_extension::prepare));
    m.impl("divide_bits",TORCH_FN(damp_prefill_float_probe_extension::divide_bits));
}
TORCH_LIBRARY_IMPL(qwen36_damp_prefill_float_probe,Meta,m) {
    m.impl("prepare",&prepare_meta);m.impl("divide_bits",&divide_meta);
}
}
