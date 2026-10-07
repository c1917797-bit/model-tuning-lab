#ifndef QWEN36_GDN_KVBUFFER_SHORT_HORIZON_V3_DECODE_KERNEL_H
#define QWEN36_GDN_KVBUFFER_SHORT_HORIZON_V3_DECODE_KERNEL_H

#include "kernel_operator.h"
#include "qwen36_gdn_kvbuffer_short_horizon_v3_tiling.h"

namespace Qwen36KVBufferShortHorizonV3 {

using namespace AscendC;

constexpr uint32_t KEY_HEADS = 4;
constexpr uint32_t VALUE_HEADS = 12;
constexpr uint32_t HEAD_DIM = 128;
constexpr uint32_t LOG_CAPACITY = 16;
// Keep sixteen-lane storage and the four-level tree fold unchanged.
// This independently named adaptation bounds deferred history at eight steps.
constexpr uint32_t FLUSH_INTERVAL = 8;
static_assert(FLUSH_INTERVAL > 1 && FLUSH_INTERVAL <= LOG_CAPACITY,
              "deferred materialization horizon must fit the retained ABI");
// v2 used 8 FP32 values (32 bytes) per head and still showed exact pairwise
// metadata clobbering.  One 128-byte metadata row per AIV writer avoids cross-head overlap.
constexpr uint32_t META_STRIDE = 32;
constexpr uint32_t V_STEP = 32;
constexpr uint32_t BF16_PER_BLOCK = 16;
constexpr uint32_t FP32_PER_BLOCK = 8;
constexpr uint32_t REPEAT_LENGTH = 64;
constexpr uint32_t MAX_REPEAT = 255;

struct KVBufferInitParams {
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

class KVBufferKernel {
public:
    __aicore__ inline explicit KVBufferKernel(const __gm__ KVBufferTilingData *tiling)
        : tokens_(tiling->tokens), slots_(tiling->stateSlots),
          vStep_(tiling->vStep), scale_(tiling->scale)
    {
    }

