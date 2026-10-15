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
#include "../op_kernel/qwen36_gdn_deltalog_decode_readout_mac042_kernel.asc"

namespace ascend_kernel {
namespace {

constexpr int64_t kMaxTokens = 16;
constexpr int64_t kKeyHeads = 4;
constexpr int64_t kValueHeads = 12;
constexpr int64_t kHeadDim = 128;
constexpr int64_t kCapacity = 7;
using TilingCacheKey = std::tuple<int32_t, int64_t, int64_t, int64_t>;

void check_npu_contiguous(const at::Tensor& tensor, const char* name)
{
    TORCH_CHECK(tensor.is_privateuseone(), name, " must be on NPU");
    TORCH_CHECK(tensor.is_contiguous(), name, " must be contiguous");
}

at::Tensor get_or_create_tiling_tensor(
    const at::Tensor& like,
    const Qwen36DeltaLogReadoutMac042::DeltalogTilingData& tiling,
    int32_t deviceId,
    int64_t tokens,
    int64_t stateSlots,
    int64_t availableCoreNum)
{
    static auto* cache = new std::map<TilingCacheKey, at::Tensor>();
    static auto* cacheMutex = new std::mutex();
    const TilingCacheKey key{deviceId, tokens, stateSlots, availableCoreNum};
    std::lock_guard<std::mutex> lock(*cacheMutex);
    const auto found = cache->find(key);
    if (found != cache->end()) {
        return found->second;
    }
    at::Tensor tensor = at::empty(
        {static_cast<int64_t>(sizeof(Qwen36DeltaLogReadoutMac042::DeltalogTilingData))},
        like.options().dtype(at::kByte));
    TORCH_CHECK(
        aclrtMemcpy(tensor.mutable_data_ptr(), sizeof(Qwen36DeltaLogReadoutMac042::DeltalogTilingData),
                    &tiling, sizeof(Qwen36DeltaLogReadoutMac042::DeltalogTilingData),
                    ACL_MEMCPY_HOST_TO_DEVICE) == ACL_SUCCESS,
        "failed to upload DeltaLog tiling data during eager warmup");
    return cache->emplace(key, tensor).first->second;
}

} // namespace

at::Tensor qwen36_gdn_deltalog_decode_readout_mac042_torch(
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
    const at::Tensor& stateIndices)
{
    const c10::OptionalDeviceGuard guard(query.device());
    check_npu_contiguous(query, "query");
    check_npu_contiguous(key, "key");
    check_npu_contiguous(value, "value");
    check_npu_contiguous(g, "g");
    check_npu_contiguous(beta, "beta");
    check_npu_contiguous(baseState, "base_state");
    check_npu_contiguous(kLog, "k_log");
    check_npu_contiguous(uLog, "u_log");
    check_npu_contiguous(lambdaLog, "lambda_log");
    check_npu_contiguous(cumulativeDecay, "cumulative_decay");
    check_npu_contiguous(logLength, "log_length");
    check_npu_contiguous(actualSeqLengths, "actual_seq_lengths");
    check_npu_contiguous(stateIndices, "state_indices");

    TORCH_CHECK(query.scalar_type() == at::kBFloat16 &&
                    key.scalar_type() == at::kBFloat16 &&
                    value.scalar_type() == at::kBFloat16 &&
                    beta.scalar_type() == at::kBFloat16 &&
                    kLog.scalar_type() == at::kBFloat16,
                "query/key/value/beta/k_log must be BF16");
    TORCH_CHECK(g.scalar_type() == at::kFloat &&
                    baseState.scalar_type() == at::kFloat &&
                    uLog.scalar_type() == at::kFloat &&
                    lambdaLog.scalar_type() == at::kFloat &&
                    cumulativeDecay.scalar_type() == at::kFloat,
                "g/base_state/u_log/lambda_log/cumulative_decay must be FP32");
    TORCH_CHECK(logLength.scalar_type() == at::kInt &&
                    actualSeqLengths.scalar_type() == at::kInt &&
                    stateIndices.scalar_type() == at::kInt,
                "log_length and decode metadata must be int32");

    TORCH_CHECK(query.dim() == 3 && query.size(1) == kKeyHeads &&
                    query.size(2) == kHeadDim,
                "query must have shape [T,4,128]");
    const int64_t tokens = query.size(0);
    TORCH_CHECK(tokens > 0 && tokens <= kMaxTokens,
                "DeltaLog v1 supports 1..16 non-spec decode tokens");
    TORCH_CHECK(key.sizes() == query.sizes(), "key must match query shape");
    TORCH_CHECK(value.sizes() == at::IntArrayRef({tokens, kValueHeads, kHeadDim}),
                "value must have shape [T,12,128]");
    TORCH_CHECK(g.sizes() == at::IntArrayRef({tokens, kValueHeads}) &&
                    beta.sizes() == at::IntArrayRef({tokens, kValueHeads}),
                "g and beta must have shape [T,12]");
    TORCH_CHECK(baseState.dim() == 4 && baseState.size(0) > 0 &&
                    baseState.size(1) == kValueHeads &&
                    baseState.size(2) == kHeadDim && baseState.size(3) == kHeadDim,
                "base_state must have shape [S,12,128,128]");
    const int64_t slots = baseState.size(0);
    TORCH_CHECK(kLog.sizes() == at::IntArrayRef({slots, kKeyHeads, kCapacity, kHeadDim}),
                "k_log must have shape [S,4,7,128]");
    TORCH_CHECK(uLog.sizes() == at::IntArrayRef({slots, kValueHeads, kCapacity, kHeadDim}),
                "u_log must have shape [S,12,7,128]");
    TORCH_CHECK(lambdaLog.sizes() == at::IntArrayRef({slots, kValueHeads, 16}),
                "lambda_log must have padded shape [S,12,16]");
    TORCH_CHECK(cumulativeDecay.sizes() == at::IntArrayRef({slots, kValueHeads, 16}),
                "cumulative_decay must have padded shape [S,12,16]");
    TORCH_CHECK(logLength.sizes() == at::IntArrayRef({slots, kValueHeads, 16}),
                "log_length must have padded shape [S,12,16]");
    TORCH_CHECK(actualSeqLengths.dim() == 1 &&
                    actualSeqLengths.numel() == tokens + 1,
                "actual_seq_lengths must contain T+1 elements");
    TORCH_CHECK(stateIndices.dim() == 1 && stateIndices.numel() == tokens,
                "state_indices must contain T elements");

    at::Tensor out = at::empty({tokens, kValueHeads, kHeadDim}, query.options());
    int32_t deviceId = -1;
    TORCH_CHECK(aclrtGetDevice(&deviceId) == ACL_SUCCESS, "failed to get NPU device");
    int64_t availableCoreNum = 0;
    TORCH_CHECK(
        aclrtGetDeviceInfo(deviceId, ACL_DEV_ATTR_VECTOR_CORE_NUM, &availableCoreNum) == ACL_SUCCESS &&
            availableCoreNum > 0,
        "failed to get NPU vector-core count");

    Qwen36DeltaLogReadoutMac042::DeltalogTilingData tiling{
        static_cast<uint32_t>(tokens), static_cast<uint32_t>(slots),
        static_cast<uint32_t>(availableCoreNum), 64,
        1.0f / std::sqrt(static_cast<float>(kHeadDim))};
    at::Tensor tilingTensor = get_or_create_tiling_tensor(
        query, tiling, deviceId, tokens, slots, availableCoreNum);
    const uint32_t blockNum = static_cast<uint32_t>(
        std::min<int64_t>(availableCoreNum, tokens * kValueHeads));
    auto stream = c10_npu::getCurrentNPUStream().stream(false);

    auto aclCall = [=]() -> int {
        qwen36_gdn_deltalog_decode_readout_mac042_kernel<<<blockNum, nullptr, stream>>>(
            (GM_ADDR)query.mutable_data_ptr(),
            (GM_ADDR)key.mutable_data_ptr(),
            (GM_ADDR)value.mutable_data_ptr(),
            (GM_ADDR)g.mutable_data_ptr(),
            (GM_ADDR)beta.mutable_data_ptr(),
            (GM_ADDR)baseState.mutable_data_ptr(),
            (GM_ADDR)kLog.mutable_data_ptr(),
            (GM_ADDR)uLog.mutable_data_ptr(),
            (GM_ADDR)lambdaLog.mutable_data_ptr(),
            (GM_ADDR)cumulativeDecay.mutable_data_ptr(),
            (GM_ADDR)logLength.mutable_data_ptr(),
            (GM_ADDR)actualSeqLengths.mutable_data_ptr(),
            (GM_ADDR)stateIndices.mutable_data_ptr(),
            (GM_ADDR)out.mutable_data_ptr(),
            (GM_ADDR)tilingTensor.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36GdnDeltalogDecodeReadoutMac042", aclCall);
    return out;
}

} // namespace ascend_kernel
