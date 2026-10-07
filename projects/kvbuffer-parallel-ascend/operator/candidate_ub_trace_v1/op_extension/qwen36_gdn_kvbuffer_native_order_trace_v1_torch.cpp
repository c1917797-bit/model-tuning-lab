#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <mutex>
#include <tuple>
#include <vector>
#include "acl/acl.h"
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"
#include "torch_npu/csrc/aten/CustomFunctions.h"
#include "../op_kernel/qwen36_gdn_kvbuffer_native_order_trace_v1_kernel.asc"
#include "ops.h"

namespace ascend_kernel {
namespace {
constexpr int64_t KH=4,VH=12,D=128,CAP=16;
using Key=std::tuple<int32_t,int64_t,int64_t,int64_t>;
std::map<Key,at::Tensor>& cache(){ static auto* v=new std::map<Key,at::Tensor>();return *v; }
std::mutex& mutex(){static auto* v=new std::mutex();return *v;}
void check(const at::Tensor& t,const at::Tensor& q,at::ScalarType dtype,const char* name){
    TORCH_CHECK(t.is_privateuseone(),name," must be NPU");
    TORCH_CHECK(t.device()==q.device(),name," must share query device");
    TORCH_CHECK(t.is_contiguous(),name," must be contiguous");
    TORCH_CHECK(at_npu::native::custom_ops::get_npu_format(t)==ACL_FORMAT_ND,
                name," must have physical ND storage; contiguous is insufficient");
    TORCH_CHECK(t.scalar_type()==dtype,name," dtype mismatch");
}
void geometry(const at::Tensor& q,const at::Tensor& base){
    check(q,q,at::kBFloat16,"query");check(base,q,at::kFloat,"base_state");
    TORCH_CHECK(q.dim()==3 && q.size(1)==KH && q.size(2)==D && q.size(0)>0 && q.size(0)<=16,
                "query must be [T,4,128],1<=T<=16");
    TORCH_CHECK(base.dim()==4 && base.size(0)>0 && base.size(1)==VH &&
                base.size(2)==D && base.size(3)==D,"base must be [S,12,128,128]");
}
Key get_key(const at::Tensor& q,const at::Tensor& base){
    int32_t dev=-1;int64_t cores=0;
    TORCH_CHECK(aclrtGetDevice(&dev)==ACL_SUCCESS,"aclrtGetDevice failed");
    TORCH_CHECK(aclrtGetDeviceInfo(dev,ACL_DEV_ATTR_VECTOR_CORE_NUM,&cores)==ACL_SUCCESS &&
                cores>0,"vector core count unavailable");
    return Key{dev,q.size(0),base.size(0),cores};
}
void disjoint(const std::vector<at::Tensor>& all,const std::vector<size_t>& mut){
    for(size_t m:mut) for(size_t j=0;j<all.size();++j){
        if(m==j)continue;
        uintptr_t a=reinterpret_cast<uintptr_t>(all[m].data_ptr()),
                  b=reinterpret_cast<uintptr_t>(all[j].data_ptr());
        uintptr_t ae=a+all[m].numel()*all[m].element_size(),
                  be=b+all[j].numel()*all[j].element_size();
        TORCH_CHECK(ae<=b || be<=a,"mutable storage ranges overlap");
    }
}
} // namespace

void qwen36_gdn_kvbuffer_native_order_trace_v1_prepare(const at::Tensor& q,const at::Tensor& base){
    const c10::OptionalDeviceGuard guard(q.device());geometry(q,base);
    const Key key=get_key(q,base);
    std::lock_guard<std::mutex> lock(mutex());if(cache().count(key))return;
    Qwen36KVBufferNativeOrderTraceV1::KVBufferTilingData data{
        static_cast<uint32_t>(q.size(0)),static_cast<uint32_t>(base.size(0)),
        static_cast<uint32_t>(std::get<3>(key)),32,1.0f/std::sqrt(128.0f)};
    auto t=at::empty({static_cast<int64_t>(sizeof(data))},q.options().dtype(at::kByte));
    check(t,q,at::kByte,"tiling");
    TORCH_CHECK(aclrtMemcpy(t.mutable_data_ptr(),sizeof(data),&data,sizeof(data),
                           ACL_MEMCPY_HOST_TO_DEVICE)==ACL_SUCCESS,"tiling upload failed");
    cache().emplace(key,t); // prepare is explicitly outside capture
}

at::Tensor qwen36_gdn_kvbuffer_native_order_trace_v1_decode_trace(
    const at::Tensor& q,const at::Tensor& k,const at::Tensor& v,
    const at::Tensor& g,const at::Tensor& beta,const at::Tensor& base,
    const at::Tensor& kl,const at::Tensor& ul,const at::Tensor& lam,
    const at::Tensor& decay,const at::Tensor& len,const at::Tensor& seq,
    const at::Tensor& idx,const at::Tensor& traceStates,
    const at::Tensor& traceOutput,const at::Tensor& traceMeta){
    const c10::OptionalDeviceGuard guard(q.device());geometry(q,base);
    check(k,q,at::kBFloat16,"key");check(v,q,at::kBFloat16,"value");
    check(g,q,at::kFloat,"g");check(beta,q,at::kBFloat16,"beta");
    check(kl,q,at::kBFloat16,"k_log");check(ul,q,at::kFloat,"u_log");
    check(lam,q,at::kFloat,"lambda_log");check(decay,q,at::kFloat,"cumulative_decay");
    check(len,q,at::kInt,"log_length");check(seq,q,at::kInt,"actual_seq_lengths");
    check(idx,q,at::kInt,"state_indices");
    check(traceStates,q,at::kFloat,"trace_states");check(traceOutput,q,at::kFloat,"trace_output");
    check(traceMeta,q,at::kInt,"trace_meta");
    TORCH_CHECK(traceStates.sizes()==at::IntArrayRef({3,32,128}) &&
                traceOutput.sizes()==at::IntArrayRef({32}) &&
                traceMeta.sizes()==at::IntArrayRef({16}),"bounded exact trace geometry");
    int64_t T=q.size(0),S=base.size(0);
    TORCH_CHECK(T==16 && S==19,"diagnostic fixture is exactly T16/S19");
    TORCH_CHECK(k.sizes()==q.sizes(),"key geometry");
    TORCH_CHECK(v.sizes()==at::IntArrayRef({T,VH,D}),"value geometry");
    TORCH_CHECK(g.sizes()==at::IntArrayRef({T,VH}) && beta.sizes()==g.sizes(),"g/beta geometry");
    TORCH_CHECK(kl.sizes()==at::IntArrayRef({S,KH,CAP,D}),"k_log geometry");
    TORCH_CHECK(ul.sizes()==at::IntArrayRef({S,VH,CAP,D}),"u_log geometry");
    TORCH_CHECK(lam.sizes()==at::IntArrayRef({S,VH,32}) &&
                decay.sizes()==lam.sizes() && len.sizes()==lam.sizes(),"metadata geometry");
    TORCH_CHECK(seq.dim()==1 && seq.numel()==T+1 && idx.dim()==1 && idx.numel()==T,
                "decode lengths ABI is [initial_offset,per_sequence_lengths]; T+1 required");
    // Values and unique live slots are admitted from CPU scheduling mirrors;
    // this wrapper never .cpu()/.item() or uploads tiling during graph replay.
    disjoint({q,k,v,g,beta,base,kl,ul,lam,decay,len,seq,idx,traceStates,traceOutput,traceMeta},
             {5,6,7,8,9,10,13,14,15});
    Key key=get_key(q,base);at::Tensor tiling;
    {std::lock_guard<std::mutex> lock(mutex());auto it=cache().find(key);
     TORCH_CHECK(it!=cache().end(),"cold geometry: call prepare outside capture");tiling=it->second;}
    auto out=at::empty({T,VH,D},q.options());check(out,q,at::kBFloat16,"out");
    uint32_t blocks=static_cast<uint32_t>(std::min<int64_t>(std::get<3>(key),T*VH));
    auto stream=c10_npu::getCurrentNPUStream().stream(false);
    auto call=[=]()->int{
        qwen36_gdn_kvbuffer_native_order_trace_v1_kernel<<<blocks,nullptr,stream>>>(
            (GM_ADDR)q.mutable_data_ptr(),(GM_ADDR)k.mutable_data_ptr(),(GM_ADDR)v.mutable_data_ptr(),
            (GM_ADDR)g.mutable_data_ptr(),(GM_ADDR)beta.mutable_data_ptr(),(GM_ADDR)base.mutable_data_ptr(),
            (GM_ADDR)kl.mutable_data_ptr(),(GM_ADDR)ul.mutable_data_ptr(),(GM_ADDR)lam.mutable_data_ptr(),
            (GM_ADDR)decay.mutable_data_ptr(),(GM_ADDR)len.mutable_data_ptr(),(GM_ADDR)seq.mutable_data_ptr(),
            (GM_ADDR)idx.mutable_data_ptr(),(GM_ADDR)out.mutable_data_ptr(),
            (GM_ADDR)traceStates.mutable_data_ptr(),(GM_ADDR)traceOutput.mutable_data_ptr(),
            (GM_ADDR)traceMeta.mutable_data_ptr(),(GM_ADDR)tiling.mutable_data_ptr());
        return 0;
    };
    at_npu::native::OpCommand::RunOpApi("Qwen36GdnKVBufferNativeOrderTraceV1",call);
    return out;
}
} // namespace ascend_kernel
