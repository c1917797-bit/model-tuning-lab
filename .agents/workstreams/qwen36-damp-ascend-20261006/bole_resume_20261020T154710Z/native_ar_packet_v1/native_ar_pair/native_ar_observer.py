"""Default-OFF actual native AR observer. No cache, logits, or outputs substituted.

Advisory source only until MAIN binds and checks the actual image. PA and FIA
are observed as distinct real routes. No private FP16 precision shim is used.
"""
import contextvars
import functools
import inspect
import os
import types
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C


def identity(x):
    return dict(storage_ptr=x.untyped_storage().data_ptr(), data_ptr=x.data_ptr(),
        storage_offset=x.storage_offset(), shape=list(x.shape), stride=list(x.stride()),
        dtype=str(x.dtype), device=str(x.device))


def code(fn, reference):
    C.need(C.ref(inspect.getsourcefile(getattr(fn, '__func__', fn))) == reference,
           'exact original callable source')


def native_method(obj, name, reference):
    fn = getattr(obj, name)
    C.need(name not in obj.__dict__ and getattr(fn, '__func__', None) is getattr(type(obj), name),
           'unmodified actual instance/class method ' + name)
    code(fn, reference)
    return fn


def snapshot(t, value, *, large=False):
    if isinstance(value, t.Tensor):
        C.need(value.numel()*value.element_size() <= (16*2**20 if large else 2**20),
               'bounded actual metadata tensor')
        return value.detach().cpu().contiguous().clone()
    if value is None or type(value) in (str,int,float,bool):
        return value
    if type(value) in (list,tuple):
        C.need(len(value) <= 65536, 'bounded primitive metadata')
        return [snapshot(t,x,large=large) for x in value]
    if type(value) is dict:
        C.need(len(value) <= 512 and all(type(k) in (str,int) for k in value), 'primitive metadata')
        return {k:snapshot(t,v,large=large) for k,v in value.items()}
    raise ValueError('opaque native metadata is not serializable: '+type(value).__name__)


def schemas(t, name):
    found = {}
    for namespace in ('npu','_C_ascend'):
        try:
            packet = getattr(getattr(t.ops,namespace),name)
            family = packet._schemas
        except (AttributeError, RuntimeError):
            continue
        if family:
            found[namespace+'.'+name] = {k:str(v) for k,v in family.items()}
    return found


class Proxy:
    """A module-local delegate, never a mutation of the torch_npu module."""
    def __init__(self, delegate, t, frame):
        self.delegate, self.t, self.frame = delegate,t,frame
    def __getattr__(self, name):
        original = getattr(self.delegate,name)
        if name not in ('npu_fused_infer_attention_score','_npu_paged_attention'):
            return original
        def call(*args, **kwargs):
            active = self.frame.get()
            if active is None:
                return original(*args,**kwargs)
            C.need(not args and not active['kernel'], 'one exact actual lower PA/FIA call per target layer')
            excluded = {'query','key','value','key_cache','value_cache','out'}
            q = kwargs['query']
            C.need(self.t.equal(q.contiguous().view(self.t.uint8),active['query_device'].contiguous().view(self.t.uint8)),
                   'actual lower query equals native post-norm/RoPE query')
            names = ('key_cache','value_cache') if name=='_npu_paged_attention' else ('key','value')
            expected = active['cache_identities'] if name=='_npu_paged_attention' else active['FIA_cache_view_identities']
            owned=[]
            for key,wanted,before in zip(names,expected,(active['dense_key_device'],active['dense_value_device'])):
                value=kwargs[key];actual=identity(value)
                if name=='_npu_paged_attention':
                    C.need(actual==wanted,'actual PA operands alias original native arenas')
                else:
                    C.need(actual['shape']==wanted['shape'] and actual['dtype']==wanted['dtype']
                           and actual['device']==wanted['device'] and value.is_contiguous(),
                           'actual original FIA cache.view(...).contiguous() ABI, including a genuine native copy')
                selected=value.reshape(-1,1,256).index_select(0,active['owned_indices'])
                C.need(self.t.equal(selected.contiguous().view(self.t.uint8),before.contiguous().view(self.t.uint8)),
                       'actual lower PA/FIA owned-prefix operands equal original native cache bytes')
                owned.append(selected.detach().cpu().contiguous().clone())
            actual_kwargs = {k:(dict(tensor_identity=identity(v)) if k in excluded and
                            isinstance(v,self.t.Tensor) else snapshot(self.t,v,large=True))
                             for k,v in kwargs.items()}
            query_before = q.detach().clone()
            result = original(*args,**kwargs)  # exactly one call; original result object is returned
            output = kwargs['out'] if name=='_npu_paged_attention' else result[0]
            C.need(self.t.equal(q.contiguous().view(self.t.uint8),query_before.contiguous().view(self.t.uint8)),
                   'actual original native query unchanged')
            active['kernel'].append(dict(name=name, callable_object_id=id(original),
                explicit_kwargs=actual_kwargs, actual_schema_family=schemas(self.t,name),
                actual_owned_key=owned[0],actual_owned_value=owned[1],
                output=output.detach().cpu().contiguous().clone(), original_called_exactly_once=True,
                omitted_defaults_resolved=False, precision_intervention=False))
            return result
        return call


