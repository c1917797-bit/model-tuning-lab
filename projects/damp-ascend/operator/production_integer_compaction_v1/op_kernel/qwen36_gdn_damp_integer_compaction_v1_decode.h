// Copyright (c) 2025 Huawei Technologies Co., Ltd.
// Separate default-OFF integer-compaction v1 draft; never overwrites original v4.
// Modified 2026-10-06: DAMP mixed-state load/update/readout/requantization,
// full-head DMA ownership, static permutation/SR and fail-closed metadata.
// Native recurrent arithmetic attribution: see README.md and LICENSE-APACHE.
#ifndef QWEN36_GDN_DAMP_INTEGER_COMPACTION_V1_DECODE_KERNEL_H
#define QWEN36_GDN_DAMP_INTEGER_COMPACTION_V1_DECODE_KERNEL_H

#include "kernel_operator.h"
#include "qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h"
#include "../../quantizer/fast_integer_certificate/integer_certificate_ascendc.h"
#define DAMP_QUANTIZER_ASCENDC
#include "../../quantizer/exact_quantizer_bits.h"

namespace Qwen36DampIntegerCompactionV1 {
using namespace AscendC;
constexpr uint32_t FP32_PER_BLOCK = 8;
constexpr uint32_t REPEAT_LENGTH = 64;

struct DampInitParams {
    // GM_ADDR expands to __gm__ uint8_t*: every field needs its own macro.
    GM_ADDR query;
    GM_ADDR key;
    GM_ADDR value;
    GM_ADDR g;
    GM_ADDR beta;
    GM_ADDR highState;
    GM_ADDR lowState;
    GM_ADDR lowScale;
    GM_ADDR pk;
    GM_ADDR pv;
    GM_ADDR invPv;
    GM_ADDR sr;
    GM_ADDR actualSeqLengths;
    GM_ADDR stateIndices;
    GM_ADDR out;
};

// One AIV task owns an entire (token,value-head), including its four V groups
// and the full original-coordinate output. No dense FP32 state exists in GM.
class DampKernel {
public:
    __aicore__ inline explicit DampKernel(const __gm__ DampTilingData* tiling)
        : tokens_(tiling->tokens), slots_(tiling->stateSlots),
          scale_(tiling->qScale), abiVersion_(tiling->abiVersion)
    {
        quantizerLutGm_.SetGlobalBuffer(
            const_cast<__gm__ int32_t*>(reinterpret_cast<const __gm__ int32_t*>(tiling)) + LUT_OFFSET_INTS);
    }

