#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"
namespace {
void geometry(const at::Tensor& q,const at::Tensor& s){
 TORCH_CHECK(q.scalar_type()==at::kBFloat16 && q.sizes()==at::IntArrayRef({16,4,128}),
             "Meta query BF16 T16/H4/D128");
 TORCH_CHECK(s.scalar_type()==at::kFloat && s.sizes()==at::IntArrayRef({19,12,128,128}),
             "Meta state FP32 S19/H12/V128/K128");
 TORCH_CHECK(q.is_contiguous() && s.is_contiguous(),"Meta contiguous geometry");
}
void prepare_meta(const at::Tensor& q,const at::Tensor& s){geometry(q,s);}
at::Tensor tiling_meta(const at::Tensor& q,const at::Tensor& s){
 geometry(q,s);return at::empty({72},q.options().dtype(at::kByte));
}
at::Tensor decode_meta(const at::Tensor& q,const at::Tensor& k,const at::Tensor& v,
 const at::Tensor& g,const at::Tensor& beta,const at::Tensor& s,
 const at::Tensor& seq,const at::Tensor& idx,const at::Tensor& precast,const at::Tensor& selected){
 geometry(q,s);
 TORCH_CHECK(k.scalar_type()==at::kBFloat16 && k.sizes()==q.sizes(),"Meta key");
 TORCH_CHECK(v.scalar_type()==at::kBFloat16 && v.sizes()==at::IntArrayRef({16,12,128}),"Meta value");
 TORCH_CHECK(g.scalar_type()==at::kFloat && g.sizes()==at::IntArrayRef({16,12}) &&
             beta.scalar_type()==at::kBFloat16 && beta.sizes()==g.sizes(),"Meta g/beta");
 TORCH_CHECK(seq.scalar_type()==at::kInt && seq.sizes()==at::IntArrayRef({17}) &&
             idx.scalar_type()==at::kInt && idx.sizes()==at::IntArrayRef({16}),"Meta native seq/idx");
 TORCH_CHECK(precast.scalar_type()==at::kFloat && precast.sizes()==at::IntArrayRef({16,12,128}) &&
             selected.scalar_type()==at::kFloat && selected.sizes()==at::IntArrayRef({16,12,128,128}),
             "Meta trace buffers");
 for(const auto& t:{k,v,g,beta,seq,idx,precast,selected})
  TORCH_CHECK(t.is_contiguous(),"Meta contiguous arguments");
 return at::empty({16,12,128},q.options());
}
TORCH_LIBRARY_FRAGMENT(qwen36_native_recurrent_copy_trace_v2,m){
 m.def("prepare(Tensor query, Tensor state) -> ()");
 m.def("tiling_info(Tensor query, Tensor state) -> Tensor");
 m.def("decode_trace(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, "
       "Tensor(a!) state, Tensor actual_seq_lengths, Tensor state_indices, "
       "Tensor(b!) precast_trace, Tensor(c!) selected_state_trace) -> Tensor");
}
TORCH_LIBRARY_IMPL(qwen36_native_recurrent_copy_trace_v2,PrivateUse1,m){
 m.impl("prepare",TORCH_FN(ascend_kernel::qwen36_native_recurrent_copy_trace_v2_prepare));
 m.impl("tiling_info",TORCH_FN(ascend_kernel::qwen36_native_recurrent_copy_trace_v2_tiling_info));
 m.impl("decode_trace",TORCH_FN(ascend_kernel::qwen36_native_recurrent_copy_trace_v2_decode_trace));
}
TORCH_LIBRARY_IMPL(qwen36_native_recurrent_copy_trace_v2,Meta,m){
 m.impl("prepare",&prepare_meta);m.impl("tiling_info",&tiling_meta);m.impl("decode_trace",&decode_meta);
}
}
