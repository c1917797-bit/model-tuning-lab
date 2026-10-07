#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <map>
#include <mutex>
#include <vector>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "tiling/platform/platform_ascendc.h"
#include "../op_kernel/qwen36_native_recurrent_copy_trace_v2_kernel.asc"
#include "native_tiling.h"
#include "ops.h"

namespace ascend_kernel {
namespace {
using Data=NativeRecurrentCopyTraceV2::NativeRecurrentCopyTraceV2TilingData;
struct Entry { at::Tensor tiling; Data data; std::array<uint8_t,72> bytes; };
std::map<int32_t,Entry>& cache(){static auto* m=new std::map<int32_t,Entry>();return *m;}
std::mutex& mutex(){static auto* m=new std::mutex();return *m;}
void check(const at::Tensor& t,const at::Tensor& q,at::ScalarType dtype,const char* name){
 TORCH_CHECK(t.is_privateuseone() && t.device()==q.device(),name," requires same NPU");
 TORCH_CHECK(t.is_contiguous() && at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND,
             name," requires actual contiguous ND storage");
 TORCH_CHECK(t.scalar_type()==dtype,name," dtype mismatch");
 const auto pointer=reinterpret_cast<uintptr_t>(t.data_ptr());
 const auto bytes=static_cast<uint64_t>(t.numel())*t.element_size();
 const auto offset=static_cast<uint64_t>(t.storage_offset())*t.element_size();
 TORCH_CHECK(pointer%32==0 && bytes<=std::numeric_limits<uintptr_t>::max()-pointer,
             name," alignment/range");
 TORCH_CHECK(offset<=t.storage().nbytes() && bytes<=t.storage().nbytes()-offset,
             name," storage bound");
}
void geometry(const at::Tensor& q,const at::Tensor& s){
 check(q,q,at::kBFloat16,"query");check(s,q,at::kFloat,"state");
 TORCH_CHECK(q.sizes()==at::IntArrayRef({16,4,128}) &&
             s.sizes()==at::IntArrayRef({19,12,128,128}),"exact saved T16/S19 fixture");
}
int32_t device(){
 int32_t dev=-1;TORCH_CHECK(aclrtGetDevice(&dev)==ACL_SUCCESS && dev>=0,"actual ACL device");
 return dev;
}
Entry prepared(){
 std::lock_guard<std::mutex> lock(mutex());auto it=cache().find(device());
 TORCH_CHECK(it!=cache().end(),"cold fixture: call prepare outside capture");
 return it->second;
}
void disjoint(const std::vector<at::Tensor>& all){
 for(size_t m:{size_t(5),size_t(8),size_t(9),size_t(10)})
  for(size_t j=0;j<all.size();++j){
   if(m==j)continue;
   uintptr_t a=reinterpret_cast<uintptr_t>(all[m].data_ptr()),
             b=reinterpret_cast<uintptr_t>(all[j].data_ptr());
   TORCH_CHECK(a+all[m].numel()*all[m].element_size()<=b ||
               b+all[j].numel()*all[j].element_size()<=a,"mutable storage ranges overlap");
  }
}
}
void qwen36_native_recurrent_copy_trace_v2_prepare(const at::Tensor& q,const at::Tensor& s){
 const c10::OptionalDeviceGuard guard(q.device());geometry(q,s);int32_t dev=device();
 std::lock_guard<std::mutex> lock(mutex());if(cache().count(dev))return;
 auto* platform=platform_ascendc::PlatformAscendCManager::GetInstance();
 TORCH_CHECK(platform && platform->GetSocVersion()==platform_ascendc::SocVersion::ASCEND910B,
             "only actual dav-2201/910B platform");
 uint64_t ub=0;platform->GetCoreMemSize(platform_ascendc::CoreMemType::UB,ub);
 uint32_t cores=platform->GetCoreNumAiv();int64_t actualCores=0;
 TORCH_CHECK(aclrtGetDeviceInfo(dev,ACL_DEV_ATTR_VECTOR_CORE_NUM,&actualCores)==ACL_SUCCESS &&
             actualCores==cores && cores>0 && ub>0 && ub<=UINT32_MAX,"actual UB/core identity");
 Data data=NativeRecurrentCopyTraceV2::make_tiling(ub,cores,1.0f/std::sqrt(128.0f));
 static_assert(offsetof(Data,hasAcceptedTokens)+sizeof(uint32_t)==68,"native field layout");
 std::array<uint8_t,72> bytes{};std::memcpy(bytes.data(),&data,68); // deterministic tail padding
 auto tiling=at::empty({72},q.options().dtype(at::kByte));check(tiling,q,at::kByte,"tiling");
 TORCH_CHECK(aclrtMemcpy(tiling.mutable_data_ptr(),72,bytes.data(),72,
                         ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"tiling upload");
 cache().emplace(dev,Entry{tiling,data,bytes}); // explicitly outside capture
}
at::Tensor qwen36_native_recurrent_copy_trace_v2_tiling_info(const at::Tensor& q,const at::Tensor& s){
 const c10::OptionalDeviceGuard guard(q.device());geometry(q,s);auto entry=prepared();
 auto result=at::empty({72},at::TensorOptions().dtype(at::kByte).device(at::kCPU));
 std::memcpy(result.mutable_data_ptr(),entry.bytes.data(),72);return result;
}
at::Tensor qwen36_native_recurrent_copy_trace_v2_decode_trace(
 const at::Tensor& q,const at::Tensor& k,const at::Tensor& v,const at::Tensor& g,
 const at::Tensor& beta,const at::Tensor& s,const at::Tensor& seq,const at::Tensor& idx,
 const at::Tensor& precast,const at::Tensor& selected){
 const c10::OptionalDeviceGuard guard(q.device());geometry(q,s);
 check(k,q,at::kBFloat16,"key");check(v,q,at::kBFloat16,"value");
 check(g,q,at::kFloat,"g");check(beta,q,at::kBFloat16,"beta");
 check(seq,q,at::kInt,"actual_seq_lengths");check(idx,q,at::kInt,"state_indices");
 check(precast,q,at::kFloat,"precast_trace");check(selected,q,at::kFloat,"selected_state_trace");
 TORCH_CHECK(k.sizes()==q.sizes() && v.sizes()==at::IntArrayRef({16,12,128}) &&
             g.sizes()==at::IntArrayRef({16,12}) && beta.sizes()==g.sizes(),"input geometry");
 TORCH_CHECK(seq.sizes()==at::IntArrayRef({17}) && idx.sizes()==at::IntArrayRef({16}),
             "native lengths: initial offset plus 16 per-sequence lengths");
 TORCH_CHECK(precast.sizes()==at::IntArrayRef({16,12,128}) &&
             selected.sizes()==at::IntArrayRef({16,12,128,128}),"trace geometry");
 // CPU scheduling mirrors admit seq=[0]+[1]*12+[0]*4 and unique active indices.
 // No tensor values or tiling are copied to/from the host during replay.
 auto entry=prepared();auto out=at::empty({16,12,128},q.options());check(out,q,at::kBFloat16,"out");
 disjoint({q,k,v,g,beta,s,seq,idx,precast,selected,out,entry.tiling});
 auto stream=c10_npu::getCurrentNPUStream().stream(false);
 auto call=[=]()->int{
  qwen36_native_recurrent_copy_trace_v2_kernel<<<entry.data.vectorCoreNum,nullptr,stream>>>(
   (GM_ADDR)q.mutable_data_ptr(),(GM_ADDR)k.mutable_data_ptr(),(GM_ADDR)v.mutable_data_ptr(),
   (GM_ADDR)g.mutable_data_ptr(),(GM_ADDR)beta.mutable_data_ptr(),(GM_ADDR)s.mutable_data_ptr(),
   (GM_ADDR)seq.mutable_data_ptr(),(GM_ADDR)idx.mutable_data_ptr(),(GM_ADDR)out.mutable_data_ptr(),
   (GM_ADDR)precast.mutable_data_ptr(),(GM_ADDR)selected.mutable_data_ptr(),
   (GM_ADDR)entry.tiling.mutable_data_ptr());
  return 0;
 };
 at_npu::native::OpCommand::RunOpApi("Qwen36NativeRecurrentCopyTraceV2",call);return out;
}
}
