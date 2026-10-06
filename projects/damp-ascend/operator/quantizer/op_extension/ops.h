// SPDX-License-Identifier: Apache-2.0
#ifndef QWEN36_DAMP_QUANTIZER_OPS_H
#define QWEN36_DAMP_QUANTIZER_OPS_H
#include <torch/extension.h>
#include <tuple>
namespace damp_quantizer_extension {
void prepare(const at::Tensor& xBits, const at::Tensor& scaleBits);
std::tuple<at::Tensor, at::Tensor> exact_bits(
    const at::Tensor& xBits, const at::Tensor& scaleBits);
}
#endif

