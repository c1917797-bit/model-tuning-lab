// Copyright (c) 2025 Huawei Technologies Co., Ltd.
// SPDX-License-Identifier: Apache-2.0
// NEW default-OFF native transient FP32 final-prefill -> selected DAMP slots.
// Four packing methods copied byte-exact from frozen production15142a...40ff1.
// No recurrence/readout, external image/runtime or persistent FP32 sidecar.
#ifndef QWEN36_DAMP_SELECTED_PREFILL_H
#define QWEN36_DAMP_SELECTED_PREFILL_H
#if !defined(__NPU_ARCH__) || __NPU_ARCH__ != 2201
#error "Selected-slot prefill preparation is restricted to dav_c220/2201"
#endif
#include "kernel_operator.h"
#include "prefill_plan.h"
#include "../../../quantizer/fast_integer_certificate/integer_certificate_ascendc.h"
#define DAMP_QUANTIZER_ASCENDC
#include "../../exact_float_div_bits.h"
namespace Qwen36DampSelectedPrefill {
using namespace AscendC;
class Kernel {
public:
    __aicore__ inline explicit Kernel(const __gm__ Tiling* t)
      : prefills_(t->prefills),slots_(t->stateSlots),abiVersion_(t->abiVersion),
        useFloatCandidate_(t->useFloatCandidate) {
        quantizerLutGm_.SetGlobalBuffer(const_cast<__gm__ int32_t*>(
            reinterpret_cast<const __gm__ int32_t*>(t))+LUT_OFFSET_INTS);
    }
    __aicore__ inline void Init(GM_ADDR dense,GM_ADDR high,GM_ADDR low,GM_ADDR scales,
      GM_ADDR pk,GM_ADDR pv,GM_ADDR sr,GM_ADDR indices,GM_ADDR status,TPipe* pipe) {
        pipe_=pipe;
        denseGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(dense));
        highGm_.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(high));
        lowGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int8_t*>(low));
        scalesGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(scales));
        pkGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(pk));
        pvGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(pv));
        srGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(sr));
        indicesGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(indices));
        statusGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(status));
        pipe_->InitBuffer(quantizerWork_,QUANTIZER_WORK_BYTES);
        for(uint32_t i=0;i<16;++i)
            certWork_[i]=quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT,i*QUANTIZER_PLANE_BYTES);
        accepted_=quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT,28672);
        quotient_=quantizerWork_.GetWithOffset<float>(QUANTIZER_COUNT,30464);
        repeatedScale_=quantizerWork_.GetWithOffset<float>(QUANTIZER_COUNT,32256);
        magnitude_=quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT,34048);
        correctedCodes_=quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT,35840);
        originIndices_=quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT,37632);
        compactIndices_=quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT,39424);
        cTable_=quantizerWork_.GetWithOffset<int32_t>(128,41216);
        fTable_=quantizerWork_.GetWithOffset<int32_t>(128,41728);
        rejectMask_=quantizerWork_.GetWithOffset<uint8_t>(256,42240);
        pipe_->InitBuffer(metaIn_,1,160);
        pipe_->InitBuffer(planIn_,1,2048);
        pipe_->InitBuffer(rowIn_,1,512);
        pipe_->InitBuffer(packedOut_,2,PACKED_GROUP_BYTES);
        pipe_->InitBuffer(statusOut_,1,32);
        pipe_->InitBuffer(work_,WORK_BYTES);
        meta_=work_.GetWithOffset<int32_t>(40,0);
        pkOffsets_=work_.GetWithOffset<uint32_t>(128,256);
        pv_=work_.GetWithOffset<int32_t>(128,768);
        sr_=work_.GetWithOffset<float>(128,1280);
        rowRaw_=work_.GetWithOffset<float>(128,1792);
        candidate_=work_.GetWithOffset<float>(128,2304);
        divisor_=work_.GetWithOffset<float>(128,2816);
        state_=work_.GetWithOffset<float>(4096,3328);
        highFloat_=work_.GetWithOffset<float>(512,19712);
        scaleVector_=work_.GetWithOffset<float>(128,21760);
        ones_=work_.GetWithOffset<float>(128,22272);
        mask_=work_.GetWithOffset<uint8_t>(256,22784);
        lowFloat_=work_.GetWithOffset<float>(3584,23040);
        absA_=work_.GetWithOffset<float>(3584,37376);
        scratchB_=work_.GetWithOffset<float>(2048,51712);
    }
    __aicore__ inline void Process() {
        const bool metadataValid=LoadValidateMetadata();
        if(metadataValid) LoadQuantizerTables();
        for(uint32_t task=GetBlockIdx();task<prefills_*VALUE_HEADS;task+=GetBlockNum()) {
            uint32_t groups=0,certified=0,fallback=0,error=1;
            if(metadataValid) {
                const uint32_t source=task/VALUE_HEADS,head=task%VALUE_HEADS;
                LoadPlan(head);
                const uint64_t headSlot=static_cast<uint64_t>(meta_.GetValue(source))*VALUE_HEADS+head;
                error=0;
                for(uint32_t group=0;group<VALUE_GROUPS;++group) {
                    if(!LoadTransform(source,head,group,certified,fallback)) {error=2;break;}
                    if(!PackStore(headSlot,group)) {error=3;break;}
                    ++groups;
                }
            }
            StoreStatus(task,error,groups,certified,fallback);
        }
    }
