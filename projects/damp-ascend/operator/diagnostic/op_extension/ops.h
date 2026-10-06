#ifndef QWEN36_GDN_DAMP_TRACE_OPS_H
#define QWEN36_GDN_DAMP_TRACE_OPS_H
#include <torch/extension.h>
#include <tuple>

namespace damp_trace_extension {
void qwen36_gdn_damp_trace_prepare_torch(
    const at::Tensor& query, const at::Tensor& highState,
    const at::Tensor& pk, const at::Tensor& pv,
    const at::Tensor& invPv, const at::Tensor& sr);

std::tuple<at::Tensor, at::Tensor, at::Tensor> qwen36_gdn_damp_trace_torch(
    const at::Tensor& query, const at::Tensor& key, const at::Tensor& value,
    const at::Tensor& g, const at::Tensor& beta,
    const at::Tensor& highState, const at::Tensor& lowState,
    const at::Tensor& lowScale, const at::Tensor& pk, const at::Tensor& pv,
    const at::Tensor& invPv, const at::Tensor& sr,
    const at::Tensor& actualSeqLengths, const at::Tensor& stateIndices);
} // namespace damp_trace_extension
#endif
