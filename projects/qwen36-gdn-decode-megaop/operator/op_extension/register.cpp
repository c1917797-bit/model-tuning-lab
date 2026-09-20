/**
 * Copyright (c) 2026 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under the terms and conditions of
 * CANN Open Software License Agreement Version 2.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"

namespace {

TORCH_LIBRARY_FRAGMENT(qwen36_gdn, m)
{
    m.def(
        "decode_core(Tensor query, Tensor key, Tensor value, Tensor a_log, Tensor a, Tensor b, "
        "Tensor dt_bias, Tensor(a!) state, Tensor actual_seq_lengths, "
        "Tensor state_indices) -> Tensor");
}

TORCH_LIBRARY_IMPL(qwen36_gdn, PrivateUse1, m)
{
    m.impl("decode_core", TORCH_FN(ascend_kernel::qwen36_gdn_decode_core_torch));
}

at::Tensor qwen36_gdn_decode_core_meta(
    const at::Tensor& query,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&,
    const at::Tensor&)
{
    return at::empty({query.size(0), 12, 128}, query.options());
}

TORCH_LIBRARY_IMPL(qwen36_gdn, Meta, m)
{
    m.impl("decode_core", &qwen36_gdn_decode_core_meta);
}

} // namespace
