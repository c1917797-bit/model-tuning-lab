#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <mutex>
#include <tuple>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "../op_kernel/qwen36_gdn_damp_trace_kernel.asc"
#include "ops.h"

namespace damp_trace_extension {
namespace {
using CacheKey = std::tuple<
    int32_t, int64_t, int64_t, int64_t,
    uintptr_t, uintptr_t, uintptr_t, uintptr_t,
    int64_t, int64_t, int64_t, int64_t>;

struct PreparedEntry {
    at::Tensor tiling;
    // Retain immutable plans, preventing freed storage addresses from reusing a
    // previously validated cache identity. No recurrent state is retained here.
    at::Tensor pk, pv, invPv, sr;
};
std::map<CacheKey, PreparedEntry>& tiling_cache()
{
    static auto* cache = new std::map<CacheKey, PreparedEntry>();
    return *cache;
}
std::mutex& tiling_mutex()
{
    static auto* mutex = new std::mutex();
    return *mutex;
}
int64_t plan_version(const at::Tensor& tensor)
{
    const auto& counter = tensor.unsafeGetTensorImpl()->version_counter();
    // Inference tensors have no version counter; their plan is immutable by ABI.
    return counter.enabled() ? static_cast<int64_t>(counter.current_version()) : -1;
}
void check_tensor(const at::Tensor& tensor, const at::Tensor& query,
                  at::ScalarType dtype, const char* name)
{
    TORCH_CHECK(tensor.is_privateuseone(), name, " must be on NPU");
    TORCH_CHECK(tensor.device() == query.device(), name, " device must match query");
    TORCH_CHECK(tensor.is_contiguous(), name, " must be contiguous");
    // Use this version's TORCH_NPU_API export. FormatHelper::GetFormat has a
    // header declaration but no dynamic export in the deployed libtorch_npu.
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(tensor) == ACL_FORMAT_ND,
                name, " must use physical ACL_FORMAT_ND; contiguous shape alone "
                      "does not authorize a blocked/internal format");
    TORCH_CHECK(tensor.scalar_type() == dtype, name, " has unsupported dtype");
}
int64_t check_query_state(const at::Tensor& query, const at::Tensor& highState)
{
    check_tensor(query, query, at::kBFloat16, "query");
    TORCH_CHECK(query.dim() == 3 && query.size(1) == 4 && query.size(2) == 128,
                "query must have shape [T,4,128]");
    const int64_t tokens = query.size(0);
    TORCH_CHECK(tokens == 1 || tokens == 16, "DAMP v1 accepts exactly B1 or B16");
    check_tensor(highState, query, at::kHalf, "high_state");
    TORCH_CHECK(highState.dim() == 4 && highState.size(0) > 0 &&
                    highState.size(0) <= UINT32_MAX && highState.size(1) == 12 &&
                    highState.size(2) == 128 && highState.size(3) == 16,
                "high_state must have shape [S,12,128,16]");
    return tokens;
}
void check_plans(const at::Tensor& query, const at::Tensor& pk,
                 const at::Tensor& pv, const at::Tensor& invPv,
                 const at::Tensor& sr)
{
    for (const auto& entry : {std::make_pair(&pk, "pk"),
                              std::make_pair(&pv, "pv"),
                              std::make_pair(&invPv, "inv_pv")}) {
        check_tensor(*entry.first, query, at::kInt, entry.second);
        TORCH_CHECK(entry.first->sizes() == at::IntArrayRef({12, 128}),
                    entry.second, " must be INT32 [12,128] logical indices");
    }
    check_tensor(sr, query, at::kFloat, "sr");
    TORCH_CHECK(sr.sizes() == at::IntArrayRef({12, 128}),
                "sr must be FP32 [12,128] in original value coordinates");
}
void check_static_plan_values(const at::Tensor& pk, const at::Tensor& pv,
                              const at::Tensor& invPv, const at::Tensor& sr)
{
    // Only prepare() calls this. These synchronous copies are forbidden in
    // capture and absent from decode(). No dense state is ever copied here.
    const at::Tensor pkCpu = pk.to(at::kCPU);
    const at::Tensor pvCpu = pv.to(at::kCPU);
    const at::Tensor invCpu = invPv.to(at::kCPU);
    const at::Tensor srCpu = sr.to(at::kCPU);
    const int32_t* kp = pkCpu.data_ptr<int32_t>();
    const int32_t* vp = pvCpu.data_ptr<int32_t>();
    const int32_t* ip = invCpu.data_ptr<int32_t>();
    const float* cp = srCpu.data_ptr<float>();
    for (int64_t h = 0; h < 12; ++h) {
        bool seenK[128] = {};
        bool seenV[128] = {};
        for (int64_t i = 0; i < 128; ++i) {
            const int64_t offset = h * 128 + i;
            const int32_t ki = kp[offset];
            const int32_t vi = vp[offset];
            const int32_t ii = ip[offset];
            TORCH_CHECK(ki >= 0 && ki < 128 && vi >= 0 && vi < 128 &&
                            ii >= 0 && ii < 128,
                        "permutation index is outside 0..127");
            TORCH_CHECK(!seenK[ki] && !seenV[vi],
                        "pk/pv must each be a full permutation");
            seenK[ki] = true;
            seenV[vi] = true;
            TORCH_CHECK(ip[h * 128 + vi] == i,
                        "inv_pv must map original to reordered value coordinates");
            TORCH_CHECK(std::isfinite(cp[offset]) && cp[offset] > 0.0f,
                        "sr must be finite and strictly positive");
        }
    }
}
CacheKey make_key(const at::Tensor& query, const at::Tensor& highState,
                  const at::Tensor& pk, const at::Tensor& pv,
                  const at::Tensor& invPv, const at::Tensor& sr,
                  int32_t& deviceId, int64_t& coreNum)
{
    TORCH_CHECK(aclrtGetDevice(&deviceId) == ACL_SUCCESS,
                "failed to get current NPU");
    TORCH_CHECK(aclrtGetDeviceInfo(deviceId, ACL_DEV_ATTR_VECTOR_CORE_NUM, &coreNum) ==
                    ACL_SUCCESS && coreNum > 0,
                "failed to query vector-core count");
    return CacheKey{
        deviceId, query.size(0), highState.size(0), coreNum,
        reinterpret_cast<uintptr_t>(pk.data_ptr()),
        reinterpret_cast<uintptr_t>(pv.data_ptr()),
        reinterpret_cast<uintptr_t>(invPv.data_ptr()),
        reinterpret_cast<uintptr_t>(sr.data_ptr()),
        plan_version(pk), plan_version(pv), plan_version(invPv), plan_version(sr)};
}
void check_disjoint(const at::Tensor& a, const at::Tensor& b)
{
    const uintptr_t ab = reinterpret_cast<uintptr_t>(a.data_ptr());
    const uintptr_t bb = reinterpret_cast<uintptr_t>(b.data_ptr());
    const uintptr_t ae = ab + static_cast<uintptr_t>(a.numel() * a.element_size());
    const uintptr_t be = bb + static_cast<uintptr_t>(b.numel() * b.element_size());
    TORCH_CHECK(ae <= bb || be <= ab, "DAMP mutable state buffers must not alias");
}
} // namespace