    __aicore__ inline void Init(const KVBufferInitParams &p, TPipe *pipe)
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
        pipe_->InitBuffer(kInQueue_, 1, LOG_CAPACITY * HEAD_DIM * sizeof(bfloat16_t));
        pipe_->InitBuffer(vInQueue_, 1, V_STEP * sizeof(bfloat16_t));
        pipe_->InitBuffer(betaInQueue_, 1, 16 * sizeof(bfloat16_t));
        pipe_->InitBuffer(stateInQueue_, 1, V_STEP * HEAD_DIM * sizeof(float));
        pipe_->InitBuffer(stateOutQueue_, 1, V_STEP * HEAD_DIM * sizeof(float));
        pipe_->InitBuffer(uOutQueue_, 1, V_STEP * sizeof(float));
        pipe_->InitBuffer(outQueue_, 1, V_STEP * sizeof(bfloat16_t));
        pipe_->InitBuffer(kOutQueue_, 1, HEAD_DIM * sizeof(bfloat16_t));
        pipe_->InitBuffer(tmpBuff_, 128 * 1024);

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
        offset += V_STEP * HEAD_DIM * sizeof(float);
        uLogUb_ = tmpBuff_.GetWithOffset<float>(V_STEP, offset);
        offset += V_STEP * sizeof(float);
        kBatchUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * HEAD_DIM, offset);
        offset += LOG_CAPACITY * HEAD_DIM * sizeof(float);
        dotBatchUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * HEAD_DIM, offset);
        offset += LOG_CAPACITY * HEAD_DIM * sizeof(float);
        uBatchUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * V_STEP, offset);
        offset += LOG_CAPACITY * V_STEP * sizeof(float);
        weightedUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * V_STEP, offset);
        offset += LOG_CAPACITY * V_STEP * sizeof(float);
        outerLeftUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * 8 * 64, offset);
        offset += LOG_CAPACITY * 8 * 64 * sizeof(float);
        outerRightUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * 8 * 64, offset);
        offset += LOG_CAPACITY * 8 * 64 * sizeof(float);
        kTileUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * 64, offset);
        offset += LOG_CAPACITY * 64 * sizeof(float);
        uSmallUb_ = tmpBuff_.GetWithOffset<float>(LOG_CAPACITY * 8, offset);
        offset += LOG_CAPACITY * 8 * sizeof(float);
        coeffUb_ = tmpBuff_.GetWithOffset<float>(32, offset); offset += 128;
        lambdaUb_ = tmpBuff_.GetWithOffset<float>(32, offset); offset += 128;
        qDotsUb_ = tmpBuff_.GetWithOffset<float>(32, offset); offset += 128;
        kDotsUb_ = tmpBuff_.GetWithOffset<float>(32, offset); offset += 128;
        qWeightsUb_ = tmpBuff_.GetWithOffset<float>(32, offset); offset += 128;
        kWeightsUb_ = tmpBuff_.GetWithOffset<float>(32, offset);
        offset += 128;
        // Public five-argument Broadcast ABI: no implicit LCM stack allocation.
        // Aligned FP32 last-dim expansion needs at most128 rows *32 B.
        broadcastTmpUb_ = tmpBuff_.GetWithOffset<uint8_t>(4096, offset);
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
        // RAW: Exp must observe the scalar vector initialized by Duplicate.
        PipeBarrier<PIPE_V>();
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

    __aicore__ inline void LoadULog(uint64_t offset, uint32_t rows,
                                    LocalTensor<float> destination)
    {
        LocalTensor<float> local = stateInQueue_.AllocTensor<float>();
        DataCopyExtParams params{1, static_cast<uint32_t>(rows * sizeof(float)), 0, 0, 0};
        DataCopyPadExtParams<float> pad{true, 0, 0, 0.0f};
        DataCopyPad(local, uLogGm_[offset], params, pad);
        stateInQueue_.EnQue<float>(local);
        local = stateInQueue_.DeQue<float>();
        DataCopy(destination, local, rows);
        stateInQueue_.FreeTensor(local);
    }

    __aicore__ inline float DotQK(LocalTensor<float> left, LocalTensor<float> right)
    {
        Mul(broadUb_, left, right, HEAD_DIM);
        PipeBarrier<PIPE_V>();
        ReduceRows(scalarUb_, broadUb_, 1);
        event_t eventVToS = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::V_S));
        SetFlag<HardEvent::V_S>(eventVToS);
        WaitFlag<HardEvent::V_S>(eventVToS);
        return scalarUb_.GetValue(0);
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

    // Same 128-wide reduction layout as the pinned native recurrent kernel.
    __aicore__ inline void ReduceRows(LocalTensor<float> destination,
                                      LocalTensor<float> source, uint32_t rows)
    {
        Add(source[64], source, source[64], 64, rows, {1,1,1,16,16,16});
        PipeBarrier<PIPE_V>();
        WholeReduceSum(destination, source[64], 64, rows, 1, 1, 16);
    }

    // No data-dependent loop over log entries. Four vector folds over all16.
    __aicore__ inline void TreeFold(LocalTensor<float> source,
                                    LocalTensor<float> scratch, uint32_t width)
    {
        for (uint32_t half = LOG_CAPACITY / 2; half > 0; half /= 2) {
            Add(scratch, source, source[half * width], half * width);
            PipeBarrier<PIPE_V>();
            LocalTensor<float> swap = source; source = scratch; scratch = swap;
        }
        // Four levels: result is back in the original source.
    }

    __aicore__ inline void PrepareLogs(uint32_t slot, uint32_t head,
                                      uint32_t length, float cumulative)
    {
        const uint64_t ho = static_cast<uint64_t>(slot) * VALUE_HEADS + head;
        const uint32_t kh = head / (VALUE_HEADS / KEY_HEADS);
        LoadBf16Vector(kLogGm_,
            (static_cast<uint64_t>(slot) * KEY_HEADS + kh) * LOG_CAPACITY * HEAD_DIM,
            kBatchUb_, kInQueue_, LOG_CAPACITY * HEAD_DIM);
        LocalTensor<float> local = stateInQueue_.AllocTensor<float>();
        DataCopyPad(local, lambdaLogGm_[ho * META_STRIDE],
                    DataCopyExtParams{1, LOG_CAPACITY * sizeof(float), 0, 0, 0},
                    DataCopyPadExtParams<float>{true,0,0,0.0f});
        stateInQueue_.EnQue<float>(local); local = stateInQueue_.DeQue<float>();
        DataCopy(lambdaUb_, local, LOG_CAPACITY);
        stateInQueue_.FreeTensor(local);
        Duplicate(coeffUb_, 0.0f, 32);
        PipeBarrier<PIPE_V>();
        if (length > 0) {
            Duplicate(qWeightsUb_, cumulative, 32);
            PipeBarrier<PIPE_V>();
            // Exp touches only live lanes. Stale dead lambda can be +/-1e30.
            Sub(coeffUb_, qWeightsUb_, lambdaUb_, length);
            PipeBarrier<PIPE_V>();
            Exp(coeffUb_, coeffUb_, length);
            PipeBarrier<PIPE_V>();
        }
        MatVecMul(kBatchUb_, qUb_, dotBatchUb_, LOG_CAPACITY, false);
        PipeBarrier<PIPE_V>();
        ReduceRows(qDotsUb_, dotBatchUb_, LOG_CAPACITY);
        // WAR: reduction still reads dotBatch before the next MatVec writes it.
        PipeBarrier<PIPE_V>();
        MatVecMul(kBatchUb_, kUb_, dotBatchUb_, LOG_CAPACITY, false);
        PipeBarrier<PIPE_V>();
        ReduceRows(kDotsUb_, dotBatchUb_, LOG_CAPACITY);
        PipeBarrier<PIPE_V>();
        Mul(qWeightsUb_, qDotsUb_, coeffUb_, LOG_CAPACITY);
        Mul(kWeightsUb_, kDotsUb_, coeffUb_, LOG_CAPACITY);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline void LoadUTile(uint64_t headOffset, uint32_t vStart)
    {
        LocalTensor<float> local = stateInQueue_.AllocTensor<float>();
        DataCopyPad(local, uLogGm_[headOffset * LOG_CAPACITY * HEAD_DIM + vStart],
                    DataCopyExtParams{LOG_CAPACITY,V_STEP*sizeof(float),
                                      (HEAD_DIM-V_STEP)*sizeof(float),0,0},
                    DataCopyPadExtParams<float>{true,0,0,0.0f});
        stateInQueue_.EnQue<float>(local); local = stateInQueue_.DeQue<float>();
        DataCopy(uBatchUb_, local, LOG_CAPACITY * V_STEP);
        stateInQueue_.FreeTensor(local);
    }

    __aicore__ inline void LoggedMatVec(LocalTensor<float> weights,
                                       LocalTensor<float> destination)
    {
        uint32_t dstShape[2] = {LOG_CAPACITY, V_STEP};
        uint32_t srcShape[2] = {LOG_CAPACITY,1};
        Broadcast<float,2,1>(weightedUb_, weights, dstShape, srcShape, broadcastTmpUb_);
        PipeBarrier<PIPE_V>();
        Mul(weightedUb_, weightedUb_, uBatchUb_, LOG_CAPACITY * V_STEP);
        PipeBarrier<PIPE_V>();
        TreeFold(weightedUb_, broadUb_, V_STEP);
        Add(destination, destination, weightedUb_, V_STEP);
        PipeBarrier<PIPE_V>();
    }

    __aicore__ inline void ParallelFlush(float previousScale)
    {
        Muls(stateUb_, stateUb_, previousScale, V_STEP * HEAD_DIM);
        uint32_t us[2] = {LOG_CAPACITY,V_STEP}, cs[2] = {LOG_CAPACITY,1};
        Broadcast<float,2,1>(weightedUb_, coeffUb_, us, cs, broadcastTmpUb_);
        PipeBarrier<PIPE_V>();
        Mul(weightedUb_, weightedUb_, uBatchUb_, LOG_CAPACITY * V_STEP);
        PipeBarrier<PIPE_V>();
        // V/K tiling is allowed; every tile batches the whole log dimension.
        for (uint32_t vs = 0; vs < V_STEP; vs += 8) {
            DataCopy(uSmallUb_, weightedUb_[vs], DataCopyParams{16,1,3,0});
            for (uint32_t ks = 0; ks < HEAD_DIM; ks += 64) {
                DataCopy(kTileUb_, kBatchUb_[ks], DataCopyParams{16,8,8,0});
                // UB-to-UB DataCopy is V on dav_c220: complete both tile copies
                // before kTile is read below and uSmall is read by Broadcast.
                PipeBarrier<PIPE_V>();
                for (uint32_t v = 0; v < 8; ++v) {
                    DataCopy(outerRightUb_[v*64], kTileUb_,
                             DataCopyParams{16,8,0,56});
                }
                uint32_t dst[2] = {LOG_CAPACITY*8,64};
                uint32_t src[2] = {LOG_CAPACITY*8,1};
                Broadcast<float,2,1>(outerLeftUb_, uSmallUb_, dst, src, broadcastTmpUb_);
                PipeBarrier<PIPE_V>();
                Mul(outerLeftUb_, outerLeftUb_, outerRightUb_,
                    LOG_CAPACITY*8*64);
                PipeBarrier<PIPE_V>();
                TreeFold(outerLeftUb_, outerRightUb_, 8*64);
                Add(stateUb_[vs*HEAD_DIM+ks], stateUb_[vs*HEAD_DIM+ks],
                    outerLeftUb_, 64, 8, {1,1,1,16,16,8});
                PipeBarrier<PIPE_V>();
            }
        }
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
            ((static_cast<uint64_t>(slot) * KEY_HEADS + qHead) * LOG_CAPACITY + entry) * HEAD_DIM;
        LoadBf16Vector(keyGm_, sourceOffset, kLogUb_, kInQueue_, HEAD_DIM);
        // RAW: first Cast writes kLogUb; the output Cast must observe it.
        PipeBarrier<PIPE_V>();
        LocalTensor<bfloat16_t> local = kOutQueue_.AllocTensor<bfloat16_t>();
        Cast(local, kLogUb_, RoundMode::CAST_RINT, HEAD_DIM);
        kOutQueue_.EnQue<bfloat16_t>(local);
        local = kOutQueue_.DeQue<bfloat16_t>();
        DataCopyParams outParams{1, HEAD_DIM * sizeof(bfloat16_t), 0, 0};
        DataCopyPad(kLogGm_[targetOffset], local, outParams);
        kOutQueue_.FreeTensor(local);
    }

    // Native-order follow-up: reconstruct only in UB; never materialize the
    // persistent FP32 base on append steps.  This is a NEW numerical candidate,
    // not an assertion that reconstruction matches native FP32 roundoff.
    __aicore__ inline void ProcessTile(
        uint32_t token, uint32_t slot, uint32_t head, uint32_t length,
        uint32_t vStart, uint64_t baseOffset, float previousScale,
        float currentScale, float beta, float kq, bool merge)
    {
        const uint64_t ho = static_cast<uint64_t>(slot) * VALUE_HEADS + head;
        LoadBase(baseOffset, V_STEP);
        LoadUTile(ho, vStart);
        PipeBarrier<PIPE_V>();
        ParallelFlush(previousScale);
        Muls(stateUb_, stateUb_, currentScale, V_STEP * HEAD_DIM);
        PipeBarrier<PIPE_V>();

        MatVecMul(stateUb_, kUb_, broadUb_, V_STEP, false);
        PipeBarrier<PIPE_V>();
        ReduceRows(deltaUb_, broadUb_, V_STEP);
        PipeBarrier<PIPE_V>();
        const uint64_t vo =
            (static_cast<uint64_t>(token) * VALUE_HEADS + head) * HEAD_DIM + vStart;
        LoadBf16Vector(valueGm_, vo, vUb_, vInQueue_, V_STEP);
        PipeBarrier<PIPE_V>();
        // Preserve the pinned native LocalTensor expression, not an assumed
        // equivalent explicit Sub lowering.  Actual compiler/NPU parity is pending.
        deltaUb_ = vUb_ - deltaUb_;
        PipeBarrier<PIPE_V>();
        Muls(deltaUb_, deltaUb_, beta, V_STEP);
        PipeBarrier<PIPE_V>();
        uint32_t dst[2] = {V_STEP, HEAD_DIM}, src[2] = {V_STEP, 1};
        Broadcast<float,2,1>(broadUb_, deltaUb_, dst, src, broadcastTmpUb_);
        PipeBarrier<PIPE_V>();
        MatVecMul(broadUb_, kUb_, stateUb_, V_STEP, true);
        PipeBarrier<PIPE_V>();
        MatVecMul(stateUb_, qUb_, broadUb_, V_STEP, false);
        PipeBarrier<PIPE_V>();
        ReduceRows(attnUb_, broadUb_, V_STEP);
        PipeBarrier<PIPE_V>();

        if (merge) {
            StoreBase(baseOffset, V_STEP);
        } else {
            StoreULog((ho * LOG_CAPACITY + length) * HEAD_DIM + vStart, V_STEP);
        }
        StoreOutput(vo, V_STEP);
    }

    __aicore__ inline void ProcessTask(uint32_t token, uint32_t head)
    {
        // Graph padding's slot can be0: sequence length, never slot ID,
        // decides activity. Dummy must not READ or WRITE any state/log.
        const int32_t n = actualSeqLengthsGm_.GetValue(token+1);
        if (n <= 0) {
            Duplicate(attnUb_, 0.0f, V_STEP);
            // RAW: zero output must complete before StoreOutput's vector Cast.
            PipeBarrier<PIPE_V>();
            for (uint32_t vs=0; vs<HEAD_DIM; vs+=V_STEP)
                StoreOutput((static_cast<uint64_t>(token)*VALUE_HEADS+head)*HEAD_DIM+vs,V_STEP);
            return;
        }
        const int32_t sv = stateIndicesGm_.GetValue(token);
        if (n != 1 || sv < 0 || static_cast<uint32_t>(sv) >= slots_) return;
        const uint32_t slot = static_cast<uint32_t>(sv);
        const uint64_t mo=(static_cast<uint64_t>(slot)*VALUE_HEADS+head)*META_STRIDE;
        const int32_t lv=logLengthGm_.GetValue(mo);
        if (lv<0 || lv>=static_cast<int32_t>(FLUSH_INTERVAL)) return;
        const uint32_t length=static_cast<uint32_t>(lv);
        const bool merge=length+1==FLUSH_INTERVAL;
        const float cumulative=cumulativeDecayGm_.GetValue(mo);
        const float gate=gGm_.GetValue(static_cast<uint64_t>(token)*VALUE_HEADS+head);
        const float beta=LoadBeta(token,head);
        const float previousScale=ExpScalar(cumulative), currentScale=ExpScalar(gate);
        LoadQK(token,head);
        const float kq=DotQK(kUb_,qUb_);
        PrepareLogs(slot,head,length,cumulative);
        for(uint32_t vs=0;vs<HEAD_DIM;vs+=V_STEP) {
            const uint64_t bo=((static_cast<uint64_t>(slot)*VALUE_HEADS+head)*HEAD_DIM+vs)*HEAD_DIM;
            ProcessTile(token,slot,head,length,vs,bo,previousScale,currentScale,beta,kq,merge);
        }
        if(merge) {
            cumulativeDecayGm_.SetValue(mo,0.0f); logLengthGm_.SetValue(mo,0);
        } else {
            if(head%(VALUE_HEADS/KEY_HEADS)==0) StoreKLog(token,slot,head,length);
            lambdaLogGm_.SetValue(mo+length,cumulative+gate);
            cumulativeDecayGm_.SetValue(mo,cumulative+gate);
            logLengthGm_.SetValue(mo,static_cast<int32_t>(length+1));
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
    TQue<QuePosition::VECOUT, 1> kOutQueue_;
    TBuf<TPosition::VECCALC> tmpBuff_;
    LocalTensor<uint8_t> broadcastTmpUb_;
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
    LocalTensor<float> uLogUb_;
    LocalTensor<float> kBatchUb_, dotBatchUb_, uBatchUb_, weightedUb_;
    LocalTensor<float> outerLeftUb_, outerRightUb_, kTileUb_, uSmallUb_;
    LocalTensor<float> coeffUb_, lambdaUb_, qDotsUb_, kDotsUb_, qWeightsUb_, kWeightsUb_;
    uint32_t tokens_;
    uint32_t slots_;
    uint32_t vStep_;
    float scale_;
    uint32_t blockIdx_;
    uint32_t blockNum_;
};

} // namespace Qwen36KVBufferShortHorizonV3

#endif
