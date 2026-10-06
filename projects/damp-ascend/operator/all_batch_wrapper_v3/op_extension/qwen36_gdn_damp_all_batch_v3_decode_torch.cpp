#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <limits>
#include <string>
#include <optional>
#include <mutex>
#include <tuple>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "../op_kernel/qwen36_gdn_damp_all_batch_v3_decode_kernel.asc"
#include "ops.h"

namespace ascend_kernel {
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
std::pair<uintptr_t, uintptr_t> tensor_span(const at::Tensor& tensor)
{
    // Only contiguous physical ND tensors reach dispatch. Never infer disjoint
    // addresses from Tensor/Storage object identity: Mamba SoA shares storage.
    // Every view must be wholly contained in its actual backing byte interval.
    const int64_t elements = tensor.numel();
    const size_t itemBytes = tensor.element_size();
    const uintptr_t maximum = std::numeric_limits<uintptr_t>::max();
    TORCH_CHECK(elements > 0 && itemBytes > 0,
                "arena ABI requires nonempty positive-width tensors");
    TORCH_CHECK(static_cast<uint64_t>(elements) <=
                    maximum / static_cast<uint64_t>(itemBytes),
                "tensor byte-count multiplication overflow");
    const uintptr_t bytes = static_cast<uintptr_t>(elements) *
                            static_cast<uintptr_t>(itemBytes);
    const auto storage = tensor.storage();
    const uintptr_t base = reinterpret_cast<uintptr_t>(storage.data_ptr().get());
    const uint64_t backingBytes = static_cast<uint64_t>(storage.nbytes());
    TORCH_CHECK(base != 0 && backingBytes > 0 && backingBytes <= maximum - base,
                "backing storage byte range is empty/overflows");
    const uintptr_t storageEnd = base + static_cast<uintptr_t>(backingBytes);
    // storage_offset is in THIS view's elements, including dtype-reinterpreted
    // raw-cache views. Check its byte conversion, not the allocator's indices.
    const int64_t elementOffset = tensor.storage_offset();
    TORCH_CHECK(elementOffset >= 0 &&
                    static_cast<uint64_t>(elementOffset) <=
                        maximum / static_cast<uint64_t>(itemBytes),
                "tensor storage offset is negative/overflows byte conversion");
    const uintptr_t offsetBytes = static_cast<uintptr_t>(elementOffset) *
                                  static_cast<uintptr_t>(itemBytes);
    TORCH_CHECK(offsetBytes < backingBytes && offsetBytes <= maximum - base,
                "tensor storage offset lies outside its backing storage");
    const uintptr_t begin = reinterpret_cast<uintptr_t>(tensor.data_ptr());
    TORCH_CHECK(begin == base + offsetBytes,
                "tensor data pointer disagrees with storage offset/element width");
    TORCH_CHECK(begin >= base && begin < storageEnd && bytes <= storageEnd - begin,
                "tensor data interval lies outside its backing storage");
    return {begin, begin + bytes};
}
void check_writer_dma_span(const at::Tensor& tensor, const char* name)
{
    const auto span = tensor_span(tensor);
    TORCH_CHECK((span.second - span.first) % 32 == 0,
                name, " writer byte length must be 32B aligned");
    // Do not impose this length rule on readonly short metadata. Their existing
    // DataCopyPad path legitimately reads B1 indices=4B and lengths=8B.

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
    TORCH_CHECK(reinterpret_cast<uintptr_t>(tensor.data_ptr()) % 32 == 0,
                name, " requires a 32B-aligned physical pointer");
    (void)tensor_span(tensor); // Bounds for EVERY readonly/mutable tensor, before writer dispatch.
}
int64_t check_query_state(const at::Tensor& query, const at::Tensor& highState)
{
    check_tensor(query, query, at::kBFloat16, "query");
    TORCH_CHECK(query.dim() == 3 && query.size(1) == 4 && query.size(2) == 128,
                "query must have shape [T,4,128]");
    const int64_t tokens = query.size(0);
    TORCH_CHECK(tokens >= 1 && tokens <= 16, "DAMP all-batch v3 accepts T1..16 only");
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
    const char* soc = aclrtGetSocName();
    TORCH_CHECK(soc != nullptr && std::string(soc) == "Ascend910B4",
                "unvalidated all-batch-wrapper v3 is restricted to Ascend910B4");
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
    const auto sa = tensor_span(a), sb = tensor_span(b);
    TORCH_CHECK(sa.second <= sb.first || sb.second <= sa.first,
                "typed tensor DATA byte intervals overlap; shared backing storage alone is allowed");
}
uint32_t bit_length(uint32_t value)
{
    uint32_t count = 0;
    while (value != 0) { ++count; value >>= 1; }
    return count;
}
void initialize_quantizer_lut(Qwen36DampIntegerCompactionV1::DampTilingData& tiling)
{
    // Identical logical C/F values to the frozen integer_certificate.py tables.
    // j127 is an unused safe duplicate of j126; all gathers are clamped earlier.
    for (uint32_t j = 0; j < 128; ++j) {
        const uint32_t safeJ = std::min<uint32_t>(j, 126);
        const uint32_t twiceT = 2 * safeJ + 1;
        const int32_t exponent = static_cast<int32_t>(bit_length(twiceT)) - 2;
        const uint32_t center = twiceT << (23 - exponent);
        tiling.cTable[j] = static_cast<int32_t>((safeJ & 1) ? center - 1 : center + 1);
        tiling.fTable[j] = exponent;
    }
}
} // namespace

