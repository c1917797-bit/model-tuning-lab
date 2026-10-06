// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <torch/extension.h>
#include <tuple>
namespace damp_prefill_float_probe_extension {
using Outputs=std::tuple<at::Tensor,at::Tensor,at::Tensor,at::Tensor>;
void prepare(const at::Tensor& x,const at::Tensor& scale,const at::Tensor& proposal,bool useCandidate);
Outputs divide_bits(const at::Tensor& x,const at::Tensor& scale,const at::Tensor& proposal,bool useCandidate);
}
