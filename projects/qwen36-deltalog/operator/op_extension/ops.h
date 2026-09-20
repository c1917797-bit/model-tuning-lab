#ifndef QWEN36_GDN_DELTALOG_DECODE_OPS_H
#define QWEN36_GDN_DELTALOG_DECODE_OPS_H

#include <torch/extension.h>

namespace ascend_kernel {

at::Tensor qwen36_gdn_deltalog_decode_torch(
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
