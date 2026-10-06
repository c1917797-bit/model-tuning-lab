// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "kernel_operator.h"
#include "probe_plan.h"
#if !defined(__NPU_ARCH__) || __NPU_ARCH__ != 2201
#error "DAMP exact-float probe device path requires verified dav-2201"
#endif
#define DAMP_QUANTIZER_ASCENDC
#include "../../exact_float_div_bits.h"
namespace DampPrefillFloatProbe {
using namespace AscendC;
class Kernel {
public:
    __aicore__ inline void Init(GM_ADDR x,GM_ADDR sr,GM_ADDR proposal,GM_ADDR bits,
        GM_ADDR valid,GM_ADDR finite,GM_ADDR certified,const __gm__ Tiling* tiling,TPipe* pipe) {
        count_=tiling->count;useCandidate_=tiling->useCandidate==1;
        admitted_=tiling->abiVersion==ABI_VERSION && tiling->reserved==0 &&
            tiling->useCandidate<=1 && (count_==64 || count_==MAX_COUNT);
        inputGm_[0].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(x));
        inputGm_[1].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(sr));
        inputGm_[2].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(proposal));
        outputGm_[0].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(bits));
        outputGm_[1].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(valid));
        outputGm_[2].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(finite));
        outputGm_[3].SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(certified));
        for (uint32_t i=0;i<3;++i) pipe->InitBuffer(inputs_[i],1,MAX_COUNT*4);
        for (uint32_t i=0;i<OUTPUTS;++i) pipe->InitBuffer(outputs_[i],1,MAX_COUNT*4);
    }
    __aicore__ inline void Process() {
        if (!admitted_) { return; } // no event acquired/writer before invalid tiling
        for (uint32_t i=0;i<3;++i) {
            in_[i]=inputs_[i].AllocTensor<uint32_t>();
            DataCopy(in_[i],inputGm_[i],count_);
            inputs_[i].EnQue(in_[i]);in_[i]=inputs_[i].DeQue<uint32_t>();
        }
        for (uint32_t i=0;i<OUTPUTS;++i) out_[i]=outputs_[i].AllocTensor<uint32_t>();
        // MTE2-produced inputs are consumed by scalar GetValue, not merely V.
        const event_t mteToScalar=static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::MTE2_S));
        SetFlag<HardEvent::MTE2_S>(mteToScalar);
        WaitFlag<HardEvent::MTE2_S>(mteToScalar);
        for (uint32_t lane=0;lane<count_;++lane) {
            const uint32_t xb=in_[0].GetValue(lane),cb=in_[1].GetValue(lane);
            const uint32_t proposal=in_[2].GetValue(lane);
            const bool accepted=useCandidate_ &&
                Qwen36DampPrefill::CertifiesFloat(xb,cb,proposal);
            const auto result=accepted
                ? Qwen36DampPrefill::FloatResult{true,true,(xb&0x80000000U)|proposal}
                : Qwen36DampPrefill::ExactFloatDiv(xb,cb);
            out_[0].SetValue(lane,result.bits);
            out_[1].SetValue(lane,result.valid ? 1 : 0);
            out_[2].SetValue(lane,result.finite ? 1 : 0);
            out_[3].SetValue(lane,accepted ? 1 : 0);
        }
        const event_t scalarToVector=static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::S_V));
        SetFlag<HardEvent::S_V>(scalarToVector);WaitFlag<HardEvent::S_V>(scalarToVector);
        for (uint32_t i=0;i<OUTPUTS;++i) {
            outputs_[i].EnQue(out_[i]);out_[i]=outputs_[i].DeQue<uint32_t>();
            DataCopy(outputGm_[i][GUARD_INTS],out_[i],count_);
            outputs_[i].FreeTensor(out_[i]);
        }
        for (uint32_t i=0;i<3;++i) inputs_[i].FreeTensor(in_[i]);
    }
    uint32_t count_=0;bool useCandidate_=false,admitted_=false;
    GlobalTensor<uint32_t> inputGm_[3],outputGm_[OUTPUTS];
    LocalTensor<uint32_t> in_[3],out_[OUTPUTS];
    TQue<QuePosition::VECIN,1> inputs_[3];
    TQue<QuePosition::VECOUT,1> outputs_[OUTPUTS];
};
}