    __aicore__ inline void Init(const DampInitParams& p, TPipe* pipe)
    {
        pipe_ = pipe;
        queryGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t*>(p.query));
        keyGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t*>(p.key));
        valueGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t*>(p.value));
        gGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(p.g));
        betaGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t*>(p.beta));
        highGm_.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(p.highState));
        lowGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int8_t*>(p.lowState));
        scalesGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(p.lowScale));
        pkGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(p.pk));
        pvGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(p.pv));
        invPvGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(p.invPv));
        srGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(p.sr));
        lengthsGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(p.actualSeqLengths));
        indicesGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(p.stateIndices));
        outGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t*>(p.out));

        // New disjoint TBuf first; every offset below is an explicit byte range.
        pipe_->InitBuffer(quantizerWork_, QUANTIZER_WORK_BYTES);
        for (uint32_t i = 0; i < 16; ++i) {
            certWork_[i] = quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT, i * QUANTIZER_PLANE_BYTES);
        }
        accepted_ = quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT, 28672);
        quotient_ = quantizerWork_.GetWithOffset<float>(QUANTIZER_COUNT, 30464);
        repeatedScale_ = quantizerWork_.GetWithOffset<float>(QUANTIZER_COUNT, 32256);
        magnitude_ = quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT, 34048);
        correctedCodes_ = quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT, 35840);
        originIndices_ = quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT, 37632);
        compactIndices_ = quantizerWork_.GetWithOffset<int32_t>(QUANTIZER_COUNT, 39424);
        cTable_ = quantizerWork_.GetWithOffset<int32_t>(128, 41216);
        fTable_ = quantizerWork_.GetWithOffset<int32_t>(128, 41728);
        rejectMask_ = quantizerWork_.GetWithOffset<uint8_t>(256, 42240);
        pipe_->InitBuffer(metaIn_, 1, 160);
        pipe_->InitBuffer(tokenIn_, 1, 864);
        pipe_->InitBuffer(planIn_, 1, 2048);
        pipe_->InitBuffer(stateIn_, 1, PACKED_GROUP_BYTES);
        pipe_->InitBuffer(packedOut_, 2, PACKED_GROUP_BYTES);
        pipe_->InitBuffer(output_, 2, 256);
        pipe_->InitBuffer(work_, WORK_BYTES);
        meta_ = work_.GetWithOffset<int32_t>(64, 0);
        qOrig_ = work_.GetWithOffset<float>(128, 256);
        kOrig_ = work_.GetWithOffset<float>(128, 768);
        vOrig_ = work_.GetWithOffset<float>(128, 1280);
        q_ = work_.GetWithOffset<float>(128, 1792);
        k_ = work_.GetWithOffset<float>(128, 2304);
        v_ = work_.GetWithOffset<float>(128, 2816);
        sr_ = work_.GetWithOffset<float>(128, 3328);
        pkOffsets_ = work_.GetWithOffset<uint32_t>(128, 3840);
        pvOffsets_ = work_.GetWithOffset<uint32_t>(128, 4352);
        invOffsets_ = work_.GetWithOffset<uint32_t>(128, 4864);
        delta_ = work_.GetWithOffset<float>(64, 5376);
        attn_ = work_.GetWithOffset<float>(128, 5632);
        outOrig_ = work_.GetWithOffset<float>(128, 6144);
        scalar_ = work_.GetWithOffset<float>(64, 6656);
        highFloat_ = work_.GetWithOffset<float>(512, 6912);
        scaleVector_ = work_.GetWithOffset<float>(128, 8960);
        ones_ = work_.GetWithOffset<float>(128, 9472);
        mask_ = work_.GetWithOffset<uint8_t>(256, 9984);
        state_ = work_.GetWithOffset<float>(4096, 10240);
        broad_ = work_.GetWithOffset<float>(4096, 26624);
        lowFloat_ = work_.GetWithOffset<float>(3584, 43008);
        absA_ = work_.GetWithOffset<float>(3584, 57344);
        scratchB_ = work_.GetWithOffset<float>(2048, 71680);
    }

    __aicore__ inline void Process()
    {
        const bool valid = LoadValidateMetadata();
        if (valid) { LoadQuantizerTables(); }
        const uint32_t tasks = tokens_ * VALUE_HEADS;
        for (uint32_t task = GetBlockIdx(); task < tasks; task += GetBlockNum()) {
            if (!valid) {
                StoreInvalid(task);
            } else {
                ProcessTask(task / VALUE_HEADS, task % VALUE_HEADS);
            }
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

    // Validate every active slot before any writer touches state. On malformed
    // metadata the complete invocation emits NaNs and leaves state unchanged.
    // Serving must additionally reject this metadata on its CPU scheduling seam.
    __aicore__ inline bool LoadValidateMetadata()
    {
        LocalTensor<int32_t> local = metaIn_.AllocTensor<int32_t>();
        DataCopyExtParams indicesParams{
            1, static_cast<uint32_t>(tokens_ * sizeof(int32_t)), 0, 0, 0};
        DataCopyPadExtParams<int32_t> indicesPad{
            true, 0, static_cast<uint8_t>((8 - tokens_ % 8) % 8), 0};
        DataCopyPad(local, indicesGm_, indicesParams, indicesPad);
        DataCopyExtParams lengthsParams{
            1, static_cast<uint32_t>((tokens_ + 1) * sizeof(int32_t)), 0, 0, 0};
        DataCopyPadExtParams<int32_t> lengthsPad{
            true, 0, static_cast<uint8_t>((8 - (tokens_ + 1) % 8) % 8), 0};
        DataCopyPad(local[16], lengthsGm_, lengthsParams, lengthsPad);
        metaIn_.EnQue<int32_t>(local);
        local = metaIn_.DeQue<int32_t>();
        DataCopy(meta_, local, 40);
        metaIn_.FreeTensor(local);
        VectorToScalar();
        if (abiVersion_ != ABI_VERSION || (tokens_ != 1 && tokens_ != 16) ||
            meta_.GetValue(16) != 0) {
            return false;
        }
        for (uint32_t t = 0; t < tokens_; ++t) {
            const int32_t slot = meta_.GetValue(t);
            if (slot < 0 || static_cast<uint32_t>(slot) >= slots_ ||
                meta_.GetValue(17 + t) != 1) {
                return false;
            }
            for (uint32_t j = 0; j < t; ++j) {
                if (meta_.GetValue(j) == slot) {
                    return false;
                }
            }
        }
        return true;
    }

    // Cold H2D happened in prepare(). Only 1024B immutable LUT are loaded per
    // launched core, once, using the existing planIn queue, not a new TQue.
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

    // raw lowFloat_ remains unchanged throughout all 8 chunks. Approximate Div
    // proposes only: integer raw-bit abs/cap makes every RINT and Gather safe.
    // The frozen certificate proves RN32 division -> integer RNE, not direct
    // rational RNE. It does not rely on IEEE vmul/Div or approximate error bounds.
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

    __aicore__ inline void LoadPlan(uint32_t head)
    {
        LocalTensor<int32_t> local = planIn_.AllocTensor<int32_t>();
        const uint64_t offset = static_cast<uint64_t>(head) * HEAD_DIM;
        DataCopyExtParams params{1, 512, 0, 0, 0};
        DataCopyPadExtParams<int32_t> pad{true, 0, 0, 0};
        DataCopyPad(local, pkGm_[offset], params, pad);
        DataCopyPad(local[128], pvGm_[offset], params, pad);
        DataCopyPad(local[256], invPvGm_[offset], params, pad);
        LocalTensor<float> asFloat = local.ReinterpretCast<float>();
        DataCopyPadExtParams<float> floatPad{true, 0, 0, 0.0f};
        DataCopyPad(asFloat[384], srGm_[offset], params, floatPad);
        planIn_.EnQue<int32_t>(local);
        local = planIn_.DeQue<int32_t>();
        LocalTensor<uint32_t> logical = local.ReinterpretCast<uint32_t>();
        // Static ABI is INT32 logical indices. Gather alone consumes byte offsets.
        ShiftLeft(pkOffsets_, logical, static_cast<uint32_t>(2), HEAD_DIM);
        ShiftLeft(pvOffsets_, logical[128], static_cast<uint32_t>(2), HEAD_DIM);
        ShiftLeft(invOffsets_, logical[256], static_cast<uint32_t>(2), HEAD_DIM);
        DataCopy(sr_, local.ReinterpretCast<float>()[384], HEAD_DIM);
        planIn_.FreeTensor(local);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline void LoadToken(uint32_t token, uint32_t head,
                                   float& beta, float& decay)
    {
        const uint32_t qHead = head / (VALUE_HEADS / KEY_HEADS);
        const uint64_t qOffset = (static_cast<uint64_t>(token) * KEY_HEADS + qHead) * HEAD_DIM;
        const uint64_t vOffset = (static_cast<uint64_t>(token) * VALUE_HEADS + head) * HEAD_DIM;
        LocalTensor<bfloat16_t> local = tokenIn_.AllocTensor<bfloat16_t>();
        DataCopyExtParams vectorParams{1, 256, 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> pad{true, 0, 0, static_cast<bfloat16_t>(0)};
        DataCopyPad(local, queryGm_[qOffset], vectorParams, pad);
        DataCopyPad(local[128], keyGm_[qOffset], vectorParams, pad);
        DataCopyPad(local[256], valueGm_[vOffset], vectorParams, pad);
        LocalTensor<float> asFloat = local.ReinterpretCast<float>();
        DataCopyExtParams gParams{1, VALUE_HEADS * sizeof(float), 0, 0, 0};
        DataCopyPadExtParams<float> gPad{true, 0, 4, 0.0f};
        DataCopyPad(asFloat[192], gGm_[static_cast<uint64_t>(token) * VALUE_HEADS], gParams, gPad);
        DataCopyExtParams betaParams{1, VALUE_HEADS * sizeof(bfloat16_t), 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> betaPad{
            true, 0, 4, static_cast<bfloat16_t>(0)};
        DataCopyPad(local[416], betaGm_[static_cast<uint64_t>(token) * VALUE_HEADS], betaParams, betaPad);
        tokenIn_.EnQue<bfloat16_t>(local);
        local = tokenIn_.DeQue<bfloat16_t>();
        Cast(qOrig_, local, RoundMode::CAST_NONE, HEAD_DIM);
        Cast(kOrig_, local[128], RoundMode::CAST_NONE, HEAD_DIM);
        Cast(vOrig_, local[256], RoundMode::CAST_NONE, HEAD_DIM);
        Cast(scalar_, local[416], RoundMode::CAST_NONE, 16);
        DataCopy(scalar_[16], local.ReinterpretCast<float>()[192], 16);
        tokenIn_.FreeTensor(local);
        PipeBarrier<PIPE_V>();
        Div(vOrig_, vOrig_, sr_, HEAD_DIM);
        Gather(q_, qOrig_, pkOffsets_, 0, HEAD_DIM);
        Gather(k_, kOrig_, pkOffsets_, 0, HEAD_DIM);
        Gather(v_, vOrig_, pvOffsets_, 0, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        Muls(q_, q_, scale_, HEAD_DIM);
        VectorToScalar();
        beta = scalar_.GetValue(head);
        const float g = scalar_.GetValue(16 + head);
        Duplicate(scalar_, g, 8);
        PipeBarrier<PIPE_V>();
        Exp(scalar_, scalar_, 8);
        VectorToScalar();
        decay = scalar_.GetValue(0);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline void LoadState(uint64_t headSlot, uint32_t group)
    {
        const uint64_t vRow = headSlot * HEAD_DIM + group * GROUP_VALUES;
        const uint64_t scaleOffset = (headSlot * VALUE_GROUPS + group) * LOW_KEYS;
        LocalTensor<half> local = stateIn_.AllocTensor<half>();
        DataCopyExtParams hiParams{1, 1024, 0, 0, 0};
        DataCopyPadExtParams<half> hiPad{true, 0, 0, static_cast<half>(0)};
        DataCopyPad(local, highGm_[vRow * HIGH_KEYS], hiParams, hiPad);
        LocalTensor<int8_t> asInt8 = local.ReinterpretCast<int8_t>();
        DataCopyExtParams loParams{1, 3584, 0, 0, 0};
        DataCopyPadExtParams<int8_t> loPad{true, 0, 0, 0};
        DataCopyPad(asInt8[1024], lowGm_[vRow * LOW_KEYS], loParams, loPad);
        LocalTensor<float> asFloat = local.ReinterpretCast<float>();
        DataCopyExtParams scaleParams{1, 448, 0, 0, 0};
        DataCopyPadExtParams<float> scalePad{true, 0, 0, 0.0f};
        DataCopyPad(asFloat[1152], scalesGm_[scaleOffset], scaleParams, scalePad);
        stateIn_.EnQue<half>(local);
        local = stateIn_.DeQue<half>();
        Cast(highFloat_, local, RoundMode::CAST_NONE, GROUP_VALUES * HIGH_KEYS);
        Cast(scratchB_.ReinterpretCast<half>(), local.ReinterpretCast<int8_t>()[1024],
             RoundMode::CAST_NONE, GROUP_VALUES * LOW_KEYS);
        PipeBarrier<PIPE_V>();
        Cast(lowFloat_, scratchB_.ReinterpretCast<half>(), RoundMode::CAST_NONE,
             GROUP_VALUES * LOW_KEYS);
        DataCopy(scaleVector_, local.ReinterpretCast<float>()[1152], LOW_KEYS);
        stateIn_.FreeTensor(local);
        PipeBarrier<PIPE_V>();
        LowBroadcast(lowFloat_, lowFloat_, scaleVector_, false);
        PipeBarrier<PIPE_V>();
        // UB-to-UB block lengths/strides are 32-byte units, unlike Pad GM bytes.
        DataCopyParams hiLayout{GROUP_VALUES, 2, 0, 14};
        DataCopyParams loLayout{GROUP_VALUES, 14, 0, 2};
        DataCopy(state_, highFloat_, hiLayout);
        DataCopy(state_[HIGH_KEYS], lowFloat_, loLayout);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline void LowBroadcast(LocalTensor<float> dst,
        LocalTensor<float> src, LocalTensor<float> scales, bool divide)
    {
        // 112 FP32 columns = 14 blocks. The 48-element tail avoids scale padding.
        if (divide) {
            Div(dst, src, scales, 64, GROUP_VALUES, {1, 1, 1, 14, 14, 0});
            Div(dst[64], src[64], scales[64], 48, GROUP_VALUES, {1, 1, 1, 14, 14, 0});
        } else {
            Mul(dst, src, scales, 64, GROUP_VALUES, {1, 1, 1, 14, 14, 0});
            Mul(dst[64], src[64], scales[64], 48, GROUP_VALUES, {1, 1, 1, 14, 14, 0});
        }
    }

    // Arithmetic and row reduction intentionally follow the ordinary 910B
    // recurrent kernel / existing DeltaLog K128 route, not an arch35 kernel.
    __aicore__ inline void MatVec(LocalTensor<float> matrix,
        LocalTensor<float> vector, LocalTensor<float> dst, bool add)
    {
        for (uint32_t col = 0; col < HEAD_DIM; col += REPEAT_LENGTH) {
            if (add) {
                MulAddDst(dst[col], matrix[col], vector[col], REPEAT_LENGTH,
                          GROUP_VALUES, {1, 1, 1, 16, 16, 0});
            } else {
                Mul(dst[col], matrix[col], vector[col], REPEAT_LENGTH,
                    GROUP_VALUES, {1, 1, 1, 16, 16, 0});
            }
        }
    }

    __aicore__ inline void ReduceRows(LocalTensor<float> dst, LocalTensor<float> src)
    {
        for (uint32_t row = 0; row < GROUP_VALUES; ++row) {
            const uint32_t offset = row * HEAD_DIM;
            Add(src[offset + 64], src[offset], src[offset + 64], 64);
            PipeBarrier<PIPE_V>();
            WholeReduceSum(dst[row], src[offset + 64], 64, 1, 1, 1, FP32_PER_BLOCK);
        }
    }

    __aicore__ inline void UpdateReadout(uint32_t group, float beta, float decay)
    {
        Muls(state_, state_, decay, GROUP_VALUES * HEAD_DIM);
        PipeBarrier<PIPE_V>();
        MatVec(state_, k_, broad_, false);
        PipeBarrier<PIPE_V>();
        ReduceRows(delta_, broad_);
        PipeBarrier<PIPE_V>();
        Sub(delta_, v_[group * GROUP_VALUES], delta_, GROUP_VALUES);
        PipeBarrier<PIPE_V>();
        Muls(delta_, delta_, beta, GROUP_VALUES);
        PipeBarrier<PIPE_V>();
        uint32_t dstShape[2] = {GROUP_VALUES, HEAD_DIM};
        uint32_t srcShape[2] = {GROUP_VALUES, 1};
        // Existing 8192B scratch is dead after LoadState and before PackStore.
        // Public fifth-argument API avoids the implicit PopStackBuffer/LCM path.
        auto broadcastTmp = scratchB_.ReinterpretCast<uint8_t>();
        Broadcast<float, 2, 1>(broad_, delta_, dstShape, srcShape, broadcastTmp);
        PipeBarrier<PIPE_V>();
        MatVec(broad_, k_, state_, true);
        PipeBarrier<PIPE_V>();
        MatVec(state_, q_, broad_, false);
        PipeBarrier<PIPE_V>();
        ReduceRows(attn_[group * GROUP_VALUES], broad_);
        PipeBarrier<PIPE_V>(); // Output comes from updated FP32 BEFORE PackStore.
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

    __aicore__ inline void StoreHead(uint32_t task)
    {
        LocalTensor<bfloat16_t> local = output_.AllocTensor<bfloat16_t>();
        Cast(local, outOrig_, RoundMode::CAST_RINT, HEAD_DIM);
        output_.EnQue<bfloat16_t>(local);
        local = output_.DeQue<bfloat16_t>();
        DataCopyParams params{1, 256, 0, 0};
        DataCopyPad(outGm_[static_cast<uint64_t>(task) * HEAD_DIM], local, params);
        output_.FreeTensor(local);
    }

    __aicore__ inline void StoreInvalid(uint32_t task)
    {
        union { uint32_t bits; float value; } nan;
        nan.bits = 0x7fc00000;
        Duplicate(outOrig_, nan.value, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        StoreHead(task);
    }

    __aicore__ inline void ProcessTask(uint32_t token, uint32_t head)
    {
        LoadPlan(head);
        float beta = 0.0f;
        float decay = 0.0f;
        LoadToken(token, head, beta, decay);
        const uint64_t headSlot =
            static_cast<uint64_t>(meta_.GetValue(token)) * VALUE_HEADS + head;
        for (uint32_t group = 0; group < VALUE_GROUPS; ++group) {
            LoadState(headSlot, group);
            UpdateReadout(group, beta, decay);
            if (!PackStore(headSlot, group)) {
                StoreInvalid(token * VALUE_HEADS + head);
                return;
            }
        }
        Gather(outOrig_, attn_, invOffsets_, 0, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        Mul(outOrig_, outOrig_, sr_, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        StoreHead(token * VALUE_HEADS + head);
    }

private:
    GlobalTensor<bfloat16_t> queryGm_, keyGm_, valueGm_, betaGm_, outGm_;
    GlobalTensor<float> gGm_, scalesGm_, srGm_;
    GlobalTensor<half> highGm_;
    GlobalTensor<int8_t> lowGm_;
    GlobalTensor<int32_t> pkGm_, pvGm_, invPvGm_, lengthsGm_, indicesGm_;
    TPipe* pipe_;
    TQue<QuePosition::VECIN, 1> metaIn_, tokenIn_, planIn_, stateIn_;
    TQue<QuePosition::VECOUT, 2> packedOut_, output_;
    TBuf<TPosition::VECCALC> work_, quantizerWork_;
    GlobalTensor<int32_t> quantizerLutGm_;
    LocalTensor<int32_t> certWork_[16], accepted_, magnitude_, correctedCodes_;
    LocalTensor<int32_t> originIndices_, compactIndices_, cTable_, fTable_;
    LocalTensor<float> quotient_, repeatedScale_;
    LocalTensor<uint8_t> rejectMask_;
    LocalTensor<int32_t> meta_;
    LocalTensor<float> qOrig_, kOrig_, vOrig_, q_, k_, v_, sr_;
    LocalTensor<uint32_t> pkOffsets_, pvOffsets_, invOffsets_;
    LocalTensor<float> delta_, attn_, outOrig_, scalar_, highFloat_, scaleVector_, ones_;
    LocalTensor<uint8_t> mask_;
    LocalTensor<float> state_, broad_, lowFloat_, absA_, scratchB_;
    uint32_t tokens_, slots_;
    float scale_;
    uint32_t abiVersion_;
};
} // namespace Qwen36DampIntegerCompactionV1
#endif
