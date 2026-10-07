/**
 * Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under the terms and conditions of
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

// Exact native UB/profile arithmetic from the pinned v0.23 910B source.
// Specialization: BF16 Q/K/V/beta, FP32 state/g, T16/S19, no GK/MTP.
#pragma once
#include <array>
#include <cstddef>
#include <stdexcept>
#include <cstdint>
#include <type_traits>
#include <algorithm>
#include "../op_kernel/native_trace_tiling_data.h"
#define NATIVE_TRACE_LOG(...) do {} while(false)
namespace NativeTraceHost {
using NativeRecurrentCopyTraceV2::NativeRecurrentCopyTraceV2TilingData;
constexpr size_t MAX_MTP = 16;
template<class A,class B> static A CeilDiv(A a,B b){return b==0?0:(a+b-1)/b;}
template<class T> static T CeilAlign(T x,T a){return CeilDiv(x,a)*a;}
struct BufferProfile {
 uint32_t stateOutBufferNum,attnOutBufferNum,vStep,repeatTime; bool valid;
 BufferProfile(uint32_t s=1,uint32_t a=1,uint32_t v=0,uint32_t r=0,bool ok=false):
 stateOutBufferNum(s),attnOutBufferNum(a),vStep(v),repeatTime(r),valid(ok){}
};
class NativeTiling {
public:
 NativeRecurrentCopyTraceV2TilingData tilingData_{};
 struct {uint64_t ubSize;uint32_t aivNum;} compileInfo_{};
 struct {int64_t fixedUbBytes;} ubCalcCtx_{};
 // Only op-name logging uses this null node; macro discards its arguments.
 struct {const char* GetNodeName() const {return "native-copy-trace";}} *context_=nullptr;
 int64_t CalcFixedUbBytes(int64_t,int64_t,int64_t) const;
 int64_t CalcWorkingUbBytes(int64_t,int64_t,int64_t) const;
 int64_t CalcVStepCoeff(int64_t,uint32_t,uint32_t) const;
 bool EvaluateBufferProfile(int64_t,int64_t,int64_t,uint32_t,uint32_t,BufferProfile&) const;
 bool IsBetterProfile(const BufferProfile&,const BufferProfile&) const;
 bool FinalizeVStepFromUb(int64_t,int64_t,int64_t);
};
int64_t NativeTiling::CalcFixedUbBytes(int64_t aNv, int64_t aDv, int64_t aDk) const
{
    int64_t usedUbBytes = MAX_MTP * (4 * aDk + 2 * aDv); // 4 for qInQueue_ & kInQueue_, 2 for vInQueue_
    usedUbBytes += 128;                                  // reserve 128 Bytes
    if (tilingData_.hasGamaK) {
        usedUbBytes += MAX_MTP * 4 * aDk; // 4 for gk gamaInQueue_
    }
    if (tilingData_.hasGama) {
        usedUbBytes += MAX_MTP * 4 * aNv; // 4 for g gamaInQueue_
    }
    usedUbBytes += MAX_MTP * 2 * aNv; // 2 for betaInQueue_
    return usedUbBytes;
}

int64_t NativeTiling::CalcWorkingUbBytes(int64_t aNv, int64_t aDv, int64_t aDk) const
{
    int64_t usedUbBytes = CalcFixedUbBytes(aNv, aDv, aDk);
    usedUbBytes += MAX_MTP * (8 * aDk + 4 * aDv + 4 * aNv); // 8 for qk in ub, 4 for v in ub, 4 for beta in ub
    return usedUbBytes;
}

int64_t NativeTiling::CalcVStepCoeff(int64_t aDk, uint32_t stateOutBufferNum,
                                                       uint32_t attnOutBufferNum) const
{
    int64_t stateDtypeSize = 4;
    int64_t coeff = (stateDtypeSize + static_cast<int64_t>(stateDtypeSize * stateOutBufferNum)) * aDk +
                    static_cast<int64_t>(4 * attnOutBufferNum); // stateIn/stateOut/attnOut queues
    coeff += (4 + 4) * aDk + 4 + 4;                             // qInUb/kInUb/vInUb/deltaInUb/attnInUb
    return coeff;
}

bool NativeTiling::EvaluateBufferProfile(int64_t ubSize, int64_t usedUbBytes, int64_t aDk,
                                                           uint32_t stateOutBufferNum, uint32_t attnOutBufferNum,
                                                           BufferProfile &profile) const
{
    int64_t coeff = CalcVStepCoeff(aDk, stateOutBufferNum, attnOutBufferNum);
    int64_t vStep = (ubSize - usedUbBytes) / coeff / 8 * 8; // 8 * sizeof(float) = 32
    if (vStep < 8) {
        return false;
    }
    int64_t repeatTime = CeilDiv(tilingData_.dv, static_cast<uint32_t>(vStep));
    vStep = CeilAlign(CeilDiv(tilingData_.dv, static_cast<uint32_t>(repeatTime)),
                                 static_cast<uint32_t>(8));
    if (vStep < 8) {
        return false;
    }
    profile.stateOutBufferNum = stateOutBufferNum;
    profile.attnOutBufferNum = attnOutBufferNum;
    profile.vStep = static_cast<uint32_t>(vStep);
    profile.repeatTime = static_cast<uint32_t>(repeatTime);
    profile.valid = true;
    return true;
}

bool NativeTiling::IsBetterProfile(const BufferProfile &candidate, const BufferProfile &current) const
{
    if (!current.valid) {
        return true;
    }
    if (candidate.repeatTime != current.repeatTime) {
        return candidate.repeatTime < current.repeatTime;
    }
    uint32_t candidateDepth = candidate.stateOutBufferNum + candidate.attnOutBufferNum;
    uint32_t currentDepth = current.stateOutBufferNum + current.attnOutBufferNum;
    if (candidateDepth != currentDepth) {
        return candidateDepth > currentDepth;
    }
    return candidate.vStep > current.vStep;
}

bool NativeTiling::FinalizeVStepFromUb(int64_t ubSize, int64_t usedUbBytes, int64_t coeff)
{
    (void)coeff;
    int64_t aDk = CeilAlign(tilingData_.dk, static_cast<uint32_t>(16)); // 16 * 2 = 32B
    BufferProfile selected;
    const std::array<BufferProfile, 4> candidates = {{
        BufferProfile(1u, 1u, 0u, 0u, false),
        BufferProfile(1u, 2u, 0u, 0u, false),
        BufferProfile(2u, 2u, 0u, 0u, false),
        BufferProfile(3u, 3u, 0u, 0u, false)
    }};
    for (const auto &candidate : candidates) {
        BufferProfile profile;
        if (!EvaluateBufferProfile(ubSize, usedUbBytes, aDk, candidate.stateOutBufferNum, candidate.attnOutBufferNum,
                                   profile)) {
            continue;
        }
        if (IsBetterProfile(profile, selected)) {
            selected = profile;
        }
    }
    
    NATIVE_TRACE_LOG(context_->GetNodeName(), "selected profile: stateOutBufferNum=[%u], attnOutBufferNum=[%u], vStep=[%u], repeatTime=[%u], valid=[%d]",
            selected.stateOutBufferNum, selected.attnOutBufferNum, selected.vStep, selected.repeatTime, selected.valid);

    if (!selected.valid) {
        NATIVE_TRACE_LOG(context_->GetNodeName(), "vStep should be bigger than 8, shape is too big");
        return false;
    }

    int64_t stateDtypeSize = 4;

    int64_t queueCoeff = (stateDtypeSize + static_cast<int64_t>(stateDtypeSize * selected.stateOutBufferNum)) * aDk +
                         static_cast<int64_t>(4 * selected.attnOutBufferNum);
    int64_t ubRestBytes = ubSize - ubCalcCtx_.fixedUbBytes - queueCoeff * static_cast<int64_t>(selected.vStep);
    if (ubRestBytes < 0) {
        NATIVE_TRACE_LOG(context_->GetNodeName(), "ubRestBytes should be non-negative, but got %ld", ubRestBytes);
        return false;
    }
    tilingData_.ubCalSize = compileInfo_.ubSize;
    tilingData_.vStep = selected.vStep;
    tilingData_.stateOutBufferNum = selected.stateOutBufferNum;
    tilingData_.attnOutBufferNum = selected.attnOutBufferNum;
    tilingData_.ubRestBytes = static_cast<uint32_t>(ubRestBytes);
    return true;
}
inline NativeRecurrentCopyTraceV2TilingData make_tiling(uint64_t ub,uint32_t cores,float scale) {
 NativeTiling n;
 n.compileInfo_.ubSize=ub; n.compileInfo_.aivNum=cores;
 auto& d=n.tilingData_;
 d.vectorCoreNum=std::min(cores,16u*12u); d.t=16;d.nk=4;d.dk=128;
 d.nv=12;d.dv=128;d.sBlockNum=19;d.b=16;d.scale=scale;
 d.hasGama=1;d.hasGamaK=0;d.hasAcceptedTokens=0;
 n.ubCalcCtx_.fixedUbBytes=n.CalcFixedUbBytes(16,128,128);
 if(!cores||!ub||!n.FinalizeVStepFromUb(ub,n.CalcWorkingUbBytes(16,128,128),n.CalcVStepCoeff(128,1,1)))
  throw std::runtime_error("native UB profile unavailable");
 return d;
}
static_assert(sizeof(NativeRecurrentCopyTraceV2TilingData)==72,"native 17-field aligned tiling ABI");
}
#undef NATIVE_TRACE_LOG
