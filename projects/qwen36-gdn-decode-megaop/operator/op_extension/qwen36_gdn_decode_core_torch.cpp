/**
 * Copyright (c) 2026 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under the terms and conditions of
 * CANN Open Software License Agreement Version 2.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the software repository for the full text of the License.
 */

// This translation unit deliberately contains both the Ascend C kernel and
// the PyTorch host wrapper.  That is required for the queue-safe fast-launch
// pattern used by ops-transformer:
//   stream(false) + triple-chevron launch + OpCommand::RunOpApi.
// A separate C++ wrapper can only call the generated C launcher and therefore
// needs stream(true), whose per-layer queue flush regressed end-to-end decode.

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
#include "../op_kernel/qwen36_gdn_decode_core_kernel.asc"

namespace ascend_kernel {

namespace {

constexpr int64_t kMaxTokens = 16;
constexpr int64_t kKeyHeads = 4;
constexpr int64_t kValueHeads = 12;
constexpr int64_t kHeadDim = 128;
constexpr uint32_t kUbBytes = 196608;
constexpr uint32_t kVStep = 64;

using TilingCacheKey = std::tuple<int32_t, int64_t, int64_t, int64_t>;

at::Tensor get_or_create_tiling_tensor(
    const at::Tensor& like,
    const RecurrentGatedDeltaRule::RecurrentGatedDeltaRuleTilingData& tiling,
    int32_t deviceId,
    int64_t tokens,
    int64_t stateSlots,
    int64_t availableCoreNum)
{
    // NPUGraph capture rejects a synchronous host-to-device memcpy.  The
    // fixed-shape service warmup creates one process-lifetime device tensor
    // per audited tiling key; capture and replay only reuse its stable pointer.
    // Heap allocation intentionally avoids NPU tensor destruction after the
    // runtime has already shut down at process exit.
    static auto* cache = new std::map<TilingCacheKey, at::Tensor>();
    static auto* cacheMutex = new std::mutex();
    const TilingCacheKey key{
        deviceId, tokens, stateSlots, availableCoreNum};
    std::lock_guard<std::mutex> lock(*cacheMutex);
    const auto found = cache->find(key);
    if (found != cache->end()) {
        return found->second;
    }

    at::Tensor tensor = at::empty(
        {static_cast<int64_t>(
            sizeof(RecurrentGatedDeltaRule::RecurrentGatedDeltaRuleTilingData))},
        like.options().dtype(at::kByte));
    TORCH_CHECK(
        aclrtMemcpy(tensor.mutable_data_ptr(),
                    sizeof(RecurrentGatedDeltaRule::RecurrentGatedDeltaRuleTilingData),
                    &tiling,
                    sizeof(RecurrentGatedDeltaRule::RecurrentGatedDeltaRuleTilingData),
                    ACL_MEMCPY_HOST_TO_DEVICE) == ACL_SUCCESS,
        "failed to upload tiling data during eager warmup");
    return cache->emplace(key, tensor).first->second;
}

void check_npu_contiguous(const at::Tensor& tensor, const char* name)
{
    TORCH_CHECK(tensor.is_privateuseone(), name, " must be on NPU");
    TORCH_CHECK(tensor.is_contiguous(), name, " must be contiguous");
}

} // namespace

at::Tensor qwen36_gdn_decode_core_torch(
    const at::Tensor& query,
    const at::Tensor& key,
    const at::Tensor& value,
    const at::Tensor& aLog,
    const at::Tensor& a,
    const at::Tensor& b,
    const at::Tensor& dtBias,
    const at::Tensor& state,
    const at::Tensor& actualSeqLengths,
    const at::Tensor& stateIndices)
{
    const c10::OptionalDeviceGuard guard(query.device());
    check_npu_contiguous(query, "query");
    check_npu_contiguous(key, "key");
    check_npu_contiguous(value, "value");
    check_npu_contiguous(aLog, "a_log");
    check_npu_contiguous(a, "a");
    check_npu_contiguous(b, "b");
    check_npu_contiguous(dtBias, "dt_bias");
    check_npu_contiguous(state, "state");
    check_npu_contiguous(actualSeqLengths, "actual_seq_lengths");
    check_npu_contiguous(stateIndices, "state_indices");

    TORCH_CHECK(query.scalar_type() == at::kBFloat16 &&
                    key.scalar_type() == at::kBFloat16 &&
                    value.scalar_type() == at::kBFloat16,
                "query, key, and value must be BF16");
    TORCH_CHECK(a.scalar_type() == at::kBFloat16 && b.scalar_type() == at::kBFloat16,
                "a and b must be BF16");
    TORCH_CHECK(aLog.scalar_type() == at::kFloat, "a_log must be FP32");
    TORCH_CHECK(dtBias.scalar_type() == at::kBFloat16,
                "dt_bias must be BF16, matching the loaded Qwen3.6 parameter");
    TORCH_CHECK(state.scalar_type() == at::kFloat, "state must be FP32");
    TORCH_CHECK(actualSeqLengths.scalar_type() == at::kInt &&
                    stateIndices.scalar_type() == at::kInt,
                "decode metadata must be int32");

    TORCH_CHECK(query.dim() == 3 && query.size(1) == kKeyHeads &&
                    query.size(2) == kHeadDim,
                "query must have shape [T, 4, 128]");
    const int64_t tokens = query.size(0);
    TORCH_CHECK(key.sizes() == query.sizes(), "key must match query shape");
    TORCH_CHECK(value.sizes() == at::IntArrayRef({tokens, kValueHeads, kHeadDim}),
                "value must have shape [T, 12, 128]");
    TORCH_CHECK(tokens > 0 && tokens <= kMaxTokens,
                "prototype supports 1..16 non-spec decode tokens");
    TORCH_CHECK(a.sizes() == at::IntArrayRef({tokens, kValueHeads}) &&
                    b.sizes() == at::IntArrayRef({tokens, kValueHeads}),
                "a and b must have shape [T, 12]");
    TORCH_CHECK(aLog.numel() == kValueHeads && dtBias.numel() == kValueHeads,
                "a_log and dt_bias must contain 12 elements");
    TORCH_CHECK(state.dim() == 4 && state.size(0) > 0 &&
                    state.size(1) == kValueHeads && state.size(2) == kHeadDim &&
                    state.size(3) == kHeadDim,
                "state must have shape [S, 12, 128, 128]");
    TORCH_CHECK(actualSeqLengths.dim() == 1 &&
                    actualSeqLengths.numel() == tokens + 1,
                "actual_seq_lengths must have T+1 elements");
    TORCH_CHECK(stateIndices.dim() == 1 && stateIndices.numel() == tokens,
                "state_indices must have T elements");

    at::Tensor out = at::empty({tokens, kValueHeads, kHeadDim}, query.options());

    int32_t deviceId = -1;
    TORCH_CHECK(aclrtGetDevice(&deviceId) == ACL_SUCCESS, "failed to get NPU device");
    int64_t availableCoreNum = 0;
    auto ret = aclrtGetDeviceInfo(deviceId, ACL_DEV_ATTR_VECTOR_CORE_NUM, &availableCoreNum);
    TORCH_CHECK(ret == ACL_SUCCESS && availableCoreNum > 0, "failed to get NPU core count");

    using RecurrentGatedDeltaRule::RecurrentGatedDeltaRuleTilingData;
    RecurrentGatedDeltaRuleTilingData tiling{};
    tiling.vectorCoreNum = static_cast<uint32_t>(availableCoreNum);
    tiling.ubCalSize = kUbBytes;
    tiling.t = static_cast<uint32_t>(tokens);
    tiling.nk = kKeyHeads;
    tiling.dk = kHeadDim;
    tiling.nv = kValueHeads;
    tiling.dv = kHeadDim;
    tiling.sBlockNum = static_cast<uint32_t>(state.size(0));
    tiling.b = static_cast<uint32_t>(tokens);
    tiling.vStep = kVStep;
    tiling.stateOutBufferNum = 1;
    tiling.attnOutBufferNum = 2;
    tiling.scale = 1.0f / std::sqrt(static_cast<float>(kHeadDim));
    tiling.hasGama = 1;
    tiling.hasGamaK = 0;
    tiling.hasAcceptedTokens = 0;

    // Keep this arithmetic identical to the audited v0.23 host tiler.  TPipe
    // reserves another 128 bytes and applies a distinct fixed/dynamic split;
    // subtracting only the apparent tensor payload over-allocates tmpBuff.
    constexpr uint32_t kMaxMtp = 16;
    constexpr uint32_t kAlignedNv = 16;
    constexpr uint32_t fixedUbBytes =
        kMaxMtp * (4 * kHeadDim + 2 * kHeadDim) + 128 +
        kMaxMtp * 4 * kAlignedNv + kMaxMtp * 2 * kAlignedNv;
    constexpr uint32_t queueCoeff =
        (sizeof(float) + sizeof(float) * 1) * kHeadDim +
        4 * 2;
    static_assert(
        fixedUbBytes + queueCoeff * kVStep < kUbBytes,
        "fixed Qwen3.6 decode tiling exceeds 910B vector UB");
    tiling.ubRestBytes = kUbBytes - fixedUbBytes - queueCoeff * kVStep;

    uint32_t blockNum = static_cast<uint32_t>(
        std::min<int64_t>(availableCoreNum, tokens * kValueHeads));

    at::Tensor tilingTensor = get_or_create_tiling_tensor(
        query,
        tiling,
        deviceId,
        tokens,
        state.size(0),
        availableCoreNum);

    auto stream = c10_npu::getCurrentNPUStream().stream(false);
    auto queryPtr = (GM_ADDR)query.mutable_data_ptr();
    auto keyPtr = (GM_ADDR)key.mutable_data_ptr();
    auto valuePtr = (GM_ADDR)value.mutable_data_ptr();
    auto aLogPtr = (GM_ADDR)aLog.mutable_data_ptr();
    auto aPtr = (GM_ADDR)a.mutable_data_ptr();
    auto bPtr = (GM_ADDR)b.mutable_data_ptr();
    auto dtBiasPtr = (GM_ADDR)dtBias.mutable_data_ptr();
    auto statePtr = (GM_ADDR)state.mutable_data_ptr();
    auto actualSeqLengthsPtr = (GM_ADDR)actualSeqLengths.mutable_data_ptr();
    auto stateIndicesPtr = (GM_ADDR)stateIndices.mutable_data_ptr();
    auto outPtr = (GM_ADDR)out.mutable_data_ptr();
    auto tilingPtr = (GM_ADDR)tilingTensor.mutable_data_ptr();

    auto aclCall = [=]() -> int {
        qwen36_gdn_decode_core_kernel<<<blockNum, nullptr, stream>>>(
            queryPtr,
            keyPtr,
            valuePtr,
            aLogPtr,
            aPtr,
            bPtr,
            dtBiasPtr,
            statePtr,
            actualSeqLengthsPtr,
            stateIndicesPtr,
            outPtr,
            tilingPtr);
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36GdnDecodeCore", aclCall);

    return out;
}

} // namespace ascend_kernel
