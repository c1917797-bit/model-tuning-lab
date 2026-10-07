#ifndef QWEN36_GDN_KVBUFFER_SHORT_HORIZON_V3_TILING_H
#define QWEN36_GDN_KVBUFFER_SHORT_HORIZON_V3_TILING_H

#include <cstdint>

namespace Qwen36KVBufferShortHorizonV3 {

struct KVBufferTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t vStep;
    float scale;
};

} // namespace Qwen36KVBufferShortHorizonV3

#endif
