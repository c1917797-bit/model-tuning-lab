#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"

namespace {

TORCH_LIBRARY_FRAGMENT(qwen36_kvbuffer_native_order_trace_v1, m)
{
    m.def("prepare(Tensor query, Tensor base_state) -> ()");
    m.def(
        "decode_trace(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, "
        "Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
        "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, "
        "Tensor(f!) log_length, Tensor actual_seq_lengths, "
        "Tensor state_indices, Tensor(g!) trace_states, Tensor(h!) trace_output, "
        "Tensor(i!) trace_meta) -> Tensor");
}

TORCH_LIBRARY_IMPL(qwen36_kvbuffer_native_order_trace_v1, PrivateUse1, m)
{
    m.impl("prepare", TORCH_FN(ascend_kernel::qwen36_gdn_kvbuffer_native_order_trace_v1_prepare));
    m.impl("decode_trace", TORCH_FN(ascend_kernel::qwen36_gdn_kvbuffer_native_order_trace_v1_decode_trace));
}

void check_meta_geometry(const at::Tensor& q,const at::Tensor& base)
{
    TORCH_CHECK(q.scalar_type()==at::kBFloat16 && q.sizes()==at::IntArrayRef({16,4,128}),
                "trace Meta query requires exact T16/BF16 geometry");
    TORCH_CHECK(base.scalar_type()==at::kFloat && base.sizes()==at::IntArrayRef({19,12,128,128}),
                "trace Meta base requires exact S19/FP32 geometry");
}

at::Tensor qwen36_gdn_kvbuffer_native_order_trace_v1_meta(
    const at::Tensor& query,const at::Tensor& key,const at::Tensor& value,
    const at::Tensor& g,const at::Tensor& beta,const at::Tensor& base,
    const at::Tensor& kl,const at::Tensor& ul,const at::Tensor& lam,
    const at::Tensor& decay,const at::Tensor& len,const at::Tensor& seq,
    const at::Tensor& idx,const at::Tensor& traceStates,
    const at::Tensor& traceOutput,const at::Tensor& traceMeta)
{
    check_meta_geometry(query,base);
    TORCH_CHECK(key.scalar_type()==at::kBFloat16 && key.sizes()==query.sizes(),"trace Meta key");
    TORCH_CHECK(value.scalar_type()==at::kBFloat16 && value.sizes()==at::IntArrayRef({16,12,128}),"trace Meta value");
    TORCH_CHECK(g.scalar_type()==at::kFloat && g.sizes()==at::IntArrayRef({16,12}),"trace Meta g");
    TORCH_CHECK(beta.scalar_type()==at::kBFloat16 && beta.sizes()==g.sizes(),"trace Meta beta");
    TORCH_CHECK(kl.scalar_type()==at::kBFloat16 && kl.sizes()==at::IntArrayRef({19,4,16,128}),"trace Meta Klog");
    TORCH_CHECK(ul.scalar_type()==at::kFloat && ul.sizes()==at::IntArrayRef({19,12,16,128}),"trace Meta Ulog");
    TORCH_CHECK(lam.scalar_type()==at::kFloat && lam.sizes()==at::IntArrayRef({19,12,32}) &&
                decay.scalar_type()==at::kFloat && decay.sizes()==lam.sizes() &&
                len.scalar_type()==at::kInt && len.sizes()==lam.sizes(),"trace Meta metadata");
    TORCH_CHECK(seq.scalar_type()==at::kInt && seq.sizes()==at::IntArrayRef({17}) &&
                idx.scalar_type()==at::kInt && idx.sizes()==at::IntArrayRef({16}),"trace Meta sequence ABI");
    TORCH_CHECK(traceStates.scalar_type()==at::kFloat && traceStates.sizes()==at::IntArrayRef({3,32,128}) &&
                traceOutput.scalar_type()==at::kFloat && traceOutput.sizes()==at::IntArrayRef({32}) &&
                traceMeta.scalar_type()==at::kInt && traceMeta.sizes()==at::IntArrayRef({16}),
                "trace Meta explicit mutation buffers");
    // Meta only describes shape/dtype: not physical ND, aliases, copy ordering or NPU truth.
    return at::empty({16, 12, 128}, query.options());
}
void prepare_meta(const at::Tensor& q,const at::Tensor& base)
{
    check_meta_geometry(q,base);
}

TORCH_LIBRARY_IMPL(qwen36_kvbuffer_native_order_trace_v1, Meta, m)
{
    m.impl("prepare", &prepare_meta);
    m.impl("decode_trace", &qwen36_gdn_kvbuffer_native_order_trace_v1_meta);
}

} // namespace
