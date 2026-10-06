#ifndef QWEN36_GDN_DAMP_TRACE_TILING_H
#define QWEN36_GDN_DAMP_TRACE_TILING_H

#include <cstdint>

namespace Qwen36DampTrace {
constexpr uint32_t ABI_VERSION = 1;
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
constexpr uint32_t TRACE_QUEUE_BYTES = GROUP_VALUES * HEAD_DIM * sizeof(float);
constexpr uint32_t DECLARED_UB_BYTES = WORK_BYTES + QUEUE_BYTES + TRACE_QUEUE_BYTES;
// Exactly IEEE754 binary32 0x3c010204. No constant division or fast reciprocal.
constexpr float SCALE_RECIPROCAL_FP32 = 0.007874015718698502f;

struct DampTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t abiVersion;
    float qScale;
};
} // namespace Qwen36DampTrace
#endif
