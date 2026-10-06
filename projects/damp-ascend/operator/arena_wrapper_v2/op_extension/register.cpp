#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"

namespace {
TORCH_LIBRARY_FRAGMENT(qwen36_damp_arena_v2, m)
{
    m.def("prepare(Tensor query, Tensor high_state, Tensor pk, Tensor pv, "
          "Tensor inv_pv, Tensor sr) -> ()");
    m.def(
        "decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, "
        "Tensor(a!) high_state, Tensor(b!) low_state, Tensor(c!) low_scale, "
        "Tensor pk, Tensor pv, Tensor inv_pv, Tensor sr, "
        "Tensor actual_seq_lengths, Tensor state_indices) -> Tensor");
}
TORCH_LIBRARY_IMPL(qwen36_damp_arena_v2, PrivateUse1, m)
{
    m.impl("prepare", TORCH_FN(ascend_kernel::qwen36_gdn_damp_arena_v2_prepare_torch));
    m.impl("decode", TORCH_FN(ascend_kernel::qwen36_gdn_damp_arena_v2_decode_torch));
}
void check_meta_plan(const at::Tensor& tensor, at::ScalarType dtype, const char* name)
{
    TORCH_CHECK(tensor.scalar_type() == dtype && tensor.is_contiguous() &&
                    tensor.sizes() == at::IntArrayRef({12, 128}),
                name, " has unsupported static plan shape/dtype/layout");
}
void prepare_meta(
    const at::Tensor& query, const at::Tensor& hi, const at::Tensor& pk,
    const at::Tensor& pv, const at::Tensor& invPv, const at::Tensor& sr)
{
    TORCH_CHECK(query.scalar_type() == at::kBFloat16 && query.is_contiguous() &&
                    query.dim() == 3 && query.size(1) == 4 && query.size(2) == 128 &&
                    (query.size(0) == 1 || query.size(0) == 16),
                "query must be BF16 B1/B16 [T,4,128]");
    TORCH_CHECK(hi.scalar_type() == at::kHalf && hi.is_contiguous() &&
                    hi.dim() == 4 && hi.size(0) > 0 && hi.size(1) == 12 &&
                    hi.size(2) == 128 && hi.size(3) == 16,
                "high_state must be contiguous FP16 [S,12,128,16]");
    check_meta_plan(pk, at::kInt, "pk");
    check_meta_plan(pv, at::kInt, "pv");
    check_meta_plan(invPv, at::kInt, "inv_pv");
    check_meta_plan(sr, at::kFloat, "sr");
    // No values, NPU resources, or H2D transfers are available on Meta.
}
at::Tensor decode_meta(
    const at::Tensor& query, const at::Tensor& key, const at::Tensor& value,
    const at::Tensor& g, const at::Tensor& beta, const at::Tensor& hi,
    const at::Tensor& lo, const at::Tensor& scales, const at::Tensor& pk,
    const at::Tensor& pv, const at::Tensor& invPv, const at::Tensor& sr,
    const at::Tensor& lengths, const at::Tensor& indices)
{
    prepare_meta(query, hi, pk, pv, invPv, sr);
    const int64_t tokens = query.size(0);
    const int64_t slots = hi.size(0);
    TORCH_CHECK(key.scalar_type() == at::kBFloat16 && key.sizes() == query.sizes() &&
                    value.scalar_type() == at::kBFloat16 &&
                    value.sizes() == at::IntArrayRef({tokens, 12, 128}),
                "key/value Meta shape/dtype mismatch");
    TORCH_CHECK(g.scalar_type() == at::kFloat && beta.scalar_type() == at::kBFloat16 &&
                    g.sizes() == at::IntArrayRef({tokens, 12}) &&
                    beta.sizes() == g.sizes(), "g/beta Meta shape/dtype mismatch");
    TORCH_CHECK(lo.scalar_type() == at::kChar &&
                    lo.sizes() == at::IntArrayRef({slots, 12, 128, 112}) &&
                    scales.scalar_type() == at::kFloat &&
                    scales.sizes() == at::IntArrayRef({slots, 12, 4, 112}),
                "packed state Meta shape/dtype mismatch");
    TORCH_CHECK(lengths.scalar_type() == at::kInt && indices.scalar_type() == at::kInt &&
                    lengths.sizes() == at::IntArrayRef({tokens + 1}) &&
                    indices.sizes() == at::IntArrayRef({tokens}),
                "one-token metadata Meta shape/dtype mismatch");
    return at::empty({tokens, 12, 128}, query.options());
}
TORCH_LIBRARY_IMPL(qwen36_damp_arena_v2, Meta, m)
{
    m.impl("prepare", &prepare_meta);
    m.impl("decode", &decode_meta);
}
} // namespace
