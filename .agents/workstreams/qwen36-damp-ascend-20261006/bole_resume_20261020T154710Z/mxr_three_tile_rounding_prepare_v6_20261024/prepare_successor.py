"""Source-only three-tile rounding successor. Original Owned controller retained."""
import ast,copy,hashlib,json
from pathlib import Path
WORK=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
PREP=WORK/'mxr_three_tile_rounding_prepare_v6_20261024'
ROOT=PREP/'prepared-source'
PARENT={'path':str(WORK/'mxr_private_terminal_observer_prepare_v2_20261023/prepared-source/SOURCE_MANIFEST.json'),'bytes':151216,'sha256':'3f3d79ad102d32a9792c8b55d4509bd54a7e090b5eb99be558834832fc2b43a1'}
BUILDER=WORK/'mxr_private_terminal_observer_prepare_v2_20261023/prepare_successor.py'
OUTPUTS={s:'/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-THREE_TILE_ROUNDING_'+s+'_20261024_V6'for s in('CPU','NPU')}
def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
    p=Path(r['path']);need(type(r)is dict and set(r)=={'path','bytes','sha256'}and p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'exact immutable successor ref');return p
def once(s,a,b):
    need(s.count(a)==1,'exact successor source seam '+a[:60]);return s.replace(a,b,1)
def function(s,name,body):
    n=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name==name)
    return once(s,ast.get_source_segment(s,n),body)
