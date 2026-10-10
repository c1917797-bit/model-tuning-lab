"""Called only by MAIN's native worker extension after weights in admitted eager TP4.
No hardware/framework import on import. Factory requires actual compiled-reader whole.
"""
import os,sys
from pathlib import Path
import contract as C
def capture_registry():
    W,_=C.writer_modules();cm=C.obj(W.CAPTURE);rows={Path(r["path"]).name:r for r in cm["files"]}
    C.load("io_contract",C.IO)
    for name in("tp_provider_current","post_rope_current","raw_sink","text_input_current"):
        C.load(name,rows[name+".py"])
    return C.load("runtime_capture_current",rows["runtime_capture_current.py"])
def policy(worker):
    c=worker.vllm_config;p=c.parallel_config;m=c.model_config;s=c.scheduler_config
    C.need(p.tensor_parallel_size==4 and p.pipeline_parallel_size==p.data_parallel_size==1 and
      p.prefill_context_parallel_size==p.decode_context_parallel_size==1 and
      c.speculative_config is None and c.lora_config is None and c.kv_transfer_config is None,"actual original TP4/no auxiliary algorithm")
    C.need(m.model=="/cache/efim/Qwen3.6-27B"and m.max_model_len==33792 and m.enforce_eager is True and
      c.compilation_config.mode.name=="NONE"and str(m.dtype)in("torch.float16","torch.bfloat16")and
      not m.is_encoder_decoder,"actual Qwen33792 eager decoder")
    C.need(s.max_num_seqs==1 and s.max_num_batched_tokens==33792 and s.enable_chunked_prefill is True and
      s.async_scheduling is False and c.cache_config.enable_prefix_caching is False and c.cache_config.cache_dtype=="auto",
      "explicit fixed one full32768 prefill; chunked supported, no active split/prefix/async")
    C.need(c.cache_config.kv_cache_memory_bytes==10*2**30,"preregistered native dense cache retained10GiB, no savings claim")
    return c
class Factory:
    def __init__(self,worker,reader_whole_ref,prompt_ref,root,expected):
        C.need(os.environ.get("MAIN_SKVQ_COMPILED_READER_MODEL_ENABLE")=="1","MAIN explicit actual model opt-in")
        self.source=C.source(expected);self.whole=C.reader_whole(reader_whole_ref)
        original=capture_registry();worker=original.actual_worker(worker);policy(worker)
        original.deployed_sources();_,registry,_=original.registry_for(worker)
        self.rank_provider=original.RankProvider();rank=self.rank_provider()
        C.need(worker.rank==rank["public_TP_rank"],"actual native initialized rank/group identity")
        self.root=Path(root);C.need(self.root.is_absolute()and self.root.parent.is_dir()and not self.root.exists(),"absent owned actual rank work")
        self.root.mkdir();self.worker=worker;self.rank=rank
        import torch,torch_npu,triton,triton.language as tl
        from kernel import build
        from native_binding import Bind
        from model_raw import Publisher
        from native_finish import Finish
        from worker_patch import Session
        W,_=C.writer_modules();F=C.load("_skvq_reader_actual_format",W.HOST_BINDINGS["n1_format.py"])
        getter,enum,qualification=F.qualify(torch,torch_npu,self.source);format_policy=F.policy()
        self.format_ref=C.atomic(self.root/"FORMAT_QUALIFICATION.json",qualification)
        def nd(t):return format_policy.serial(getter(t),enum)
        props=torch.npu.get_device_properties(worker.local_rank);cores=dict(num_aicore=props.num_aicore,num_vectorcore=props.num_vectorcore)
        rows=C.input_rows(C.obj(self.whole["writer_whole_ref"]))
        layouts={r["logical_layer"]:{a:r["axes"][a]["layout"]for a in("K","V")}for r in rows if r["rank"]==worker.rank and r["bits"]==2}
        C.need(len(layouts)==16,"all16 actual current rank calibration layouts")
        layout_module=C.load("_skvq_model_original_layout",W.LAYOUT);writer=C.load("_skvq_model_original_device_writer",W.WRITER)
        def qualify_rank():
            current=self.rank_provider()
            C.need(all(current[k]==rank[k]for k in("pid","pid_start_ticks","parallel_source","native_group_class","public_TP_rank","groups")),
              "same live native TP/process/group identity; dynamic timestamp is not identity")
        self.binding=Bind(worker,self.source,rank,prompt_ref,registry=registry,qualify_rank=qualify_rank)
        self.publisher=Publisher(self.root/"raw",self.source,torch)
        self.finish=Finish(worker,self.binding,self.source,rank,self.root)
        self.session=None
        try:
            reader=build(torch,triton,tl,device_properties=cores,validate_nd=nd,qualify=lambda:C.source(expected))()
            self.session=Session(worker,registry,layouts,reader,torch,layout_module,writer,source_ref=self.source,
              rank_identity=rank,reader_whole_ref=reader_whole_ref,bind_native_request=self.binding,
              publish_frame=self.publisher,publish_prefill=self.publisher.prefill,consume_native_finish=self.finish.consume)
            self.install=self.session.install()
        except BaseException:
            if self.session is not None:self.session.restore()
            self.finish.restore();raise
        self.install_ref=C.atomic(self.root/"INSTALL.json",dict(source_ref=self.source,rank_identity=rank,
          reader_whole_ref=reader_whole_ref,original_runtime_sources=original.deployed_sources(),format_ref=self.format_ref,
          actual_core_properties=cores,installed=self.install,**C.scopes()))
    def complete(self):
        C.need(self.finish.ref is not None,"actual original all4 finished pending, never substitute HTTP DONE")
        value=self.session.finish(self.finish.ref);self.finish.restore()
        value["actual_original_update_restored"]=True;value["install_ref"]=self.install_ref
        return C.atomic(self.root/"FINAL.json",value)
    def restore(self):
        if not self.session.closed:self.session.restore()
        if not self.finish.closed:self.finish.restore()
        return dict(rank=self.worker.rank,restored=True,**C.scopes())
