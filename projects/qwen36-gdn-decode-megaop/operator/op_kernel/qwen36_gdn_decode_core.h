/**
?* Copyright (c) 2025 Huawei Technologies Co., Ltd.
?* This program is free software, you can redistribute it and/or modify it under the terms and conditions of
?* Please refer to the License for details. You may not use this file except in compliance with the License.
?* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
?* INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
?* See LICENSE in the root of the software repository for the full text of the License.
?*/

/*!
 * \file grouped_matmul_finalize_routing.h
 * \brief
 */

#ifndef QWEN36_GDN_DECODE_CORE_KERNEL_H
#define QWEN36_GDN_DECODE_CORE_KERNEL_H

#include "kernel_operator.h"
#include "lib/matmul_intf.h"
#include "qwen36_gdn_decode_core_tiling.h"

namespace RecurrentGatedDeltaRule {

using namespace matmul;
using namespace AscendC;
constexpr uint64_t BUFFER_NUM = 1;
constexpr uint32_t MAX_OUT_BUFFER_NUM = 2;
constexpr uint64_t MAX_MTP = 16;
constexpr uint64_t BF16_NUM_PER_BLOCK = 16;
constexpr uint64_t FP32_NUM_PER_BLOCK = 8;
constexpr uint32_t REPEAT_LENTH = 64; // 256Byte for float
constexpr uint32_t MAX_REPEAT_TIME = 255;
constexpr uint32_t ADD_FOLD_REDUCE_MIN_K = 128;
constexpr uint32_t Q_WIDTH = 512;
constexpr uint32_t V_WIDTH = 1536;
constexpr uint32_t GATING_ALIGN = 16;
constexpr float L2_EPSILON = 1.0e-6f;

#ifndef RGDR_ENABLE_ADD_FOLD_REDUCE
#define RGDR_ENABLE_ADD_FOLD_REDUCE  1
#endif
struct RGDRInitParams {
    GM_ADDR query;
    GM_ADDR key;
    GM_ADDR value;
    GM_ADDR aLog;
    GM_ADDR a;
    GM_ADDR b;
    GM_ADDR dtBias;
    GM_ADDR initState;
    GM_ADDR cuSeqlens;
    GM_ADDR ssmStateIndices;
    GM_ADDR attnOut;
    GM_ADDR finalState;
};

template <typename inType, typename outType, typename stateType>
class RGDR {
public:
    __aicore__ inline RGDR(const __gm__ RecurrentGatedDeltaRuleTilingData *tilingData)
    {
        B_ = tilingData->b;
        T_ = tilingData->t;
        NK_ = tilingData->nk;
        realK_ = tilingData->dk;
        NV_ = tilingData->nv;
        realV_ = tilingData->dv;
        scale_ = tilingData->scale;
        hasAcceptedTokens_ = false;
        hasGama_ = true;
        hasGamaK_ = false;
        useAddFoldReduce_ = (RGDR_ENABLE_ADD_FOLD_REDUCE != 0);
        vStep_ = tilingData->vStep;
        stateOutBufferNum_ = (tilingData->stateOutBufferNum == MAX_OUT_BUFFER_NUM) ? MAX_OUT_BUFFER_NUM : BUFFER_NUM;
        attnOutBufferNum_ = (tilingData->attnOutBufferNum == MAX_OUT_BUFFER_NUM) ? MAX_OUT_BUFFER_NUM : BUFFER_NUM;
        restUbSize_ = tilingData->ubRestBytes;
        alignK_ = Ceil(tilingData->dk, BF16_NUM_PER_BLOCK) * BF16_NUM_PER_BLOCK;
        alignV_ = Ceil(tilingData->dv, BF16_NUM_PER_BLOCK) * BF16_NUM_PER_BLOCK;
        load = 0;
        usedblk = 0;
    }

    __aicore__ inline void Init(const RGDRInitParams &initParams, TPipe *pipe)
    {
        uint64_t blockDim = GetBlockNum();
        blockIdx = GetBlockIdx();
        if (blockIdx >= blockDim) {
            return;
        }
        pipe_ = pipe;
        SetGlobalTensors(initParams);
        InitLocalBuffers();
    }

