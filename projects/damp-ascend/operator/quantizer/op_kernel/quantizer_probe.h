// SPDX-License-Identifier: Apache-2.0
#ifndef QWEN36_DAMP_QUANTIZER_PROBE_H
#define QWEN36_DAMP_QUANTIZER_PROBE_H
#include "kernel_operator.h"
#define DAMP_QUANTIZER_ASCENDC
#include "../exact_quantizer_bits.h"
namespace Qwen36DampQuantizerProbe {
using namespace AscendC;
constexpr uint32_t ABI_VERSION = 1;
constexpr uint32_t MAX_COUNT = 1792;
constexpr uint32_t GUARD_INTS = 8;
struct Tiling { uint32_t count; uint32_t abiVersion; };
class ExactBitsKernel {
public:
    __aicore__ inline void Init(
        GM_ADDR x, GM_ADDR scale, GM_ADDR codes, GM_ADDR valid,
        const __gm__ Tiling* tiling, TPipe* pipe)
    {
        count_ = tiling->count;
        validTiling_ = tiling->abiVersion == ABI_VERSION &&
            count_ >= 64 && count_ <= MAX_COUNT && count_ % 64 == 0;
        xGm_.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(x));
        sGm_.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(scale));
        codesGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(codes));
        validGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(valid));
        pipe->InitBuffer(xQueue_, 1, MAX_COUNT*sizeof(uint32_t));
        pipe->InitBuffer(sQueue_, 1, MAX_COUNT*sizeof(uint32_t));
        pipe->InitBuffer(codeQueue_, 1, MAX_COUNT*sizeof(int32_t));
        pipe->InitBuffer(validQueue_, 1, MAX_COUNT*sizeof(int32_t));
    }
    __aicore__ inline void Process()
    {
        if (!validTiling_) { return; } // no writes; initialized interiors expose failure
        auto x = xQueue_.AllocTensor<uint32_t>();
        auto s = sQueue_.AllocTensor<uint32_t>();
        DataCopy(x, xGm_, count_);
        DataCopy(s, sGm_, count_);
        xQueue_.EnQue<uint32_t>(x);
        sQueue_.EnQue<uint32_t>(s);
        x = xQueue_.DeQue<uint32_t>();
        s = sQueue_.DeQue<uint32_t>();
        // MTE2 produces raw bits, scalar S consumes them; explicit public pair.
        const event_t inputToScalar = static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::MTE2_S));
        SetFlag<HardEvent::MTE2_S>(inputToScalar);
        WaitFlag<HardEvent::MTE2_S>(inputToScalar);
        auto codes = codeQueue_.AllocTensor<int32_t>();
        auto valid = validQueue_.AllocTensor<int32_t>();
        for (uint32_t lane = 0; lane < count_; ++lane) {
            const auto result = Qwen36DampQuantizer::ExactCode(
                x.GetValue(lane), s.GetValue(lane));
            codes.SetValue(lane, result.code);
            valid.SetValue(lane, result.valid ? 1 : 0);
        }
        xQueue_.FreeTensor(x);
        sQueue_.FreeTensor(s);
        // S writes codes; S->V wait precedes VECOUT queue's V->MTE3 handshake.
        const event_t scalarToVector = static_cast<event_t>(
            GetTPipePtr()->FetchEventID(HardEvent::S_V));
        SetFlag<HardEvent::S_V>(scalarToVector);
        WaitFlag<HardEvent::S_V>(scalarToVector);
        codeQueue_.EnQue<int32_t>(codes);
        validQueue_.EnQue<int32_t>(valid);
        codes = codeQueue_.DeQue<int32_t>();
        valid = validQueue_.DeQue<int32_t>();
        // Entire contiguous write is 32B aligned, owner is this sole AIV.
        DataCopy(codesGm_[GUARD_INTS], codes, count_);
        DataCopy(validGm_[GUARD_INTS], valid, count_);
        codeQueue_.FreeTensor(codes);
        validQueue_.FreeTensor(valid);
    }
private:
    uint32_t count_ = 0;
    bool validTiling_ = false;
    TQue<QuePosition::VECIN, 1> xQueue_, sQueue_;
    TQue<QuePosition::VECOUT, 1> codeQueue_, validQueue_;
    GlobalTensor<uint32_t> xGm_, sGm_;
    GlobalTensor<int32_t> codesGm_, validGm_;
};
}
#endif

