#pragma once
#include <torch/extension.h>
namespace ascend_kernel {
void qwen36_native_recurrent_copy_trace_v2_prepare(const at::Tensor&,const at::Tensor&);
at::Tensor qwen36_native_recurrent_copy_trace_v2_tiling_info(const at::Tensor&,const at::Tensor&);
at::Tensor qwen36_native_recurrent_copy_trace_v2_decode_trace(const at::Tensor&,const at::Tensor&,const at::Tensor&,
 const at::Tensor&,const at::Tensor&,const at::Tensor&,const at::Tensor&,
 const at::Tensor&,const at::Tensor&,const at::Tensor&);
}
