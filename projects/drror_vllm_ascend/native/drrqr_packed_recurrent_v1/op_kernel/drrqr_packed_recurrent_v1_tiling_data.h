/**
 * Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under the terms and conditions of
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

/*!
 * \file drrqr_packed_recurrent_v1.cpp
 * \brief
 */
#ifndef DRRQR_PACKED_RECURRENT_V1_TILING_DATA_H
#define DRRQR_PACKED_RECURRENT_V1_TILING_DATA_H

#include "kernel_tiling/kernel_tiling.h"

namespace DrrqrPackedRecurrentV1 {
#pragma pack(push, 8)
struct alignas(8) DrrqrPackedRecurrentV1TilingData { // alignas(8)确保8字节对齐
    uint32_t vectorCoreNum;
    uint32_t ubCalSize;
    uint32_t ubRestBytes;
    uint32_t t;
    uint32_t nk;
    uint32_t dk;
    uint32_t nv;
    uint32_t dv;
    uint32_t sBlockNum;
    uint32_t b;
    uint32_t vStep;
    uint32_t stateOutBufferNum;
    uint32_t attnOutBufferNum;
    float scale;
    uint32_t hasGama;
    uint32_t hasGamaK;
    uint32_t hasAcceptedTokens;
};
#pragma pack(pop)
} // DrrqrPackedRecurrentV1

#endif // DRRQR_PACKED_RECURRENT_V1_TILING_DATA_H
