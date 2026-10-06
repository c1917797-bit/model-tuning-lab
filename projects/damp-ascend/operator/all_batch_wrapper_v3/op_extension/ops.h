#ifndef QWEN36_GDN_DAMP_ALL_BATCH_V3_OPS_H
#define QWEN36_GDN_DAMP_ALL_BATCH_V3_OPS_H
#include <torch/extension.h>

namespace ascend_kernel {
void qwen36_gdn_damp_all_batch_v3_prepare_torch(
    const at::Tensor& query, const at::Tensor& highState,
    const at::Tensor& pk, const at::Tensor& pv,
    const at::Tensor& invPv, const at::Tensor& sr);

at::Tensor qwen36_gdn_damp_all_batch_v3_decode_torch(
    const at::Tensor& query, const at::Tensor& key, const at::Tensor& value,
    const at::Tensor& g, const at::Tensor& beta,
    const at::Tensor& highState, const at::Tensor& lowState,
    const at::Tensor& lowScale, const at::Tensor& pk, const at::Tensor& pv,
    const at::Tensor& invPv, const at::Tensor& sr,
    const at::Tensor& actualSeqLengths, const at::Tensor& stateIndices);
} // namespace ascend_kernel
#endif