B=dict(__file__=str(BUILDER),__name__='_rounding_original_owner')
exec(compile(BUILDER.read_bytes(),str(BUILDER),'exec'),B)
def render():
    parent=json.loads(checked(PARENT).read_bytes());before={n:checked(r).read_bytes()for n,r in parent['files'].items()};f=dict(before)
    w=f['wu_boundary.py'].decode()
    w=once(w,'CHUNKS=(31,)','CHUNKS=(0,3,19)')
    n=next(n for n in ast.parse(w).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='CONTRACT'for t in n.targets))
    contract="CONTRACT=dict(schema='mxr.native2048-three-tile-rounding/v1',chunks=list(CHUNKS),arms=['saved_candidate'],tiles=[[0,0],[3,2],[19,5]],tokens_per_matrix=64,heads_q=4,heads_v=12,width=128,variants=['precast'],raw_cap_bytes=32*2**20,qualification=False,performance=False,thresholds_changed=False,launch_geometry=NG.CONTRACT)"
    w=once(w,ast.get_source_segment(w,n),contract)
    w=function(w,'run',"def run(torch,chunk,wy,builder,output):\n    from rounding_capture import run as capture\n    return capture(torch,chunk,wy,builder,output)")
    f['wu_boundary.py']=w.encode()
    f['native_geometry.py']=once(f['native_geometry.py'].decode(),'selected_source_tokens=[1984,2048]','selected_source_tokens=None,selected_tiles=[[0,0],[3,2],[19,5]]').encode()
    c=f['wu_consume.py'].decode()
    c=function(c,'consume',"def consume(torch,source,report):\n    from rounding_capture import consume as classify\n    return classify(torch,source,report)")
    c=c.replace('mxr.native2048-chunk31-WU-independent','mxr.native2048-three-tile-rounding-independent')
    f['wu_consume.py']=c.encode()
    soft=f['event_software.py'].decode()
    soft=once(soft,"write_new(a.output.parent/'COMPACT_SERIALIZATION.json',compact)",chr(10).join(["write_new(a.output.parent/'COMPACT_SERIALIZATION.json',compact)","    from rounding_capture import software_check","    write_new(a.output.parent/'ROUNDING_SERIALIZATION.json',software_check(torch,sr))"]))
    f['event_software.py']=soft.encode()
    for name in('event_host.py','test_exact_wrapper.py'):
        h=f[name].decode().replace('mxr.native2048-chunk31-WU-independent','mxr.native2048-three-tile-rounding-independent')
        h=h.replace('ACTUAL_NATIVE2048_CHUNK31_WU_DIAGNOSTIC_NOT_QUALIFICATION','ACTUAL_THREE_TILE_ROUNDING_DIAGNOSTIC_NOT_QUALIFICATION')
        h=h.replace('mxr-wu-native2048-chunk31-single6-20261023-v2','mxr-three-tile-rounding-single6-20261024-v6')
        f[name]=h.encode()
    prior=WORK/'mxr_three_tile_rounding_prepare_v1_20261024'
    pinned={'prepare_successor.py':(7891,'64de7069b9a5d2c5b3f45928655a4b4e16741afe1ce740d518df8919c9d4daf7'),'rounding_capture.py':(16005,'89cad8d5f988a402349be4b8a008613dfc66bfe4c83da97112afeb2731f8da47'),'test_rounding.py':(2153,'5941790b6f4c164254bd89c24b7339bf9ccc85f18abf76ce64966a32cc2890a4')}
    for name,(size,sha)in pinned.items():checked(dict(path=str(prior/name),bytes=size,sha256=sha))
    f['successor_bindings.py']=once(f['successor_bindings.py'].decode(),'mxr_private_terminal_observer_prepare_v2_20261023','mxr_three_tile_rounding_prepare_v6_20261024').encode()
    bindings=f['successor_bindings.py'].decode()
    bindings=once(bindings,"def checked(r):","def checked(r, *, preparation=False):")
    bindings=once(bindings,"r['bytes']>0,","(r['bytes']>0 or (preparation is True and r == dict(path=r['path'],bytes=0,sha256=EMPTY_SHA) and r['path'] in EMPTY_PREPARATION_PATHS)),")
    bindings=once(bindings,"for r in m['preparation_readset']:checked(r)","for r in m['preparation_readset']:checked(r,preparation=True)")
    prefix="EMPTY_SHA='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'\nEMPTY_PREPARATION_PATHS=frozenset('/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-mxr-y16-build-owned-main-R156_038_001/cpu/build/'+n for n in ('compile.stderr','compile.stdout','nm.stderr'))\n"
    bindings=once(bindings,"def need(v,s):",prefix+"def need(v,s):")
    f['successor_bindings.py']=bindings.encode()
    for name in('rounding_capture.py','prepare_successor.py','test_rounding.py'):f[name]=(PREP/name).read_bytes()
    predecessor=WORK/'mxr_three_tile_rounding_prepare_v2_20261024'
    predecessor_refs=[dict(path=str(predecessor/n),bytes=size,sha256=sha)for n,size,sha in(
        ('prepare_successor.py',8577,'da61bc2dec6c3493e8e4caf2de4d71da2bb16c154c4ea5c7cb38bbe7188b4eae'),
        ('rounding_capture.py',16305,'5f0d3c7c6205e33293ad26e66ba4efb471e9c0bd2c8764af2c3372524ff5f536'),
        ('test_rounding.py',2711,'a184072346cd8b1b170cdcb36a79800c95e6993b3b7666e33ea3cc3b6c8b162b'))]
    for r in predecessor_refs:checked(r)
    c=f['event_contract.py'].decode()
    helper="def preparation_checked(ref):\n    # Exact preparation evidence domain only; normal checked remains nonempty.\n    from successor_bindings import checked as exact_preparation_reader\n    return exact_preparation_reader(ref,preparation=True)\n"
    c=once(c,"def obj(ref):",helper+"def obj(ref):")
    f['event_contract.py']=c.encode()
    h=f['event_host.py'].decode()
    h=once(h,"for item in[sr,AUTHORITY_REF,obj(AUTHORITY_REF)['MAIN_review_ref'],m['prepared_template_ref'],*m['preparation_readset'],*m['files'].values(),*[x['ref']for x in FRAME_REFS]]:","for item in[sr,AUTHORITY_REF,obj(AUTHORITY_REF)['MAIN_review_ref'],m['prepared_template_ref'],*m['files'].values(),*[x['ref']for x in FRAME_REFS]]:")
    h=once(h,"    need(prerequisites is None,'no GE qualification borrowed for exact H')","    from event_contract import preparation_checked\n    for item in m['preparation_readset']:\n        preparation_checked(item);need(item['path']not in catalog or catalog[item['path']]==item,'whole unambiguous preparation evidence readset');catalog[item['path']]=item\n    need(prerequisites is None,'no GE qualification borrowed for exact H')")
    h=once(h,"    checked_after(r,obj(source['actual_input_ref']),O.readset_checked)","    if r in source['preparation_readset']:\n        from event_contract import preparation_checked\n        preparation_checked(r)\n    checked_after(r,obj(source['actual_input_ref']),O.readset_checked)")
    f['event_host.py']=h.encode()
    predecessor3=WORK/'mxr_three_tile_rounding_prepare_v3_20261024'
    predecessor3_refs=[dict(path=str(predecessor3/n),bytes=size,sha256=sha)for n,size,sha in(
        ('prepare_successor.py',9989,'276377aec33e744ff298788ff2691bfe4b64f56f70e550380cebd2b4f681820f'),
        ('test_empty_evidence.py',5015,'16bb33459671400775aacdd62db8f9c7ed309c6290d6a4606a2155336661227c'))]
    for r in predecessor3_refs:checked(r)
    fixture=f['wu_cpu_fixture.py'].decode()
    # Historical storage-view regression is independent of the new capture tiles.
    fixture=once(fixture,"for ordinal in W.CHUNKS:rows.append(case(actual['B'],actual['G'],arm,ordinal,raw_ref))","for ordinal in (31,):rows.append(case(actual['B'],actual['G'],arm,ordinal,raw_ref))")
    f['wu_cpu_fixture.py']=fixture.encode()
    predecessor4=WORK/'mxr_three_tile_rounding_prepare_v4_20261024'
    predecessor4_refs=[dict(path=str(predecessor4/'prepare_successor.py'),bytes=11949,sha256='9d351a436a06289663e4017ae596ad9c4b116a7c9f1d2b66a8b4c0cd34efe485'),
        dict(path=str(predecessor4/'test_audit_closure.py'),bytes=7684,sha256='90d6729a09c9db72572014d84485f9b7b8b16ce41a09a467d4f1197d1b556df5')]
    for r in predecessor4_refs:checked(r)
    trace=f['wu_stage_trace.py'].decode()
    trace=once(trace,"STAGES=('cpu_reference','h2d','call','sync','d2h','compact','serialize','metrics')","STAGES=('h2d','call','sync','serialize')")
    trace=once(trace,"VARIANTS=('original','explicit_W_ieee','bf16_operand_negative')","VARIANTS=('precast',)")
    trace=once(trace,"mxr.native2048-chunk31-stage/v1","mxr.native2048-three-tile-rounding-stage/v1")
    trace=once(trace,"MXR_CHUNK31_STAGE ","MXR_THREE_TILE_STAGE ")
    trace=once(trace,"if self.failed or self.active or stage not in STAGES or arm!='saved_candidate'or type(chunk)is not int or chunk!=31 or variant not in(*VARIANTS,None):","if self.failed or self.active or type(stage)is not str or stage not in STAGES or type(arm)is not str or arm!='saved_candidate' or type(variant)is not str or variant!='precast':")
    trace=once(trace,"if (stage in('cpu_reference','h2d'))!=(variant is None):raise ValueError('exact variant stage')","if not ((stage in ('h2d','call','sync') and chunk is None) or (stage=='serialize' and type(chunk)is int and chunk in (0,3,19))):raise ValueError('exact whole2K versus selected-tile stage')")
    f['rounding_stage_trace.py']=trace.encode()
    f['trace_contract_check.py']=(PREP/'trace_contract_check.py').read_bytes()
    soft=f['event_software.py'].decode()
    hook="    write_new(a.output.parent/'ROUNDING_SERIALIZATION.json',software_check(torch,sr))"
    soft=once(soft,hook,hook+"\n    from trace_contract_check import check as check_trace_contract\n    write_new(a.output.parent/'TRACE_CONTRACT.json',check_trace_contract(sr))")
    f['event_software.py']=soft.encode()
    predecessor5=WORK/'mxr_three_tile_rounding_prepare_v5_20261024'
    predecessor5_refs=[dict(path=str(predecessor5/'prepare_successor.py'),bytes=12757,sha256='9198f35559aa3f9eb4f94bd48eabe82d85ed4a5dea93b85fa62ca4e592481527'),
        dict(path=str(predecessor5/'rounding_capture.py'),bytes=16305,sha256='5f0d3c7c6205e33293ad26e66ba4efb471e9c0bd2c8764af2c3372524ff5f536')]
    for r in predecessor5_refs:checked(r)
    donor=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-third-residual-saved3frame-new24h-v1-125/SOURCE_MANIFEST.json')
    own=json.loads(donor.read_bytes())
    oldrefs={r['path']:(n,r)for n,r in parent['files'].items()}
    nr={n:dict(path=str(ROOT/n),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for n,b in sorted(f.items())}
    def rebase(v):
        if type(v)is dict:
            if set(v)=={'path','bytes','sha256'}and v['path']in oldrefs:
                n,r=oldrefs[v['path']];need(v==r,'same parent source reference');return nr[n]
            return{k:rebase(x)for k,x in v.items()}
        if type(v)is list:return[rebase(x)for x in v]
        return v
    m=rebase(copy.deepcopy(parent));cat={r['path']:r for r in parent['preparation_readset']}
    extra=[PARENT,ref(BUILDER),ref(WORK/'mxr_three_tile_rounding_prepare_v1_20261024/prepare_successor.py'),ref(WORK/'mxr_three_tile_rounding_prepare_v1_20261024/rounding_capture.py'),ref(WORK/'mxr_three_tile_rounding_prepare_v1_20261024/test_rounding.py'),ref(donor),own['variant_ref'],own['common_precision'],own['component044'],own['actual037_prerequisite'],own['files']['third_residual125.py'],*[ref(PREP/n)for n in('rounding_capture.py','prepare_successor.py','test_rounding.py')],*parent['files'].values()]
    extra+=predecessor_refs+predecessor3_refs+predecessor4_refs+predecessor5_refs+[ref(PREP/'trace_contract_check.py')]
    component=json.loads(checked(own['component044']).read_bytes());extra+=list(component['files'].values())
    passed=json.loads(checked(own['actual037_prerequisite']).read_bytes());extra+=passed['readset']
    for r in extra:
        checked(r);need(r['path']not in cat or cat[r['path']]==r,'no readset identity conflict');cat[r['path']]=r
    ns=dict(__file__=str(PREP/'rounding_capture.py'),__name__='_round_source')
    exec(compile(f['rounding_capture.py'],ns['__file__'],'exec'),ns)
    _,observation_inverse=ns['adapt_variant'](checked(ns['VARIANT']).read_bytes())
    scope=dict(schema='mxr.native2048-three-tile-rounding/v1',chunks=[0,3,19],arms=['saved_candidate'],tiles=[[0,0],[3,2],[19,5]],tokens_per_matrix=64,heads_q=4,heads_v=12,width=128,variants=['precast'],raw_cap_bytes=32*2**20,qualification=False,performance=False,thresholds_changed=False,launch_geometry=parent['wu_boundary_scope']['launch_geometry'])
    scope['launch_geometry']=dict(scope['launch_geometry'],selected_source_tokens=None,selected_tiles=[[0,0],[3,2],[19,5]])
    m.update(root=str(ROOT),files=nr,outputs=OUTPUTS,prepared_only=True,authority_ref=None,prepared_template_ref=None,status='PREPARED_MAIN_AUTHORITY_PENDING',
        parent_source_ref=PARENT,preparation_readset=list(cat.values()),wu_boundary_scope=scope,wu_boundary_output=OUTPUTS['NPU']+'/physical6/numeric/actual-native',rounding_source125=ref(donor))
    need(m['resources']==parent['resources']and m['window']==parent['window']and(m['phase_seconds'],m['child_seconds'],m['cleanup_seconds'])==(600,300,90),'original resources/window retained')
    for n,b in f.items():
        if n.endswith('.py'):compile(b,n,'exec')
    delta={n:dict(before=before[n].decode()if n in before else None,after=b.decode())for n,b in f.items()if before.get(n)!=b}
    return dict(files=f,manifest=m,before=before,parent=parent,delta=dict(schema='mxr.three-tile-rounding-source-inverse/v1',changed_files=delta,parent_source_ref=PARENT,observation_inverse=observation_inverse))
def inverse(b):
    out=dict(b['files']);old=b['before'];delta=b['delta']['changed_files']
    need({n for n in set(out)|set(old)if out.get(n)!=old.get(n)}==set(delta),'exact full inverse domain')
    for n,v in delta.items():
        need(out[n].decode()==v['after']and v['before']==(old[n].decode()if n in old else None),'actual inverse values')
        if n in old:out[n]=v['before'].encode()
        else:del out[n]
    need(out==old,'entire immutable parent restored');return out
PUB=B['PUB'];PUB.update(PREP=PREP,ROOT=ROOT,OUTPUTS=OUTPUTS,render=render,inverse=inverse)
def main():return PUB['main']()
if __name__=='__main__':main()