def install(worker, t, *, source_ref, get_forward_context, native_proposer, native_get_tp_group, publish):
    if os.environ.get('BOLE_NATIVE_AR_PAIR_ENABLE') != '1':
        return None
    m = C.source(source_ref); refs = m['runtime_sources']
    C.need(C.ref(__file__) == m['files']['native_ar_observer.py'], 'exact AR observer source')
    code(get_forward_context,refs['forward_context']); code(publish,m['files']['native_ar_capture.py'])
    C.need(C.ref(native_proposer.__file__) == refs['proposer'], 'actual original vocabulary-policy module')
    group = native_get_tp_group()
    C.need(native_get_tp_group is native_proposer.get_tp_group
           and group.world_size == 4 and group.rank_in_group in range(4)
           and t.npu.matmul.allow_hf32 is False, 'actual TP4 and unchanged HF32OFF policy')
    runner = worker.model_runner
    C.need(runner.speculative_config is None and runner.num_spec_tokens == 0 and runner.drafter is None
           and not runner.use_async_scheduling and not runner.use_cp
           and runner.pcp_size == runner.dcp_size == 1 and runner.model_config.enforce_eager,
           'actual eager C1 native AR has no speculative drafter')
    C.need(not any(os.environ.get(k)=='1' for k in ('BOLE_THREE_NODE_MODEL_ENABLE',
        'BOLE_G1_MULTI_REQUEST_ENABLE','BOLE_CONTINUOUS_SERVICE_ENABLE')),
        'BOLE intervention switches are OFF for the actual native AR process')
    import worker_entry as W
    C.need(C.ref(W.__file__) == m['files']['worker_entry.py'], 'exact actual model registry source')
    inner,outer = (worker._bole_model_objects[k] for k in ('inner','outer'))
    head_method = W.actual_logits_head(C,outer,inner,refs['qwen35'])
    head = head_method.__self__
    vocab = head.config.vocab_size
    C.need(type(vocab) is int and vocab > 1 and not native_proposer.lmhead_tp_enable(),
           'actual native target vocabulary and supported head policy')
    old_inner = native_method(inner,'forward',refs['qwen_next'])
    old_head = native_method(head,'compute_logits',refs['qwen35'])
    old_sample = native_method(runner,'_sample',refs['runner'])
    old_samples = native_method(runner,'sample_tokens',refs['torch_contextlib'])
    wrapped = old_samples.__func__
    original = getattr(wrapped,'__wrapped__',None)
    C.need(original is not None, 'actual inference-mode original sample_tokens')
    code(original,refs['runner'])
    closure = inspect.getclosurevars(wrapped).nonlocals
    C.need(closure.get('func') is original and callable(closure.get('ctx_factory')),
           'same original inference-mode closure')
    code(closure['ctx_factory'],refs['torch_grad_mode'])
    context = getattr(closure['ctx_factory'],'__self__',None)
    C.need(type(context) is t.inference_mode and context.mode is True, 'actual inference_mode factory')
    old_update = runner._update_states
    C.need('_update_states' not in runner.__dict__ and getattr(old_update,'_actual_identity_capture',False),
           'actual worker identity journal remains in native update chain')
    code(old_update,m['files']['identity_capture.py'])
    underlying = inspect.getclosurevars(old_update.__func__).nonlocals.get('original')
    C.need(underlying is not None, 'actual journal preserves original native update')
    code(underlying,refs['runner'])
    active = contextvars.ContextVar('bole_native_ar_actual_fa',default=None)
    records,retired,strong = [],[],[]
    current = dict(request=None,forward=None,head=None,pending=None,closed=False,poisoned=False)
    from vllm.sampling_params import SamplingParams
    from vllm.v1.sample.metadata import SamplingMetadata
    from vllm.v1.worker.gpu_input_batch import CachedRequestState,InputBatch
    from vllm_ascend.worker.npu_input_batch import NPUInputBatch
    for cls,key in ((SamplingParams,'sampling_params'),(SamplingMetadata,'sampling_metadata'),
                    (CachedRequestState,'gpu_input_batch'),(InputBatch,'gpu_input_batch'),
                    (NPUInputBatch,'npu_input_batch')):
        C.need(C.ref(inspect.getsourcefile(cls))==refs[key],'actual native sampling class '+key)
    C.need(type(runner.input_batch)is NPUInputBatch and InputBatch in NPUInputBatch.__mro__
           and NPUInputBatch.no_thinking_budget is InputBatch.__dict__['no_thinking_budget'],
           'actual NPU batch inherits source-proved native thinking-budget policy')
    code(InputBatch.__dict__['no_thinking_budget'].fget,refs['gpu_input_batch'])
    restorers = []
    def guard(fn):
        @functools.wraps(fn)
        def guarded(*args,**kwargs):
            try:return fn(*args,**kwargs)
            except BaseException as error:
                if not current['poisoned']:
                    current['poisoned']=True
                    try:
                        publish(t=t,source_ref=source_ref,rank=group.rank_in_group,
                            payload=dict(schema=C.AR_RAW,source=source_ref,rank=group.rank_in_group,
                                requests=records,primary=repr(error),model_ready=False),primary=repr(error))
                    except BaseException:
                        # Preserve the original first fault; MAIN retains the owned process logs.
                        pass
                raise
        return guarded
    def patch(obj,name,fn):
        C.need(name not in obj.__dict__, 'no prior instance patch '+name)
        actual=guard(fn)
        setattr(obj,name,types.MethodType(actual,obj))
        def restore():
            C.need(getattr(obj,name).__func__ is actual, 'owned observer method before restoration')
            delattr(obj,name)
        restorers.append(restore)
    def need_request():
        ids = runner.input_batch.req_ids
        C.need(not current['poisoned'] and len(ids)==1 and ids[0] in runner.requests
               and runner.input_batch.req_id_to_index=={ids[0]:0}, 'actual exclusive native C1 owner')
        rid,req = ids[0],runner.requests[ids[0]]
        item = next((r for r in records if r['request']==rid),None)
        if item is None:
            C.need(len(records)<2 and all(req is not old and rid!=oldrid for oldrid,old in strong),
                   'two distinct strongly retained actual native request objects')
            C.need(len(req.prompt_token_ids)==131 and len(req.output_token_ids)==0,
                   'fresh native 131-token smoke request')
            item = dict(request=rid,generation=len(records)+1,request_object_id=id(req),
                        prompt_token_ids=list(req.prompt_token_ids),samples=[],FA=[],retirement=None)
            records.append(item);strong.append((rid,req))
        C.need(req is strong[item['generation']-1][1] and len(req.output_token_ids)<2,
               'same live native AR request object and bounded output')
        current['request'] = (rid,req,item)
        return rid,req,item
    def neutral(req):
        p=req.sampling_params; s=runner.input_batch.sampling_metadata
        C.need(type(req)is CachedRequestState and type(p)is SamplingParams and type(s)is SamplingMetadata,
               'actual unchanged native request/parameters/sampling metadata types')
        expected=dict(n=1,temperature=0,top_p=1,min_p=0,repetition_penalty=1,
            frequency_penalty=0,presence_penalty=0,max_tokens=2,min_tokens=0,ignore_eos=True)
        C.need(all(getattr(p,k)==v for k,v in expected.items()) and p.top_k in (0,-1)
            and p.stop==[] and p.stop_token_ids==[] and p.bad_words==[]
            and p._bad_words_token_ids in (None,[]) and all(getattr(p,k) is None for k in
            ('logprobs','prompt_logprobs','logprob_token_ids','structured_outputs','logit_bias',
             'allowed_token_ids','extra_args','thinking_token_budget','repetition_detection'))
            and runner.model_config.logits_processors in (None,[],())
            and s.all_greedy is True and s.all_random is False and s.no_penalties is True
            and s.temperature is None and s.top_p is None and s.top_k is None
            and s.max_num_logprobs is None and s.allowed_token_ids_mask is None
            and not s.bad_words_token_ids and s.logprob_token_ids is None
            and runner.input_batch.no_thinking_budget, 'actual neutral original native greedy sampler')
        return dict(expected,top_k=p.top_k,all_greedy=True,no_penalties=True,no_thinking_budget=True)
    targets=[]; modules={}
    for layer in inner.layers:
        if layer.layer_type!='full_attention': continue
        obj=layer.self_attn.attn; impl=obj.impl; module=inspect.getmodule(type(impl))
        C.need(C.ref(module.__file__)==refs['ascend_attention'] and
               type(impl) is module.AscendAttentionBackendImpl, 'actual native target FA backend')
        old=native_method(impl,'forward_impl',refs['ascend_attention'])
        for name in ('forward','forward_paged_attention','forward_fused_infer_attention','reshape_and_cache'):
            code(getattr(impl,name),refs['ascend_attention'])
        C.need(impl.sliding_window is None and impl.sinks is None and not impl.enable_hamming_sparse
               and obj.kv_sharing_target_layer_name is None and obj.query_quant is None
               and obj.calculate_kv_scales is False, 'only unquantized causal full target FA')
        device=inspect.getmodule(module.DeviceOperator.npu_fused_infer_attention_score.__func__)
        C.need(C.ref(device.__file__)==refs['device_op'] and module.DeviceOperator is device.DeviceOperator
               and module.DeviceOperator in (device.BaseDeviceAdaptor,device.A5DeviceAdaptor),
               'actual native256-head Base/A5 device dispatcher')
        for mod in (module,device):
            C.need(mod.torch_npu is not None and not isinstance(mod.torch_npu,Proxy),
                   'unmodified module-local native torch_npu binding')
            modules[id(mod)]=mod
        targets.append((layer.layer_idx,obj,impl,old,module))
    C.need(len(targets)==16, 'all16 actual target FA layers')
    def forward(this,input_ids,positions,intermediate_tensors=None,inputs_embeds=None):
        ctx=get_forward_context()
        if getattr(ctx,'in_profile_run',False) or ctx.attn_metadata is None:
            return old_inner(input_ids,positions,intermediate_tensors,inputs_embeds)
        rid,req,item=need_request(); policy=neutral(req)
        C.need(current['forward'] is None and current['pending'] is None,
               'one original native forward before one original native sample')
        ordinal=len(item['samples'])
        count=131 if ordinal==0 else 1
        C.need(intermediate_tensors is None and req.prompt_embeds is None and not req.mm_features
               and (req.prompt_is_token_ids is None or list(req.prompt_is_token_ids)==[True]*131),
               'actual PP1 pure-text native token inputs')
        expected_ids=list(req.prompt_token_ids) if ordinal==0 else [req.output_token_ids[-1]]
        gpu=runner.input_ids.gpu[:count]
        computed=int(runner.input_batch.num_computed_tokens_cpu[0])
        cpu=runner.input_batch.token_ids_cpu[0,computed:computed+count].tolist()
        C.need(gpu.dtype==t.int32 and gpu.cpu().tolist()==cpu==expected_ids,
               'actual current native GPU/CPU/request token-ID chain')
        native_input=dict(actual_token_ids=gpu.detach().cpu().clone(),actual_CPU_token_ids=cpu,
            request_prompt_token_ids=list(req.prompt_token_ids),request_id=rid,
            no_mm_features=True,no_soft_prompt=True,
            sources={k:refs[k] for k in ('runner','base_runner','qwen35','qwen_next')})
        if inputs_embeds is None:
            C.need(input_ids is not None and t.equal(input_ids,gpu), 'actual native token-ID argument')
            native_input['actual_input_mode']='native-token-ids'
        else:
            C.need(runner.supports_mm_inputs and not runner.enable_prompt_embeds
                   and not runner.model_config.is_encoder_decoder, 'actual native text embedding route')
            code(head.embed_input_ids,refs['qwen35']);code(inner.embed_input_ids,refs['qwen_next'])
            expected=head.embed_input_ids(gpu)
            C.need(inputs_embeds.shape==expected.shape==(count,5120)
                   and inputs_embeds.dtype==expected.dtype==t.bfloat16
                   and t.equal(inputs_embeds.contiguous().view(t.uint8),expected.contiguous().view(t.uint8)),
                   'actual untouched native embeddings equal original token embedding')
            native_input.update(actual_input_mode='native-text-embeddings',
                actual_native_embeddings=inputs_embeds.detach().cpu().clone(),
                independent_token_embeddings=expected.detach().cpu().clone())
            if input_ids is not None:C.need(t.equal(input_ids,gpu),'optional raw IDs agree with real native input')
        frame=dict(ordinal=len(item['samples']),request=rid,request_object_id=id(req),
            computed_tokens=int(runner.input_batch.num_computed_tokens_cpu[0]),
            output_tokens_before=list(req.output_token_ids),policy=policy,
            input=native_input,positions=positions.detach().cpu().clone())
        current['forward']=frame
        hidden=old_inner(input_ids,positions,intermediate_tensors,inputs_embeds)
        C.need(isinstance(hidden,t.Tensor) and hidden.dtype==t.bfloat16 and hidden.ndim==2,
               'actual native normalized target hidden')
        frame['last_hidden']=hidden[-1:].detach().cpu().clone()
        return hidden
    def head_forward(this,hidden_states,*args,**kwargs):
        result=old_head(hidden_states,*args,**kwargs)
        frame=current['forward']
        if frame is None:return result
        C.need(current['head'] is None and isinstance(result,t.Tensor)
               and t.equal(hidden_states.detach().cpu().contiguous().view(t.uint8),
                           frame['last_hidden'].contiguous().view(t.uint8)),
               'actual target head consumes final native hidden row')
        current['head']=dict(hidden=hidden_states.detach().cpu().clone(),
                             local_logits=result.detach().cpu().clone())
        return result
    def sample(this,logits,spec_decode_metadata):
        rid,req,item=need_request();frame=current['forward'];head=current['head']
        C.need(frame is not None and head is not None and spec_decode_metadata is None
               and current['pending'] is None and logits.shape[0]==1
               and t.equal(logits.detach().cpu().contiguous().view(t.uint8),
                           head['local_logits'].contiguous().view(t.uint8)),
               'actual unmodified AR head→native sampler logits and no rejection sampler')
        neutral(req)
        result=old_sample(logits,spec_decode_metadata)
        C.need(result.sampled_token_ids.shape==(1,1) and result.logprobs_tensors is None,
               'actual original native one-token greedy sampler output')
        frame.update(head=head,local_logits=logits.detach().cpu().clone(),
                     sampler_token_ids=result.sampled_token_ids.detach().cpu().clone())
        current['pending']=frame
        return result
    def samples(this,grammar_output):
        C.need(grammar_output is None, 'no grammar mutation on native AR smoke')
        result=old_samples(grammar_output)
        frame=current['pending']
        if frame is None:return result
        rid,req,item=current['request']
        C.need(result.req_ids==[rid] and len(result.sampled_token_ids)==1
               and len(result.sampled_token_ids[0])==1,
               'actual original native ModelRunnerOutput')
        frame['native_output']=dict(req_ids=list(result.req_ids),
            sampled_token_ids=result.sampled_token_ids,
            request_output_tokens_after=list(req.output_token_ids),
            num_tokens_no_spec_after=int(runner.input_batch.num_tokens_no_spec[0]))
        item['samples'].append(frame)
        current.update(forward=None,head=None,pending=None)
        return result
    def fa_forward(this,*args,_index=None,_obj=None,_old=None,_module=None,**kwargs):
        signature=inspect.signature(_old);bound=signature.bind(*args,**kwargs);bound.apply_defaults();a=bound.arguments
        meta=a['attn_metadata']
        if meta is None or meta.num_prefills>0 or _module._EXTRA_CTX.is_draft_model:
            return _old(*args,**kwargs)
        rid,req,item=need_request();frame=current['forward']
        C.need(frame is not None and frame['ordinal']==1 and active.get() is None
               and meta.attn_state==_module.AscendAttentionState.DecodeOnly
               and meta.num_actual_tokens==1 and meta.num_decodes==1 and meta.causal is True
               and list(meta.seq_lens_list)==[132] and list(meta.actual_seq_lengths_q)==[1],
               'actual first single-token native AR decode, before branch selection')
        ctx=get_forward_context();prefix=_obj.layer_name
        C.need(ctx.attn_metadata[prefix] is meta and ctx.no_compile_layers[prefix] is _obj
               and str(ctx.cudagraph_runtime_mode).split('.')[-1]=='NONE', 'actual target metadata and dispatcher')
        q,k,v=a['query'],a['key'],a['value'];kc,vc=_obj.kv_cache
        C.need(q.shape==(1,6,256) and k.shape==v.shape==(1,1,256)
               and q.dtype==k.dtype==v.dtype==kc.dtype==vc.dtype==t.bfloat16
               and identity(kc)==identity(this.key_cache) and identity(vc)==identity(this.value_cache),
               'actual post-norm/RoPE BF16 native operands and cache arenas')
        gids=[i for i,g in enumerate(runner.kv_cache_config.kv_cache_groups) if prefix in g.layer_names]
        C.need(len(gids)==1,'unique current native FA cache group');gid=gids[0]
        block=runner.input_batch.block_table[gid];code(block.get_cpu_tensor,refs['block_table'])
        physical=list(req.block_ids[gid]);n=int(block.num_blocks_per_row[0])
        table=block.get_cpu_tensor()[0,:n].tolist();ratio=block.blocks_per_phys_block
        C.need(ratio==12 and block.physical_block_size==1536 and block.block_size==block.logical_block_size==128
               and block.use_hybrid_blocks and block.pcp_world_size==block.dcp_world_size==1
               and table==[p*12+j for p in physical for j in range(12)]
               and meta.block_tables[0,:n].cpu().tolist()==table
               and block.get_device_tensor(1)[0,:n].cpu().tolist()==table,
               'actual current physical1536→kernel128 allocation, CPU/GPU/metadata table')
        slots=[table[p//128]*128+p%128 for p in range(132)]
        C.need(meta.slot_mapping[:1].cpu().tolist()==slots[-1:], 'actual native current KV write')
        ix=t.tensor(slots,dtype=t.long,device=kc.device)
        dense_k=kc.reshape(-1,1,256).index_select(0,ix)
        dense_v=vc.reshape(-1,1,256).index_select(0,ix)
        C.need(t.equal(dense_k[-1:].view(t.uint8),k.contiguous().view(t.uint8))
               and t.equal(dense_v[-1:].view(t.uint8),v.contiguous().view(t.uint8)),
               'native cache already contains exact current post-RoPE K/V')
        record=dict(schema='bole.actual-production-native-FA-frame/v1',request=rid,
            request_object_id=id(req),generation=item['generation'],ordinal=1,layer=_index,
            prefix_length=131,query=q.detach().cpu().clone(),key=dense_k.detach().cpu().clone(),
            value=dense_v.detach().cpu().clone(),current_key=k.detach().cpu().clone(),
            current_value=v.detach().cpu().clone(),request_physical_blocks=physical,kernel_table=table,
            slot_mapping=slots[-1:],cache_identities=[identity(kc),identity(vc)],
            FIA_cache_view_identities=[identity(x.view(x.shape[0],128,-1))for x in(kc,vc)],kernel=[])
        context=dict(query_device=q,cache_identities=record['cache_identities'],
                     FIA_cache_view_identities=record['FIA_cache_view_identities'],kernel=record['kernel'],
                     owned_indices=ix,dense_key_device=dense_k,dense_value_device=dense_v)
        token=active.set(context)
        try:
            result=_old(*args,**kwargs)
        finally:
            active.reset(token)
        C.need(len(record['kernel'])==1 and runner.requests.get(rid) is req,
               'one actual PA or FIA call, same actual current request')
        record['output']=result[:1].detach().cpu().clone()
        for arena,dense in ((kc,dense_k),(vc,dense_v)):
            C.need(t.equal(arena.reshape(-1,1,256).index_select(0,ix).contiguous().view(t.uint8),
                           dense.contiguous().view(t.uint8)), 'actual original attention preserves owned live prefix KV bytes')
        record.update(precision_intervention=False,omitted_defaults_resolved=False,
                      private_dense_FP16_control_used=False,production_globally_qualified=False)
        item['FA'].append(record)
        return result
    def update(this,scheduler_output):
        result=old_update(scheduler_output)
        for item in records:
            rid=item['request']
            if rid in scheduler_output.finished_req_ids and item['retirement'] is None:
                req=strong[item['generation']-1][1]
                C.need(rid not in runner.requests and rid not in runner.input_batch.req_ids
                       and len(item['samples'])==2 and len(req.output_token_ids)==2
                       and len(item['FA'])==16 and current['pending'] is None,
                       'actual native request removed after exactly2 outputs and all16 native decode FA calls')
                item['retirement']=dict(request=rid,request_object_id=id(req),generation=item['generation'],
                    actual_output_token_ids=list(req.output_token_ids),native_removed=True)
                retired.append(rid)
        if len(retired)==2:
            for restore in reversed(restorers):restore()
            current['closed']=True
            payload=dict(schema=C.AR_RAW,source=source_ref,rank=group.rank_in_group,pid=os.getpid(),
                requests=records,native_policy=dict(reduce_sample=native_proposer.get_ascend_config().enable_reduce_sample,
                    lmhead_tp=False,vocab_size=vocab,proposer_source=refs['proposer']),
                source_after=m['files'],runtime_sources_after=refs,primary=None,
                native_AR=True,speculative_config=None,precision_intervention=False,
                private_dense_FP16_control_used=False,model_ready=False)
            publish(t=t,source_ref=source_ref,rank=group.rank_in_group,payload=payload,primary=None)
        return result
    # Every guard above precedes the first mutation; installation rolls back its own hooks.
    try:
        for module in modules.values():
            old=module.torch_npu;proxy=Proxy(old,t,active);module.torch_npu=proxy
            def restore_module(module=module,old=old,proxy=proxy):
                C.need(module.torch_npu is proxy,'owned module-local observer proxy');module.torch_npu=old
            restorers.append(restore_module)
        for index,obj,impl,old,module in targets:
            def wrapper(this,*args,_i=index,_o=obj,_old=old,_m=module,**kwargs):
                return fa_forward(this,*args,_index=_i,_obj=_o,_old=_old,_module=_m,**kwargs)
            patch(impl,'forward_impl',wrapper)
        for obj,name,fn in ((inner,'forward',forward),(head,'compute_logits',head_forward),
                            (runner,'_sample',sample),(runner,'sample_tokens',samples),
                            (runner,'_update_states',update)):
            patch(obj,name,fn)
    except BaseException:
        for restore in reversed(restorers):restore()
        raise
    def restore():
        C.need(not current['closed'] and active.get() is None,'inactive observer before explicit restoration')
        for fn in reversed(restorers):fn()
        current['closed']=True
        return dict(restored=True,completed_requests=len(retired),model_ready=False)
    return restore