void qwen36_gdn_damp_trace_prepare_torch(
    const at::Tensor& query, const at::Tensor& highState,
    const at::Tensor& pk, const at::Tensor& pv,
    const at::Tensor& invPv, const at::Tensor& sr)
{
    const c10::OptionalDeviceGuard guard(query.device());
    check_query_state(query, highState);
    check_plans(query, pk, pv, invPv, sr);
    int32_t deviceId = -1;
    int64_t coreNum = 0;
    const CacheKey cacheKey = make_key(query, highState, pk, pv, invPv, sr,
                                      deviceId, coreNum);
    std::lock_guard<std::mutex> lock(tiling_mutex());
    if (tiling_cache().find(cacheKey) != tiling_cache().end()) {
        return;
    }
    check_static_plan_values(pk, pv, invPv, sr);
    const Qwen36DampTrace::DampTilingData tiling{
        static_cast<uint32_t>(query.size(0)),
        static_cast<uint32_t>(highState.size(0)),
        static_cast<uint32_t>(coreNum), Qwen36DampTrace::ABI_VERSION,
        1.0f / std::sqrt(128.0f)};
    at::Tensor tensor = at::empty(
        {static_cast<int64_t>(sizeof(tiling))}, query.options().dtype(at::kByte));
    check_tensor(tensor, query, at::kByte, "tiling");
    TORCH_CHECK(aclrtMemcpy(tensor.mutable_data_ptr(), sizeof(tiling), &tiling,
                            sizeof(tiling), ACL_MEMCPY_HOST_TO_DEVICE) == ACL_SUCCESS,
                "DAMP prepare tiling upload failed; prepare must run outside capture");
    tiling_cache().emplace(cacheKey, PreparedEntry{tensor, pk, pv, invPv, sr});
}