void qwen36_gdn_damp_all_batch_v3_prepare_torch(
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
    Qwen36DampIntegerCompactionV1::DampTilingData tiling{};
    tiling.tokens = static_cast<uint32_t>(query.size(0));
    tiling.stateSlots = static_cast<uint32_t>(highState.size(0));
    tiling.vectorCoreNum = static_cast<uint32_t>(coreNum);
    tiling.abiVersion = Qwen36DampIntegerCompactionV1::ABI_VERSION;
    tiling.qScale = 1.0f / std::sqrt(128.0f);
    initialize_quantizer_lut(tiling);
    at::Tensor tensor = at_npu::native::custom_ops::npu_format_cast(
        at::empty({static_cast<int64_t>(sizeof(tiling))}, query.options().dtype(at::kByte)),
        ACL_FORMAT_ND, std::nullopt, std::nullopt);
    check_tensor(tensor, query, at::kByte, "tiling");
    // Cold preparation only. Flush queued allocation/format work outside any
    // RunOpApi lambda before the synchronous immutable LUT/tiling upload.
    auto prepareStream = c10_npu::getCurrentNPUStream().stream(true);
    TORCH_CHECK(aclrtSynchronizeStream(prepareStream) == ACL_SUCCESS, "prepare sync failed");
    TORCH_CHECK(aclrtMemcpy(tensor.mutable_data_ptr(), sizeof(tiling), &tiling,
                            sizeof(tiling), ACL_MEMCPY_HOST_TO_DEVICE) == ACL_SUCCESS,
                "DAMP prepare tiling upload failed; prepare must run outside capture");
    tiling_cache().emplace(cacheKey, PreparedEntry{tensor, pk, pv, invPv, sr});
}

at::Tensor qwen36_gdn_damp_all_batch_v3_decode_torch(
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
    check_writer_dma_span(highState, "high_state");
    check_plans(query, pk, pv, invPv, sr);
    check_tensor(key, query, at::kBFloat16, "key");
    check_tensor(value, query, at::kBFloat16, "value");
    check_tensor(g, query, at::kFloat, "g");
    check_tensor(beta, query, at::kBFloat16, "beta");
    check_tensor(lowState, query, at::kChar, "low_state");
    check_tensor(lowScale, query, at::kFloat, "low_scale");
    check_writer_dma_span(lowState, "low_state");
    check_writer_dma_span(lowScale, "low_scale");
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
    check_tensor(tilingTensor, query, at::kByte, "tiling");
    check_disjoint(highState, tilingTensor);
    check_disjoint(lowState, tilingTensor);
    check_disjoint(lowScale, tilingTensor);
    at::Tensor out = at_npu::native::custom_ops::npu_format_cast(
        at::empty({tokens, 12, 128}, query.options()), ACL_FORMAT_ND,
        std::nullopt, std::nullopt);
    check_tensor(out, query, at::kBFloat16, "out");
    check_writer_dma_span(out, "out");
    const at::Tensor* outputInputs[] = {&query, &key, &value, &g, &beta, &highState,
                                      &lowState, &lowScale, &pk, &pv, &invPv, &sr,
                                      &actualSeqLengths, &stateIndices, &tilingTensor};
    for (const at::Tensor* input : outputInputs) {
        check_disjoint(out, *input);
    }
    const uint32_t blockNum =
        static_cast<uint32_t>(std::min<int64_t>(coreNum, tokens * 12));
    // This TU is compiled as ASC, includes the kernel, and enqueues its launch.
    // Do not replace with an unqueued C++ direct launch or stream(true) per layer.
    auto stream = c10_npu::getCurrentNPUStream().stream(false);
    auto aclCall = [=]() -> int {
        qwen36_gdn_damp_all_batch_v3_decode_kernel<<<blockNum, nullptr, stream>>>(
            (GM_ADDR)query.mutable_data_ptr(), (GM_ADDR)key.mutable_data_ptr(),
            (GM_ADDR)value.mutable_data_ptr(), (GM_ADDR)g.mutable_data_ptr(),
            (GM_ADDR)beta.mutable_data_ptr(), (GM_ADDR)highState.mutable_data_ptr(),
            (GM_ADDR)lowState.mutable_data_ptr(), (GM_ADDR)lowScale.mutable_data_ptr(),
            (GM_ADDR)pk.mutable_data_ptr(), (GM_ADDR)pv.mutable_data_ptr(),
            (GM_ADDR)invPv.mutable_data_ptr(), (GM_ADDR)sr.mutable_data_ptr(),
            (GM_ADDR)actualSeqLengths.mutable_data_ptr(),
            (GM_ADDR)stateIndices.mutable_data_ptr(), (GM_ADDR)out.mutable_data_ptr(),
            (GM_ADDR)tilingTensor.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36GdnDampAllBatchV3Decode", aclCall);
    return out;
}
} // namespace ascend_kernel
