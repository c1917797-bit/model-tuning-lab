#ifndef QWEN36_GDN_DELTALOG_DECODE_READOUT_SIDECAR_V015_TILING_H
#define QWEN36_GDN_DELTALOG_DECODE_READOUT_SIDECAR_V015_TILING_H

#include <cstdint>

namespace Qwen36DeltaLogReadoutSidecarV015 {

struct DeltalogTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t vStep;
    float scale;
};

} // namespace Qwen36DeltaLogReadoutSidecarV015

#endif
