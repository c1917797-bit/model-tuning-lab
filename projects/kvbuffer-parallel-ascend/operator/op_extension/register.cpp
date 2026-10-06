#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"

namespace {

TORCH_LIBRARY_FRAGMENT(qwen36_kvbuffer_parallel_fp32, m)
{
    m.def("prepare(Tensor query, Tensor base_state) -> ()");
    m.def(
        "decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, "
        "Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
        "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, "
        "Tensor(f!) log_length, Tensor actual_seq_lengths, "
        "Tensor state_indices) -> Tensor");
}

TORCH_LIBRARY_IMPL(qwen36_kvbuffer_parallel_fp32, PrivateUse1, m)
{
    m.impl("prepare", TORCH_FN(ascend_kernel::qwen36_gdn_kvbuffer_parallel_prepare));
    m.impl("decode", TORCH_FN(ascend_kernel::qwen36_gdn_kvbuffer_parallel_decode));
}

at::Tensor qwen36_gdn_kvbuffer_parallel_meta(
    const at::Tensor& query,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&)
{
    return at::empty({query.size(0), 12, 128}, query.options());
}

void prepare_meta(const at::Tensor&,const at::Tensor&) {}

TORCH_LIBRARY_IMPL(qwen36_kvbuffer_parallel_fp32, Meta, m)
{
    m.impl("prepare", &prepare_meta);
    m.impl("decode", &qwen36_gdn_kvbuffer_parallel_meta);
}

} // namespace
