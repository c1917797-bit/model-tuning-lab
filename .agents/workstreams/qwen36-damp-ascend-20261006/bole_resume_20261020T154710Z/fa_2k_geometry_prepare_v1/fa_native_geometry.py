"""Live native-prefill FA geometry. No guessed pages, allocation or NPU work."""
import os
from dataclasses import dataclass

def need(v,s):
    if not v:raise ValueError(s)

def integer(v,name,minimum=0):
    need(type(v)is int and v>=minimum,'typed '+name)
    return v

def vector(v,name):
    need(type(v)in(list,tuple)and v,'nonempty '+name)
    for x in v:integer(x,name)
    need(len(set(v))==len(v),'unique '+name)
    return tuple(v)

def plan(length,output_tokens):
    integer(length,'native prefix',1);integer(output_tokens,'output tokens',2)
    need(length==2048 and output_tokens in(8,160,1024),'explicit representative2k scope')
    return dict(prefix=length,output_tokens=output_tokens,max_before=length+output_tokens-2,
                maximum_publication_pages=(length+output_tokens+127)//128,
                maximum_scratch_pages=(length+output_tokens+1+127)//128,
                NPU_observed=False,allocation_proven=False)

def metadata(*,prefix,output_tokens,physical_blocks,ratio,physical_size,kernel_size,
             use_hybrid,pcp,dcp,cpu_table,gpu_table,metadata_table,native_slots,metadata_slots,
             cache_shape,cache_dtype,num_prefills,num_decodes,num_actual_tokens,seq_lens,query_lens):
    p=plan(prefix,output_tokens)
    integer(ratio,'physical/kernel ratio',1)
    need(type(use_hybrid)is bool and use_hybrid and kernel_size==128 and
         physical_size==ratio*128 and pcp==dcp==1,'actual ND hybrid CP1 geometry')
    blocks=vector(physical_blocks,'request physical blocks')
    expanded=tuple(block*ratio+j for block in blocks for j in range(ratio))
    table=vector(cpu_table,'allocated CPU kernel pages')
    need(table==tuple(gpu_table)==tuple(metadata_table)==expanded,'all native committed allocated tables agree')
    need(len(cache_shape)==4 and all(type(x)is int and x>0 for x in cache_shape)and
         tuple(cache_shape[1:])==(128,1,256)and cache_dtype=='torch.bfloat16',
         'actual BF16 ND128 KV1 D256 cache')
    need(all(x<cache_shape[0]for x in table),'allocated pages inside native cache arena')
    need(num_prefills==1 and num_decodes==0 and num_actual_tokens==prefix and
         list(seq_lens)==list(query_lens)==[prefix],'actual complete pure native prefill chronology')
    need(len(table)*128>=prefix,'actual native table covers all prefill positions before indexing')
    expected=tuple(table[pos//128]*128+pos%128 for pos in range(prefix))
    need(tuple(native_slots)==tuple(metadata_slots)==expected,'every real native prefill destination')
    need(len(table)>=p['maximum_publication_pages'],
         'native prefill did not allocate enough accepted-path pages; no inferred allocation/growth')
    return dict(p,physical_blocks=blocks,table=table,ratio=ratio,physical_size=physical_size,
                kernel_size=kernel_size,cache_shape=tuple(cache_shape))

_TOKEN=object()

@dataclass(frozen=True)
class NativeGeometry:
    token:object
    source:object
    runner:object
    request:object
    request_id:str
    generation:int
    group:int
    group_object:object
    block:object
    layer:object
    key:object
    value:object
    key_identity:object
    value_identity:object
    facts:object
    tensor_identity:object

    def check(self,length):
        need(self.token is _TOKEN,'real native prefill observation required; JSON/plan refused')
        integer(length,'current committed length')
        f=self.facts;need(f['prefix']<=length<=f['max_before'],'current representative2k committed domain')
        r=self.runner;rid=self.request_id
        need(r.requests.get(rid)is self.request and r.input_batch.req_ids==[rid]and
             r.input_batch.req_id_to_index=={rid:0},'same strong native request and C1 row')
        need(r.kv_cache_config.kv_cache_groups[self.group]is self.group_object and
             r.input_batch.block_table[self.group]is self.block,'same native cache group/table object')
        b=self.block;count=int(b.num_blocks_per_row[0]);cpu=b.get_cpu_tensor()
        need(cpu.device.type=='cpu'and count==len(f['table'])and
             tuple(int(x)for x in cpu[0,:count].tolist())==f['table']and
             tuple(self.request.block_ids[self.group])==f['physical_blocks'],
             'native allocation stays frozen; appended/reordered/removed pages need new qualification')
        need((b.blocks_per_phys_block,b.physical_block_size,b.logical_block_size,b.block_size,
              b.use_hybrid_blocks,b.pcp_world_size,b.dcp_world_size)==
             (f['ratio'],f['physical_size'],128,128,True,1,1),'native geometry unchanged')
        identity=self.tensor_identity;obj=self.layer
        need(len(obj.kv_cache)==2 and identity(self.key)==self.key_identity==identity(obj.kv_cache[0])==identity(obj.impl.key_cache)and
             identity(self.value)==self.value_identity==identity(obj.kv_cache[1])==identity(obj.impl.value_cache),
             'same live native layer/backend K/V storage')
        publication=(length+2+127)//128;scratch=(length+3+127)//128
        need(publication<=len(f['table'])and length+2<=len(f['table'])*128,
             'all root/accepted-child publication destinations allocated natively')
        return dict(length=length,query_shape=(1,6,3,256),KV_shape=(scratch,1,128,256),
            mask_shape=(1,1,3,scratch*128),table_shape=(1,scratch),
            scratch_kernel_pages=scratch,publication_kernel_pages=publication,
            initial_kernel_pages=len(f['table']),physical_allocation_growth_proven=False)

    def allocation(self,*,table,physical_blocks,ratio,physical_size,kernel_size,use_hybrid):
        self.check(self.facts['prefix'])
        need(tuple(table)==self.facts['table']and tuple(physical_blocks)==self.facts['physical_blocks']and
             (ratio,physical_size,kernel_size,use_hybrid)==
             (self.facts['ratio'],self.facts['physical_size'],128,True),'actual registered native geometry exact')
        return True

def require(value):
    need(type(value)is NativeGeometry and value.token is _TOKEN,
         'real source-bound native2k prefill geometry missing; no guessed17/24/25 pages')
    return value

def bind_layer(torch,C,m,source,runner,request_id,request,layer,group,metadata,context,
               get_attention_context,*,length,output_tokens,generation):
    # Only the original native-return seam may invoke this, never a metadata
    # packet loader. Strong objects and all actual buffers are retained.
    need(os.environ.get('BOLE_NATIVE_2K_GEOMETRY_ENABLE')=='1','native2k geometry default OFF')
    import inspect
    import model_entry as E
    import fa_prefill131r10 as ORIGINAL
    need(C.ref(__file__)==m['files']['fa_native_geometry.py']and
         C.ref(ORIGINAL.__file__)==m['files']['fa_prefill131r10.py'],'actual source-bound geometry/mapping helpers')
    need(C.ref(inspect.getsourcefile(type(runner)))==m['runtime_sources']['runner'],
         'actual installed native runner class')
    need(length==2048 and type(generation)is int and generation in(1,2),'actual representative native2k request epoch')
    need(runner.requests.get(request_id)is request and runner.input_batch.req_ids==[request_id]and
         runner.input_batch.req_id_to_index=={request_id:0},'actual strong native request before geometry bind')
    need(layer.layer_type=='full_attention','actual FA layer')
    obj=layer.self_attn.attn;prefix=obj.layer_name;groups=runner.kv_cache_config.kv_cache_groups
    need(type(group)is int and 0<=group<len(groups)and prefix in groups[group].layer_names,
         'actual unique native FA cache group')
    need([i for i,g in enumerate(groups)if prefix in g.layer_names]==[group],'unique native FA group')
    need(context.attn_metadata is metadata and context.dp_metadata is None and context.ubatch_slices is None and
         str(context.cudagraph_runtime_mode).split('.')[-1]=='NONE','native eager CP1 forward context')
    need(runner.vllm_config.compilation_config.static_forward_context[prefix]is obj and
         context.no_compile_layers[prefix]is obj,'actual registered static/live native FA dispatcher')
    E.code_source(C,get_attention_context,m['runtime_sources']['attention'])
    E.code_source(C,type(obj).forward,m['runtime_sources']['attention'])
    E.code_source(C,obj.impl.forward,m['runtime_sources']['ascend_attention'])
    E.code_source(C,obj.impl.reshape_and_cache,m['runtime_sources']['ascend_attention'])
    meta,actual,kv,generic=get_attention_context(prefix)
    need(actual is obj and meta is metadata[prefix]and kv is obj.kv_cache and len(kv)==2,
         'actual native FA cache/context aliases')
    need(obj.kv_sharing_target_layer_name is None and obj.query_quant is None and
         obj.calculate_kv_scales is False,'unquantized nonsharing native FA')
    key,value=kv
    need(key.device.type==value.device.type=='npu'and key.shape==value.shape and
         key.dtype==value.dtype==torch.bfloat16,'real NPU BF16 K/V, CPU/synthetic observations refused')
    b=runner.input_batch.block_table[group]
    E.code_source(C,b.get_cpu_tensor,m['runtime_sources']['block_table'])
    E.code_source(C,b.get_device_tensor,m['runtime_sources']['block_table'])
    count=int(b.num_blocks_per_row[0]);cpu=b.get_cpu_tensor();table=cpu[0,:count].tolist()
    ORIGINAL.mapping(torch,b,meta,context,prefix,generic,table,count,length,request.block_ids[group])
    facts=metadata_values(torch,b,meta,key,request.block_ids[group],table,length,output_tokens)
    need(E.tensor_id(key)==E.tensor_id(obj.impl.key_cache)and
         E.tensor_id(value)==E.tensor_id(obj.impl.value_cache),'actual native backend cache aliases')
    g=NativeGeometry(_TOKEN,source,runner,request,request_id,generation,group,groups[group],b,obj,key,value,
                     E.tensor_id(key),E.tensor_id(value),facts,E.tensor_id)
    g.check(length)
    return g

def metadata_values(torch,block,meta,key,request_blocks,table,length,output_tokens):
    return metadata(prefix=length,output_tokens=output_tokens,physical_blocks=request_blocks,
        ratio=block.blocks_per_phys_block,physical_size=block.physical_block_size,
        kernel_size=block.logical_block_size,use_hybrid=block.use_hybrid_blocks,
        pcp=block.pcp_world_size,dcp=block.dcp_world_size,cpu_table=table,
        gpu_table=block.get_device_tensor(1)[0,:len(table)].cpu().tolist(),
        metadata_table=meta.block_tables[0,:len(table)].cpu().tolist(),
        native_slots=block.slot_mapping.gpu[:length].cpu().tolist(),
        metadata_slots=meta.slot_mapping[:length].cpu().tolist(),cache_shape=tuple(key.shape),
        cache_dtype=str(key.dtype),num_prefills=meta.num_prefills,num_decodes=meta.num_decodes,
        num_actual_tokens=meta.num_actual_tokens,seq_lens=meta.seq_lens_list,query_lens=meta.actual_seq_lengths_q)

def shape(length,geometry):
    return require(geometry).check(length)

@dataclass(frozen=True)
class Registration:
    token:object
    runner:object
    request:object
    request_id:str
    generation:int
    length:int
    rows:object

    def attach(self,bindings):
        need(self.token is _TOKEN and len(self.rows)==16,'actual complete16 native FA geometry registration')
        actual={b['index']:b for b in bindings if b['kind']=='fa'}
        need(set(actual)==set(self.rows),'exact registered actual FA layer indices')
        for index,g in self.rows.items():
            b=actual[index];g.check(self.length)
            need(b['layer'].self_attn.attn is g.layer and b['key']is g.key and b['value']is g.value and
                 b['group']==g.group and tuple(b['table'])==g.facts['table'],'same registry/cache geometry objects')
        for index,g in self.rows.items():actual[index]['native_geometry']=g
        return bindings

def require_registration(value,runner,request_id,request,length,generation):
    need(type(value)is Registration and value.token is _TOKEN and value.runner is runner and
         value.request is request and value.request_id==request_id and value.length==length and
         value.generation==generation,'actual complete same-prefill native2k registration required')
    return value

def bind_all(torch,C,m,source,worker,inner,*,request_id,request,metadata,context,get_attention_context,
             input_ids,positions,generation):
    need(os.environ.get('BOLE_NATIVE_2K_GEOMETRY_ENABLE')=='1','native2k geometry default OFF')
    need(input_ids.device.type=='npu'and input_ids.dtype==torch.int32 and tuple(input_ids.shape)==(2048,),
         'actual returned native2k target input, not generated metadata packet')
    axes=positions.ndim
    need(positions.dtype==torch.int64 and (axes==1 or tuple(positions.shape)==(3,2048))and
         positions.cpu().tolist()==(list(range(2048))if axes==1 else[list(range(2048))]*3),
         'actual native2k prefill RoPE coordinates')
    output=m['performance_profile']['scope']['output_tokens'];plan(2048,output)
    runner=worker.model_runner;rows={};groups=runner.kv_cache_config.kv_cache_groups
    for layer in inner.layers:
        if layer.layer_type=='linear_attention':continue
        need(layer.layer_type=='full_attention','known actual hybrid FA layer')
        prefix=layer.self_attn.attn.layer_name
        gids=[i for i,g in enumerate(groups)if prefix in g.layer_names]
        need(len(gids)==1,'unique native group for each actual FA layer')
        rows[layer.layer_idx]=bind_layer(torch,C,m,source,runner,request_id,request,layer,gids[0],metadata,context,
            get_attention_context,length=2048,output_tokens=output,generation=generation)
    need(len(rows)==16,'all16 native FA layers observed before candidate registration')
    return Registration(_TOKEN,runner,request,request_id,generation,2048,rows)
