// Test-only independent native-derived reference. See ../README.md.
#pragma once
#include <tuple>
#include <ATen/ATen.h>
namespace qwen36_damp_reference {
using Outputs = std::tuple<at::Tensor, at::Tensor, at::Tensor>;
Outputs decode(const at::Tensor& q, const at::Tensor& k, const at::Tensor& v,
               const at::Tensor& g, const at::Tensor& beta,
               const at::Tensor& selected, const at::Tensor& pk,
               const at::Tensor& pv, const at::Tensor& invPv, const at::Tensor& sr);
Outputs meta(const at::Tensor& q, const at::Tensor& k, const at::Tensor& v,
             const at::Tensor& g, const at::Tensor& beta,
             const at::Tensor& selected, const at::Tensor& pk,
             const at::Tensor& pv, const at::Tensor& invPv, const at::Tensor& sr);
}
