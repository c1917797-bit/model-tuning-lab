/**
 * Copyright (c) 2026 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under the terms and conditions of
 * CANN Open Software License Agreement Version 2.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the software repository for the full text of the License.
 */

// Test-only native-derived reference wrapper. Infrastructure follows Cannbot
// direct-invoke multi-TU route: stream(true) + direct C kernel function call.
#include "acl/acl.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstdint>
#include <optional>
#include <string>
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "ops.h"
#include "tiling/platform/platform_ascendc.h"
extern "C" void qwen36_damp_native_sr_reference_kernel(
    uint32_t blockDim, void* l2, aclrtStream stream,
    uint8_t* q, uint8_t* k, uint8_t* v, uint8_t* g, uint8_t* beta,
    uint8_t* selected, uint8_t* pk, uint8_t* pv, uint8_t* invPv, uint8_t* sr,
    uint8_t* updated, uint8_t* fpOut, uint8_t* bfOut, uint32_t tokens, float qScale);
namespace qwen36_damp_reference {
namespace {
void check_shape(const at::Tensor& t, at::IntArrayRef shape,
                 at::ScalarType type, const char* name) {
    TORCH_CHECK(t.sizes() == shape, name, " shape mismatch");
    TORCH_CHECK(t.scalar_type() == type, name, " dtype mismatch");
    TORCH_CHECK(t.is_contiguous(), name, " must be contiguous");
}
int64_t check_shapes(const at::Tensor& q, const at::Tensor& k, const at::Tensor& v,
                     const at::Tensor& g, const at::Tensor& beta, const at::Tensor& selected,
                     const at::Tensor& pk, const at::Tensor& pv,
                     const at::Tensor& invPv, const at::Tensor& sr) {
    TORCH_CHECK(q.dim() == 3 && q.size(1) == 4 && q.size(2) == 128,
                "query must be [T,4,128]");
    const int64_t t = q.size(0);
    TORCH_CHECK(t == 1 || t == 16, "reference v1 supports exactly B1/B16 one-token turns");
    check_shape(q, {t,4,128}, at::kBFloat16, "q");
    check_shape(k, {t,4,128}, at::kBFloat16, "k");
    check_shape(v, {t,12,128}, at::kBFloat16, "v");
    check_shape(g, {t,12}, at::kFloat, "g");
    check_shape(beta, {t,12}, at::kBFloat16, "beta");
    check_shape(selected, {t,12,128,128}, at::kFloat, "state_selected");
    check_shape(pk, {12,128}, at::kInt, "pk");
    check_shape(pv, {12,128}, at::kInt, "pv");
    check_shape(invPv, {12,128}, at::kInt, "inv_pv");
    check_shape(sr, {12,128}, at::kFloat, "sr");
    return t;
}
void check_device(const at::Tensor& q, const at::Tensor& x, const char* name) {
    TORCH_CHECK(x.is_privateuseone() && x.device() == q.device(),
                name, " must be on the query NPU");
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(x) == ACL_FORMAT_ND,
                name, " must use physical ACL_FORMAT_ND");
}
void check_plans(const at::Tensor& pk, const at::Tensor& pv,
                 const at::Tensor& invPv, const at::Tensor& sr) {
    // Explicit EAGER TEST path. This synchronous validation is deliberately
    // outside any numerical kernel and cannot certify graph capture.
    const at::Tensor a = pk.to(at::kCPU), b = pv.to(at::kCPU);
    const at::Tensor c = invPv.to(at::kCPU), d = sr.to(at::kCPU);
    const int32_t* kp = a.data_ptr<int32_t>();
    const int32_t* vp = b.data_ptr<int32_t>();
    const int32_t* ip = c.data_ptr<int32_t>();
    const float* sp = d.data_ptr<float>();
    for (int h = 0; h < 12; ++h) {
        bool seenK[128] = {}, seenV[128] = {};
        for (int i = 0; i < 128; ++i) {
            const int p = h * 128 + i;
            TORCH_CHECK(kp[p] >= 0 && kp[p] < 128 && vp[p] >= 0 && vp[p] < 128 &&
                        ip[p] >= 0 && ip[p] < 128, "plan indices must be logical 0..127");
            TORCH_CHECK(!seenK[kp[p]] && !seenV[vp[p]], "pk/pv must be permutations");
            seenK[kp[p]] = true; seenV[vp[p]] = true;
            TORCH_CHECK(ip[h * 128 + vp[p]] == i, "inverse Pv mismatch");
            TORCH_CHECK(std::isfinite(sp[p]) && sp[p] > 0.0f,
                        "SR must be finite positive original-coordinate FP32");
        }
    }
}
Outputs allocate(const at::Tensor& q, int64_t t) {
    return {at::empty({t,12,128,128}, q.options().dtype(at::kFloat)),
            at::empty({t,12,128}, q.options().dtype(at::kFloat)),
            at::empty({t,12,128}, q.options().dtype(at::kBFloat16))};
}
uint8_t* ptr(const at::Tensor& t) {
    return reinterpret_cast<uint8_t*>(t.mutable_data_ptr());
}
}
Outputs meta(const at::Tensor& q, const at::Tensor& k, const at::Tensor& v,
             const at::Tensor& g, const at::Tensor& beta, const at::Tensor& selected,
             const at::Tensor& pk, const at::Tensor& pv,
             const at::Tensor& invPv, const at::Tensor& sr) {
    return allocate(q, check_shapes(q,k,v,g,beta,selected,pk,pv,invPv,sr));
}
Outputs decode(const at::Tensor& q, const at::Tensor& k, const at::Tensor& v,
               const at::Tensor& g, const at::Tensor& beta, const at::Tensor& selected,
               const at::Tensor& pk, const at::Tensor& pv,
               const at::Tensor& invPv, const at::Tensor& sr) {
    const char* enabled = std::getenv("DAMP_ENABLE_NATIVE_REFERENCE");
    TORCH_CHECK(enabled != nullptr && std::string(enabled) == "1",
                "test-only reference requires DAMP_ENABLE_NATIVE_REFERENCE=1");
    const c10::OptionalDeviceGuard guard(q.device());
    const int64_t t = check_shapes(q,k,v,g,beta,selected,pk,pv,invPv,sr);
    for (const auto& item : {std::make_pair(&q,"q"), std::make_pair(&k,"k"),
         std::make_pair(&v,"v"), std::make_pair(&g,"g"), std::make_pair(&beta,"beta"),
         std::make_pair(&selected,"state_selected"), std::make_pair(&pk,"pk"),
         std::make_pair(&pv,"pv"), std::make_pair(&invPv,"inv_pv"), std::make_pair(&sr,"sr")})
        check_device(q, *item.first, item.second);
    check_plans(pk,pv,invPv,sr);
    const char* soc = aclrtGetSocName();
    TORCH_CHECK(soc != nullptr && (std::string(soc).rfind("Ascend910B",0) == 0 ||
                                  std::string(soc).rfind("Ascend910_93",0) == 0),
                "reference is pinned to DAV2201 ordinary recurrent arithmetic");
    int32_t device = -1;
    int64_t cores = 0;
    TORCH_CHECK(aclrtGetDevice(&device) == ACL_SUCCESS &&
                aclrtGetDeviceInfo(device, ACL_DEV_ATTR_VECTOR_CORE_NUM, &cores) == ACL_SUCCESS &&
                cores > 0, "cannot query real vector-core count");
    uint64_t ubBytes = 0;
    auto* platform = platform_ascendc::PlatformAscendCManager::GetInstance();
    TORCH_CHECK(platform != nullptr, "cannot obtain actual AscendC platform");
    platform->GetCoreMemSize(platform_ascendc::CoreMemType::UB, ubBytes);
    TORCH_CHECK(ubBytes >= 75680, "actual per-AIV UB is below reference allocation");
    Outputs result = allocate(q,t);
    // Actual default four-dimensional FP32 allocations can be non-ND on
    // this deployed TorchNPU. Convert only in the eager device path; Meta
    // allocation remains device-free. Never waive the raw-pointer ND gate.
    std::get<0>(result) = at_npu::native::custom_ops::npu_format_cast(
        std::get<0>(result), ACL_FORMAT_ND, std::nullopt, std::nullopt);
    check_device(q, std::get<0>(result), "updated_fp32");
    check_device(q, std::get<1>(result), "original_output_fp32");
    check_device(q, std::get<2>(result), "original_output_bf16");
    // Allocate empty outputs first, then flush queue. Never use stream(false)
    // with this C++ direct function call or put NPUStream inside OpCommand.
    auto stream = c10_npu::getCurrentNPUStream().stream(true);
    qwen36_damp_native_sr_reference_kernel(
        static_cast<uint32_t>(std::min<int64_t>(cores,t*12)), nullptr, stream,
        ptr(q),ptr(k),ptr(v),ptr(g),ptr(beta),ptr(selected),ptr(pk),ptr(pv),ptr(invPv),ptr(sr),
        ptr(std::get<0>(result)),ptr(std::get<1>(result)),ptr(std::get<2>(result)),
        static_cast<uint32_t>(t), 1.0f/std::sqrt(128.0f));
    return result;
}
}