    __aicore__ inline void SetGlobalTensors(const RGDRInitParams &initParams)
    {
        queryGm_.SetGlobalBuffer((__gm__ inType *)initParams.query);
        keyGm_.SetGlobalBuffer((__gm__ inType *)initParams.key);
        valueGm_.SetGlobalBuffer((__gm__ inType *)initParams.value);
        aLogGm_.SetGlobalBuffer((__gm__ float *)initParams.aLog);
        aGm_.SetGlobalBuffer((__gm__ inType *)initParams.a);
        bGm_.SetGlobalBuffer((__gm__ inType *)initParams.b);
        dtBiasGm_.SetGlobalBuffer((__gm__ inType *)initParams.dtBias);
        initStateGm_.SetGlobalBuffer((__gm__ stateType *)initParams.initState);
        cuSeqlensGm_.SetGlobalBuffer((__gm__ int32_t *)initParams.cuSeqlens);
        ssmStateIndicesGm_.SetGlobalBuffer((__gm__ int32_t *)initParams.ssmStateIndices);
        finalStateGm_.SetGlobalBuffer((__gm__ stateType *)initParams.finalState);
        attnOutGm_.SetGlobalBuffer((__gm__ outType *)initParams.attnOut);
    }

    __aicore__ inline void InitLocalBuffers()
    {
        uint32_t cubeSize = alignK_ * vStep_ * sizeof(float);
        uint32_t singleVSize = vStep_ * sizeof(float);
        uint32_t vSize = MAX_MTP * alignV_ * sizeof(float);
        uint32_t kSize = MAX_MTP * alignK_ * sizeof(float);
        uint32_t betaUbSize = MAX_MTP * GATING_ALIGN * sizeof(float);
        pipe_->InitBuffer(qInQueue_, BUFFER_NUM, MAX_MTP * alignK_ * sizeof(inType));
        pipe_->InitBuffer(kInQueue_, BUFFER_NUM, MAX_MTP * alignK_ * sizeof(inType));
        pipe_->InitBuffer(vInQueue_, BUFFER_NUM, MAX_MTP * alignV_ * sizeof(inType));
        pipe_->InitBuffer(stateInQueue_, BUFFER_NUM, alignK_ * vStep_ * sizeof(stateType));
        if (hasGama_) {
            pipe_->InitBuffer(gamaInQueue_, BUFFER_NUM, MAX_MTP * GATING_ALIGN * sizeof(float));
        }
        if (hasGamaK_) {
            pipe_->InitBuffer(gamaKInQueue_, BUFFER_NUM, MAX_MTP * alignK_ * sizeof(float));
        }
        pipe_->InitBuffer(betaInQueue_, BUFFER_NUM, MAX_MTP * GATING_ALIGN * sizeof(inType));
        pipe_->InitBuffer(stateOutQueue_, stateOutBufferNum_, alignK_ * vStep_ * sizeof(stateType));
        pipe_->InitBuffer(attnOutQueue_, attnOutBufferNum_, vStep_ * sizeof(outType));
        pipe_->InitBuffer(tmpBuff, restUbSize_);
        uint32_t buffOffset = 0;
        deltaInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(vStep_), buffOffset);
        buffOffset += singleVSize;
        attnInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(vStep_), buffOffset);
        buffOffset += singleVSize;
        vInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(MAX_MTP * alignV_), buffOffset);
        buffOffset += vSize;
        qInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(MAX_MTP * alignK_), buffOffset);
        buffOffset += kSize;
        kInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(MAX_MTP * alignK_), buffOffset);
        buffOffset += kSize;
        stateInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(alignK_ * vStep_), buffOffset);
        buffOffset += cubeSize;
        broadTmpInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(alignK_ * vStep_), buffOffset);
        buffOffset += cubeSize;
        betaInUb = tmpBuff.GetWithOffset<float>(static_cast<uint32_t>(betaUbSize), buffOffset);
    }

    __aicore__ inline void ComputeAvgload()
    {
        uint64_t realT = 0;
        for (uint64_t batch_i = 1; batch_i < B_ + 1; batch_i++) {
            realT += cuSeqlensGm_.GetValue(batch_i);
        }
        avgload = Ceil(realT * NV_, GetBlockNum());
    }

    __aicore__ inline void Process()
    {
        ComputeAvgload();
        int32_t seq1 = cuSeqlensGm_.GetValue(0);
        for (uint64_t batch_i = 0; batch_i < B_; batch_i++) {
            int32_t seqLen = cuSeqlensGm_.GetValue(batch_i+1);
            if (seqLen <= 0) {
                continue;
            }
            if (seqLen > static_cast<int32_t>(MAX_MTP)) {
                return;
            }
            if (seq1 < 0 || seq1 > static_cast<int32_t>(T_) || (seq1 + seqLen) > static_cast<int32_t>(T_)) {
                return;
            }
            int32_t seq0 = seq1;
            seq1 += seqLen;
            uint32_t copyFlag = 0;
            uint64_t stateOffset;
            for (uint64_t head_i = 0; head_i < NV_; head_i++) {
                if (!IsCurrentBlock(seq1 - seq0)) {
                    continue;
                }
                copyFlag++;
                if (copyFlag == 1) {
                    int32_t stateTokenIdx = seq0;
                    stateOffset = ssmStateIndicesGm_.GetValue(stateTokenIdx);
                    CopyInGamaBeta(seq0, seq1);
                }
                ProcessHead(seq0, seq1, head_i, stateOffset);
            }
            if (hasGama_ && copyFlag != 0) {
                gamaInQueue_.FreeTensor(gamaInUb);
            }
        }
    }

