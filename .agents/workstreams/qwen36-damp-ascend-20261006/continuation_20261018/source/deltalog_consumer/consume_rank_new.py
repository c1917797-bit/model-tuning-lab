"""Independent CPU firstdecode reader; original per-layer numerical body intact.

Native prefill is the unchanged observed boundary, not unrounded FP64-prefill
qualification. Decode state/precast/RNE/native gates are NOT weakened.
"""
import ast
import hashlib
import importlib.util
import json
import json
from pathlib import Path
import types
from geometry_witness import validate_geometry_witness, validate_control_accounting

STATE_LIMIT=7.92e-7
PEAK=.00303
L2=2**-13

def need(v,s):
    if not v:raise ValueError(s)

def bits(t,a,b):
    return a.dtype==b.dtype and a.shape==b.shape and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))

def metadata_union(value):
    """Independent integer arithmetic on saved evidence, never a live permit."""
    from byteaudit import ranges
    pools=value['pools'];ss=value['selections']
    need(pools and {p['index'] for p in pools}==set(range(len(pools))),'all unique complete pool indices')
    pm={p['index']:p for p in pools};accesses=[];writes={i:[] for i in pm};roles={};groups={};selected_rows={}
    for p in pools:need(type(p['pointer']) is int and p['pointer']>0 and type(p['nbytes']) is int and p['nbytes']>0,'complete actual storage extents')
    for s in ss:
        prefix,role,kind=s['prefix'],s['role'],s['kind'];key=(prefix,role)
        need(kind in('GDN','FA') and key not in roles and type(s['group']) is int,'unique actual typed layer roles')
        roles[key]=kind
        need(prefix not in groups or groups[prefix]==(kind,s['group']),'one actual group per prefix');groups[prefix]=(kind,s['group'])
        p=pm[s['pool']];g=s['geometry'];shape=g['shape'];stride=g['strides'];e=g['element_bytes']
        need(g['format_code']==2 and len(shape)==len(stride)>=2 and all(type(n) is int and n>0 for n in(*shape,*stride)),'actual unpacked ND2 positive layout')
        need(g['dtype'] in {'u8':1,'bf16':2,'f32':4,'i32':4,'i64':8} and e=={'u8':1,'bf16':2,'f32':4,'i32':4,'i64':8}[g['dtype']],'actual type/element bytes')
        size=1
        for n,st in zip(reversed(shape[1:]),reversed(stride[1:])):need(st==size,'exact contiguous inner row');size*=n
        rowbytes=size*e;need(stride[0]>=size and g['pointer']==p['pointer']+g['storage_offset']*e
             and p['pointer']<=g['pointer'] and g['pointer']+(shape[0]-1)*stride[0]*e+rowbytes<=p['pointer']+p['nbytes'],'typed offset/full-view storage bounds')
        rows=s['cpu_rows'];need(rows==s['gpu_rows'] and rows and len(set(rows))==len(rows) and all(type(r) is int and 0<=r<shape[0] for r in rows),'complete CPU/GPU selected index equality')
        need(prefix not in selected_rows or selected_rows[prefix]==rows,'all roles of same actual layer select same committed rows');selected_rows[prefix]=rows
        if kind=='GDN':
            need(len(rows)==1 and not s['writes'] and not s['physical_rows'],'C1 exact native GDN row')
            shape_contract={'base':('f32',[12,128,128]),'K':('bf16',[4,7,128]),'U':('f32',[12,7,128]),'lambda_log':('f32',[12,16]),'decay':('f32',[12,16]),'length':('i32',[12,16])}
            if role in shape_contract:
                dt,inner=shape_contract[role];need(g['dtype']==dt and shape[1:]==inner,'unchanged selected six-state typed ABI')
        else:
            pbs,kbs=s['physical_block_tokens'],s['kernel_block_tokens'];need(pbs>=kbs>0 and pbs%kbs==0 and shape[1]==kbs,'actual physical/kernel mapping')
            need([i*(pbs//kbs)+j for i in s['physical_rows'] for j in range(pbs//kbs)]==rows,'complete actual FA expanded table')
            tokenbytes=stride[1]*e;need(2048//kbs<len(rows),'FA history covers firstdecode position2048')
            need(s['writes']==[[rows[2048//kbs],(2048%kbs)*tokenbytes,(2048%kbs+1)*tokenbytes]],'exact one-token FA write, not wholeblock write exemption')
        for r in rows:
            lo=g['pointer']+r*stride[0]*e;accesses.append((prefix,role,lo,lo+rowbytes,'rw' if kind=='GDN' else 'read'))
            if kind=='GDN':writes[s['pool']].append((lo-p['pointer'],lo+rowbytes-p['pointer']))
        for r,begin,end in s['writes']:
            need(r in rows and 0<=begin<end<=rowbytes,'FA exact write within actual read block')
            lo=g['pointer']+r*stride[0]*e;accesses.append((prefix,role,lo+begin,lo+end,'write'));writes[s['pool']].append((lo+begin-p['pointer'],lo+end-p['pointer']))
    need(len(groups)==64 and sum(k=='GDN' for k,gid in groups.values())==48 and sum(k=='FA' for k,gid in groups.values())==16,'all actual64 kind inventory')
    for prefix,(kind,gid) in groups.items():
        expected={'conv','base','K','U','lambda_log','decay','length'} if kind=='GDN' else {'K','V'}
        need({r for p,r in roles if p==prefix}==expected,'complete all native/private typed roles')
    for i,a in enumerate(accesses):
        for b in accesses[i+1:]:
            if max(a[2],b[2])<min(a[3],b[3]):
                need(a[:2]==b[:2] and a[1] in('K','V') and {a[4],b[4]}=={'read','write'},'actual simultaneously active physical alias')
    return {i:ranges(writes[i],pm[i]['nbytes']) for i in pm}

def compact_sidecar(t,R,raw,expected,slot):
    """New storage scope only: same actual production selected vs compact debug.

    Unselected wholepools are checked by the separate complete byte audit, not
    excused by compacting the production invocation (it remains fullarena).
    """
    import precast as P
    s=raw['compact_sidecar'];b=s['before'];a=s['after'];db=s['debug_before'];da=s['debug_after']
    need(len(b)==len(a)==len(db)==len(da)==13 and s['actual_production_slot']==slot and s['compact_debug_id']==0,'complete13 actual/compact ABI')
    need(b[12].flatten().tolist()==a[12].flatten().tolist()==[slot] and db[12].flatten().tolist()==da[12].flatten().tolist()==[0]
         and b[11].flatten().tolist()==a[11].flatten().tolist()==db[11].flatten().tolist()==da[11].flatten().tolist()==[0,1],'actual vs independent compact ids and individual sequence')
    need(all(bits(t,b[i],db[i]) and bits(t,a[i],da[i]) for i in range(12))
         and bits(t,s['production_output'],s['debug_output']) and bits(t,s['production_output'],raw['output']),'actual production/debug full selected values bitwise')
    for i,name in enumerate(('query','key','value','g','beta')):
        need(bits(t,b[i],raw['inputs'][name]) and bits(t,b[i],a[i]),'actual input immutable/join '+name)
    for i,name in enumerate(('base','k_log','u_log','lambda_log','decay','length'),5):
        need(bits(t,b[i],raw['before'][name]) and bits(t,a[i],raw['after'][name]) and b[i].shape[0]==a[i].shape[0]==1,'exact selected state join '+name)
    need(s['pointers_before']==s['pointers_after'] and s['debug_pointers_before']==s['debug_pointers_after'],'both real kernel pointer/stride/extent stable')
    for name in('sidecar_guards_before','sidecar_guards_after'):
        g=s[name];need(g.shape==(256,) and g.dtype==t.float32 and bool((g==13).all()),'actual debug redzones13')
    need(s['production_debug_bitwise'] is True and s['inputs_unchanged'] is True and s['sidecar_redzones_pass'] is True,'actual transparency execution receipts')
    for i,start in((8,7),(9,1),(10,1)):need(bits(t,b[i][:,:,start:],a[i][:,:,start:]),'selected metadata padding bytes unchanged')
    if int(b[10][0,0,0])<7:need(bits(t,b[5],a[5]),'append base byte invariant')
    y=s['actual_precast_FP32'];need(y.shape==(1,12,128) and y.dtype==t.float32,'actual sidecar FP32 shape')
    return P.evaluate(t,y,raw['output'],expected.unsqueeze(0))

def unchanged_decode(original_tensor_module):
    """Compile the exact old decode AST using only a storage-validator seam."""
    fn=original_tensor_module.decode
    source=Path(original_tensor_module.__file__).read_bytes();tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='decode']
    need(len(nodes)==1,'one actual original decode numerical body')
    # Runtime caller authenticates full old tensor consumer Ref before loading.
    scope=dict(vars(original_tensor_module),actual_sidecar=compact_sidecar)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(original_tensor_module.__file__)+'#compact-storage-validator-only','exec'),scope)
    made=scope['decode']
    need(ast.dump(ast.parse(source).body[next(i for i,n in enumerate(tree.body) if n is nodes[0])])==ast.dump(nodes[0]),'original AST body unchanged')
    return made

def consume_rank(t,T,R,report,load,model_sr,payload_sr,production_ref,debug_ref,*,geometry_ref):
    need(report['schema']=='deltalog.actual-first-decode-all64/v1' and report['source']==payload_sr and report['model_source']==model_sr,'actual source-bound firstdecode report')
    need(report['prefill_tokens']==2048 and report['computed_tokens_before_decode']==2048 and report['decode_query_tokens']==1
        and len(report['rows'])==48 and len({r['prefix'] for r in report['rows']})==48,'one complete actual decode after2K native prefill')
    need({r['prefix'] for r in report['rows']}=={s['prefix'] for s in report['active_metadata']['selections'] if s['kind']=='GDN'},'same actual48 numeric and footprint prefixes')
    need(all(report[k] is False for k in('model_numeric_qualified','reuse_qualified','long160_qualified','graph','performance_qualified','task_qualified')),'no broader qualification')
    f=report['footprint'];need(f['all64_selected_footprint_checked'] is True and f['all48_GDN_core_observed'] is True and f['whole_inactive_bytes_checked'] is True,'actual all64 selected and complete inactive evidence')
    geometry_witness=validate_geometry_witness(report,geometry_ref,load)
    allowed=metadata_union(report['active_metadata']);pool_map={p['index']:p for p in report['active_metadata']['pools']}
    need(report['baseline_manifest'] and len({r['name'] for r in report['baseline_manifest']})==len(report['baseline_manifest'])
         and len(report['baseline_manifest'])==len(allowed) and {r['pool'] for r in report['baseline_manifest']}==set(allowed),'every complete distinct before snapshot, no pool omission')
    for row in report['baseline_manifest']:
        # load authenticates every complete baseline Ref by streaming, but
        # baseline content must NOT be interpreted as JSON or re-materialized.
        load(row['baseline'],kind='streamed-bytes')
        c=load(row['comparison'],kind='json')
        need(c['baseline']==row['baseline'] and c['name']==row['name'] and c['bytewise_inactive_equal'] is True and c['first_difference'] is None and c['qualified'] is False,'actual completed bytewise comparison, never hash-equality substitute')
        need(row['baseline']['bytes']==pool_map[row['pool']]['nbytes'] and tuple(map(tuple,c['allowed_write_ranges']))==allowed[row['pool']],'complete actual pool bytes/exact recomputed allowed union')
    need(report['raw_bytes']==sum(r['raw']['bytes']+r['prefill']['bytes'] for r in report['rows'])<=512*1024**2,'complete unique compact raw ledger512MiB')
    b=report['storage_budget'];allocated=15*1024**3//2
    need(b['absolute_worker_cap_bytes']==8*1024**3 and b['allocated_worker_cap_bytes']==allocated
        and b['raw_cap_bytes']==512*1024**2 and b['control_cap_bytes']==16*1024**2,'unchanged absolute8 and actual allocated7.5/raw/control split')
    need(b['snapshot_bytes']==sum(x['baseline']['bytes']+x['comparison']['bytes']for x in report['baseline_manifest']),'independent complete baseline/comparison byte ledger')
    pre_control=load(b['prefill_control'],kind='json')
    need(pre_control['source']==payload_sr and pre_control['model_source']==model_sr and pre_control['candidate_decode_calls']==0
        and pre_control['wholeinactive_checked'] is False and pre_control['qualified'] is False,'actual source-bound native prefill control')
    final_bytes=len((json.dumps(report,sort_keys=True,allow_nan=False)+'\n').encode())
    geometry_accounting=validate_control_accounting(report,geometry_witness,final_bytes)
    need(len({r['raw']['path'] for r in report['rows']})==len({r['prefill']['path'] for r in report['rows']})==48,'all48 distinct actual prefix/checkpoint raws')
    decode=unchanged_decode(T);records=[]
    for row in report['rows']:
        metrics=None;primary=None
        try:
            selected=next(s for s in report['active_metadata']['selections']if s['prefix']==row['prefix']and s['role']=='base')
            need(selected['kind']=='GDN' and selected['cpu_rows']==selected['gpu_rows']==[row['actual_slot']],'same actual numeric slot and independently checked live footprint')
            need(row['production_library']==production_ref and row['debug_library']==debug_ref
                and row['engine_request_id']==report['request'] and row['generation']==report['generation'],'actual layer/library/request/generation joins')
            pre=load(row['prefill'],kind='torch');raw=load(row['raw'],kind='torch')
            need(pre['source']==payload_sr and pre['model_source']==model_sr and pre['prefix']==row['prefix']
                and pre['engine_request_id']==report['request'] and pre['generation']==report['generation']
                and pre['actual_slot']==row['actual_slot'] and pre['actual_native_clear_chunk_writeback'] is True
                and pre['private_aux_zero'] is True and pre['core_native_chunk_bitwise'] is True,'actual unchanged prefill history boundary and selected physical writeback')
            boundary=pre['state'];need(boundary.dtype==t.float32 and boundary.shape==(1,12,128,128) and bool(t.isfinite(boundary).all()),'complete finite FP32 native prefill boundary')
            need(raw['before']['length'][:,:,0].flatten().tolist()==[0]*12 and raw['actual_ids']==[row['actual_slot']]
                and bits(t,raw['native_before'],boundary),'actual firstdecode native peer from unchanged native boundary')
            _,metrics=decode(t,R,raw,boundary[0].double().clone(),row['actual_slot'])
            need(metrics['passed'],'unchanged original per-layer CPU64/state/native/precast gate')
        except BaseException as e:primary=repr(e)
        records.append(dict(identity=row,metrics=metrics,primary=primary,passed=primary is None))
    return dict(schema='deltalog.independent-first-decode-rank/v1',source=payload_sr,model_source=model_sr,domain=report['domain'],namespace_pid=report['namespace_pid'],geometry_witness=geometry_witness.evidence(),geometry_accounting=geometry_accounting,rows=records,all48_firstdecode_pass=all(r['passed'] for r in records),all64_inactive_byteexact=True,model_qualified=False,long160_qualified=False,lifecycle_reuse_qualified=False,performance_qualified=False,task_qualified=False)
