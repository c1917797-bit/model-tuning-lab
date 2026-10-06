// SPDX-License-Identifier: Apache-2.0
// ASC queued invocation adapted from frozen diagnostic scaffold, not stream(true).
#include <cstdint>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <tuple>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "../op_kernel/quantizer_probe_kernel.asc"
#include "ops.h"

namespace damp_quantizer_extension {
namespace {
constexpr int64_t CODE_GUARD = 0x13579bdf;
constexpr int64_t VALID_GUARD = 0x2468ace0;
using Key = std::pair<int32_t, int64_t>;
std::map<Key, at::Tensor>& tilings() { static auto* p = new std::map<Key, at::Tensor>(); return *p; }
std::mutex& mutex() { static auto* p = new std::mutex(); return *p; }

void check_tensor(const at::Tensor& t, const at::Tensor& x, const char* name)
{
    TORCH_CHECK(t.is_privateuseone() && t.device() == x.device(),
                name, " must be on the same NPU");
    TORCH_CHECK(t.scalar_type() == at::kInt && t.dim() == 1 && t.is_contiguous(),
                name, " must be a contiguous raw-bits INT32 vector");
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t) == ACL_FORMAT_ND,
                name, " must use physical ACL_FORMAT_ND");
    TORCH_CHECK(reinterpret_cast<uintptr_t>(t.data_ptr()) % 32 == 0,
                name, " pointer must be 32B aligned");
}
void check_disjoint(const at::Tensor& a, const at::Tensor& b)
{
    const uintptr_t aa = reinterpret_cast<uintptr_t>(a.data_ptr());
    const uintptr_t ba = reinterpret_cast<uintptr_t>(b.data_ptr());
    const uintptr_t ae = aa + static_cast<uintptr_t>(a.numel()*a.element_size());
    const uintptr_t be = ba + static_cast<uintptr_t>(b.numel()*b.element_size());
    TORCH_CHECK(ae <= ba || be <= aa, "isolated quantizer buffers must be disjoint");
}
Key check_inputs(const at::Tensor& x, const at::Tensor& scale)
{
    // Shape/count admission occurs before resource queries, upload or launch.
    TORCH_CHECK(x.scalar_type() == at::kInt && scale.scalar_type() == at::kInt &&
                x.dim() == 1 && scale.sizes() == x.sizes() &&
                x.is_contiguous() && scale.is_contiguous(),
                "raw bit inputs must be contiguous equal-shape INT32 vectors");
    TORCH_CHECK(x.numel() >= 64 && x.numel() <= 1792 && x.numel() % 64 == 0,
                "isolated count must be 64-aligned in [64,1792]");
    check_tensor(x, x, "x_bits");
    check_tensor(scale, x, "scale_bits");
    check_disjoint(x, scale);
    const char* soc = aclrtGetSocName();
    TORCH_CHECK(soc != nullptr && std::string(soc) == "Ascend910B4",
                "this isolated numerical gate is bound to Ascend910B4");
    int32_t device = -1;
    TORCH_CHECK(aclrtGetDevice(&device) == ACL_SUCCESS, "NPU device query failed");
    return {device, x.numel()};
}
at::Tensor guarded_output(const at::Tensor& x, int64_t guard)
{
    // Public deployed interface; never drop format guard to make allocation pass.
    auto output = at_npu::native::custom_ops::npu_format_cast(
        at::full({x.numel()+16}, guard, x.options()),
        ACL_FORMAT_ND, std::nullopt, std::nullopt);
    check_tensor(output, x, "guarded_output");
    return output;
}
}
void prepare(const at::Tensor& x, const at::Tensor& scale)
{
    const c10::OptionalDeviceGuard guard(x.device());
    const Key key = check_inputs(x, scale);
    std::lock_guard<std::mutex> lock(mutex());
    if (tilings().find(key) != tilings().end()) { return; }
    const Qwen36DampQuantizerProbe::Tiling tiling{
        static_cast<uint32_t>(x.numel()), Qwen36DampQuantizerProbe::ABI_VERSION};
    auto tensor = at_npu::native::custom_ops::npu_format_cast(
        at::empty({static_cast<int64_t>(sizeof(tiling))}, x.options().dtype(at::kByte)),
        ACL_FORMAT_ND, std::nullopt, std::nullopt);
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(tensor) == ACL_FORMAT_ND,
                "tiling physical format must be ND");
    TORCH_CHECK(aclrtMemcpy(tensor.mutable_data_ptr(), sizeof(tiling), &tiling,
                sizeof(tiling), ACL_MEMCPY_HOST_TO_DEVICE) == ACL_SUCCESS,
                "prepare tiling H2D failed; run outside capture");
    tilings().emplace(key, tensor); // no state or inputs retained
}
std::tuple<at::Tensor, at::Tensor> exact_bits(
    const at::Tensor& x, const at::Tensor& scale)
{
    const c10::OptionalDeviceGuard guard(x.device());
    const Key key = check_inputs(x, scale);
    at::Tensor tiling;
    {
        std::lock_guard<std::mutex> lock(mutex());
        const auto found = tilings().find(key);
        TORCH_CHECK(found != tilings().end(),
                    "call prepare outside capture before exact_bits");
        tiling = found->second;
    }
    auto codes = guarded_output(x, CODE_GUARD);
    auto valid = guarded_output(x, VALID_GUARD);
    check_disjoint(codes, valid);
    check_disjoint(codes, x); check_disjoint(codes, scale);
    check_disjoint(valid, x); check_disjoint(valid, scale);
    auto stream = c10_npu::getCurrentNPUStream().stream(false);
    auto aclCall = [=]() -> int {
        qwen36_damp_quantizer_exact_bits_kernel<<<1, nullptr, stream>>>(
            (GM_ADDR)x.mutable_data_ptr(), (GM_ADDR)scale.mutable_data_ptr(),
            (GM_ADDR)codes.mutable_data_ptr(), (GM_ADDR)valid.mutable_data_ptr(),
            (GM_ADDR)tiling.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36DampQuantizerExactBits", aclCall);
    return {codes, valid};
}
}

