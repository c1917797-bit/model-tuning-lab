/**
?* Copyright (c) 2025 Huawei Technologies Co., Ltd.
?* This program is free software, you can redistribute it and/or modify it under the terms and conditions of
?* Please refer to the License for details. You may not use this file except in compliance with the License.
?* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
?* INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
?* See LICENSE in the root of the software repository for the full text of the License.
?*/


// Modified 2026-10-06: test-only, native-derived DAMP coordinate reference.
// Pinned native commit/file identity and method mapping: ../README.md.
// No candidate compressed load/store/quantizer is included or linked.
#ifndef QWEN36_DAMP_NATIVE_SR_REFERENCE_H
#define QWEN36_DAMP_NATIVE_SR_REFERENCE_H
#include "kernel_operator.h"
#include "lib/matmul_intf.h"

namespace Qwen36DampReference {
using namespace AscendC;
using namespace matmul;
constexpr uint32_t REPEAT_LENTH = 64;
constexpr uint32_t MAX_REPEAT_TIME = 255;
constexpr uint32_t FP32_NUM_PER_BLOCK = 8;
constexpr uint32_t ADD_FOLD_REDUCE_MIN_K = 128;
constexpr uint32_t DIM = 128;
constexpr uint32_t HEADS = 12;
constexpr uint32_t ROWS = 32;
constexpr uint32_t WORK_BYTES = 39232;
struct ReferenceInputs {
    GM_ADDR query;
    GM_ADDR key;
    GM_ADDR value;
    GM_ADDR g;
    GM_ADDR beta;
    GM_ADDR selectedState;
    GM_ADDR pk;
    GM_ADDR pv;
    GM_ADDR invPv;
    GM_ADDR sr;
    GM_ADDR updated;
    GM_ADDR outputFloat;
    GM_ADDR outputBf16;
};
class NativeSrReference {
public:
    __aicore__ inline NativeSrReference(uint32_t tokens, float qScale)
        : tokens_(tokens), scale_(qScale) {}
    __aicore__ inline void Init(const ReferenceInputs& p, TPipe* pipe) {
        pipe_ = pipe;
        queryGm_.SetGlobalBuffer((__gm__ bfloat16_t*)p.query);
        keyGm_.SetGlobalBuffer((__gm__ bfloat16_t*)p.key);
        valueGm_.SetGlobalBuffer((__gm__ bfloat16_t*)p.value);
        gGm_.SetGlobalBuffer((__gm__ float*)p.g);
        betaGm_.SetGlobalBuffer((__gm__ bfloat16_t*)p.beta);
        stateGm_.SetGlobalBuffer((__gm__ float*)p.selectedState);
        pkGm_.SetGlobalBuffer((__gm__ int32_t*)p.pk);
        pvGm_.SetGlobalBuffer((__gm__ int32_t*)p.pv);
        inverseGm_.SetGlobalBuffer((__gm__ int32_t*)p.invPv);
        srGm_.SetGlobalBuffer((__gm__ float*)p.sr);
        updatedGm_.SetGlobalBuffer((__gm__ float*)p.updated);
        floatGm_.SetGlobalBuffer((__gm__ float*)p.outputFloat);
        bf16Gm_.SetGlobalBuffer((__gm__ bfloat16_t*)p.outputBf16);
        pipe_->InitBuffer(qInput_, 1, 256);
        pipe_->InitBuffer(kInput_, 1, 256);
        pipe_->InitBuffer(vInput_, 1, 256);
        pipe_->InitBuffer(betaInput_, 1, 32);
        pipe_->InitBuffer(gInput_, 1, 64);
        pipe_->InitBuffer(planInput_, 1, 2048);
        pipe_->InitBuffer(stateInput_, 1, ROWS * DIM * sizeof(float));
        pipe_->InitBuffer(stateOutput_, 1, ROWS * DIM * sizeof(float));
        pipe_->InitBuffer(floatOutput_, 1, DIM * sizeof(float));
        pipe_->InitBuffer(bf16Output_, 1, DIM * sizeof(bfloat16_t));
        pipe_->InitBuffer(work_, WORK_BYTES);
        stateInUb = work_.GetWithOffset<float>(ROWS * DIM, 0);
        broadTmpInUb = work_.GetWithOffset<float>(ROWS * DIM, 16384);
        qOriginal_ = work_.GetWithOffset<float>(DIM, 32768);
        kOriginal_ = work_.GetWithOffset<float>(DIM, 33280);
        vOriginal_ = work_.GetWithOffset<float>(DIM, 33792);
        qInUb = work_.GetWithOffset<float>(DIM, 34304);
        kInUb = work_.GetWithOffset<float>(DIM, 34816);
        vScaled_ = work_.GetWithOffset<float>(DIM, 35328);
        vInUb = work_.GetWithOffset<float>(DIM, 35840);
        readoutReordered_ = work_.GetWithOffset<float>(DIM, 36352);
        readoutOriginal_ = work_.GetWithOffset<float>(DIM, 36864);
        pkBytes_ = work_.GetWithOffset<uint32_t>(DIM, 37376);
        pvBytes_ = work_.GetWithOffset<uint32_t>(DIM, 37888);
        inverseBytes_ = work_.GetWithOffset<uint32_t>(DIM, 38400);
        deltaInUb = work_.GetWithOffset<float>(ROWS, 38912);
        attnInUb = work_.GetWithOffset<float>(ROWS, 39040);
        betaInUb = work_.GetWithOffset<float>(16, 39168);
        // gk is absent by the explicit test ABI. This unused view permits the
        // copied native Compute text to retain its optional gk branch verbatim.
        gamaKInUb = qOriginal_;
    }
    __aicore__ inline void Process() {
        for (uint32_t task = GetBlockIdx(); task < tokens_ * HEADS; task += GetBlockNum())
            ProcessHead(task / HEADS, task % HEADS);
    }
private:
    __aicore__ inline void VectorToScalar() {
        TEventID id = GetTPipePtr()->FetchEventID(HardEvent::V_S);
        SetFlag<HardEvent::V_S>(id);
        WaitFlag<HardEvent::V_S>(id);
    }
    __aicore__ inline void LoadPlans(uint32_t h) {
        planLocal_ = planInput_.AllocTensor<int32_t>();
        DataCopyExtParams params{1, 512, 0, 0, 0};
        DataCopyPadExtParams<int32_t> pad{true, 0, 0, 0};
        const uint64_t off = static_cast<uint64_t>(h) * DIM;
        DataCopyPad(planLocal_, pkGm_[off], params, pad);
        DataCopyPad(planLocal_[128], pvGm_[off], params, pad);
        DataCopyPad(planLocal_[256], inverseGm_[off], params, pad);
        DataCopyPadExtParams<float> fpPad{true, 0, 0, 0.0f};
        DataCopyPad(planLocal_.ReinterpretCast<float>()[384], srGm_[off], params, fpPad);
        planInput_.EnQue(planLocal_);
        planLocal_ = planInput_.DeQue<int32_t>();
        // Input INT32 plans are logical indices; only Gather consumes bytes.
        ShiftLeft(pkBytes_, planLocal_.ReinterpretCast<uint32_t>(), 2u, DIM);
        ShiftLeft(pvBytes_, planLocal_.ReinterpretCast<uint32_t>()[128], 2u, DIM);
        ShiftLeft(inverseBytes_, planLocal_.ReinterpretCast<uint32_t>()[256], 2u, DIM);
        srLocal_ = planLocal_.ReinterpretCast<float>()[384];
        PipeBarrier<PIPE_V>();
    }
    __aicore__ inline void CopyInQKV(uint32_t token, uint32_t h) {
        LocalTensor<bfloat16_t> qLocal = qInput_.AllocTensor<bfloat16_t>();
        LocalTensor<bfloat16_t> kLocal = kInput_.AllocTensor<bfloat16_t>();
        LocalTensor<bfloat16_t> vLocal = vInput_.AllocTensor<bfloat16_t>();
        DataCopyExtParams params{1, 256, 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> pad{true, 0, 0, (bfloat16_t)0};
        const uint64_t qoff = (static_cast<uint64_t>(token) * 4 + h / 3) * DIM;
        const uint64_t voff = (static_cast<uint64_t>(token) * HEADS + h) * DIM;
        DataCopyPad(qLocal, queryGm_[qoff], params, pad);
        DataCopyPad(kLocal, keyGm_[qoff], params, pad);
        DataCopyPad(vLocal, valueGm_[voff], params, pad);
        qInput_.EnQue(qLocal); kInput_.EnQue(kLocal); vInput_.EnQue(vLocal);
        qLocal = qInput_.DeQue<bfloat16_t>();
        kLocal = kInput_.DeQue<bfloat16_t>();
        vLocal = vInput_.DeQue<bfloat16_t>();
        // Native casts precede scaling; DAMP adds no BF16 V/c intermediate.
        Cast(qOriginal_, qLocal, RoundMode::CAST_NONE, DIM);
        Cast(kOriginal_, kLocal, RoundMode::CAST_NONE, DIM);
        Cast(vOriginal_, vLocal, RoundMode::CAST_NONE, DIM);
        PipeBarrier<PIPE_V>();
        Div(vScaled_, vOriginal_, srLocal_, DIM);
        Gather(qInUb, qOriginal_, pkBytes_, 0, DIM);
        Gather(kInUb, kOriginal_, pkBytes_, 0, DIM);
        PipeBarrier<PIPE_V>();
        Gather(vInUb, vScaled_, pvBytes_, 0, DIM);
        Muls(qInUb, qInUb, scale_, DIM);
        PipeBarrier<PIPE_V>();
        qInput_.FreeTensor(qLocal); kInput_.FreeTensor(kLocal); vInput_.FreeTensor(vLocal);
    }
    __aicore__ inline void CopyInGamaBeta(uint32_t token, uint32_t h) {
        LocalTensor<bfloat16_t> bLocal = betaInput_.AllocTensor<bfloat16_t>();
        DataCopyExtParams bp{1, 24, 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> bpad{true, 0, 4, (bfloat16_t)0};
        DataCopyPad(bLocal, betaGm_[static_cast<uint64_t>(token) * HEADS], bp, bpad);
        betaInput_.EnQue(bLocal); bLocal = betaInput_.DeQue<bfloat16_t>();
        Cast(betaInUb, bLocal, RoundMode::CAST_NONE, 16);
        betaInput_.FreeTensor(bLocal);
        LocalTensor<float> gLocal = gInput_.AllocTensor<float>();
        DataCopyExtParams gp{1, 48, 0, 0, 0};
        DataCopyPadExtParams<float> gpad{true, 0, 4, 0.0f};
        DataCopyPad(gLocal, gGm_[static_cast<uint64_t>(token) * HEADS], gp, gpad);
        gInput_.EnQue(gLocal); gLocal = gInput_.DeQue<float>();
        // Frozen native CopyInGamaBeta exponentiates the complete Nv row.
        Exp(gLocal, gLocal, HEADS);
        PipeBarrier<PIPE_V>();
        VectorToScalar();
        gama_ = gLocal.GetValue(h);
        beta_ = betaInUb.GetValue(h);
        gInput_.FreeTensor(gLocal);
    }
    __aicore__ inline void LoadState(uint64_t offset) {
        LocalTensor<float> stateLocal = stateInput_.AllocTensor<float>();
        DataCopy(stateLocal, stateGm_[offset], ROWS * DIM);
        stateInput_.EnQue(stateLocal); stateLocal = stateInput_.DeQue<float>();
        // Frozen native LoadPrefetchedState's float32_t branch.
        DataCopy(stateInUb, stateLocal, ROWS * DIM);
        stateInput_.FreeTensor(stateLocal);
        PipeBarrier<PIPE_V>();
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

        // TEST seam: expose native updated state BEFORE any rounding/packing.
        PipeBarrier<PIPE_V>();
    }
    __aicore__ inline void StoreState(uint64_t offset) {
        LocalTensor<float> local = stateOutput_.AllocTensor<float>();
        DataCopy(local, stateInUb, ROWS * DIM);
        stateOutput_.EnQue(local); local = stateOutput_.DeQue<float>();
        DataCopy(updatedGm_[offset], local, ROWS * DIM);
        stateOutput_.FreeTensor(local);
    }
    __aicore__ inline void StoreRestoredReadout(uint64_t offset) {
        Gather(readoutOriginal_, readoutReordered_, inverseBytes_, 0, DIM);
        PipeBarrier<PIPE_V>();
        Mul(readoutOriginal_, readoutOriginal_, srLocal_, DIM);
        PipeBarrier<PIPE_V>();
        LocalTensor<float> fp = floatOutput_.AllocTensor<float>();
        LocalTensor<bfloat16_t> bf = bf16Output_.AllocTensor<bfloat16_t>();
        DataCopy(fp, readoutOriginal_, DIM);
        Cast(bf, readoutOriginal_, RoundMode::CAST_RINT, DIM);
        floatOutput_.EnQue(fp); bf16Output_.EnQue(bf);
        fp = floatOutput_.DeQue<float>(); bf = bf16Output_.DeQue<bfloat16_t>();
        DataCopy(floatGm_[offset], fp, DIM);
        DataCopy(bf16Gm_[offset], bf, DIM);
        floatOutput_.FreeTensor(fp); bf16Output_.FreeTensor(bf);
    }
    __aicore__ inline void ProcessHead(uint32_t token, uint32_t h) {
        LoadPlans(h); CopyInQKV(token, h); CopyInGamaBeta(token, h);
        const uint64_t headOffset = (static_cast<uint64_t>(token) * HEADS + h) * DIM;
        for (uint32_t v = 0; v < DIM; v += ROWS) {
            const uint64_t stateOffset = (headOffset + v) * DIM;
            LoadState(stateOffset);
            Compute(ROWS, 0, v);
            // No scatter to per-32row original-V outputs: one head owner
            // performs a single full-head aligned DMA after inverse Pv.
            DataCopy(readoutReordered_[v], attnInUb, ROWS);
            PipeBarrier<PIPE_V>();
            StoreState(stateOffset);
        }
        StoreRestoredReadout(headOffset);
        planInput_.FreeTensor(planLocal_);
    }
    GlobalTensor<bfloat16_t> queryGm_, keyGm_, valueGm_, betaGm_, bf16Gm_;
    GlobalTensor<float> gGm_, stateGm_, srGm_, updatedGm_, floatGm_;
    GlobalTensor<int32_t> pkGm_, pvGm_, inverseGm_;
    TPipe* pipe_;
    TQue<QuePosition::VECIN, 1> qInput_, kInput_, vInput_, betaInput_, gInput_, planInput_, stateInput_;
    TQue<QuePosition::VECOUT, 1> stateOutput_, floatOutput_, bf16Output_;
    TBuf<TPosition::VECCALC> work_;
    LocalTensor<int32_t> planLocal_;
    LocalTensor<uint32_t> pkBytes_, pvBytes_, inverseBytes_;
    LocalTensor<float> stateInUb, broadTmpInUb, qInUb, kInUb, vInUb, deltaInUb, attnInUb;
    LocalTensor<float> qOriginal_, kOriginal_, vOriginal_, vScaled_, readoutReordered_, readoutOriginal_;
    LocalTensor<float> srLocal_, betaInUb, gamaKInUb;
    const uint32_t alignK_ = DIM;
    const bool hasGama_ = true, hasGamaK_ = false, useAddFoldReduce_ = true;
    uint32_t tokens_;
    float scale_, gama_, beta_;
};
} // namespace Qwen36DampReference
#endif
