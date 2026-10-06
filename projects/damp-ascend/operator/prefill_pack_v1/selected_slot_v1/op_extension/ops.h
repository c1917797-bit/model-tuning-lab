// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <torch/extension.h>
namespace damp_selected_prefill_extension {
void prepare(const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&,
             const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&,bool);
at::Tensor pack(const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&,
                const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&,bool);
}