std::tuple<at::Tensor, at::Tensor, at::Tensor> qwen36_gdn_damp_trace_torch(
    const at::Tensor& query, const at::Tensor& key, const at::Tensor& value,
    const at::Tensor& g, const at::Tensor& beta,
    const at::Tensor& highState, const at::Tensor& lowState,
    const at::Tensor& lowScale, const at::Tensor& pk, const at::Tensor& pv,
    const at::Tensor& invPv, const at::Tensor& sr,
    const at::Tensor& actualSeqLengths, const at::Tensor& stateIndices)
{
    const c10::OptionalDeviceGuard guard(query.device());
    const int64_t tokens = check_query_state(query, highState);
    const int64_t slots = highState.size(0);
    check_plans(query, pk, pv, invPv, sr);
    check_tensor(key, query, at::kBFloat16, "key");
    check_tensor(value, query, at::kBFloat16, "value");
    check_tensor(g, query, at::kFloat, "g");
    check_tensor(beta, query, at::kBFloat16, "beta");
    check_tensor(lowState, query, at::kChar, "low_state");
    check_tensor(lowScale, query, at::kFloat, "low_scale");
    check_tensor(actualSeqLengths, query, at::kInt, "actual_seq_lengths");
    check_tensor(stateIndices, query, at::kInt, "state_indices");
    TORCH_CHECK(key.sizes() == query.sizes(), "key must match query [T,4,128]");
    TORCH_CHECK(value.sizes() == at::IntArrayRef({tokens, 12, 128}),
                "value must have shape [T,12,128]");
    TORCH_CHECK(g.sizes() == at::IntArrayRef({tokens, 12}) &&
                    beta.sizes() == at::IntArrayRef({tokens, 12}),
                "g/beta must have shape [T,12]");
    TORCH_CHECK(lowState.sizes() == at::IntArrayRef({slots, 12, 128, 112}),
                "low_state must have shape [S,12,128,112]");
    TORCH_CHECK(lowScale.sizes() == at::IntArrayRef({slots, 12, 4, 112}),
                "low_scale must have shape [S,12,4,112]");
    TORCH_CHECK(actualSeqLengths.sizes() == at::IntArrayRef({tokens + 1}) &&
                    stateIndices.sizes() == at::IntArrayRef({tokens}),
                "one-token metadata shapes must be [T+1] and [T]");
    check_disjoint(highState, lowState);
    check_disjoint(highState, lowScale);
    check_disjoint(lowState, lowScale);
    for (const at::Tensor* input : {&query, &key, &value, &g, &beta,
                                   &pk, &pv, &invPv, &sr,
                                   &actualSeqLengths, &stateIndices}) {
        check_disjoint(highState, *input);
        check_disjoint(lowState, *input);
        check_disjoint(lowScale, *input);
    }

    int32_t deviceId = -1;
    int64_t coreNum = 0;
    const CacheKey cacheKey = make_key(query, highState, pk, pv, invPv, sr,
                                      deviceId, coreNum);
    at::Tensor tilingTensor;
    {
        std::lock_guard<std::mutex> lock(tiling_mutex());
        const auto found = tiling_cache().find(cacheKey);
        TORCH_CHECK(found != tiling_cache().end(),
                    "DAMP decode is cold: call prepare outside capture for this "
                    "device/T/S/immutable-plan identity first");
        tilingTensor = found->second.tiling;
    }
    at::Tensor out = at::empty({tokens, 12, 128}, query.options());
    check_tensor(out, query, at::kBFloat16, "out");
    // The deployed factory can select a non-ND format for 4D FP32 outputs.
    // This conversion is diagnostic-only; retain the physical-format gate.
    at::Tensor updated = at_npu::native::custom_ops::npu_format_cast(
        at::empty({tokens, 12, 128, 128}, query.options().dtype(at::kFloat)),
        ACL_FORMAT_ND, std::nullopt, std::nullopt);
    at::Tensor quotient = at_npu::native::custom_ops::npu_format_cast(
        at::empty({tokens, 12, 128, 112}, query.options().dtype(at::kFloat)),
        ACL_FORMAT_ND, std::nullopt, std::nullopt);
    check_tensor(updated, query, at::kFloat, "updated_trace");
    check_tensor(quotient, query, at::kFloat, "quotient_trace");
    for (const at::Tensor* result : {&out, &updated, &quotient}) {
        for (const at::Tensor* input : {&query, &key, &value, &g, &beta,
                                       &highState, &lowState, &lowScale,
                                       &pk, &pv, &invPv, &sr,
                                       &actualSeqLengths, &stateIndices}) {
            check_disjoint(*result, *input);
        }
    }
    check_disjoint(out, updated);
    check_disjoint(out, quotient);
    check_disjoint(updated, quotient);
    const uint32_t blockNum =
        static_cast<uint32_t>(std::min<int64_t>(coreNum, tokens * 12));
    // This TU is compiled as ASC, includes the kernel, and enqueues its launch.
    // Do not replace with an unqueued C++ direct launch or stream(true) per layer.
    auto stream = c10_npu::getCurrentNPUStream().stream(false);
    auto aclCall = [=]() -> int {
        qwen36_gdn_damp_trace_kernel<<<blockNum, nullptr, stream>>>(
            (GM_ADDR)query.mutable_data_ptr(), (GM_ADDR)key.mutable_data_ptr(),
            (GM_ADDR)value.mutable_data_ptr(), (GM_ADDR)g.mutable_data_ptr(),
            (GM_ADDR)beta.mutable_data_ptr(), (GM_ADDR)highState.mutable_data_ptr(),
            (GM_ADDR)lowState.mutable_data_ptr(), (GM_ADDR)lowScale.mutable_data_ptr(),
            (GM_ADDR)pk.mutable_data_ptr(), (GM_ADDR)pv.mutable_data_ptr(),
            (GM_ADDR)invPv.mutable_data_ptr(), (GM_ADDR)sr.mutable_data_ptr(),
            (GM_ADDR)actualSeqLengths.mutable_data_ptr(),
            (GM_ADDR)stateIndices.mutable_data_ptr(), (GM_ADDR)out.mutable_data_ptr(),
            (GM_ADDR)updated.mutable_data_ptr(), (GM_ADDR)quotient.mutable_data_ptr(),
            (GM_ADDR)tilingTensor.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36GdnDampTrace", aclCall);
    return {out, updated, quotient};
}
} // namespace damp_trace_extension
