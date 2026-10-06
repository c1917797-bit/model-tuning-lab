// SPDX-License-Identifier: Apache-2.0
#ifndef QWEN36_DAMP_SELECTED_PREFILL_PLAN_H
#define QWEN36_DAMP_SELECTED_PREFILL_PLAN_H
#include <cstdint>
#include <cstddef>
#include "../../../production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h"
namespace Qwen36DampSelectedPrefill {
using Qwen36DampIntegerCompactionV1::HEAD_DIM;
using Qwen36DampIntegerCompactionV1::VALUE_HEADS;
using Qwen36DampIntegerCompactionV1::HIGH_KEYS;
using Qwen36DampIntegerCompactionV1::LOW_KEYS;
using Qwen36DampIntegerCompactionV1::GROUP_VALUES;
using Qwen36DampIntegerCompactionV1::VALUE_GROUPS;
using Qwen36DampIntegerCompactionV1::PACKED_GROUP_BYTES;
using Qwen36DampIntegerCompactionV1::QUANTIZER_COUNT;
using Qwen36DampIntegerCompactionV1::QUANTIZER_WORK_BYTES;
using Qwen36DampIntegerCompactionV1::QUANTIZER_PLANE_BYTES;
using Qwen36DampIntegerCompactionV1::LUT_OFFSET_INTS;
using Qwen36DampIntegerCompactionV1::SCALE_RECIPROCAL_FP32;
constexpr uint32_t ABI_VERSION=1;
constexpr uint32_t WORK_BYTES=59904;
constexpr uint32_t QUEUE_BYTES=160+2048+512+2*PACKED_GROUP_BYTES+32;
constexpr uint32_t UB_BYTES=WORK_BYTES+QUEUE_BYTES+QUANTIZER_WORK_BYTES;
static_assert(UB_BYTES==115392);
struct alignas(32) Tiling {
    uint32_t prefills;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t abiVersion;
    uint32_t useFloatCandidate;
    uint32_t reserved[3];
    int32_t cTable[128];
    int32_t fTable[128];
};
static_assert(sizeof(Tiling)==1056 && offsetof(Tiling,cTable)==32 &&
              offsetof(Tiling,fTable)==544);
}
#endif
