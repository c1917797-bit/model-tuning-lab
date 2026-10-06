#ifndef QWEN36_GDN_KVBUFFER_PARALLEL_TILING_H
#define QWEN36_GDN_KVBUFFER_PARALLEL_TILING_H

#include <cstdint>

namespace Qwen36KVBufferParallel {

struct KVBufferTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t vStep;
    float scale;
};

} // namespace Qwen36KVBufferParallel

#endif
