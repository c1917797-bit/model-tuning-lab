"""Same full2K 097 arithmetic; three selected pre-BF16 observations only."""
import ast, hashlib, io, json, os, struct, types
from pathlib import Path
TILES=((0,0),(3,2),(19,5))
VARIANT={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-two-residual-new24h-v1-097-repair1/two_residual097.py','bytes':7165,'sha256':'58b68fe106356d5fc608ac09a29728fb45a0aba07e970deabfbb2f87ae63aceb'}
RAW_CAP=32*2**20
FILE_CAP=512*1024
def need(v,s):
    if not v:raise ValueError(s)
def once(s,a,b):
    need(s.count(a)==1,'one exact observation seam');return s.replace(a,b,1)
def adapt_variant(raw):
    need(len(raw)==VARIANT['bytes'] and hashlib.sha256(raw).hexdigest()==VARIANT['sha256'],'actual097 bytes before compile')
    text=raw.decode()
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='_correct_blocks')
    old=ast.get_source_segment(text,node);new=old;changes=[]
    replacements=[
      ('saved={}if trace is not None else None',
       "selected=[(c,h,i*12+h)for c,h in TILES for i,(_,start,length)in enumerate(rows)if start==c*64 and length==64]\n  pick=torch.tensor([i for c,h,i in selected],dtype=torch.int64,device=A.device)\n  saved={}if trace is not None else None"),
      ('saved.update(A32=ap.clone(),X0=xp.clone())','saved.update(A32=ap.index_select(0,pick).clone(),X0=xp.index_select(0,pick).clone())'),
      ("X1.clone(),'R'+str(iteration+1):R.clone()","X1.index_select(0,pick).clone(),'R'+str(iteration+1):R.index_select(0,pick).clone()"),
      ('trace.append(dict(rows=rows,**saved))','trace.append(dict(tiles=[(c,h)for c,h,i in selected],**saved))')]
    for a,b in replacements:new=once(new,a,b);changes.append((a,b))
    inverse=new
    for a,b in reversed(changes):inverse=once(inverse,b,a)
    need(inverse==old,'whole arithmetic body restored, only observations changed')
    ns=dict(__file__=VARIANT['path'],__name__='_round_exact097',TILES=TILES)
    exec(compile(text,VARIANT['path'],'exec'),ns)
    eager=ns['eager'];original_code=eager.__code__
    exec(compile(new,VARIANT['path']+'#three-tile-observation','exec'),ns)
    need(ns['eager'].__code__ is original_code,'original eager/launch/pool/FP32/BF16 arithmetic untouched')
    return types.SimpleNamespace(**ns),dict(original=old,observed=new,replacements=replacements)
def round_f32_bits(bits):
    need(type(bits)is int and 0<=bits<2**32,'exact f32 bits')
    need((bits&0x7f800000)!=0x7f800000,'finite diagnostic domain')
    return ((bits+0x7fff+((bits>>16)&1))>>16)&0xffff
def classify_bits(xbits,bbits,nbits,cbits):
    expected=round_f32_bits(xbits)
    return dict(f32_bits=xbits,actual_B_bits=bbits,native_B_bits=nbits,same_A_CPU64_B_bits=cbits,
        direct_f32_RNE_B_bits=expected,actual_matches_f32_RNE=bbits==expected,
        native_matches_candidate=nbits==bbits,same_A_CPU64_matches_candidate=cbits==bbits,
        f32_ticks_to_bf16_midpoint=abs((xbits&0xffff)-0x8000),
        exactly_at_bf16_midpoint=(xbits&0xffff)==0x8000,
        native_precast='unknown; not observed or modified',exact_real_inverse_rounding_proven=False)
def validate_raw_labels(raw):
    expected={'schema':'mxr.actual-three-tile-rounding-raw/v1','arm':'saved_candidate','variant':'precast'}
    need(type(raw)is dict and all(type(raw.get(k))is str and raw[k]==v for k,v in expected.items()),'strict raw schema/arm/variant ABI')
def compact(torch,t):
    need(t.device.type=='cpu','CPU snapshot')
    t=t.detach().clone(memory_format=torch.contiguous_format)
    need(t.storage_offset()==0 and t.is_contiguous()and t.untyped_storage().nbytes()==t.numel()*t.element_size(),'compact CPU storage')
    return t
