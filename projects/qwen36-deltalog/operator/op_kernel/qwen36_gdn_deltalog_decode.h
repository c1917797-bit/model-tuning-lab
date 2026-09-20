#ifndef QWEN36_GDN_DELTALOG_DECODE_KERNEL_H
#define QWEN36_GDN_DELTALOG_DECODE_KERNEL_H

#include "kernel_operator.h"
#include "qwen36_gdn_deltalog_decode_tiling.h"

namespace Qwen36DeltaLog {

using namespace AscendC;

constexpr uint32_t KEY_HEADS = 4;
constexpr uint32_t VALUE_HEADS = 12;
constexpr uint32_t HEAD_DIM = 128;
constexpr uint32_t LOG_CAPACITY = 7;
constexpr uint32_t META_STRIDE = 8;
constexpr uint32_t V_STEP = 64;
constexpr uint32_t BF16_PER_BLOCK = 16;
constexpr uint32_t FP32_PER_BLOCK = 8;
constexpr uint32_t REPEAT_LENGTH = 64;
constexpr uint32_t MAX_REPEAT = 255;

struct DeltaLogInitParams {
    GM_ADDR query;
    GM_ADDR key;
    GM_ADDR value;
    GM_ADDR g;
    GM_ADDR beta;
    GM_ADDR baseState;
    GM_ADDR kLog;
    GM_ADDR uLog;
    GM_ADDR lambdaLog;
    GM_ADDR cumulativeDecay;
    GM_ADDR logLength;
    GM_ADDR actualSeqLengths;
    GM_ADDR stateIndices;
    GM_ADDR out;
};

class DeltaLogKernel {
public:
    __aicore__ inline explicit DeltaLogKernel(const __gm__ DeltalogTilingData *tiling)
        : tokens_(tiling->tokens), slots_(tiling->stateSlots),
          vStep_(tiling->vStep), scale_(tiling->scale)
    {
    }

    __aicore__ inline void Init(const DeltaLogInitParams &p, TPipe *pipe)
    {
        pipe_ = pipe;
        blockIdx_ = GetBlockIdx();
        blockNum_ = GetBlockNum();
        queryGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t *>(p.query));
        keyGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t *>(p.key));
        valueGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t *>(p.value));
        gGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float *>(p.g));
        betaGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t *>(p.beta));
        baseStateGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float *>(p.baseState));
        kLogGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t *>(p.kLog));
        uLogGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float *>(p.uLog));
        lambdaLogGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float *>(p.lambdaLog));
        cumulativeDecayGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float *>(p.cumulativeDecay));
        logLengthGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t *>(p.logLength));
        actualSeqLengthsGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t *>(p.actualSeqLengths));
        stateIndicesGm_.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t *>(p.stateIndices));
        outGm_.SetGlobalBuffer(reinterpret_cast<__gm__ bfloat16_t *>(p.out));

        pipe_->InitBuffer(qInQueue_, 1, HEAD_DIM * sizeof(bfloat16_t));
        pipe_->InitBuffer(kInQueue_, 1, HEAD_DIM * sizeof(bfloat16_t));
        pipe_->InitBuffer(vInQueue_, 1, V_STEP * sizeof(bfloat16_t));
        pipe_->InitBuffer(betaInQueue_, 1, 16 * sizeof(bfloat16_t));
        pipe_->InitBuffer(stateInQueue_, 1, V_STEP * HEAD_DIM * sizeof(float));
        pipe_->InitBuffer(stateOutQueue_, 1, V_STEP * HEAD_DIM * sizeof(float));
        pipe_->InitBuffer(uOutQueue_, 1, V_STEP * sizeof(float));
        pipe_->InitBuffer(outQueue_, 1, V_STEP * sizeof(bfloat16_t));
        pipe_->InitBuffer(tmpBuff_, 80 * 1024);

        uint32_t offset = 0;
        qUb_ = tmpBuff_.GetWithOffset<float>(HEAD_DIM, offset);
        offset += HEAD_DIM * sizeof(float);
        kUb_ = tmpBuff_.GetWithOffset<float>(HEAD_DIM, offset);
        offset += HEAD_DIM * sizeof(float);
        kLogUb_ = tmpBuff_.GetWithOffset<float>(HEAD_DIM, offset);
        offset += HEAD_DIM * sizeof(float);
        vUb_ = tmpBuff_.GetWithOffset<float>(V_STEP, offset);
        offset += V_STEP * sizeof(float);
        deltaUb_ = tmpBuff_.GetWithOffset<float>(V_STEP, offset);
        offset += V_STEP * sizeof(float);
        attnUb_ = tmpBuff_.GetWithOffset<float>(V_STEP, offset);
        offset += V_STEP * sizeof(float);
        scalarUb_ = tmpBuff_.GetWithOffset<float>(16, offset);
        offset += 16 * sizeof(float);
        betaUb_ = tmpBuff_.GetWithOffset<float>(16, offset);
        offset += 16 * sizeof(float);
        stateUb_ = tmpBuff_.GetWithOffset<float>(V_STEP * HEAD_DIM, offset);
        offset += V_STEP * HEAD_DIM * sizeof(float);
        broadUb_ = tmpBuff_.GetWithOffset<float>(V_STEP * HEAD_DIM, offset);
    }

    __aicore__ inline void Process()
    {
        const uint32_t tasks = tokens_ * VALUE_HEADS;
        for (uint32_t task = blockIdx_; task < tasks; task += blockNum_) {
            ProcessTask(task / VALUE_HEADS, task % VALUE_HEADS);
        }
    }

