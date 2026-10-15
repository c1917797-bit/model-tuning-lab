#ifndef QWEN36_GDN_DELTALOG_DECODE_READOUT_MAC042_DEBUG_TILING_H
#define QWEN36_GDN_DELTALOG_DECODE_READOUT_MAC042_DEBUG_TILING_H

#include <cstdint>

namespace Qwen36DeltaLogReadoutMac042Debug {

struct DeltalogTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t vStep;
    float scale;
};

} // namespace Qwen36DeltaLogReadoutMac042Debug

#endif
