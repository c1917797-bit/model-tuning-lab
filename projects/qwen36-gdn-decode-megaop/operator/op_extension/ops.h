/**
 * Copyright (c) 2026 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under the terms and conditions of
 * CANN Open Software License Agreement Version 2.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

#ifndef QWEN36_GDN_DECODE_CORE_OPS_H
#define QWEN36_GDN_DECODE_CORE_OPS_H

#include <torch/extension.h>

// [MODIFY] 函数声明 - add_custom → <your_op>，保持 _torch 后缀
namespace ascend_kernel {

at::Tensor qwen36_gdn_decode_core_torch(
    const at::Tensor& query,
    const at::Tensor& key,
    const at::Tensor& value,
    const at::Tensor& aLog,
    const at::Tensor& a,
    const at::Tensor& b,
    const at::Tensor& dtBias,
    const at::Tensor& state,
    const at::Tensor& actualSeqLengths,
    const at::Tensor& stateIndices);

} // namespace ascend_kernel

#endif // QWEN36_GDN_DECODE_CORE_OPS_H
