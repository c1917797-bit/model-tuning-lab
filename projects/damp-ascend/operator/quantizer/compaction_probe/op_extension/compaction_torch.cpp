// SPDX-License-Identifier: Apache-2.0
// ASC compilation + actual host-visible global definition + queued launch.
// Blocking value admission is DIAGNOSTIC ONLY. Eager, not graph/performance ABI.
#include <array>
#include <cstdint>
#include <limits>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "../op_kernel/compaction_probe_kernel.asc"
#include "ops.h"
namespace damp_compaction_extension {
namespace {
using Key=std::pair<int32_t,int64_t>;
std::map<Key,at::Tensor>& plans() { static auto* p=new std::map<Key,at::Tensor>(); return *p; }
std::mutex& mutex() { static auto* p=new std::mutex(); return *p; }
void check_tensor(const at::Tensor& t,const at::Tensor& x,const char* name) {
    TORCH_CHECK(t.is_privateuseone() && t.device()==x.device(),name," same NPU required");
    TORCH_CHECK(t.scalar_type()==at::kInt && t.dim()==1 && t.is_contiguous(),
                name," contiguous INT32 vector required");
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND,
                name," physical ACL_FORMAT_ND required");
    TORCH_CHECK(reinterpret_cast<uintptr_t>(t.data_ptr())%32==0,name,"32B pointer required");
}
std::pair<uintptr_t,uintptr_t> storage_span(const at::Tensor& t) {
    const auto storage=t.storage();
    const uintptr_t b=reinterpret_cast<uintptr_t>(storage.data_ptr().get());
    const uintptr_t n=static_cast<uintptr_t>(storage.nbytes());
    TORCH_CHECK(n<=std::numeric_limits<uintptr_t>::max()-b,"storage range overflow");
    return {b,b+n};
}
void check_disjoint(const at::Tensor& a,const at::Tensor& b) {
    const auto sa=storage_span(a),sb=storage_span(b);
    TORCH_CHECK(sa.second<=sb.first || sb.second<=sa.first,
                "complete backing byte intervals must be disjoint");
}
Key check_inputs(const at::Tensor& a,const at::Tensor& x,
                 const at::Tensor& s,const at::Tensor& n) {
    for(const auto& t:{a,x,s,n}) {
        check_tensor(t,a,"input");
        TORCH_CHECK(t.sizes()==a.sizes(),"four equal shapes required");
    }
    TORCH_CHECK(a.numel()==64 || a.numel()==448 || a.numel()==896,"N64/448/896 only");
    const std::array<at::Tensor,4> inputs={a,x,s,n};
    for(uint32_t i=0;i<4;++i) for(uint32_t j=0;j<i;++j) check_disjoint(inputs[i],inputs[j]);
    // Synchronous values BEFORE dispatch.0/1 flags are logical lanes, not packed
    // masks. Candidate magnitude is a supplied proposal, not trusted math.
    const auto ah=a.to(at::kCPU).contiguous(),nh=n.to(at::kCPU).contiguous();
    const auto* flags=ah.data_ptr<int32_t>(); const auto* mags=nh.data_ptr<int32_t>();
    for(int64_t i=0;i<a.numel();++i) {
        TORCH_CHECK(flags[i]==0 || flags[i]==1,"accepted must be0/1 before dispatch; lane",i);
        TORCH_CHECK(mags[i]>=0 && mags[i]<=127,"magnitude must be0..127 before dispatch; lane",i);
    }
    const char* soc=aclrtGetSocName();
    TORCH_CHECK(soc && std::string(soc)=="Ascend910B4","probe bound to Ascend910B4");
    int32_t device=-1;
    TORCH_CHECK(aclrtGetDevice(&device)==ACL_SUCCESS,"device query failed");
    return {device,a.numel()};
}
at::Tensor raw_buffer(const at::Tensor& a,int64_t count,at::ScalarType dtype) {
    auto t=at_npu::native::custom_ops::npu_format_cast(
        at::empty({count},a.options().dtype(dtype)),ACL_FORMAT_ND,std::nullopt,std::nullopt);
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND &&
        reinterpret_cast<uintptr_t>(t.data_ptr())%32==0,"buffer requires physical ND/32B");
    return t;
}
}
void prepare(const at::Tensor& a,const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    const c10::OptionalDeviceGuard guard(a.device());
    const Key key=check_inputs(a,x,s,n);
    std::lock_guard<std::mutex> lock(mutex());
    if(plans().find(key)!=plans().end()) return;
    auto tiling=raw_buffer(a,sizeof(DampCompactionProbe::Tiling),at::kByte);
    for(const auto& t:{a,x,s,n}) check_disjoint(tiling,t);
    auto stream=c10_npu::getCurrentNPUStream().stream(true);
    TORCH_CHECK(aclrtSynchronizeStream(stream)==ACL_SUCCESS,"cold prepare sync failed");
    const DampCompactionProbe::Tiling host{static_cast<uint32_t>(a.numel()),
        DampCompactionProbe::ABI_VERSION,{0,0,0,0,0,0}};
    TORCH_CHECK(aclrtMemcpy(tiling.mutable_data_ptr(),sizeof(host),&host,sizeof(host),
        ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"tiling H2D failed");
    plans().emplace(key,tiling); // no input/state cache, only immutable count/ABI
}
Outputs compact(const at::Tensor& a,const at::Tensor& x,const at::Tensor& s,const at::Tensor& n) {
    const c10::OptionalDeviceGuard guard(a.device());
    const Key key=check_inputs(a,x,s,n);
    at::Tensor tiling;
    {
        std::lock_guard<std::mutex> lock(mutex());
        const auto found=plans().find(key);
        TORCH_CHECK(found!=plans().end(),"explicit prepare required outside capture");
        tiling=found->second;
    }
    for(const auto& t:{a,x,s,n}) check_disjoint(tiling,t);
    std::array<at::Tensor,4> out;
    for(uint32_t i=0;i<4;++i) {
        out[i]=at_npu::native::custom_ops::npu_format_cast(
            at::full({a.numel()+16},DampCompactionProbe::GUARDS[i],a.options()),
            ACL_FORMAT_ND,std::nullopt,std::nullopt);
        check_tensor(out[i],a,"guarded output");
        for(const auto& t:{a,x,s,n,tiling}) check_disjoint(out[i],t);
        for(uint32_t j=0;j<i;++j) check_disjoint(out[i],out[j]);
    }
    auto stream=c10_npu::getCurrentNPUStream().stream(false);
    auto aclCall=[=]()->int {
        qwen36_damp_compaction_kernel<<<1,nullptr,stream>>>(
            (GM_ADDR)a.mutable_data_ptr(),(GM_ADDR)x.mutable_data_ptr(),
            (GM_ADDR)s.mutable_data_ptr(),(GM_ADDR)n.mutable_data_ptr(),
            (GM_ADDR)out[0].mutable_data_ptr(),(GM_ADDR)out[1].mutable_data_ptr(),
            (GM_ADDR)out[2].mutable_data_ptr(),(GM_ADDR)out[3].mutable_data_ptr(),
            (GM_ADDR)tiling.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36DampCompactionProbe",aclCall);
    return {out[0],out[1],out[2],out[3]};
}
}