def run(torch,chunk,wy,builder,output):
    import wu_boundary as W
    import event_contract as C
    from rounding_stage_trace import Trace
    need(os.environ.get('MXR_WU_BOUNDARY_ENABLE')=='1','existing explicit owner optin')
    root=Path(output);sr=C.reference(W.HERE/'SOURCE_MANIFEST.json');m=C.current(sr,W.HERE)
    need(m['wu_boundary_scope']==W.CONTRACT and str(root)==m['wu_boundary_output']and not root.exists()and root.parent.is_dir(),'new source-owned rounding output')
    spec=W.fixed();donor=C.load(spec['donor'],'_round_actual125')
    own=C.obj(m['rounding_source125'])
    need(own['variant_ref']==VARIANT,'same production097, not diagnostic candidate_refine')
    codec=C.load(spec['codec'],'_round_actual_codec');saved=codec.read(torch,W.checked(spec['case']['raw']))
    x=donor.validate_frame(torch,saved);need(x['cu_seqlens'].tolist()==[0,2048],'full original2K cu')
    runtime=donor.construct_runtime(torch,own)
    variant,delta=adapt_variant(W.checked(VARIANT).read_bytes())
    runtime_variant=runtime['variant']
    need(Path(runtime_variant.__file__).read_bytes()==W.checked(VARIANT).read_bytes(),'actual runtime097 pin')
    A=saved['solve']['A'];need(A.is_contiguous()and tuple(A.shape)==(1,2048,12,64),'full actual A32 layout')
    original_fp=donor.fp(torch,A);root.mkdir(mode=0o700);trace=Trace(sr);captures=[];rows=[];total=0
    try:
        with trace.stage('h2d','saved_candidate',None,'precast'):
            devA=A.to('npu:0');cu=x['cu_seqlens'].to('npu:0')
            W.NG.codepin(builder._build_non_spec_chunked_prefill_metadata,W.NG.BUILDER,'_build_non_spec_chunked_prefill_metadata')
            W.NG.codepin(builder.prepare_chunk_indices,W.NG.UTILS,'prepare_chunk_indices')
            meta=builder._build_non_spec_chunked_prefill_metadata(
                types.SimpleNamespace(vllm_config=types.SimpleNamespace(model_config=types.SimpleNamespace(hf_text_config=types.SimpleNamespace(linear_num_value_heads=48)),parallel_config=types.SimpleNamespace(tensor_parallel_size=4,prefill_context_parallel_size=1))),x['cu_seqlens'],torch.device('npu:0'))
            indices=meta.chunk_indices_chunk64
            W.NG.metadata_values(cu.cpu().tolist(),indices.cpu().tolist())
            need(donor.fp(torch,devA)==original_fp,'full H2D A unchanged')
            geometry=dict(A=original_fp,A_stride=list(A.stride()),device_A_stride=list(devA.stride()),cu=donor.fp(torch,cu),indices=donor.fp(torch,indices),cu_values=cu.cpu().tolist(),indices_values=indices.cpu().tolist(),builder=W.NG.BUILDER,metadata_utils=W.NG.UTILS,T=2048,chunks=32,full_original037_launch=True)
        with trace.stage('call','saved_candidate',None,'precast'):
            B=variant.eager(runtime['solver'],devA,cu,32,torch.bfloat16,runtime['pool'],runtime['backend'],[0,2048],trace=captures)
        with trace.stage('sync','saved_candidate',None,'precast'):torch.npu.synchronize()
        need(donor.equal(torch,B,saved['solve']['output']),'complete saved B bitwise anchor, not only selected tiles')
        geometry.update(full_actual_B=donor.fp(torch,B),A_after=donor.fp(torch,devA),cu_after=donor.fp(torch,cu),indices_after=donor.fp(torch,indices))
        need(donor.fp(torch,devA)==original_fp and donor.equal(torch,cu,x['cu_seqlens']),'full immutable A/cu')
        values={}
        for group in captures:
            for i,tile in enumerate(group['tiles']):
                need(tuple(tile)not in values,'one actual captured tile')
                values[tuple(tile)]={n:compact(torch,group[n][i].detach().cpu())for n in('A32','X0','X1','X2','R1','R2')}
        need(set(values)==set(TILES),'all and only three real selected097 tiles')
        for c,h in TILES:
            z=slice(c*64,(c+1)*64);values[(c,h)]['B']=compact(torch,B[0,z,h].detach().cpu())
        del B,captures
        for name,ar in zip(('saved_candidate','native','cpu64_cast'),spec['arms']):
            arm=torch.load(W.checked(ar),map_location='cpu',weights_only=True)
            need(arm['arm']==name and donor.equal(torch,arm['A'],A),'actual retained same-A arm')
            for c,h in TILES:
                val=compact(torch,arm['B'][0,c*64:(c+1)*64,h])
                if name=='saved_candidate':need(donor.equal(torch,val,values[(c,h)]['B']),'selected saved anchor')
                else:values[(c,h)]['native_B'if name=='native'else'cpu64_sameA_B']=val
            del arm
        for c,h in TILES:
            payload=dict(schema='mxr.actual-three-tile-rounding-raw/v1',source=sr,variant_ref=VARIANT,case=spec['case'],chunk=c,head=h,arm='saved_candidate',variant='precast',
                full_geometry=geometry,full_saved_B_bitwise=True,native_precast='unknown',qualification=False,tensors=values[(c,h)])
            path=root/('saved_candidate-c%02d-precast.pt'%c)
            with trace.stage('serialize','saved_candidate',c,'precast'):
                buffer=io.BytesIO()
                try:
                    torch.save(payload,buffer);size=buffer.tell()
                    need(size<=FILE_CAP and total+size<=RAW_CAP,'actual prewrite512KiB/32MiB unchanged; retain failure')
                    with path.open('xb')as f:f.write(buffer.getbuffer());f.flush();os.fsync(f.fileno())
                finally:buffer.close()
                rr=W.ref(path);need(rr['bytes']==size,'actual durable wire')
            total+=size;rows.append(dict(raw=rr,arm='saved_candidate',chunk=c,head=h,variant='precast',wire_bytes=size))
        return C.write_new(root/'RESULT.json',dict(schema='mxr.actual-three-tile-rounding/v1',source=sr,scope=W.CONTRACT,raw=rows,raw_bytes=total,full_geometry=geometry,timing_events=trace.events,
            diagnostic_complete=True,qualification=False,performance=False,task_accuracy=False,native_precast='unknown',algorithm_arithmetic_changed=False,thresholds_changed=False))
    finally:
        runtime['pool'].finish()
