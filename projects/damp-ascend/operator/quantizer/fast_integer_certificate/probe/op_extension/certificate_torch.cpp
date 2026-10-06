// SPDX-License-Identifier: Apache-2.0
// ASC-compiled queued launch, same deployed RunOpApi ABI as exact_bits.
// Blocking proposal admission is DIAGNOSTIC ONLY: not graph/performance usable.
#include <array>
#include <cstdint>
#include <limits>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <vector>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "../op_kernel/certificate_probe_kernel.asc"
#include "ops.h"
namespace damp_integer_probe_extension {
namespace {
using Key=std::pair<int32_t,int64_t>;
struct Resources { at::Tensor tiling,c,f; };
std::map<Key,Resources>& plans() { static auto* p=new std::map<Key,Resources>(); return *p; }
std::mutex& mutex() { static auto* p=new std::mutex(); return *p; }
void check_tensor(const at::Tensor& t,const at::Tensor& x,const char* name) {
    TORCH_CHECK(t.is_privateuseone() && t.device()==x.device(),name," must be on same NPU");
    TORCH_CHECK(t.scalar_type()==at::kInt && t.dim()==1 && t.is_contiguous(),
                name," must be contiguous INT32 vector (raw bits or logical magnitude)");
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND,
                name," must have physical ACL_FORMAT_ND");
    TORCH_CHECK(reinterpret_cast<uintptr_t>(t.data_ptr())%32==0,name," requires32B pointer");
}
std::pair<uintptr_t,uintptr_t> storage_span(const at::Tensor& t) {
    const auto storage=t.storage();
    const uintptr_t b=reinterpret_cast<uintptr_t>(storage.data_ptr().get());
    const uintptr_t n=static_cast<uintptr_t>(storage.nbytes());
    TORCH_CHECK(n<=std::numeric_limits<uintptr_t>::max()-b,"storage byte range overflow");
    return {b,b+n}; // complete backing interval, including guarded input roots
}
void check_disjoint(const at::Tensor& a,const at::Tensor& b) {
    const auto sa=storage_span(a),sb=storage_span(b);
    TORCH_CHECK(sa.second<=sb.first || sb.second<=sa.first,
                "probe backing byte intervals must be disjoint");
}
Key check_inputs(const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    TORCH_CHECK(x.scalar_type()==at::kInt && s.scalar_type()==at::kInt &&
                n.scalar_type()==at::kInt && x.dim()==1 && s.sizes()==x.sizes() &&
                n.sizes()==x.sizes() && x.is_contiguous() && s.is_contiguous() &&
                n.is_contiguous(),"three equal-shape contiguous INT32 vectors required");
    TORCH_CHECK(x.numel()==64 || x.numel()==896,"probe accepts N64 or896 only");
    check_tensor(x,x,"x_bits"); check_tensor(s,x,"scale_bits"); check_tensor(n,x,"proposal");
    check_disjoint(x,s); check_disjoint(x,n); check_disjoint(s,n);
    // Synchronous actual value admission MUST precede Gather/kernel dispatch.
    // No proposal is trusted just because the final certificate can reject it.
    const auto host=n.to(at::kCPU).contiguous();
    const auto* magnitudes=host.data_ptr<int32_t>();
    for (int64_t i=0;i<n.numel();++i)
        TORCH_CHECK(magnitudes[i]>=0 && magnitudes[i]<=127,
                    "proposal magnitude must be in0..127 before Gather; lane",i);
    const char* soc=aclrtGetSocName();
    TORCH_CHECK(soc!=nullptr && std::string(soc)=="Ascend910B4","probe bound to Ascend910B4");
    int32_t device=-1;
    TORCH_CHECK(aclrtGetDevice(&device)==ACL_SUCCESS,"NPU device query failed");
    return {device,x.numel()};
}
at::Tensor raw_buffer(const at::Tensor& x,int64_t count,at::ScalarType dtype) {
    auto t=at_npu::native::custom_ops::npu_format_cast(
        at::empty({count},x.options().dtype(dtype)),ACL_FORMAT_ND,std::nullopt,std::nullopt);
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND &&
                reinterpret_cast<uintptr_t>(t.data_ptr())%32==0,"plan must be ND/32B");
    return t;
}
at::Tensor guarded_output(const at::Tensor& x,int32_t sentinel) {
    auto t=at_npu::native::custom_ops::npu_format_cast(
        at::full({x.numel()+16},sentinel,x.options()),ACL_FORMAT_ND,std::nullopt,std::nullopt);
    check_tensor(t,x,"output"); return t;
}
}
void prepare(const at::Tensor& x,const at::Tensor& scale,const at::Tensor& n) {
    const c10::OptionalDeviceGuard guard(x.device());
    const Key key=check_inputs(x,scale,n);
    std::lock_guard<std::mutex> lock(mutex());
    if (plans().find(key)!=plans().end()) return;
    Resources r;
    r.tiling=raw_buffer(x,sizeof(DampIntegerProbe::Tiling),at::kByte);
    r.c=raw_buffer(x,128,at::kInt); r.f=raw_buffer(x,128,at::kInt);
    check_disjoint(r.tiling,r.c); check_disjoint(r.tiling,r.f); check_disjoint(r.c,r.f);
    for (const auto& t:{r.tiling,r.c,r.f})
        for (const auto& input:{x,scale,n}) check_disjoint(t,input);
    // Cold, explicit preparation only. Flush allocations outside any kernel
    // lambda, then complete synchronous H2D before publishing immutable plans.
    auto prepareStream=c10_npu::getCurrentNPUStream().stream(true);
    TORCH_CHECK(aclrtSynchronizeStream(prepareStream)==ACL_SUCCESS,"prepare sync failed");
    const DampIntegerProbe::Tiling tiling{
        static_cast<uint32_t>(x.numel()),DampIntegerProbe::ABI_VERSION};
    TORCH_CHECK(aclrtMemcpy(r.tiling.mutable_data_ptr(),sizeof(tiling),&tiling,
        sizeof(tiling),ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"tiling H2D failed");
    TORCH_CHECK(aclrtMemcpy(r.c.mutable_data_ptr(),128*4,DampIntegerProbe::C_TABLE.data(),
        128*4,ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"C LUT H2D failed");
    TORCH_CHECK(aclrtMemcpy(r.f.mutable_data_ptr(),128*4,DampIntegerProbe::F_TABLE.data(),
        128*4,ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"F LUT H2D failed");
    plans().emplace(key,r); // only immutable tables/tiling, never original inputs/state
}
Outputs certify_bits(const at::Tensor& x,const at::Tensor& scale,const at::Tensor& n) {
    const c10::OptionalDeviceGuard guard(x.device());
    const Key key=check_inputs(x,scale,n);
    Resources r;
    {
        std::lock_guard<std::mutex> lock(mutex());
        const auto found=plans().find(key);
        TORCH_CHECK(found!=plans().end(),"call prepare before certify_bits, outside capture");
        r=found->second;
    }
    std::array<at::Tensor,7> out;
    for (uint32_t i=0;i<7;++i) {
        out[i]=guarded_output(x,DampIntegerProbe::GUARDS[i]);
        for (const auto& input:{x,scale,n,r.tiling,r.c,r.f}) check_disjoint(out[i],input);
        for (uint32_t j=0;j<i;++j) check_disjoint(out[i],out[j]);
    }
    auto stream=c10_npu::getCurrentNPUStream().stream(false);
    auto aclCall=[=]()->int {
        qwen36_damp_integer_certify_bits_kernel<<<1,nullptr,stream>>>(
            (GM_ADDR)x.mutable_data_ptr(),(GM_ADDR)scale.mutable_data_ptr(),
            (GM_ADDR)n.mutable_data_ptr(),(GM_ADDR)r.c.mutable_data_ptr(),
            (GM_ADDR)r.f.mutable_data_ptr(),(GM_ADDR)out[0].mutable_data_ptr(),
            (GM_ADDR)out[1].mutable_data_ptr(),(GM_ADDR)out[2].mutable_data_ptr(),
            (GM_ADDR)out[3].mutable_data_ptr(),(GM_ADDR)out[4].mutable_data_ptr(),
            (GM_ADDR)out[5].mutable_data_ptr(),(GM_ADDR)out[6].mutable_data_ptr(),
            (GM_ADDR)r.tiling.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36DampIntegerCertifyBits",aclCall);
    return {out[0],out[1],out[2],out[3],out[4],out[5],out[6]};
}
}

