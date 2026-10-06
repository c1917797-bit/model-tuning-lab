#ifndef QWEN36_GDN_DAMP_INTEGER_COMPACTION_V1_DECODE_TILING_H
#define QWEN36_GDN_DAMP_INTEGER_COMPACTION_V1_DECODE_TILING_H

#include <cstdint>
#include <cstddef>

namespace Qwen36DampIntegerCompactionV1 {
constexpr uint32_t ABI_VERSION = 2;
constexpr uint32_t KEY_HEADS = 4;
constexpr uint32_t VALUE_HEADS = 12;
constexpr uint32_t HEAD_DIM = 128;
constexpr uint32_t HIGH_KEYS = 16;
constexpr uint32_t LOW_KEYS = 112;
constexpr uint32_t GROUP_VALUES = 32;
constexpr uint32_t VALUE_GROUPS = 4;
constexpr uint32_t MAX_TOKENS = 16;
constexpr uint32_t PACKED_GROUP_BYTES = 5120;
constexpr uint32_t WORK_BYTES = 79872;
constexpr uint32_t QUEUE_BYTES = 18944;
constexpr uint32_t QUANTIZER_COUNT = 448; // 4 values x 112 keys
constexpr uint32_t QUANTIZER_PLANE_BYTES = QUANTIZER_COUNT * sizeof(int32_t);
constexpr uint32_t QUANTIZER_WORK_BYTES = 42496;
constexpr uint32_t LUT_OFFSET_INTS = 8; // 32B padded header, logical INT32 unit
constexpr uint32_t DECLARED_UB_BYTES = WORK_BYTES + QUEUE_BYTES + QUANTIZER_WORK_BYTES;
// Explicit allocations only; old four-argument Broadcast hidden LCM/stack is
// NOT included here and must be measured/verified before NPU admission.
static_assert(DECLARED_UB_BYTES == 141312);
static_assert(QUANTIZER_COUNT % 64 == 0);
// Exactly IEEE754 binary32 0x3c010204. No constant division or fast reciprocal.
constexpr float SCALE_RECIPROCAL_FP32 = 0.007874015718698502f;

struct alignas(32) DampTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t abiVersion;
    float qScale;
    uint32_t reserved[3];
    int32_t cTable[128];
    int32_t fTable[128];
};
static_assert(offsetof(DampTilingData, cTable) == 32);
static_assert(offsetof(DampTilingData, fTable) == 544);
static_assert(sizeof(DampTilingData) == 1056);
static_assert(alignof(DampTilingData) == 32);
} // namespace Qwen36DampIntegerCompactionV1
#endif

