"""Owned instance monkeypatch at source-qualified native FA forward_impl.
B1 eager diagnostic only: native prefill and reshape/cache write unchanged;
actual decode compute invokes compiled SKVQ. No global class surgery or fake worker.
"""
import hashlib,inspect,json,sys,types
from pathlib import Path
import contract as C
from runtime_cache import Cache
BACKEND_SHA="80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
def call_raw(q,k,v):
    def desc(x):
        storage=x.untyped_storage()
        return dict(shape=list(x.shape),stride=list(x.stride()),dtype=str(x.dtype),device=str(x.device),
          data_ptr=x.data_ptr(),storage_data_ptr=storage.data_ptr(),storage_nbytes=storage.nbytes(),
          storage_offset=x.storage_offset())
    return {n:desc(x)for n,x in(("Q",q),("K",k),("V",v))}
class Session:
    def __init__(self,worker,registry,layouts,reader,torch,layout_module,device_writer,*,
                 source_ref,rank_identity,reader_whole_ref,bind_native_request,publish_frame,publish_prefill,consume_native_finish):
        C.reader_whole(reader_whole_ref)
        C.need(type(registry)is dict and set(registry)=={"model.layers."+str(i)+".self_attn"for i in range(3,64,4)},
          "all16 current actual FA owner pairs")
        C.need(callable(bind_native_request)and callable(publish_frame)and callable(publish_prefill)and callable(consume_native_finish),
          "actual source-qualified native request/raw/finish callbacks required; no guessed ID")
        self.worker=worker;self.registry=registry;self.source=source_ref;self.rank_identity=rank_identity
        self.bind_request=bind_native_request;self.publish=publish_frame;self.prefill_raw=publish_prefill;self.consume_finish=consume_native_finish
        self.reader=reader;self.torch=torch;self.caches={};self.patches=[];self.closed=False;self.poisoned=False
        self.events=[];self.original_calls=0;self.candidate_calls=0
        self.layout_module=layout_module;self.device_writer=device_writer;self.layouts=layouts
        # The existing source-qualified registry identifies all48 GDN separately.
        self.gdn=tuple((x.linear_attn,id(x.linear_attn),x.linear_attn.forward.__func__)for x in worker.get_model().language_model.model.layers
          if getattr(x,"layer_type",None)=="linear_attention")
        C.need(len(self.gdn)==48,"all48 GDN layers remain native")
    def install(self):
        backend=sys.modules.get("vllm_ascend.attention.attention_v1")
        C.need(backend is not None and C.ref(backend.__file__)["sha256"]==BACKEND_SHA,"exact deployed backend source")
        for logical,(outer,child)in self.registry.items():
            impl=child.impl
            C.need(type(impl)is backend.AscendAttentionBackendImpl and outer.attn is child and
              "forward_impl"not in impl.__dict__ and "reshape_and_cache"not in impl.__dict__,
              "actual disjoint original instance; no overlapping/foreign patch")
            forward=impl.forward_impl;reshape=impl.reshape_and_cache
            C.need(forward.__func__ is backend.AscendAttentionBackendImpl.forward_impl and
              reshape.__func__ is backend.AscendAttentionBackendImpl.reshape_and_cache,"exact original compute/write functions")
            pending={}
            def factory(name,old_forward,old_reshape,p):
                def cache_write(instance,q,k,v,cache,md,out):
                    C.need(not self.closed and not self.poisoned,"owned live session")
                    bound=self.bind_request(self.worker,name,md,q,k,v)
                    C.need(bound["source_ref"]==self.source and bound["rank_identity"]==self.rank_identity and
                      bound["phase"]in("prefill","decode")and bound["graph_mode"]=="NONE"and
                      type(bound["request_id"])is str and bound["request_id"]and type(bound["epoch"])is int,
                      "real source-bound scheduler/assigned request/epoch/eager binding")
                    C.need(not p,"one native cache write before corresponding FA compute")
                    p.update(q=q,k=k,v=v,binding=bound,pre_call_descriptors=call_raw(q,k,v))
                    return old_reshape(q,k,v,cache,md,out)
                def compute(instance,q,k,v,cache,md,out):
                    C.need(p and p["q"]is q and p["k"]is k and p["v"]is v,"same actual native reshape->compute tensors")
                    bound=p["binding"];request=bound["request_id"];phase=bound["phase"]
                    try:
                        if phase=="prefill":
                            C.need(md.attn_state.name=="PrefillNoCache"and md.num_prefills==1 and
                              md.num_decodes==0 and md.seq_lens_list==[32768]and
                              md.actual_seq_lengths_q==[32768]and tuple(q.shape)==(32768,6,256),
                              "one true full32768 native prefill, not shortened/mixed/chunk dummy")
                            self.prefill_raw(name,bound,p["pre_call_descriptors"],q,k,v)
                            result=old_forward(q,k,v,cache,md,out);self.original_calls+=1
                            C.need(name not in self.caches,"one new native request per diagnostic layer")
                            c=Cache(self.torch,self.layout_module,self.device_writer,self.layouts[name],bits=2,
                              capacity=33792,dtype=q.dtype,device=q.device)
                            c.prefill(request,k,v);self.caches[name]=c
                        else:
                            C.need(md.attn_state.name=="DecodeOnly"and md.num_decodes==1 and md.num_prefills==0 and
                              md.seq_lens_list in([32769],[32770])and tuple(q.shape)==(1,6,256),"actual first/second decode only")
                            c=self.caches[name];c.append(request,k,v)
                            C.need(c.epoch==bound["epoch"]and c.length==md.seq_lens_list[0],"actual owner/control history")
                            epoch=c.epoch
                            result,scores,probs=self.reader(q,c.pool,c.controls,bits=2,capacity=33792,
                              assert_live=lambda:c.assert_live(request,epoch))
                            out.copy_(result.reshape_as(out));result=out;self.candidate_calls+=1
                            row=self.publish(name,bound,p["pre_call_descriptors"],q,k,v,c,scores,probs,result)
                            C.obj(row);self.events.append(row)
                        return result
                    except BaseException:self.poisoned=True;raise
                    finally:p.clear()
                return cache_write,compute
            f1,f2=factory(logical,forward,reshape,pending)
            for name,fn,original in(("reshape_and_cache",f1,reshape),("forward_impl",f2,forward)):
                value=types.MethodType(fn,impl);impl.__dict__[name]=value
                self.patches.append((impl,name,value,original))
        return dict(rank_identity=self.rank_identity,source_ref=self.source,actual_instance_hooks=32,
          preserves_native_prefill_and_cache_write=True,compiled_decode_enabled=True,**C.scopes())
    def finish(self,actual_finished_ref):
        C.need(not self.closed and not self.poisoned and self.original_calls==16 and self.candidate_calls==32 and len(self.events)==32,
          "all16 native prefill/two compiled decode steps; no finite-only promotion")
        self.consume_finish(actual_finished_ref,self.worker,self.caches,self.rank_identity)
        for c in self.caches.values():c.finish(c.request,c.epoch)
        self.restore()
        return dict(schema="skvq.compiled-reader.worker-final/v1",source_ref=self.source,rank_identity=self.rank_identity,
          events=self.events,actual_native_prefill_calls=16,actual_compiled_decode_calls=32,
          actual_native_finished_ref=actual_finished_ref,restored=True,GDN48_function_identities_unchanged=True,**C.scopes())
    def restore(self):
        for obj,name,fn,original in reversed(self.patches):
            C.need(obj.__dict__.get(name)is fn,"owned exact hook retained; refuse foreign overwrite")
            del obj.__dict__[name]
            C.need(getattr(obj,name).__func__ is original.__func__ and getattr(obj,name).__self__ is original.__self__,"exact original restoration")
        self.patches=[];self.closed=True
        C.need(all(id(x)==oid and x.forward.__func__ is fn for x,oid,fn in self.gdn),"all48 native GDN function owners untouched")
