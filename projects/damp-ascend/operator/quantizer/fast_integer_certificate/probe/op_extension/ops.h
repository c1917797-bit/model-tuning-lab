// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <torch/extension.h>
#include <tuple>
namespace damp_integer_probe_extension {
using Outputs=std::tuple<at::Tensor,at::Tensor,at::Tensor,at::Tensor,
                         at::Tensor,at::Tensor,at::Tensor>;
void prepare(const at::Tensor& x,const at::Tensor& scale,const at::Tensor& n);
Outputs certify_bits(const at::Tensor& x,const at::Tensor& scale,const at::Tensor& n);
}

