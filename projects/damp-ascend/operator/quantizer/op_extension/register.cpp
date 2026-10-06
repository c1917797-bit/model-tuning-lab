// SPDX-License-Identifier: Apache-2.0
#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"
namespace {
void check_meta(const at::Tensor& x, const at::Tensor& scale)
{
    TORCH_CHECK(x.device().is_meta() && scale.device() == x.device(),
                "Meta input devices must match");
    TORCH_CHECK(x.scalar_type() == at::kInt && scale.scalar_type() == at::kInt &&
                x.dim() == 1 && x.sizes() == scale.sizes(),
                "raw x_bits and scale_bits must be INT32 vectors of equal shape");
    TORCH_CHECK(x.is_contiguous() && scale.is_contiguous() &&
                x.storage_offset() % 8 == 0 && scale.storage_offset() % 8 == 0,
                "vectors must be contiguous with 32B-aligned element offset");
    TORCH_CHECK(x.numel() >= 64 && x.numel() <= 1792 && x.numel() % 64 == 0,
                "probe count must be 64-aligned in [64,1792]");
}
void prepare_meta(const at::Tensor& x, const at::Tensor& scale) { check_meta(x, scale); }
std::tuple<at::Tensor, at::Tensor> exact_meta(
    const at::Tensor& x, const at::Tensor& scale)
{
    check_meta(x, scale);
    // Full returned backing buffers, not views. Eight sentinel ints on each end.
    return {at::empty({x.numel()+16}, x.options()),
            at::empty({x.numel()+16}, x.options())};
}
TORCH_LIBRARY_FRAGMENT(qwen36_damp_quantizer, m)
{
    m.def("prepare(Tensor x_bits, Tensor scale_bits) -> ()");
    m.def("exact_bits(Tensor x_bits, Tensor scale_bits) -> (Tensor, Tensor)");
}
TORCH_LIBRARY_IMPL(qwen36_damp_quantizer, PrivateUse1, m)
{
    m.impl("prepare", TORCH_FN(damp_quantizer_extension::prepare));
    m.impl("exact_bits", TORCH_FN(damp_quantizer_extension::exact_bits));
}
TORCH_LIBRARY_IMPL(qwen36_damp_quantizer, Meta, m)
{
    m.impl("prepare", &prepare_meta);
    m.impl("exact_bits", &exact_meta);
}
}