private:
    __aicore__ inline void VectorToScalar()
    {
        const event_t event = static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::V_S));
        SetFlag<HardEvent::V_S>(event);
        WaitFlag<HardEvent::V_S>(event);
    }

    __aicore__ inline void ScalarToVector() {
        const event_t event=static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::S_V));
        SetFlag<HardEvent::S_V>(event);WaitFlag<HardEvent::S_V>(event);
    }
    // Validate ALL active selections before ANY state writer: PAD/range/duplicates
    // emit status failure without touching state. Numerical failures may follow
    // earlier committed groups: service must retire, never retry/feedback.
    __aicore__ inline bool LoadValidateMetadata() {
        if(abiVersion_!=ABI_VERSION || prefills_<1 || prefills_>16 ||
           slots_==0 || useFloatCandidate_>1) return false;
        auto local=metaIn_.AllocTensor<int32_t>();
        const DataCopyExtParams p{1,static_cast<uint32_t>(prefills_*sizeof(int32_t)),0,0,0};
        const DataCopyPadExtParams<int32_t> pad{true,0,
            static_cast<uint8_t>((8-prefills_%8)%8),0};
        DataCopyPad(local,indicesGm_,p,pad);
        metaIn_.EnQue<int32_t>(local);local=metaIn_.DeQue<int32_t>();
        DataCopy(meta_,local,static_cast<uint32_t>((prefills_+7)/8*8));
        PipeBarrier<PIPE_V>();metaIn_.FreeTensor(local);VectorToScalar();
        for(uint32_t i=0;i<prefills_;++i) {
            const int32_t slot=meta_.GetValue(i);
            if(slot<0 || static_cast<uint32_t>(slot)>=slots_) return false;
            for(uint32_t j=0;j<i;++j) if(meta_.GetValue(j)==slot) return false;
        }
        return true;
    }
    __aicore__ inline void LoadQuantizerTables()
    {
        LocalTensor<int32_t> local = planIn_.AllocTensor<int32_t>();
        DataCopy(local, quantizerLutGm_, 256);
        planIn_.EnQue<int32_t>(local);
        local = planIn_.DeQue<int32_t>();
        DataCopy(cTable_, local, 128);
        DataCopy(fTable_, local[128], 128);
        PipeBarrier<PIPE_V>();
        planIn_.FreeTensor(local);
    }

    __aicore__ inline void LoadPlan(uint32_t head) {
        auto local=planIn_.AllocTensor<int32_t>();
        const uint64_t offset=static_cast<uint64_t>(head)*HEAD_DIM;
        DataCopy(local,pkGm_[offset],128);DataCopy(local[128],pvGm_[offset],128);
        DataCopy(local.ReinterpretCast<float>()[256],srGm_[offset],128);
        planIn_.EnQue<int32_t>(local);local=planIn_.DeQue<int32_t>();
        ShiftLeft(pkOffsets_,local.ReinterpretCast<uint32_t>(),uint32_t(2),HEAD_DIM);
        DataCopy(pv_,local[128],HEAD_DIM);
        DataCopy(sr_,local.ReinterpretCast<float>()[256],HEAD_DIM);
        PipeBarrier<PIPE_V>();planIn_.FreeTensor(local);VectorToScalar();
    }
    __aicore__ inline bool LoadTransform(uint32_t source,uint32_t head,uint32_t group,
      uint32_t& certified,uint32_t& fallback) {
        for(uint32_t row=0;row<GROUP_VALUES;++row) {
            const int32_t originalV=pv_.GetValue(group*GROUP_VALUES+row);
            if(originalV<0 || originalV>=int32_t(HEAD_DIM)) return false;
            const uint64_t offset=((static_cast<uint64_t>(source)*VALUE_HEADS+head)*
                                   HEAD_DIM+static_cast<uint32_t>(originalV))*HEAD_DIM;
            auto local=rowIn_.AllocTensor<float>();
            DataCopy(local,denseGm_[offset],HEAD_DIM);
            rowIn_.EnQue<float>(local);local=rowIn_.DeQue<float>();
            DataCopy(rowRaw_,local,HEAD_DIM);PipeBarrier<PIPE_V>();
            rowIn_.FreeTensor(local);VectorToScalar();
            const uint32_t c=sr_.ReinterpretCast<uint32_t>().GetValue(originalV);
            if(c==0 || c>=0x7f800000U) return false;
            if(useFloatCandidate_) {
                union{uint32_t bits;float value;} divisor;divisor.bits=c;
                Duplicate(divisor_,divisor.value,HEAD_DIM);PipeBarrier<PIPE_V>();
                Div(candidate_,rowRaw_,divisor_,HEAD_DIM);PipeBarrier<PIPE_V>();
                VectorToScalar(); // arbitrary approximate Div is ONLY a proposal
            }
            bool valid=true;
            for(uint32_t k=0;k<HEAD_DIM;++k) {
                const uint32_t raw=rowRaw_.ReinterpretCast<uint32_t>().GetValue(k);
                Qwen36DampPrefill::FloatResult value;
                if(c==0x3f800000U) {
                    const bool finite=(raw&0x7fffffffU)<0x7f800000U;
                    value={finite,finite,finite?raw:0};++certified;
                } else if(useFloatCandidate_) {
                    const uint32_t proposal=candidate_.ReinterpretCast<uint32_t>().GetValue(k)&0x7fffffffU;
                    if(Qwen36DampPrefill::CertifiesFloat(raw,c,proposal)) {
                        value={true,true,(raw&0x80000000U)|proposal};++certified;
                    } else {value=Qwen36DampPrefill::ExactFloatDiv(raw,c);++fallback;}
                } else {value=Qwen36DampPrefill::ExactFloatDiv(raw,c);++fallback;}
                valid=valid && value.valid && value.finite;
                candidate_.ReinterpretCast<uint32_t>().SetValue(k,value.bits);
            }
            ScalarToVector();
            if(!valid) return false;
            Gather(state_[row*HEAD_DIM],candidate_,pkOffsets_,0,HEAD_DIM);
            PipeBarrier<PIPE_V>();VectorToScalar();
            // FP16 RNE overflow midpoint65520, not an arbitrary clipping floor.
            for(uint32_t k=0;k<HIGH_KEYS;++k)
                if((state_.ReinterpretCast<uint32_t>().GetValue(row*HEAD_DIM+k)&0x7fffffffU)>=0x477ff000U)
                    return false;
        }
        return true;
    }
    __aicore__ inline bool QuantizeChunk(uint32_t offset, const LocalTensor<int8_t>& dst)
    {
        constexpr uint32_t N = QUANTIZER_COUNT; // 4 reordered V rows * 112 keys
        for (uint32_t row = 0; row < 4; ++row) {
            DataCopy(repeatedScale_[row * LOW_KEYS], scaleVector_, LOW_KEYS);
        }
        PipeBarrier<PIPE_V>();
        Abs(quotient_, lowFloat_[offset], N);
        PipeBarrier<PIPE_V>();
        Div(quotient_, quotient_, repeatedScale_, N);
        PipeBarrier<PIPE_V>();
        auto quotientBits = quotient_.ReinterpretCast<uint32_t>();
        ShiftLeft(quotientBits, quotientBits, uint32_t(1), N);
        PipeBarrier<PIPE_V>();
        ShiftRight(quotientBits, quotientBits, uint32_t(1), N);
        PipeBarrier<PIPE_V>();
        // Includes Inf/NaN proposer bits; cannot reach RINT with a nonfinite
        // operand. A bad original x/scale still rejects and ExactCode invalidates.
        Mins(quotient_.ReinterpretCast<int32_t>(), quotient_.ReinterpretCast<int32_t>(), int32_t(0x42fe0000), N);
        PipeBarrier<PIPE_V>();
        Cast(magnitude_, quotient_, RoundMode::CAST_RINT, N);
        PipeBarrier<PIPE_V>();
        const auto rawX = lowFloat_[offset].ReinterpretCast<int32_t>();
        qwen36_damp_integer_certificate::Certify<QUANTIZER_COUNT>(accepted_, rawX,
            repeatedScale_.ReinterpretCast<int32_t>(), magnitude_, cTable_, fTable_, certWork_);
        // Restore sign from original raw x, vectorially. No all-lane scalar scan.
        ShiftRight(certWork_[0].ReinterpretCast<uint32_t>(), rawX.ReinterpretCast<uint32_t>(), uint32_t(31), N);
        PipeBarrier<PIPE_V>();
        Muls(certWork_[0], certWork_[0], int32_t(-2), N);
        PipeBarrier<PIPE_V>();
        Adds(certWork_[0], certWork_[0], int32_t(1), N);
        PipeBarrier<PIPE_V>();
        Mul(correctedCodes_, certWork_[0], magnitude_, N);
        PipeBarrier<PIPE_V>();
        Muls(quotient_.ReinterpretCast<int32_t>(), accepted_, int32_t(0x3f800000), N);
        PipeBarrier<PIPE_V>();
        CompareScalar(rejectMask_, quotient_, float(0), CMPMODE::EQ, N);
        PipeBarrier<PIPE_V>();
        CreateVecIndex(originIndices_, int32_t(0), N);
        PipeBarrier<PIPE_V>();
        uint64_t retained = 0;
        GatherMask(compactIndices_, originIndices_, rejectMask_.ReinterpretCast<uint32_t>(),
                   true, uint32_t(N), GatherMaskParams(1, 1, 8, 1), retained);
        PipeBarrier<PIPE_V>();
        VectorToScalar(); // compact indices and raw x/scale: V -> S, paired event
        bool valid = retained <= uint64_t(N);
        if (valid) {
            for (uint32_t rank = 0; rank < static_cast<uint32_t>(retained); ++rank) {
                const int32_t lane = compactIndices_.GetValue(rank);
                if (lane < 0 || lane >= static_cast<int32_t>(N)) {
                    valid = false;
                    continue; // never dereference an invalid compact index
                }
                const auto exact = Qwen36DampQuantizer::ExactCode(
                    static_cast<uint32_t>(rawX.GetValue(lane)),
                    static_cast<uint32_t>(repeatedScale_.ReinterpretCast<int32_t>().GetValue(lane)));
                correctedCodes_.SetValue(lane, exact.code);
                valid = valid && exact.valid;
            }
        }
        const event_t event = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::S_V));
        SetFlag<HardEvent::S_V>(event);
        WaitFlag<HardEvent::S_V>(event);
        if (!valid) { return false; } // both event directions completed
        Cast(quotient_, correctedCodes_, RoundMode::CAST_NONE, N);
        PipeBarrier<PIPE_V>();
        Cast(repeatedScale_.ReinterpretCast<half>(), quotient_, RoundMode::CAST_RINT, N);
        PipeBarrier<PIPE_V>();
        Cast(dst[offset], repeatedScale_.ReinterpretCast<half>(), RoundMode::CAST_TRUNC, N);
        PipeBarrier<PIPE_V>();
        return true;
    }

    __aicore__ inline bool PackStore(uint64_t headSlot, uint32_t group)
    {
        DataCopyParams hiLayout{GROUP_VALUES, 2, 14, 0};
        DataCopyParams loLayout{GROUP_VALUES, 14, 2, 0};
        DataCopy(highFloat_, state_, hiLayout);
        DataCopy(lowFloat_, state_[HIGH_KEYS], loLayout);
        PipeBarrier<PIPE_V>();
        LocalTensor<half> packed = packedOut_.AllocTensor<half>();
        Cast(packed, highFloat_, RoundMode::CAST_RINT, GROUP_VALUES * HIGH_KEYS);
        Abs(absA_, lowFloat_, GROUP_VALUES * LOW_KEYS);
        PipeBarrier<PIPE_V>();

        // RA max over V32 independently for each of 112 low K columns. Explicit
        // ping-pong forbids destructive source/destination overlap; finite max
        // is order-independent. This uses A2 vector Max, not 950 micro-registers.
        LocalTensor<float> a = absA_;
        LocalTensor<float> b = scratchB_;
        for (uint32_t rows = GROUP_VALUES; rows > 1; rows /= 2) {
            const uint32_t next = rows / 2;
            for (uint32_t row = 0; row < next; ++row) {
                Max(b[row * LOW_KEYS], a[row * LOW_KEYS],
                    a[(row + next) * LOW_KEYS], LOW_KEYS);
            }
            PipeBarrier<PIPE_V>();
            LocalTensor<float> swap = a;
            a = b;
            b = swap;
        }
        Duplicate(scaleVector_, 0.0f, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        DataCopy(scaleVector_, a, LOW_KEYS);
        PipeBarrier<PIPE_V>();
        // Only truly-zero amax gets scale=1. A nonzero underflow must be
        // detected by the numerical gate, not silently changed to zero semantics.
        CompareScalar(mask_, scaleVector_, 0.0f, CMPMODE::EQ, HEAD_DIM);
        Duplicate(ones_, 1.0f, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        Muls(scaleVector_, scaleVector_, SCALE_RECIPROCAL_FP32, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        Select(scaleVector_, mask_, ones_, scaleVector_,
               SELMODE::VSEL_TENSOR_TENSOR_MODE, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        for (uint32_t chunk = 0; chunk < 8; ++chunk) {
            if (!QuantizeChunk(chunk * QUANTIZER_COUNT, packed.ReinterpretCast<int8_t>()[1024])) {
                // This group has not been stored. Earlier groups/tasks may have
                // been stored: NOT a transactional full-invocation rollback.
                packedOut_.FreeTensor(packed);
                return false;
            }
        }
        DataCopy(packed.ReinterpretCast<float>()[1152], scaleVector_, LOW_KEYS);
        packedOut_.EnQue<half>(packed);
        packed = packedOut_.DeQue<half>();
        const uint64_t vRow = headSlot * HEAD_DIM + group * GROUP_VALUES;
        const uint64_t scaleOffset = (headSlot * VALUE_GROUPS + group) * LOW_KEYS;
        // Each region is a multiple of 64 bytes and belongs to this full-head
        // writer. No sub-32B row store and no arbitrary-Pv scatter DMA.
        DataCopyParams hiParams{1, 1024, 0, 0};
        DataCopyParams loParams{1, 3584, 0, 0};
        DataCopyParams scaleParams{1, 448, 0, 0};
        DataCopyPad(highGm_[vRow * HIGH_KEYS], packed, hiParams);
        DataCopyPad(lowGm_[vRow * LOW_KEYS], packed.ReinterpretCast<int8_t>()[1024], loParams);
        DataCopyPad(scalesGm_[scaleOffset], packed.ReinterpretCast<float>()[1152], scaleParams);
        packedOut_.FreeTensor(packed);
        return true;
    }

    __aicore__ inline void StoreStatus(uint32_t task,uint32_t error,uint32_t groups,
      uint32_t certified,uint32_t fallback) {
        auto local=statusOut_.AllocTensor<int32_t>();
        local.SetValue(0,error==0?1:0);local.SetValue(1,int32_t(error));
        local.SetValue(2,int32_t(groups));local.SetValue(3,int32_t(certified));
        local.SetValue(4,int32_t(fallback));local.SetValue(5,128*128);
        local.SetValue(6,0);local.SetValue(7,0);ScalarToVector();
        statusOut_.EnQue<int32_t>(local);local=statusOut_.DeQue<int32_t>();
        DataCopy(statusGm_[static_cast<uint64_t>(task)*8],local,8);
        statusOut_.FreeTensor(local);
    }
private:
    GlobalTensor<float> denseGm_,scalesGm_,srGm_;
    GlobalTensor<half> highGm_;
    GlobalTensor<int8_t> lowGm_;
    GlobalTensor<int32_t> pkGm_,pvGm_,indicesGm_,statusGm_,quantizerLutGm_;
    TPipe* pipe_;
    TQue<QuePosition::VECIN,1> metaIn_,planIn_,rowIn_;
    TQue<QuePosition::VECOUT,2> packedOut_;
    TQue<QuePosition::VECOUT,1> statusOut_;
    TBuf<TPosition::VECCALC> work_,quantizerWork_;
    LocalTensor<int32_t> certWork_[16],accepted_,magnitude_,correctedCodes_;
    LocalTensor<int32_t> originIndices_,compactIndices_,cTable_,fTable_,meta_,pv_;
    LocalTensor<float> quotient_,repeatedScale_,sr_,rowRaw_,candidate_,divisor_;
    LocalTensor<float> state_,highFloat_,scaleVector_,ones_,lowFloat_,absA_,scratchB_;
    LocalTensor<uint32_t> pkOffsets_;
    LocalTensor<uint8_t> rejectMask_,mask_;
    uint32_t prefills_,slots_,abiVersion_,useFloatCandidate_;
};
}
#endif
