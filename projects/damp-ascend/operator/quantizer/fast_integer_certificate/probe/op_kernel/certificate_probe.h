// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "kernel_operator.h"
#include "probe_plan.h"
#include "../../integer_certificate_ascendc.h"
#define DAMP_QUANTIZER_ASCENDC
#include "../../../exact_quantizer_bits.h"
namespace DampIntegerProbe {
using namespace AscendC;
class Kernel {
public:
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR scale, GM_ADDR proposal,
        GM_ADDR c, GM_ADDR f, GM_ADDR accepted, GM_ADDR lower, GM_ADDR upper,
        GM_ADDR lowerDomain, GM_ADDR upperDomain, GM_ADDR code, GM_ADDR valid,
        const __gm__ Tiling* tiling, TPipe* pipe) {
        count_=tiling->count;
        validTiling_=tiling->abiVersion==ABI_VERSION &&
                     (count_==64 || count_==MAX_COUNT);
        inputGm_[0].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(x));
        inputGm_[1].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(scale));
        inputGm_[2].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(proposal));
        tableGm_[0].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(c));
        tableGm_[1].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(f));
        outputGm_[0].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(accepted));
        outputGm_[1].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(lower));
        outputGm_[2].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(upper));
        outputGm_[3].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(lowerDomain));
        outputGm_[4].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(upperDomain));
        outputGm_[5].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(code));
        outputGm_[6].SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(valid));
        for (uint32_t i=0;i<3;++i) pipe->InitBuffer(inputs_[i],1,MAX_COUNT*4);
        for (uint32_t i=0;i<2;++i) pipe->InitBuffer(tables_[i],1,128*4);
        for (uint32_t i=0;i<OUTPUTS;++i) pipe->InitBuffer(outputs_[i],1,MAX_COUNT*4);
        pipe->InitBuffer(scratch_,16*MAX_COUNT*4);
    }
    __aicore__ inline void Process() {
        if (!validTiling_) { return; } // no event has been allocated, no output write
        if (count_==64) { Run<64>(); } else { Run<896>(); }
    }
private:
    template<int32_t N> __aicore__ inline void Run() {
        LocalTensor<int32_t> in[3], lut[2], out[OUTPUTS], w[16];
        for (uint32_t i=0;i<3;++i) {
            in[i]=inputs_[i].AllocTensor<int32_t>();
            DataCopy(in[i],inputGm_[i],N);
            inputs_[i].EnQue(in[i]); in[i]=inputs_[i].DeQue<int32_t>();
        }
        for (uint32_t i=0;i<2;++i) {
            lut[i]=tables_[i].AllocTensor<int32_t>();
            DataCopy(lut[i],tableGm_[i],128);
            tables_[i].EnQue(lut[i]); lut[i]=tables_[i].DeQue<int32_t>();
        }
        for (uint32_t i=0;i<OUTPUTS;++i) out[i]=outputs_[i].AllocTensor<int32_t>();
        auto scratch=scratch_.Get<int32_t>();
        for (uint32_t i=0;i<16;++i) w[i]=scratch[i*MAX_COUNT];
        // Original frozen helper: no change to its equations or dependency fences.
        qwen36_damp_integer_certificate::Certify<N>(
            out[0],in[0],in[1],in[2],lut[0],lut[1],w);
        // Extra calls are diagnostic exports, NOT the cost of a production fast path.
        Adds(w[4],in[2],int32_t(-1),N); PipeBarrier<PIPE_V>();
        Maxs(w[4],w[4],int32_t(0),N); PipeBarrier<PIPE_V>();
        qwen36_damp_integer_certificate::EndpointFloor<N>(lut[0],lut[1],w);
        Adds(out[1],w[5],int32_t(0),N); PipeBarrier<PIPE_V>();
        Adds(out[3],w[7],int32_t(0),N); PipeBarrier<PIPE_V>();
        Mins(w[4],in[2],int32_t(126),N); PipeBarrier<PIPE_V>();
        qwen36_damp_integer_certificate::EndpointFloor<N>(lut[0],lut[1],w);
        Adds(out[2],w[5],int32_t(0),N); PipeBarrier<PIPE_V>();
        Adds(out[4],w[7],int32_t(0),N); PipeBarrier<PIPE_V>();
        const event_t vectorToScalar=static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::V_S));
        SetFlag<HardEvent::V_S>(vectorToScalar);
        WaitFlag<HardEvent::V_S>(vectorToScalar);
        // Deliberately no GatherMask compaction yet: scalar loop reads each lane.
        // It calls exact frozen fallback only for rejected lanes. Diagnostic only.
        for (uint32_t lane=0;lane<N;++lane) {
            const uint32_t xb=static_cast<uint32_t>(in[0].GetValue(lane));
            const uint32_t sb=static_cast<uint32_t>(in[1].GetValue(lane));
            const bool scaleDomain=sb>=0x00800000u && sb<=0x7f7fffffu;
            out[3].SetValue(lane,scaleDomain && out[3].GetValue(lane)!=0 ? 1 : 0);
            out[4].SetValue(lane,scaleDomain && out[4].GetValue(lane)!=0 ? 1 : 0);
            if (out[0].GetValue(lane)!=0) {
                const int32_t n=in[2].GetValue(lane);
                out[5].SetValue(lane,(xb>>31)!=0 ? -n : n);
                out[6].SetValue(lane,1);
            } else {
                const auto result=Qwen36DampQuantizer::ExactCode(xb,sb);
                out[5].SetValue(lane,result.code);
                out[6].SetValue(lane,result.valid ? 1 : 0);
            }
        }
        const event_t scalarToVector=static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::S_V));
        SetFlag<HardEvent::S_V>(scalarToVector);
        WaitFlag<HardEvent::S_V>(scalarToVector);
        for (uint32_t i=0;i<OUTPUTS;++i) {
            outputs_[i].EnQue(out[i]); out[i]=outputs_[i].DeQue<int32_t>();
            DataCopy(outputGm_[i][GUARD_INTS],out[i],N); // sole AIV, full32B intervals
            outputs_[i].FreeTensor(out[i]);
        }
        for (uint32_t i=0;i<3;++i) inputs_[i].FreeTensor(in[i]);
        for (uint32_t i=0;i<2;++i) tables_[i].FreeTensor(lut[i]);
    }
    uint32_t count_=0; bool validTiling_=false;
    GlobalTensor<int32_t> inputGm_[3],tableGm_[2],outputGm_[OUTPUTS];
    TQue<QuePosition::VECIN,1> inputs_[3],tables_[2];
    TQue<QuePosition::VECOUT,1> outputs_[OUTPUTS];
    TBuf<QuePosition::VECCALC> scratch_;
};
}

