#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"

namespace {

TORCH_LIBRARY_FRAGMENT(qwen36_deltalog_split_scale_sidecar_v051, m)
{
    m.def(
        "decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, "
        "Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
        "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, "
        "Tensor(f!) log_length, Tensor actual_seq_lengths, "
        "Tensor state_indices, Tensor(g!) precast_fp32) -> Tensor");
}

TORCH_LIBRARY_IMPL(qwen36_deltalog_split_scale_sidecar_v051, PrivateUse1, m)
{
    m.impl("decode", TORCH_FN(ascend_kernel::qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_torch));
}

at::Tensor qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_meta(
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
    const at::Tensor&,
    const at::Tensor&)
{
    return at::empty({query.size(0), 12, 128}, query.options());
}

TORCH_LIBRARY_IMPL(qwen36_deltalog_split_scale_sidecar_v051, Meta, m)
{
    m.impl("decode", &qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_meta);
}

} // namespace
