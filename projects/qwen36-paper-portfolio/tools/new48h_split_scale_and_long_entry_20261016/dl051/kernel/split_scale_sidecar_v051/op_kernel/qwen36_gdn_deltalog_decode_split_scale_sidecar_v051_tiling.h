#ifndef QWEN36_GDN_DELTALOG_DECODE_SPLIT_SCALE_SIDECAR_V050_TILING_H
#define QWEN36_GDN_DELTALOG_DECODE_SPLIT_SCALE_SIDECAR_V050_TILING_H

#include <cstdint>

namespace Qwen36DeltaLogSplitScaleSidecarV050 {

struct DeltalogTilingData {
    uint32_t tokens;
    uint32_t stateSlots;
    uint32_t vectorCoreNum;
    uint32_t vStep;
    float scale;
};

} // namespace Qwen36DeltaLogSplitScaleSidecarV050

#endif
