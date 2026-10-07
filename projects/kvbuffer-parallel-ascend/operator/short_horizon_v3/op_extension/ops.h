#ifndef QWEN36_GDN_KVBUFFER_SHORT_HORIZON_V3_OPS_H
#define QWEN36_GDN_KVBUFFER_SHORT_HORIZON_V3_OPS_H

#include <torch/extension.h>

namespace ascend_kernel {

__attribute__((visibility("default"))) void qwen36_gdn_kvbuffer_short_horizon_v3_prepare(
    const at::Tensor& query,const at::Tensor& baseState);

__attribute__((visibility("default"))) at::Tensor qwen36_gdn_kvbuffer_short_horizon_v3_decode(
    const at::Tensor& query,
    const at::Tensor& key,
    const at::Tensor& value,
    const at::Tensor& g,
    const at::Tensor& beta,
    const at::Tensor& baseState,
    const at::Tensor& kLog,
    const at::Tensor& uLog,
    const at::Tensor& lambdaLog,
    const at::Tensor& cumulativeDecay,
    const at::Tensor& logLength,
    const at::Tensor& actualSeqLengths,
    const at::Tensor& stateIndices);

} // namespace ascend_kernel

#endif
