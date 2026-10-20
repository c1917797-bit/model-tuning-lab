"""Opt-in TREE-only FIA precision boundary; mathematical reference is unchanged."""
from sourceio import need,ref
class FiaBoundary:
    def __init__(self,t,delegate,trial):
        self.t=t;self.delegate=delegate
        need("fp16_boundary" not in trial,"one immutable boundary receipt per trial")
        self.record=dict(source=ref(__file__),completed=False,input_dtype="torch.float16",
                         output_dtype="torch.bfloat16",cast={})
        trial["fp16_boundary"]=self.record
    def npu_fused_infer_attention_score(self,**kwargs):
        t=self.t;need(not self.record["completed"],"boundary call cannot repeat")
        q,k,v=(kwargs[x] for x in ("query","key","value"))
        need(q.shape==(1,6,3,256) and k.shape==v.shape==(2,1,128,256),"exact C1 three-node Q6/KV1/D256 boundary")
        need(q.dtype==k.dtype==v.dtype==t.bfloat16,"original boundary input BF16")
        need(kwargs["input_layout"]=="BNSD" and kwargs["block_size"]==128 and
             kwargs["actual_seq_lengths"]==[3] and kwargs["actual_seq_lengths_kv"]==[134] and
             kwargs["num_heads"]==6 and kwargs["num_key_value_heads"]==1 and kwargs["scale"]==256**-.5 and
             kwargs["sparse_mode"]==1 and kwargs["pre_tokens"]==kwargs["next_tokens"]==2147483647 and
             kwargs["inner_precise"]==2,"unchanged registered paged FIA arguments")
        converted=dict(kwargs);before={}
        for key in ("query","key","value"):
            original=kwargs[key]
            need(bool(t.isfinite(original).all()),"finite original QKV")
            value=original.to(t.float16)
            need(bool(t.isfinite(value).all()),"finite FP16 conversion")
            delta=(value.double()-original.double()).abs()
            self.record["cast"][key]=dict(changed=int((delta!=0).sum()),elements=delta.numel(),peak_abs=float(delta.max()))
            converted[key]=value;before[key]=value.clone()
        result=self.delegate.npu_fused_infer_attention_score(**converted)
        for key,value in before.items():
            need(t.equal(converted[key].contiguous().view(t.uint8),value.contiguous().view(t.uint8)),
                 "FIA preserves converted inputs")
        need(isinstance(result,(tuple,list)) and len(result)==2 and result[0].dtype==t.float16 and
             result[0].shape==(1,6,3,256) and bool(t.isfinite(result[0]).all()),"actual finite FP16 FIA output")
        output=result[0].to(t.bfloat16)
        need(bool(t.isfinite(output).all()),"finite BF16 output boundary")
        self.record["completed"]=True
        return output,result[1]
