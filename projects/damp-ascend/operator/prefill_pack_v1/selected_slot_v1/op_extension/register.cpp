// SPDX-License-Identifier: Apache-2.0
#include <cstdint>
#include <torch/extension.h>
#include <torch/library.h>
#include "ops.h"
namespace {
void meta(const at::Tensor& d,const at::Tensor& hi,const at::Tensor& lo,const at::Tensor& s,
 const at::Tensor& pk,const at::Tensor& pv,const at::Tensor& sr,const at::Tensor& ix){
 const at::Tensor* tensors[]={&d,&hi,&lo,&s,&pk,&pv,&sr,&ix};
 for(const at::Tensor* t:tensors)
   TORCH_CHECK(t->device().is_meta() && t->is_contiguous() &&
     (t->storage_offset()*int64_t(t->element_size()))%32==0,"Meta contiguous32B-offset tensors");
 TORCH_CHECK(d.scalar_type()==at::kFloat && d.dim()==4 && d.size(0)>=1 && d.size(0)<=16 &&
     d.size(1)==12 && d.size(2)==128 && d.size(3)==128,"Meta transient value-major dense P1..16");
 TORCH_CHECK(hi.dim()==4 && hi.size(0)>0 && hi.size(0)<=UINT32_MAX,"Meta S");
 const int64_t p=d.size(0),n=hi.size(0);
 TORCH_CHECK(hi.scalar_type()==at::kHalf && lo.scalar_type()==at::kChar && s.scalar_type()==at::kFloat &&
     hi.sizes()==at::IntArrayRef({n,12,128,16}) &&
     lo.sizes()==at::IntArrayRef({n,12,128,112}) &&
     s.sizes()==at::IntArrayRef({n,12,4,112}),"Meta packed geometry/dtypes");
 TORCH_CHECK(pk.scalar_type()==at::kInt && pv.scalar_type()==at::kInt &&
     sr.scalar_type()==at::kFloat && ix.scalar_type()==at::kInt &&
     pk.sizes()==at::IntArrayRef({12,128}) && pv.sizes()==pk.sizes() &&
     sr.sizes()==pk.sizes() && ix.sizes()==at::IntArrayRef({p}),"Meta static-plan/selection ABI");
}
void prepare_meta(const at::Tensor& d,const at::Tensor& h,const at::Tensor& l,const at::Tensor& s,
 const at::Tensor& k,const at::Tensor& v,const at::Tensor& c,const at::Tensor& i,bool candidate)
 {meta(d,h,l,s,k,v,c,i);}
at::Tensor pack_meta(const at::Tensor& d,const at::Tensor& h,const at::Tensor& l,const at::Tensor& s,
 const at::Tensor& k,const at::Tensor& v,const at::Tensor& c,const at::Tensor& i,bool candidate)
 {meta(d,h,l,s,k,v,c,i);return at::empty({d.size(0)*12*8+16},d.options().dtype(at::kInt));}
TORCH_LIBRARY_FRAGMENT(qwen36_damp_selected_prefill_v1,m){
 m.def("prepare(Tensor dense, Tensor hi, Tensor lo, Tensor scales, Tensor pk, Tensor pv, Tensor sr, "
       "Tensor indices, bool use_float_candidate=False) -> ()");
 m.def("pack(Tensor dense, Tensor(a!) hi, Tensor(b!) lo, Tensor(c!) scales, Tensor pk, Tensor pv, Tensor sr, "
       "Tensor indices, bool use_float_candidate=False) -> Tensor");
}
TORCH_LIBRARY_IMPL(qwen36_damp_selected_prefill_v1,PrivateUse1,m){
 m.impl("prepare",TORCH_FN(damp_selected_prefill_extension::prepare));
 m.impl("pack",TORCH_FN(damp_selected_prefill_extension::pack));
}
TORCH_LIBRARY_IMPL(qwen36_damp_selected_prefill_v1,Meta,m){
 m.impl("prepare",&prepare_meta);m.impl("pack",&pack_meta);
}
}