def consume(torch,source,report):
    import wu_boundary as W
    import event_contract as C
    need(report['schema']=='mxr.actual-three-tile-rounding/v1'and report['source']==source and report['scope']==W.CONTRACT and report['diagnostic_complete']is True and report['qualification']is report['performance']is report['task_accuracy']is False,'exact diagnostic scope')
    spec=W.fixed();donor=C.load(spec['donor'],'_round_consumer125')
    codec=C.load(spec['codec'],'_round_consumer_codec');saved=codec.read(torch,W.checked(spec['case']['raw']))
    donor.validate_frame(torch,saved);total=0;rows=[];seen=set()
    geometry=report['full_geometry'];A=saved['solve']['A']
    need(geometry['A']==geometry['A_after']==donor.fp(torch,A) and geometry['A_stride']==geometry['device_A_stride']==list(A.stride()) and geometry['full_actual_B']==donor.fp(torch,saved['solve']['output']) and geometry['T']==2048 and geometry['chunks']==32 and geometry['full_original037_launch']is True and geometry['builder']==W.NG.BUILDER and geometry['metadata_utils']==W.NG.UTILS,'independent full2K geometry and saved B fingerprints')
    W.NG.metadata_values(geometry['cu_values'],geometry['indices_values'])
    for key,shape,values in(('cu',[2],[0,2048]),('indices',[32,2],[x for row in W.NG.CONTRACT['chunk_indices']for x in row])):
        expected=dict(dtype='torch.int32',shape=shape,sha256=hashlib.sha256(struct.pack('<'+'i'*len(values),*values)).hexdigest())
        need(geometry[key]==geometry[key+'_after']==expected,'actual metadata before/after full bytes')
    for r in report['raw']:
        c,h=r['chunk'],r['head'];need((c,h)in TILES and(c,h)not in seen,'exact independent tile set');seen.add((c,h))
        rr=r['raw'];need(rr['bytes']==r['wire_bytes']and rr['bytes']<=FILE_CAP,'actual wire limit');total+=rr['bytes']
        raw=torch.load(W.checked(rr),map_location='cpu',weights_only=True);validate_raw_labels(raw);t=raw['tensors']
        need(raw['source']==source and raw['variant_ref']==VARIANT and raw['case']==spec['case']and(raw['chunk'],raw['head'])==(c,h)and raw['native_precast']=='unknown'and raw['qualification']is False and raw['full_geometry']==geometry and raw['full_saved_B_bitwise']is True,'same actual source/input/tile lineage')
        need(set(t)=={'A32','X0','X1','X2','R1','R2','B','native_B','cpu64_sameA_B'},'complete actual rounding data')
        for name,value in t.items():
            dtype=torch.bfloat16 if name in('B','native_B','cpu64_sameA_B')else torch.float32
            need(value.device.type=='cpu'and value.dtype==dtype and tuple(value.shape)==(64,64)and bool(torch.isfinite(value).all())and value.is_contiguous()and value.storage_offset()==0 and value.untyped_storage().nbytes()==4096*value.element_size(),'actual finite compact tensor ABI')
        need(donor.equal(torch,t['A32'],saved['solve']['A'][0,c*64:(c+1)*64,h])and donor.equal(torch,t['B'],saved['solve']['output'][0,c*64:(c+1)*64,h]),'independent saved A/B byte anchor')
        for name,ar in zip(('saved_candidate','native','cpu64_cast'),spec['arms']):
            actual=torch.load(W.checked(ar),map_location='cpu',weights_only=True)
            need(actual['arm']==name and donor.equal(torch,actual['A'],saved['solve']['A']),'independent exact same A')
            target=t['B'if name=='saved_candidate'else'native_B'if name=='native'else'cpu64_sameA_B']
            need(donor.equal(torch,target,actual['B'][0,c*64:(c+1)*64,h]),'independent retained arm B bytes')
            del actual
        x=struct.unpack('<4096I',t['X2'].view(torch.uint8).numpy().tobytes())
        bits=[struct.unpack('<4096H',t[n].view(torch.uint8).numpy().tobytes())for n in('B','native_B','cpu64_sameA_B')]
        records=[dict(index=[i//64,i%64],**classify_bits(a,b,n,cc))for i,(a,b,n,cc)in enumerate(zip(x,*bits))if b!=n or b!=cc or b!=round_f32_bits(a)]
        need(len(records)<=4096,'bounded complete changed coordinate list')
        M=torch.eye(64,dtype=torch.float64)+t['A32'].double()
        residuals={key:float((torch.eye(64,dtype=torch.float64)-M@t[key].double()).abs().max())for key in('X0','X1','X2')}
        rows.append(dict(arm='saved_candidate',chunk=c,head=h,variant='precast',raw=rr,classification=records,changed_coordinates=len(records),residual_max_abs=residuals,
            real_inverse_not_recomputed=True,native_precast='unknown',qualification=False))
    need(seen==set(TILES)and total==report['raw_bytes']and total<=RAW_CAP,'complete three-tile wire accounting')
    return dict(schema='mxr.native2048-three-tile-rounding-independent/v1',rows=rows,raw_bytes=total,diagnostic_complete=True,qualification=False,performance=False,task_accuracy=False,thresholds_changed=False,native_precast='unknown')

def software_check(torch,source):
    """Actual target-Torch serialization ABI on synthetic CPU values, not NPU data."""
    import wu_boundary as W
    fp=torch.arange(4096,dtype=torch.float32).reshape(64,64)/4096
    tensors={name:fp.clone()for name in('A32','X0','X1','X2','R1','R2')}
    tensors.update({name:fp.to(torch.bfloat16).clone()for name in('B','native_B','cpu64_sameA_B')})
    sizes=[]
    for c,h in TILES:
        payload=dict(schema='mxr.actual-three-tile-rounding-raw/v1',source=source,variant_ref=VARIANT,case=W.fixed()['case'],chunk=c,head=h,arm='saved_candidate',variant='precast',
            full_geometry=dict(synthetic_CPU_fixture=True,A={'dtype':'torch.float32','shape':[1,2048,12,64],'sha256':'0'*64},full_actual_B={'dtype':'torch.bfloat16','shape':[1,2048,12,64],'sha256':'0'*64},indices_values=[[0,i]for i in range(32)],other_metadata_reservation='x'*8192),
            full_saved_B_bitwise=False,native_precast='unknown',qualification=False,tensors=tensors)
        b=io.BytesIO();torch.save(payload,b);sizes.append(b.tell())
        need(0<b.tell()<=FILE_CAP,'actual same-image nine-tensor serialized fixture cap')
        b.seek(0);loaded=torch.load(b,map_location='cpu',weights_only=True)
        need(set(loaded['tensors'])==set(tensors),'complete independent Torch reload')
        for name,t in loaded['tensors'].items():
            need(torch.equal(t.view(torch.uint8),tensors[name].view(torch.uint8))and t.untyped_storage().nbytes()==t.numel()*t.element_size(),'actual serialized exact compact tensor bytes')
        b.close()
    for bits in(0,0x80000000,0x3f808000,0x3f808001,0xbf818000,0x00008001):
        f=struct.unpack('<f',struct.pack('<I',bits))[0]
        v=torch.tensor([f],dtype=torch.float32).to(torch.bfloat16).view(torch.uint16).item()
        need(v==round_f32_bits(bits),'same-image direct FP32 to BF16 RNE ABI')
    return dict(schema='mxr.rounding-same-image-serialization-fixture/v1',source=source,synthetic_CPU_values=True,actual_Torch_roundtrip=True,wire_bytes=sizes,single_cap=FILE_CAP,total_cap=RAW_CAP,qualification=False,NPU=False)