private:
    __aicore__ inline void CopyInQKV(int32_t seq0, uint64_t head_i, int32_t seqLen)
    {
        LocalTensor<inType> qLocal = qInQueue_.AllocTensor<inType>();
        LocalTensor<inType> kLocal = kInQueue_.AllocTensor<inType>();
        LocalTensor<inType> vLocal = vInQueue_.AllocTensor<inType>();
        const uint32_t qkStrideBytes = (Q_WIDTH - realK_) * sizeof(inType);
        const uint32_t vStrideBytes = (V_WIDTH - realV_) * sizeof(inType);
        DataCopyExtParams qkInParams{static_cast<uint16_t>(seqLen), static_cast<uint32_t>(realK_ * sizeof(inType)),
                                     qkStrideBytes, 0, 0};
        DataCopyExtParams vInParams{static_cast<uint16_t>(seqLen), static_cast<uint32_t>(realV_ * sizeof(inType)),
                                    vStrideBytes, 0, 0};
        DataCopyPadExtParams<inType> qkPadParams{true, 0, static_cast<uint8_t>(alignK_ - realK_), 0};
        DataCopyPadExtParams<inType> vPadParams{true, 0, static_cast<uint8_t>(alignV_ - realV_), 0};
        uint64_t qHead = head_i / (NV_ / NK_);
        uint64_t qOffset = static_cast<uint64_t>(seq0) * Q_WIDTH + qHead * realK_;
        uint64_t kOffset = static_cast<uint64_t>(seq0) * Q_WIDTH + qHead * realK_;
        uint64_t vOffset = static_cast<uint64_t>(seq0) * V_WIDTH + head_i * realV_;
        DataCopyPad(qLocal, queryGm_[qOffset], qkInParams, qkPadParams);
        DataCopyPad(kLocal, keyGm_[kOffset], qkInParams, qkPadParams);
        DataCopyPad(vLocal, valueGm_[vOffset], vInParams, vPadParams);
        qInQueue_.EnQue<inType>(qLocal);
        kInQueue_.EnQue<inType>(kLocal);
        vInQueue_.EnQue<inType>(vLocal);
        qLocal = qInQueue_.DeQue<inType>();
        kLocal = kInQueue_.DeQue<inType>();
        vLocal = vInQueue_.DeQue<inType>();
        Cast(qInUb, qLocal, AscendC::RoundMode::CAST_NONE, alignK_ * seqLen);
        Cast(kInUb, kLocal, AscendC::RoundMode::CAST_NONE, alignK_ * seqLen);
        Cast(vInUb, vLocal, AscendC::RoundMode::CAST_NONE, alignV_ * seqLen);
        AscendC::PipeBarrier<PIPE_V>();

        // Q/K are already normalized and rounded to BF16 by the deployed
        // Triton l2norm_fwd path.  The v11/v12 isolation gates proved that an
        // AscendC reimplementation crosses a BF16 boundary for a real decode
        // input, so preserve that semantic boundary explicitly.
        Muls(qInUb, qInUb, scale_, seqLen * alignK_);
        qInQueue_.FreeTensor(qLocal);
        kInQueue_.FreeTensor(kLocal);
        vInQueue_.FreeTensor(vLocal);
    }

    __aicore__ inline void PrefetchState(uint64_t stateOffest, uint32_t curSingleV)
    {
        LocalTensor<stateType> stateLocal = stateInQueue_.AllocTensor<stateType>();
        DataCopyExtParams stateInParams{static_cast<uint16_t>(curSingleV),
                                        static_cast<uint16_t>(realK_ * sizeof(stateType)), 0, 0, 0};
        DataCopyPadExtParams<stateType> padParams{true, 0, static_cast<uint8_t>(alignK_ - realK_), 0};
        DataCopyPad(stateLocal, initStateGm_[stateOffest], stateInParams, padParams);
        stateInQueue_.EnQue<stateType>(stateLocal);
    }

    __aicore__ inline void LoadPrefetchedState(uint32_t curSingleV)
    {
        LocalTensor<stateType> stateLocal = stateInQueue_.DeQue<stateType>();
        if constexpr (std::is_same<stateType, float32_t>()) {
            DataCopy(stateInUb, stateLocal, alignK_ * curSingleV);
        } else {
            Cast(stateInUb, stateLocal, AscendC::RoundMode::CAST_NONE, alignK_ * curSingleV);
        }
        stateInQueue_.FreeTensor(stateLocal);
    }

    __aicore__ inline void MatVecMul(const LocalTensor<float> &cubeTensor, const LocalTensor<float> &vecTensor,
                                          LocalTensor<float> &dstTensor, uint32_t cols, bool isAdd)
    {
        uint8_t repeatStride = alignK_ / FP32_NUM_PER_BLOCK;
        for (uint32_t i = 0; i < alignK_; i += REPEAT_LENTH) {
            uint64_t mask = Std::min(REPEAT_LENTH, alignK_ - i);
            for (uint32_t j = 0; j < cols; j += MAX_REPEAT_TIME) {
                uint64_t repeatTime = Std::min(MAX_REPEAT_TIME, cols - j);
                if (isAdd) {
                    MulAddDst(dstTensor[j * alignK_ + i], cubeTensor[j * alignK_ + i], vecTensor[i], mask, repeatTime,
                              {1, 1, 1, repeatStride, repeatStride, 0});
                } else {
                    Mul(dstTensor[j * alignK_ + i], cubeTensor[j * alignK_ + i], vecTensor[i], mask, repeatTime,
                        {1, 1, 1, repeatStride, repeatStride, 0});
                }
            }
        }
    }

    __aicore__ inline void ReduceSumBaseline(LocalTensor<float> &dstTensor, const LocalTensor<float> &srcTensor,
                                             uint32_t rows)
    {
        uint32_t stateShape[2] = {rows, alignK_};
        ReduceSum<float, Pattern::Reduce::AR, true>(dstTensor, srcTensor, stateShape, true);
    }

    __aicore__ inline bool CanUseK128AddFoldFastPath(uint32_t rows) const
    {
        if (alignK_ != ADD_FOLD_REDUCE_MIN_K) {
            return false;
        }
        if (rows == 0 || rows > MAX_REPEAT_TIME) {
            return false;
        }
        return true;
    }

    __aicore__ inline void ReduceSumAddFoldK128(LocalTensor<float> &dstTensor, LocalTensor<float> &srcTensor,
                                                uint32_t rows)
    {
        const uint8_t repeatTime = static_cast<uint8_t>(rows);
        const uint8_t rowRepStride = static_cast<uint8_t>(alignK_ / FP32_NUM_PER_BLOCK);

        // Write the folded result to the upper half to avoid the multi-repeat src0/dst overlap case.
        Add(srcTensor[REPEAT_LENTH], srcTensor, srcTensor[REPEAT_LENTH], REPEAT_LENTH, repeatTime,
            {1, 1, 1, rowRepStride, rowRepStride, rowRepStride});
        AscendC::PipeBarrier<PIPE_V>();
        WholeReduceSum(dstTensor, srcTensor[REPEAT_LENTH], REPEAT_LENTH, repeatTime, 1, 1, rowRepStride);
    }

    __aicore__ inline void ReduceSumAddFold(LocalTensor<float> &dstTensor, LocalTensor<float> &srcTensor,
                                            uint32_t rows)
    {
        if (alignK_ < REPEAT_LENTH) {
            ReduceSumBaseline(dstTensor, srcTensor, rows);
            return;
        }
        
        if ((alignK_ & (alignK_ - 1)) != 0) {
            ReduceSumBaseline(dstTensor, srcTensor, rows);
            return;
        }

        if (CanUseK128AddFoldFastPath(rows)) {
            ReduceSumAddFoldK128(dstTensor, srcTensor, rows);
            return;
        }

        for (uint32_t row = 0; row < rows; ++row) {
            uint32_t rowOffset = row * alignK_;
            uint32_t activeLen = alignK_;
            while (activeLen > REPEAT_LENTH) {
                uint32_t half = activeLen >> 1;
                Add(srcTensor[rowOffset], srcTensor[rowOffset], srcTensor[rowOffset + half], half);
                AscendC::PipeBarrier<PIPE_V>();
                activeLen = half;
            }

            WholeReduceSum(dstTensor[row], srcTensor[rowOffset], REPEAT_LENTH, 1, 1, 1, FP32_NUM_PER_BLOCK);
        }
    }

    __aicore__ inline void ReduceSumDispatch(LocalTensor<float> &dstTensor, LocalTensor<float> &srcTensor,
                                             uint32_t rows)
    {
        if (useAddFoldReduce_ && alignK_ >= ADD_FOLD_REDUCE_MIN_K) {
            ReduceSumAddFold(dstTensor, srcTensor, rows);
            return;
        }
        ReduceSumBaseline(dstTensor, srcTensor, rows);
    }

    __aicore__ inline void Compute(uint32_t curSingleV, uint64_t curQKOffset, uint64_t curVOffset)
    {
        uint32_t stateShape[2] = {curSingleV, alignK_};
        uint32_t ktShape[2] = {1, alignK_};
        uint32_t deltaShape[2] = {curSingleV, 1};
        if (hasGama_) {
            Muls(stateInUb, stateInUb, gama_, alignK_ * curSingleV);
        }
        if (hasGamaK_) {
            MatVecMul(stateInUb, gamaKInUb[curQKOffset], stateInUb, curSingleV, false);
        }
        if (hasGama_ || hasGamaK_) {
            AscendC::PipeBarrier<PIPE_V>();
        }
        MatVecMul(stateInUb, kInUb[curQKOffset], broadTmpInUb, curSingleV, false);
        AscendC::PipeBarrier<PIPE_V>();
        ReduceSumDispatch(deltaInUb, broadTmpInUb, curSingleV);
        AscendC::PipeBarrier<PIPE_V>();
        deltaInUb = vInUb[curVOffset] - deltaInUb;
        AscendC::PipeBarrier<PIPE_V>();
        Muls(deltaInUb, deltaInUb, beta_, curSingleV);
        AscendC::PipeBarrier<PIPE_V>();
        Broadcast<float, 2, 1>(broadTmpInUb, deltaInUb, stateShape, deltaShape); //  2: Dim Number 1: Second Dim
        AscendC::PipeBarrier<PIPE_V>();
        MatVecMul(broadTmpInUb, kInUb[curQKOffset], stateInUb, curSingleV, true);
        AscendC::PipeBarrier<PIPE_V>();
        MatVecMul(stateInUb, qInUb[curQKOffset], broadTmpInUb, curSingleV, false);
        AscendC::PipeBarrier<PIPE_V>();
        ReduceSumDispatch(attnInUb, broadTmpInUb, curSingleV);
        LocalTensor<stateType> stateOutLocal = stateOutQueue_.AllocTensor<stateType>();
        LocalTensor<outType> attnOutLocal = attnOutQueue_.AllocTensor<outType>();
        if constexpr (std::is_same<stateType, float32_t>()) {
            DataCopy(stateOutLocal, stateInUb, alignK_ * curSingleV);
        } else {
            Cast(stateOutLocal, stateInUb, AscendC::RoundMode::CAST_RINT, alignK_ * curSingleV);
        }
        stateOutQueue_.EnQue<stateType>(stateOutLocal);
        Cast(attnOutLocal, attnInUb, AscendC::RoundMode::CAST_RINT, curSingleV);
        attnOutQueue_.EnQue<outType>(attnOutLocal);
    }

    __aicore__ inline void CopyOutAttn(uint64_t attnOffset, uint32_t curSingleV)
    {
        LocalTensor<outType> attnLocal = attnOutQueue_.DeQue<outType>();
        DataCopyParams attnOutParams{1, static_cast<uint16_t>(curSingleV * sizeof(outType)), 0, 0};
        DataCopyPad(attnOutGm_[attnOffset], attnLocal, attnOutParams);
        attnOutQueue_.FreeTensor(attnLocal);
    }

    __aicore__ inline void CopyOutState(uint64_t stateOffset, uint32_t curSingleV)
    {
        LocalTensor<stateType> stateOutLocal = stateOutQueue_.DeQue<stateType>();
        DataCopyParams stateOutParams{static_cast<uint16_t>(curSingleV),
                                      static_cast<uint16_t>(realK_ * sizeof(stateType)), 0, 0};
        DataCopyPad(finalStateGm_[stateOffset], stateOutLocal, stateOutParams);
        stateOutQueue_.FreeTensor(stateOutLocal);
    }

    __aicore__ inline void CopyInGamaBeta(int32_t seq0, int32_t seq1)
    {
        int32_t seqLen = seq1 - seq0;
        uint32_t alignedCount = static_cast<uint32_t>(seqLen) * GATING_ALIGN;

        LocalTensor<inType> aLocal = qInQueue_.AllocTensor<inType>();
        LocalTensor<inType> betaLocal = betaInQueue_.AllocTensor<inType>();
        DataCopyExtParams abParams{static_cast<uint16_t>(seqLen),
                                   static_cast<uint32_t>(NV_ * sizeof(inType)), 0, 0, 0};
        DataCopyPadExtParams<inType> abPad{true, 0,
                                          static_cast<uint8_t>(GATING_ALIGN - NV_),
                                          static_cast<inType>(0)};
        DataCopyPad(aLocal, aGm_[static_cast<uint64_t>(seq0) * NV_], abParams, abPad);
        DataCopyPad(betaLocal, bGm_[static_cast<uint64_t>(seq0) * NV_], abParams, abPad);
        qInQueue_.EnQue<inType>(aLocal);
        betaInQueue_.EnQue<inType>(betaLocal);
        aLocal = qInQueue_.DeQue<inType>();
        betaLocal = betaInQueue_.DeQue<inType>();
        Cast(qInUb, aLocal, AscendC::RoundMode::CAST_NONE, alignedCount);
        Cast(betaInUb, betaLocal, AscendC::RoundMode::CAST_NONE, alignedCount);
        qInQueue_.FreeTensor(aLocal);

        LocalTensor<float> paramLocal = stateInQueue_.AllocTensor<float>();
        LocalTensor<inType> dtBiasLocal = qInQueue_.AllocTensor<inType>();
        DataCopyExtParams dtBiasParams{1, static_cast<uint32_t>(NV_ * sizeof(inType)), 0, 0, 0};
        DataCopyPadExtParams<inType> dtBiasPad{true, 0,
                                             static_cast<uint8_t>(GATING_ALIGN - NV_),
                                             static_cast<inType>(0)};
        DataCopyPad(dtBiasLocal, dtBiasGm_, dtBiasParams, dtBiasPad);
        qInQueue_.EnQue<inType>(dtBiasLocal);
        dtBiasLocal = qInQueue_.DeQue<inType>();
        Cast(paramLocal, dtBiasLocal, AscendC::RoundMode::CAST_NONE, GATING_ALIGN);
        qInQueue_.FreeTensor(dtBiasLocal);
        DataCopyExtParams paramParams{1, static_cast<uint32_t>(NV_ * sizeof(float)), 0, 0, 0};
        DataCopyPadExtParams<float> paramPad{true, 0,
                                            static_cast<uint8_t>(GATING_ALIGN - NV_), 0.0f};
        DataCopyPad(paramLocal[GATING_ALIGN], aLogGm_, paramParams, paramPad);
        stateInQueue_.EnQue<float>(paramLocal);
        paramLocal = stateInQueue_.DeQue<float>();
        Exp(paramLocal[GATING_ALIGN * 2], paramLocal[GATING_ALIGN], GATING_ALIGN);
        AscendC::PipeBarrier<PIPE_V>();
        Muls(paramLocal[GATING_ALIGN * 2], paramLocal[GATING_ALIGN * 2], -1.0f, GATING_ALIGN);
        AscendC::PipeBarrier<PIPE_V>();

        LocalTensor<float> gamaLocal = gamaInQueue_.AllocTensor<float>();
        for (int32_t row = 0; row < seqLen; ++row) {
            uint32_t offset = static_cast<uint32_t>(row) * GATING_ALIGN;
            Add(qInUb[offset], qInUb[offset], paramLocal, GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            // Match the deployed FusedGdnGating instruction order for the
            // Qwen3.6 operating range: log(1 + exp(min(x, 20))).  The prior
            // max(x,0)+log1p(exp(-abs(x))) form is mathematically equivalent
            // but follows a different FP32 rounding path.  Add max(x-20, 0)
            // as the branch-free threshold continuation; at FP32 precision
            // log(1+exp(20)) rounds to 20, matching the native select branch.
            Mins(kInUb[offset], qInUb[offset], 20.0f, GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Exp(kInUb[offset], kInUb[offset], GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Adds(kInUb[offset], kInUb[offset], 1.0f, GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Ln(kInUb[offset], kInUb[offset], GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Adds(gamaLocal[offset], qInUb[offset], -20.0f, GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Maxs(gamaLocal[offset], gamaLocal[offset], 0.0f, GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Add(kInUb[offset], kInUb[offset], gamaLocal[offset], GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
            Mul(gamaLocal[offset], kInUb[offset], paramLocal[GATING_ALIGN * 2],
                GATING_ALIGN);
            AscendC::PipeBarrier<PIPE_V>();
        }
        Exp(gamaLocal, gamaLocal, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();

        // Numerically stable sigmoid followed by BF16 boundary rounding,
        // matching fused_gdn_gating -> recurrent_gated_delta_rule.
        Muls(betaInUb, betaInUb, -1.0f, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();
        Exp(betaInUb, betaInUb, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();
        Adds(betaInUb, betaInUb, 1.0f, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();
        Duplicate(kInUb, 1.0f, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();
        Div(betaInUb, kInUb, betaInUb, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();
        Cast(betaLocal, betaInUb, AscendC::RoundMode::CAST_RINT, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();
        Cast(betaInUb, betaLocal, AscendC::RoundMode::CAST_NONE, alignedCount);
        AscendC::PipeBarrier<PIPE_V>();

        betaInQueue_.FreeTensor(betaLocal);
        stateInQueue_.FreeTensor(paramLocal);
        gamaInQueue_.EnQue<float>(gamaLocal);
        gamaInUb = gamaInQueue_.DeQue<float>();

        // gamaInUb and betaInUb are produced by vector instructions but are
        // consumed below through scalar GetValue calls.  A PIPE_V barrier
        // orders vector instructions only; make the vector-to-scalar
        // dependency explicit before ProcessHead reads either tensor.
        event_t eventVToS = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::V_S));
        SetFlag<HardEvent::V_S>(eventVToS);
        WaitFlag<HardEvent::V_S>(eventVToS);
    }

    __aicore__ inline void ProcessHead(int32_t seq0, int32_t seq1, uint64_t head_i, uint64_t stateOffset)
    {
        CopyInQKV(seq0, head_i, seq1 - seq0);
        if (realV_ == 0) {
            if (hasGamaK_) {
                gamaKInQueue_.FreeTensor(gamaKInUb);
            }
            return;
        }
        uint64_t nextVOffset = 0;
        uint32_t nextSingleV = realV_ > vStep_ ? vStep_ : realV_;
        uint64_t nextStateOffset = ((stateOffset * NV_ + head_i) * realV_) * realK_;
        PrefetchState(nextStateOffset, nextSingleV);
        for (uint64_t v_i = 0; v_i < realV_; v_i += vStep_) {
            uint32_t curSingleV = v_i + vStep_ > realV_ ? realV_ - v_i : vStep_;
            LoadPrefetchedState(curSingleV);
            nextVOffset = v_i + vStep_;
            if (nextVOffset < realV_) {
                nextSingleV = nextVOffset + vStep_ > realV_ ? realV_ - nextVOffset : vStep_;
                nextStateOffset = ((stateOffset * NV_ + head_i) * realV_ + nextVOffset) * realK_;
                PrefetchState(nextStateOffset, nextSingleV);
            }
            uint64_t pendingAttnOffset = 0;
            uint64_t pendingStateOffset = 0;
            bool hasPendingAttn = false;
            bool hasPendingState = false;
            event_t eventSToV = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::S_V));
            for (uint64_t seq_i = seq0; seq_i < seq1; seq_i++) {
                uint64_t gbOffset = head_i + (seq_i - seq0) * GATING_ALIGN;
                uint64_t curQKOffset = (seq_i - seq0) * alignK_;
                uint64_t curVOffset = (seq_i - seq0) * alignV_ + v_i;
                uint64_t attnOffset = (seq_i * NV_ + head_i) * realV_ + v_i;
                uint64_t curStateOutOffset =
                    ((ssmStateIndicesGm_.GetValue(seq_i) * NV_ + head_i) * realV_ + v_i) * realK_;
                gama_ = hasGama_ ? gamaInUb.GetValue(gbOffset) : 1;
                beta_ = betaInUb.GetValue(gbOffset);
                SetFlag<HardEvent::S_V>(eventSToV);
                WaitFlag<HardEvent::S_V>(eventSToV);
                Compute(curSingleV, curQKOffset, curVOffset);
                if (attnOutBufferNum_ == BUFFER_NUM) {
                    CopyOutAttn(attnOffset, curSingleV);
                } else {
                    if (hasPendingAttn) {
                        CopyOutAttn(pendingAttnOffset, curSingleV);
                    }
                    pendingAttnOffset = attnOffset;
                    hasPendingAttn = true;
                }
                if (stateOutBufferNum_ == BUFFER_NUM) {
                    CopyOutState(curStateOutOffset, curSingleV);
                } else {
                    if (hasPendingState) {
                        CopyOutState(pendingStateOffset, curSingleV);
                    }
                    pendingStateOffset = curStateOutOffset;
                    hasPendingState = true;
                }
            }
            if (hasPendingAttn) {
                CopyOutAttn(pendingAttnOffset, curSingleV);
            }
            if (hasPendingState) {
                CopyOutState(pendingStateOffset, curSingleV);
            }
        }
        if (hasGamaK_) {
            gamaKInQueue_.FreeTensor(gamaKInUb);
        }
    }

    __aicore__ inline bool IsCurrentBlock(int32_t seqlen)
    {
        load += seqlen;
        bool ret = (blockIdx == usedblk && seqlen > 0);
        if (load >= avgload) {
            load = 0;
            usedblk++;
        }
        return ret;
    }

private:
    GlobalTensor<inType> queryGm_;
    GlobalTensor<inType> keyGm_;
    GlobalTensor<inType> valueGm_;
    GlobalTensor<float> aLogGm_;
    GlobalTensor<inType> aGm_;
    GlobalTensor<inType> bGm_;
    GlobalTensor<inType> dtBiasGm_;
    GlobalTensor<stateType> initStateGm_;
    GlobalTensor<int32_t> cuSeqlensGm_;
    GlobalTensor<int32_t> ssmStateIndicesGm_;
    GlobalTensor<stateType> finalStateGm_;
    GlobalTensor<outType> attnOutGm_;
    TPipe *pipe_;
    TQue<QuePosition::VECIN, 1> qInQueue_;
    TQue<QuePosition::VECIN, 1> kInQueue_;
    TQue<QuePosition::VECIN, 1> vInQueue_;
    TQue<QuePosition::VECIN, 1> gamaInQueue_;
    TQue<QuePosition::VECIN, 1> gamaKInQueue_;
    TQue<QuePosition::VECIN, 1> betaInQueue_;
    TQue<QuePosition::VECIN, 1> stateInQueue_;
    TQue<QuePosition::VECOUT, MAX_OUT_BUFFER_NUM> attnOutQueue_;
    TQue<QuePosition::VECOUT, MAX_OUT_BUFFER_NUM> stateOutQueue_;
    TBuf<TPosition::VECCALC> tmpBuff;
    LocalTensor<float> qInUb;
    LocalTensor<float> kInUb;
    LocalTensor<float> vInUb;
    LocalTensor<float> gamaInUb;
    LocalTensor<float> gamaKInUb;
    LocalTensor<float> betaInUb;
    LocalTensor<float> deltaInUb;
    LocalTensor<float> broadTmpInUb;
    LocalTensor<float> attnInUb;
    LocalTensor<float> stateInUb;
    uint32_t B_;
    uint32_t T_;
    uint32_t NK_;
    uint32_t alignK_;
    uint32_t realK_;
    uint32_t NV_;
    uint32_t alignV_;
    uint32_t realV_;
    uint32_t vStep_;
    uint32_t stateOutBufferNum_;
    uint32_t attnOutBufferNum_;
    uint32_t restUbSize_;
    uint32_t load;
    uint32_t usedblk;
    uint32_t avgload;
    bool hasAcceptedTokens_;
    bool hasGama_;
    bool hasGamaK_;
    bool useAddFoldReduce_;
    float gama_;
    float beta_;
    float scale_;
    uint64_t blockIdx;
};
} // namespace RecurrentGatedDeltaRule
#endif
