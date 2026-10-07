#ifndef QWEN36_GDN_KVBUFFER_NATIVE_ORDER_TRACE_V1_OPS_H
#define QWEN36_GDN_KVBUFFER_NATIVE_ORDER_TRACE_V1_OPS_H

#include <torch/extension.h>

namespace ascend_kernel {

__attribute__((visibility("default"))) void qwen36_gdn_kvbuffer_native_order_trace_v1_prepare(
    const at::Tensor& query,const at::Tensor& baseState);

__attribute__((visibility("default"))) at::Tensor qwen36_gdn_kvbuffer_native_order_trace_v1_decode_trace(
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
    const at::Tensor& stateIndices,
    const at::Tensor& traceStates,
    const at::Tensor& traceOutput,
    const at::Tensor& traceMeta);

} // namespace ascend_kernel

#endif