private:
    __aicore__ inline float ExpScalar(float value)
    {
        Duplicate(scalarUb_, value, 8);
        Exp(scalarUb_, scalarUb_, 8);
        event_t eventVToS = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::V_S));
        SetFlag<HardEvent::V_S>(eventVToS);
        WaitFlag<HardEvent::V_S>(eventVToS);
        return scalarUb_.GetValue(0);
    }

    __aicore__ inline void LoadBf16Vector(
        GlobalTensor<bfloat16_t> &source, uint64_t offset, LocalTensor<float> destination,
        TQue<QuePosition::VECIN, 1> &queue, uint32_t elements)
    {
        LocalTensor<bfloat16_t> local = queue.AllocTensor<bfloat16_t>();
        DataCopyExtParams params{1, static_cast<uint32_t>(elements * sizeof(bfloat16_t)), 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> pad{true, 0, 0, static_cast<bfloat16_t>(0)};
        DataCopyPad(local, source[offset], params, pad);
        queue.EnQue<bfloat16_t>(local);
        local = queue.DeQue<bfloat16_t>();
        Cast(destination, local, RoundMode::CAST_NONE, elements);
        queue.FreeTensor(local);
    }

    __aicore__ inline void LoadQK(uint32_t token, uint32_t head)
    {
        const uint32_t qHead = head / (VALUE_HEADS / KEY_HEADS);
        const uint64_t offset = (static_cast<uint64_t>(token) * KEY_HEADS + qHead) * HEAD_DIM;
        LoadBf16Vector(queryGm_, offset, qUb_, qInQueue_, HEAD_DIM);
        LoadBf16Vector(keyGm_, offset, kUb_, kInQueue_, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        Muls(qUb_, qUb_, scale_, HEAD_DIM);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline float LoadBeta(uint32_t token, uint32_t head)
    {
        LocalTensor<bfloat16_t> local = betaInQueue_.AllocTensor<bfloat16_t>();
        DataCopyExtParams params{1, VALUE_HEADS * sizeof(bfloat16_t), 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> pad{
            true, 0, static_cast<uint8_t>(16 - VALUE_HEADS), static_cast<bfloat16_t>(0)};
        DataCopyPad(local, betaGm_[static_cast<uint64_t>(token) * VALUE_HEADS], params, pad);
        betaInQueue_.EnQue<bfloat16_t>(local);
        local = betaInQueue_.DeQue<bfloat16_t>();
        Cast(betaUb_, local, RoundMode::CAST_NONE, 16);
        betaInQueue_.FreeTensor(local);
        event_t eventVToS = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::V_S));
        SetFlag<HardEvent::V_S>(eventVToS);
        WaitFlag<HardEvent::V_S>(eventVToS);
        return betaUb_.GetValue(head);
    }

    __aicore__ inline void LoadBase(uint64_t offset, uint32_t rows)
    {
        LocalTensor<float> local = stateInQueue_.AllocTensor<float>();
        DataCopyExtParams params{static_cast<uint16_t>(rows), HEAD_DIM * sizeof(float), 0, 0, 0};
        DataCopyPadExtParams<float> pad{true, 0, 0, 0.0f};
        DataCopyPad(local, baseStateGm_[offset], params, pad);
        stateInQueue_.EnQue<float>(local);
        local = stateInQueue_.DeQue<float>();
        DataCopy(stateUb_, local, rows * HEAD_DIM);
        stateInQueue_.FreeTensor(local);
    }

    __aicore__ inline void LoadULog(uint64_t offset, uint32_t rows)
    {
        LocalTensor<float> local = stateInQueue_.AllocTensor<float>();
        DataCopyExtParams params{1, static_cast<uint32_t>(rows * sizeof(float)), 0, 0, 0};
        DataCopyPadExtParams<float> pad{true, 0, 0, 0.0f};
        DataCopyPad(local, uLogGm_[offset], params, pad);
        stateInQueue_.EnQue<float>(local);
        local = stateInQueue_.DeQue<float>();
        DataCopy(deltaUb_, local, rows);
        stateInQueue_.FreeTensor(local);
    }

    __aicore__ inline void MatVecMul(
        const LocalTensor<float> &matrix, const LocalTensor<float> &vector,
        LocalTensor<float> destination, uint32_t rows, bool add)
    {
        constexpr uint8_t repeatStride = HEAD_DIM / FP32_PER_BLOCK;
        for (uint32_t col = 0; col < HEAD_DIM; col += REPEAT_LENGTH) {
            const uint64_t mask = REPEAT_LENGTH;
            const uint64_t repeats = rows;
            if (add) {
                MulAddDst(destination[col], matrix[col], vector[col], mask, repeats,
                          {1, 1, 1, repeatStride, repeatStride, 0});
            } else {
                Mul(destination[col], matrix[col], vector[col], mask, repeats,
                    {1, 1, 1, repeatStride, repeatStride, 0});
            }
        }
    }

    __aicore__ inline void ReduceRows(LocalTensor<float> destination, LocalTensor<float> source, uint32_t rows)
    {
        for (uint32_t row = 0; row < rows; ++row) {
            const uint32_t rowOffset = row * HEAD_DIM;
            Add(source[rowOffset + REPEAT_LENGTH], source[rowOffset],
                source[rowOffset + REPEAT_LENGTH], REPEAT_LENGTH);
            PipeBarrier<PIPE_V>();
            WholeReduceSum(destination[row], source[rowOffset + REPEAT_LENGTH],
                           REPEAT_LENGTH, 1, 1, 1, FP32_PER_BLOCK);
        }
    }

    __aicore__ inline void AddLoggedUpdate(
        uint32_t slot, uint32_t head, uint32_t entry, uint32_t vStart,
        uint32_t rows, float coefficient)
    {
        const uint64_t kOffset =
            ((static_cast<uint64_t>(slot) * VALUE_HEADS + head) * LOG_CAPACITY + entry) * HEAD_DIM;
        LoadBf16Vector(kLogGm_, kOffset, kLogUb_, kInQueue_, HEAD_DIM);
        const uint64_t uOffset = kOffset + vStart;
        LoadULog(uOffset, rows);
        PipeBarrier<PIPE_V>();
        Muls(deltaUb_, deltaUb_, coefficient, rows);
        uint32_t matrixShape[2] = {rows, HEAD_DIM};
        uint32_t vectorShape[2] = {rows, 1};
        Broadcast<float, 2, 1>(broadUb_, deltaUb_, matrixShape, vectorShape);
        PipeBarrier<PIPE_V>();
        MatVecMul(broadUb_, kLogUb_, stateUb_, rows, true);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline void StoreOutput(uint64_t offset, uint32_t rows)
    {
        LocalTensor<bfloat16_t> local = outQueue_.AllocTensor<bfloat16_t>();
        Cast(local, attnUb_, RoundMode::CAST_RINT, rows);
        outQueue_.EnQue<bfloat16_t>(local);
        local = outQueue_.DeQue<bfloat16_t>();
        DataCopyParams params{1, static_cast<uint16_t>(rows * sizeof(bfloat16_t)), 0, 0};
        DataCopyPad(outGm_[offset], local, params);
        outQueue_.FreeTensor(local);
    }

    __aicore__ inline void StoreBase(uint64_t offset, uint32_t rows)
    {
        LocalTensor<float> local = stateOutQueue_.AllocTensor<float>();
        DataCopy(local, stateUb_, rows * HEAD_DIM);
        stateOutQueue_.EnQue<float>(local);
        local = stateOutQueue_.DeQue<float>();
        DataCopyParams params{static_cast<uint16_t>(rows), HEAD_DIM * sizeof(float), 0, 0};
        DataCopyPad(baseStateGm_[offset], local, params);
        stateOutQueue_.FreeTensor(local);
    }

    __aicore__ inline void StoreULog(uint64_t offset, uint32_t rows)
    {
        LocalTensor<float> local = uOutQueue_.AllocTensor<float>();
        DataCopy(local, deltaUb_, rows);
        uOutQueue_.EnQue<float>(local);
        local = uOutQueue_.DeQue<float>();
        DataCopyParams params{1, static_cast<uint16_t>(rows * sizeof(float)), 0, 0};
        DataCopyPad(uLogGm_[offset], local, params);
        uOutQueue_.FreeTensor(local);
    }

    __aicore__ inline void StoreKLog(uint32_t token, uint32_t slot, uint32_t head, uint32_t entry)
    {
        const uint32_t qHead = head / (VALUE_HEADS / KEY_HEADS);
        const uint64_t sourceOffset =
            (static_cast<uint64_t>(token) * KEY_HEADS + qHead) * HEAD_DIM;
        const uint64_t targetOffset =
            ((static_cast<uint64_t>(slot) * VALUE_HEADS + head) * LOG_CAPACITY + entry) * HEAD_DIM;
        LocalTensor<bfloat16_t> local = kInQueue_.AllocTensor<bfloat16_t>();
        DataCopyExtParams inParams{1, HEAD_DIM * sizeof(bfloat16_t), 0, 0, 0};
        DataCopyPadExtParams<bfloat16_t> pad{true, 0, 0, static_cast<bfloat16_t>(0)};
        DataCopyPad(local, keyGm_[sourceOffset], inParams, pad);
        kInQueue_.EnQue<bfloat16_t>(local);
        local = kInQueue_.DeQue<bfloat16_t>();
        DataCopyParams outParams{1, HEAD_DIM * sizeof(bfloat16_t), 0, 0};
        DataCopyPad(kLogGm_[targetOffset], local, outParams);
        kInQueue_.FreeTensor(local);
    }

    __aicore__ inline void ProcessTask(uint32_t token, uint32_t head)
    {
        const int32_t slotValue = stateIndicesGm_.GetValue(token);
        if (slotValue < 0 || static_cast<uint32_t>(slotValue) >= slots_) {
            return;
        }
        const uint32_t slot = static_cast<uint32_t>(slotValue);
        const uint64_t headOffset = static_cast<uint64_t>(slot) * VALUE_HEADS + head;
        const uint64_t metaOffset = headOffset * META_STRIDE;
        const int32_t lengthValue = logLengthGm_.GetValue(metaOffset);
        if (lengthValue < 0 || lengthValue > static_cast<int32_t>(LOG_CAPACITY)) {
            return;
        }
        const uint32_t length = static_cast<uint32_t>(lengthValue);
        const bool merge = length == LOG_CAPACITY;
        const float cumulative = cumulativeDecayGm_.GetValue(metaOffset);
        const float gate = gGm_.GetValue(static_cast<uint64_t>(token) * VALUE_HEADS + head);
        const float beta = LoadBeta(token, head);
        const float previousScale = ExpScalar(cumulative);
        const float currentScale = ExpScalar(gate);
        const float nextCumulative = cumulative + gate;
        LoadQK(token, head);

        for (uint32_t vStart = 0; vStart < HEAD_DIM; vStart += vStep_) {
            const uint32_t rows = (vStart + vStep_ > HEAD_DIM) ? HEAD_DIM - vStart : vStep_;
            const uint64_t baseOffset =
                ((headOffset * HEAD_DIM + vStart) * HEAD_DIM);
            LoadBase(baseOffset, rows);
            PipeBarrier<PIPE_V>();
            Muls(stateUb_, stateUb_, previousScale, rows * HEAD_DIM);
            PipeBarrier<PIPE_V>();
            for (uint32_t entry = 0; entry < length; ++entry) {
                const uint64_t lambdaOffset = metaOffset + entry;
                const float coefficient = ExpScalar(
                    cumulative - lambdaLogGm_.GetValue(lambdaOffset));
                AddLoggedUpdate(slot, head, entry, vStart, rows, coefficient);
            }

            Muls(stateUb_, stateUb_, currentScale, rows * HEAD_DIM);
            PipeBarrier<PIPE_V>();
            MatVecMul(stateUb_, kUb_, broadUb_, rows, false);
            PipeBarrier<PIPE_V>();
            ReduceRows(deltaUb_, broadUb_, rows);
            PipeBarrier<PIPE_V>();
            const uint64_t valueOffset =
                (static_cast<uint64_t>(token) * VALUE_HEADS + head) * HEAD_DIM + vStart;
            LoadBf16Vector(valueGm_, valueOffset, vUb_, vInQueue_, rows);
            PipeBarrier<PIPE_V>();
            Sub(deltaUb_, vUb_, deltaUb_, rows);
            PipeBarrier<PIPE_V>();
            Muls(deltaUb_, deltaUb_, beta, rows);
            PipeBarrier<PIPE_V>();
            uint32_t matrixShape[2] = {rows, HEAD_DIM};
            uint32_t vectorShape[2] = {rows, 1};
            Broadcast<float, 2, 1>(broadUb_, deltaUb_, matrixShape, vectorShape);
            PipeBarrier<PIPE_V>();
            MatVecMul(broadUb_, kUb_, stateUb_, rows, true);
            PipeBarrier<PIPE_V>();
            MatVecMul(stateUb_, qUb_, broadUb_, rows, false);
            PipeBarrier<PIPE_V>();
            ReduceRows(attnUb_, broadUb_, rows);
            const uint64_t outOffset =
                (static_cast<uint64_t>(token) * VALUE_HEADS + head) * HEAD_DIM + vStart;
            StoreOutput(outOffset, rows);

            if (merge) {
                StoreBase(baseOffset, rows);
            } else {
                const uint64_t uOffset =
                    ((headOffset * LOG_CAPACITY + length) * HEAD_DIM) + vStart;
                StoreULog(uOffset, rows);
            }
        }

        if (merge) {
            cumulativeDecayGm_.SetValue(metaOffset, 0.0f);
            logLengthGm_.SetValue(metaOffset, 0);
        } else {
            StoreKLog(token, slot, head, length);
            lambdaLogGm_.SetValue(metaOffset + length, nextCumulative);
            cumulativeDecayGm_.SetValue(metaOffset, nextCumulative);
            logLengthGm_.SetValue(metaOffset, static_cast<int32_t>(length + 1));
        }
    }

private:
    GlobalTensor<bfloat16_t> queryGm_;
    GlobalTensor<bfloat16_t> keyGm_;
    GlobalTensor<bfloat16_t> valueGm_;
    GlobalTensor<float> gGm_;
    GlobalTensor<bfloat16_t> betaGm_;
    GlobalTensor<float> baseStateGm_;
    GlobalTensor<bfloat16_t> kLogGm_;
    GlobalTensor<float> uLogGm_;
    GlobalTensor<float> lambdaLogGm_;
    GlobalTensor<float> cumulativeDecayGm_;
    GlobalTensor<int32_t> logLengthGm_;
    GlobalTensor<int32_t> actualSeqLengthsGm_;
    GlobalTensor<int32_t> stateIndicesGm_;
    GlobalTensor<bfloat16_t> outGm_;

    TPipe *pipe_;
    TQue<QuePosition::VECIN, 1> qInQueue_;
    TQue<QuePosition::VECIN, 1> kInQueue_;
    TQue<QuePosition::VECIN, 1> vInQueue_;
    TQue<QuePosition::VECIN, 1> betaInQueue_;
    TQue<QuePosition::VECIN, 1> stateInQueue_;
    TQue<QuePosition::VECOUT, 1> stateOutQueue_;
    TQue<QuePosition::VECOUT, 1> uOutQueue_;
    TQue<QuePosition::VECOUT, 1> outQueue_;
    TBuf<TPosition::VECCALC> tmpBuff_;
    LocalTensor<float> qUb_;
    LocalTensor<float> kUb_;
    LocalTensor<float> kLogUb_;
    LocalTensor<float> vUb_;
    LocalTensor<float> deltaUb_;
    LocalTensor<float> attnUb_;
    LocalTensor<float> scalarUb_;
    LocalTensor<float> betaUb_;
    LocalTensor<float> stateUb_;
    LocalTensor<float> broadUb_;
    uint32_t tokens_;
    uint32_t slots_;
    uint32_t vStep_;
    float scale_;
    uint32_t blockIdx_;
    uint32_t blockNum_;
};

} // namespace Qwen36DeltaLog

#endif
