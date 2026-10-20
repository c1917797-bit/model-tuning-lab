"""Finite native BF16 ABI -> exact FP32 canonical input, never clean logits."""
import inspect
def need(v,m):
 if not v:raise ValueError(m)
def validate_sources(C,m,model):
 r=m['runtime_sources'];lp=model.logits_processor;head=model.lm_head;q=head.quant_method
 expected=(('AscendLogitsProcessor',lp,'_get_logits',r['ascend_vocab']),('AscendLogitsProcessor',lp,'_get_logits_normal',r['ascend_vocab']),('UnquantizedEmbeddingMethod',q,'apply',r['vocab_parallel']))
 for name,obj,key,ref in expected:
  C.checked(ref);fn=getattr(obj,key);body=getattr(fn,'__func__',None)
  need(type(obj).__name__==name and getattr(fn,'__self__',None)is obj and body is getattr(type(obj),key)and body.__globals__.get(name)is type(obj)and C.ref(inspect.getsourcefile(body))==ref,'exact active native logits/quantization class, receiver, method, source')
 C.checked(r['logits_processor']);forward=lp.forward;body=getattr(forward,'__func__',None)
 base=body.__globals__.get('LogitsProcessor')if body is not None else None
 need(isinstance(base,type)and base in type(lp).__mro__ and body is base.__dict__.get('forward')and getattr(forward,'__self__',None)is lp and C.ref(inspect.getsourcefile(body))==r['logits_processor'],'actual unchanged base logits forward receiver, MRO method, and source')
 need(type(head).__name__=='AscendParallelLMHead'and C.ref(inspect.getsourcefile(type(head)))==r['ascend_vocab'],'actual native LM head source')
 return True
def promote(t,value):
 need(value.ndim==2 and value.dtype in(t.bfloat16,t.float32),'only actual finite BF16 or FP32 native logits ABI')
 need(bool(t.isfinite(value).all().item()),'all original native logits finite; no padding/NaN/Inf exemption')
 if value.dtype==t.float32:return value
 bits=value.view(t.int16).clone();out=value.to(dtype=t.float32)
 need(t.equal(out.to(dtype=t.bfloat16).view(t.int16),bits)and t.equal(value.view(t.int16),bits),'BF16 to FP32 exact bitwise roundtrip and unchanged native operand')
 return out
