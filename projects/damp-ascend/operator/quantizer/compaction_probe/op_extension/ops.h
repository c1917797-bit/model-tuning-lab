// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <tuple>
#include <torch/extension.h>
namespace damp_compaction_extension {
using Outputs=std::tuple<at::Tensor,at::Tensor,at::Tensor,at::Tensor>;
void prepare(const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&);
Outputs compact(const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&);
}
