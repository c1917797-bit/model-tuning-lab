// SPDX-License-Identifier: Apache-2.0
// New selected-slot pack only; ASC queued current-stream launch.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
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
#include "../op_kernel/selected_prefill_kernel.asc"
#include "ops.h"
namespace damp_selected_prefill_extension {
namespace {
using Key=std::tuple<int32_t,int64_t,int64_t,int64_t,bool,
                     uintptr_t,uintptr_t,uintptr_t,int64_t,int64_t,int64_t>;
struct Resources {at::Tensor tiling,pk,pv,sr;};
std::map<Key,Resources>& cache(){static auto* p=new std::map<Key,Resources>();return *p;}
std::mutex& mutex(){static auto* p=new std::mutex();return *p;}
int64_t version(const at::Tensor& t){
    const auto& v=t.unsafeGetTensorImpl()->version_counter();
    return v.enabled()?int64_t(v.current_version()):-1;
}
std::pair<uintptr_t, uintptr_t> tensor_span(const at::Tensor& tensor)
{
    // Only contiguous physical ND tensors reach dispatch. Never infer disjoint
    // addresses from Tensor/Storage object identity: Mamba SoA shares storage.
    // Every view must be wholly contained in its actual backing byte interval.
    const int64_t elements = tensor.numel();
    const size_t itemBytes = tensor.element_size();
    const uintptr_t maximum = std::numeric_limits<uintptr_t>::max();
    TORCH_CHECK(elements > 0 && itemBytes > 0,
                "arena ABI requires nonempty positive-width tensors");
    TORCH_CHECK(static_cast<uint64_t>(elements) <=
                    maximum / static_cast<uint64_t>(itemBytes),
                "tensor byte-count multiplication overflow");
    const uintptr_t bytes = static_cast<uintptr_t>(elements) *
                            static_cast<uintptr_t>(itemBytes);
    const auto storage = tensor.storage();
    const uintptr_t base = reinterpret_cast<uintptr_t>(storage.data_ptr().get());
    const uint64_t backingBytes = static_cast<uint64_t>(storage.nbytes());
    TORCH_CHECK(base != 0 && backingBytes > 0 && backingBytes <= maximum - base,
                "backing storage byte range is empty/overflows");
    const uintptr_t storageEnd = base + static_cast<uintptr_t>(backingBytes);
    // storage_offset is in THIS view's elements, including dtype-reinterpreted
    // raw-cache views. Check its byte conversion, not the allocator's indices.
    const int64_t elementOffset = tensor.storage_offset();
    TORCH_CHECK(elementOffset >= 0 &&
                    static_cast<uint64_t>(elementOffset) <=
                        maximum / static_cast<uint64_t>(itemBytes),
                "tensor storage offset is negative/overflows byte conversion");
    const uintptr_t offsetBytes = static_cast<uintptr_t>(elementOffset) *
                                  static_cast<uintptr_t>(itemBytes);
    TORCH_CHECK(offsetBytes < backingBytes && offsetBytes <= maximum - base,
                "tensor storage offset lies outside its backing storage");
    const uintptr_t begin = reinterpret_cast<uintptr_t>(tensor.data_ptr());
    TORCH_CHECK(begin == base + offsetBytes,
                "tensor data pointer disagrees with storage offset/element width");
    TORCH_CHECK(begin >= base && begin < storageEnd && bytes <= storageEnd - begin,
                "tensor data interval lies outside its backing storage");
    return {begin, begin + bytes};
}

void check_disjoint(const at::Tensor& a, const at::Tensor& b)
{
    const auto sa = tensor_span(a), sb = tensor_span(b);
    TORCH_CHECK(sa.second <= sb.first || sb.second <= sa.first,
                "typed tensor DATA byte intervals overlap; shared backing storage alone is allowed");
}

void check(const at::Tensor& t,const at::Tensor& dense,at::ScalarType dtype,const char* n){
    TORCH_CHECK(t.is_privateuseone() && t.device()==dense.device(),n," same NPU required");
    TORCH_CHECK(t.scalar_type()==dtype && t.is_contiguous(),n," exact dtype/contiguous required");
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND,
                n," physical ND required");
    TORCH_CHECK(reinterpret_cast<uintptr_t>(t.data_ptr())%32==0,n," actual32B pointer required");
    (void)tensor_span(t);
}
Key checks(const at::Tensor& dense,const at::Tensor& high,const at::Tensor& low,
 const at::Tensor& scales,const at::Tensor& pk,const at::Tensor& pv,
 const at::Tensor& sr,const at::Tensor& indices,bool candidate){
    check(dense,dense,at::kFloat,"dense");
    TORCH_CHECK(dense.dim()==4 && dense.size(0)>=1 && dense.size(0)<=16 &&
      dense.size(1)==12 && dense.size(2)==128 && dense.size(3)==128,
      "transient native final state must be value-major FP32 [P1..16,12,128,128]");
    check(high,dense,at::kHalf,"high");check(low,dense,at::kChar,"low");
    check(scales,dense,at::kFloat,"scales");check(pk,dense,at::kInt,"pk");
    check(pv,dense,at::kInt,"pv");check(sr,dense,at::kFloat,"sr");
    check(indices,dense,at::kInt,"indices");
    TORCH_CHECK(high.dim()==4 && high.size(0)>0 && high.size(0)<=UINT32_MAX,
                "positive UINT32 slot count required");
    const int64_t s=high.size(0);
    TORCH_CHECK(high.sizes()==at::IntArrayRef({s,12,128,16}) &&
      low.sizes()==at::IntArrayRef({s,12,128,112}) &&
      scales.sizes()==at::IntArrayRef({s,12,4,112}),"typed SoA packed geometry required");
    TORCH_CHECK(pk.sizes()==at::IntArrayRef({12,128}) && pv.sizes()==pk.sizes() &&
      sr.sizes()==pk.sizes() && indices.sizes()==at::IntArrayRef({dense.size(0)}),
      "per-Hv INT32 logical pk/pv, original-V FP32 SR, ordered selected slot vector required");
    const at::Tensor* tensors[]={&dense,&high,&low,&scales,&pk,&pv,&sr,&indices};
    for(uint32_t i=0;i<8;++i)for(uint32_t j=0;j<i;++j)check_disjoint(*tensors[i],*tensors[j]);
    for(const at::Tensor* t:{&high,&low,&scales})
      TORCH_CHECK((tensor_span(*t).second-tensor_span(*t).first)%32==0,"writer length32B");
    const char* soc=aclrtGetSocName();
    TORCH_CHECK(soc && std::string(soc)=="Ascend910B4","unvalidated pack bound to Ascend910B4");
    int32_t device=-1;int64_t cores=0;
    TORCH_CHECK(aclrtGetDevice(&device)==ACL_SUCCESS &&
      aclrtGetDeviceInfo(device,ACL_DEV_ATTR_VECTOR_CORE_NUM,&cores)==ACL_SUCCESS &&
      cores>0,"actual NPU/core query failed");
    return {device,dense.size(0),s,cores,candidate,
            reinterpret_cast<uintptr_t>(pk.data_ptr()),reinterpret_cast<uintptr_t>(pv.data_ptr()),
            reinterpret_cast<uintptr_t>(sr.data_ptr()),version(pk),version(pv),version(sr)};
}
void plans_valid(const at::Tensor& pk,const at::Tensor& pv,const at::Tensor& sr){
    const auto kp=pk.to(at::kCPU),vp=pv.to(at::kCPU),cp=sr.to(at::kCPU);
    const auto* k=kp.data_ptr<int32_t>();const auto* v=vp.data_ptr<int32_t>();
    const auto* c=cp.data_ptr<float>();
    for(int32_t h=0;h<12;++h){
      bool seenK[128]={},seenV[128]={};
      for(int32_t i=0;i<128;++i){
        const int32_t a=k[h*128+i],b=v[h*128+i];
        TORCH_CHECK(a>=0 && a<128 && b>=0 && b<128 && !seenK[a] && !seenV[b],
                    "pk/pv each must be full0..127 permutation");
        seenK[a]=true;seenV[b]=true;
        TORCH_CHECK(std::isfinite(c[h*128+i]) && c[h*128+i]>0,
                    "original-coordinate SR finite positive FP32 required");
      }
    }
}
void lut(Qwen36DampSelectedPrefill::Tiling& t){
    for(uint32_t j=0;j<128;++j){
      const uint32_t safe=std::min<uint32_t>(j,126),a=2*safe+1;
      uint32_t length=0;for(uint32_t value=a;value;value>>=1)++length;
      const int32_t e=static_cast<int32_t>(length)-2;
      const uint32_t center=a<<(23-e);
      t.cTable[j]=static_cast<int32_t>((safe&1)?center-1:center+1);t.fTable[j]=e;
    }
}
at::Tensor nd(const at::Tensor& t){
    return at_npu::native::custom_ops::npu_format_cast(t,ACL_FORMAT_ND,std::nullopt,std::nullopt);
}
}
void prepare(const at::Tensor& dense,const at::Tensor& high,const at::Tensor& low,
 const at::Tensor& scales,const at::Tensor& pk,const at::Tensor& pv,
 const at::Tensor& sr,const at::Tensor& indices,bool candidate){
    const c10::OptionalDeviceGuard guard(dense.device());
    const Key key=checks(dense,high,low,scales,pk,pv,sr,indices,candidate);
    std::lock_guard<std::mutex> lock(mutex());
    if(cache().find(key)!=cache().end())return;
    plans_valid(pk,pv,sr); // cold only; no dense state or dynamic slot D2H
    Qwen36DampSelectedPrefill::Tiling t{};
    t.prefills=static_cast<uint32_t>(dense.size(0));t.stateSlots=static_cast<uint32_t>(high.size(0));
    t.vectorCoreNum=static_cast<uint32_t>(std::get<3>(key));t.abiVersion=1;
    t.useFloatCandidate=static_cast<uint32_t>(candidate);lut(t);
    auto tiling=nd(at::empty({int64_t(sizeof(t))},dense.options().dtype(at::kByte)));
    check(tiling,dense,at::kByte,"tiling");
    const at::Tensor* inputs[]={&dense,&high,&low,&scales,&pk,&pv,&sr,&indices};
    for(const at::Tensor* input:inputs)check_disjoint(tiling,*input);
    auto stream=c10_npu::getCurrentNPUStream().stream(true);
    TORCH_CHECK(aclrtSynchronizeStream(stream)==ACL_SUCCESS,"cold prepare sync failed");
    TORCH_CHECK(aclrtMemcpy(tiling.mutable_data_ptr(),sizeof(t),&t,sizeof(t),
                           ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"cold tiling H2D failed");
    cache().emplace(key,Resources{tiling,pk,pv,sr});
}
at::Tensor pack(const at::Tensor& dense,const at::Tensor& high,const at::Tensor& low,
 const at::Tensor& scales,const at::Tensor& pk,const at::Tensor& pv,
 const at::Tensor& sr,const at::Tensor& indices,bool candidate){
    const c10::OptionalDeviceGuard guard(dense.device());
    const Key key=checks(dense,high,low,scales,pk,pv,sr,indices,candidate);
    Resources r;
    {std::lock_guard<std::mutex> lock(mutex());auto p=cache().find(key);
     TORCH_CHECK(p!=cache().end(),"call cold prepare outside capture for actual P/S/plans first");
     r=p->second;}
    check(r.tiling,dense,at::kByte,"tiling");
    const at::Tensor* inputs[]={&dense,&high,&low,&scales,&pk,&pv,&sr,&indices,&r.tiling};
    for(uint32_t i=0;i<8;++i)check_disjoint(r.tiling,*inputs[i]);
    auto status=nd(at::full({dense.size(0)*12*8+16},int64_t(0x13579bdf),
                            dense.options().dtype(at::kInt)));
    check(status,dense,at::kInt,"guarded status");
    for(const at::Tensor* input:inputs)check_disjoint(status,*input);
    const uint32_t blocks=static_cast<uint32_t>(std::min<int64_t>(std::get<3>(key),dense.size(0)*12));
    auto stream=c10_npu::getCurrentNPUStream().stream(false);
    auto aclCall=[=]()->int{
      qwen36_damp_selected_prefill_pack_kernel<<<blocks,nullptr,stream>>>(
        (GM_ADDR)dense.mutable_data_ptr(),(GM_ADDR)high.mutable_data_ptr(),
        (GM_ADDR)low.mutable_data_ptr(),(GM_ADDR)scales.mutable_data_ptr(),
        (GM_ADDR)pk.mutable_data_ptr(),(GM_ADDR)pv.mutable_data_ptr(),(GM_ADDR)sr.mutable_data_ptr(),
        (GM_ADDR)indices.mutable_data_ptr(),
        (GM_ADDR)(static_cast<uint8_t*>(status.mutable_data_ptr())+32),
        (GM_ADDR)r.tiling.mutable_data_ptr());return 0;};
    at_npu::native::OpCommand::RunOpApi("Qwen36DampSelectedPrefillPackV1",aclCall);
    return status; // full prefix/tail32B guards retained, not silently sliced away
}
}
