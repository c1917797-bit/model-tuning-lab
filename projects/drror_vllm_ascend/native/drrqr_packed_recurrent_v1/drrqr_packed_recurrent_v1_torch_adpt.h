/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2026. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef DRRQR_PACKED_RECURRENT_V1_TORCH_ADPT_H
#define DRRQR_PACKED_RECURRENT_V1_TORCH_ADPT_H

namespace vllm_ascend {

at::Tensor npu_drrqr_packed_recurrent_v1(
    const at::Tensor& packedQkv,
    at::Tensor& state,
    const c10::optional<at::Tensor>& beta,
    const c10::optional<double> scale,
    const c10::optional<at::Tensor>& actual_seq_lengths,
    const c10::optional<at::Tensor>& ssm_state_indices,
    const c10::optional<at::Tensor>& num_accepted_tokens,
    const c10::optional<at::Tensor>& g,
    const c10::optional<at::Tensor>& gk)
{
    TORCH_CHECK(scale.has_value(), "scale cannot be empty.");

    TORCH_CHECK(packedQkv.dim() == 2, "packedQkv must be [T, packedWidth].");
    TORCH_CHECK(state.dim() == 4, "state must be [slots, Nv, Dv, Dk].");
    auto options = packedQkv.options().dtype(at::ScalarType::BFloat16);
    at::Tensor output = at::empty(
        {packedQkv.size(0), state.size(1), state.size(2)}, options);
    float scale_real = static_cast<float>(scale.value());
    EXEC_NPU_CMD(aclnnDrrqrPackedRecurrentV1,
                 packedQkv,
                 beta,
                 state,
                 actual_seq_lengths,
                 ssm_state_indices,
                 g,
                 gk,
                 num_accepted_tokens,
                 scale_real,
                 output);
    return output;
}

} // namespace vllm_ascend
#endif
