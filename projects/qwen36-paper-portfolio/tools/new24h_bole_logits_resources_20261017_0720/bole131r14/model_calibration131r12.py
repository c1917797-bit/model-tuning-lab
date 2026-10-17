"""Original118c matrix after real model prefill; no model qualification."""
import io,json,os
from pathlib import Path
import registration_audit131r11 as RA

CAP=32*2**20
BATCH=dict(path='/usr/local/Ascend/cann-9.1.0/opp/vendors/batch_invariant/op_api/lib/libcust_opapi.so',bytes=974520,sha256='ff82d965a8a08bfa2862567022a04a1fd04df56d142f4393f1fb527592111069')
def need(v,s):
 if not v:raise ValueError(s)
def identity(reg):
 ext,ops=RA.refs(reg);return dict(extension=ext,opapi=ops)
def expected(old):
 ext,ops=RA.refs(old);need(len(ops)==1 and BATCH not in ops,'exact old single-vendor calibration')
 return dict(extension=ext,opapi=sorted(ops+[BATCH],key=lambda r:r['path']))
def schema_family(t):
 return {k:dict(schema=str(v),name=v.name,argument_names=[a.name for a in v.arguments],is_mutable=v.is_mutable)for k,v in t.ops._C_ascend.npu_causal_conv1d_custom._schemas.items()}
def own_module(C,own,module):
 need(C.ref(module.__file__)==own['files'][Path(module.__file__).name],'exact new calibration source module')
def run(t,C,sr,own,oldref,rank,native_registration):
 import calibrate_conv118 as K
 own_module(C,own,K);own_module(C,own,RA)
 need(C.obj(sr)==own and type(rank)is int and rank in range(4),'actual model source/rank')
 old=C.obj(oldref);reg=native_registration.actual(t,C,arm_verified=True)
 need(identity(reg)==expected(old['registration']),'exact preregistered old+batch library identities; no subset')
 family=schema_family(t);need(family==old['actual_schema_family'],'unchanged actual callable ABI family')
 root=Path(own['model_receipt_root'])/('CONV-MODEL-CALIBRATION-RANK-%d'%rank)
 need(root.parent==Path(os.environ['BOLE_MODEL_RAW_ROOT'])and not root.exists(),'unique existing owned calibration leaf');root.mkdir()
 refs=[];before=[];used=0
 def save(index,row,kind):
  nonlocal used
  buf=io.BytesIO();t.save(row,buf);raw=buf.getvalue();need(used+len(raw)+1024*1024<=CAP,'32MiB/rank serialization charged within original output budget')
  p=root/('%s-%02d.pt'%(kind,index))
  with p.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
  used+=len(raw);r=C.ref(p);(before if kind=='before'else refs).append(r)
 op=t.ops._C_ascend.npu_causal_conv1d_custom.default
 rows=K.execute(t,op,family['']['schema'],device=t.device('npu',t.npu.current_device()),save=lambda i,r:save(i,r,'row'),save_before=lambda i,r:save(i,r,'before'))
 # CPU tensors from original execute, original double reference. This is only
 # a same-process diagnostic prerequisite; final Devices[] reopens every row.
 report=K.consume(t,rows,require_native_metadata=True)
 after=native_registration.actual(t,C,arm_verified=True)
 value=dict(schema='bole.same-model-initialization-conv-calibration/v131r12',source=sr,rank=rank,old_abi_ref=oldref,actual_schema_family=family,callable_object_id=id(op),registration=reg,registration_after=after,expected_identity=expected(old['registration']),rows=refs,before=before,raw_bytes=used,cap_bytes=CAP,worker_reference=report,worker_diagnostic_only=True,independent_consumer_pending=True,model_ready=False)
 raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(used+len(raw)<=CAP,'whole calibration32MiB')
 p=root/'ABI.json'
 with p.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(root,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 need(identity(after)==identity(reg)==expected(old['registration']),'exact registration stable through original12 matrix')
 need(t.ops._C_ascend.npu_causal_conv1d_custom.default is op,'actual default callable unchanged through original12')
 need(report['pass_gate']and len(rows)==len(refs)==len(before)==12,'all original12 gates before diagnostic tree')
 return C.ref(p)
def validate(C,newref,oldref,sr,rank=None):
 v=C.obj(newref);old=C.obj(oldref);own=C.obj(sr)
 need(v['schema']=='bole.same-model-initialization-conv-calibration/v131r12'and v['source']==sr and v['old_abi_ref']==oldref and v['model_ready']is False,'exact new source/old ABI lineage, no qualification')
 n=v['rank'];need(type(n)is int and n in range(4)and(rank is None or n==rank),'actual rank calibration')
 root=Path(own['model_receipt_root'])/('CONV-MODEL-CALIBRATION-RANK-%d'%n)
 need(Path(newref['path'])==root/'ABI.json'and v['cap_bytes']==CAP,'exact owned source-bound calibration root/cap')
 need(v['actual_schema_family']==old['actual_schema_family']and identity(v['registration'])==identity(v['registration_after'])==v['expected_identity']==expected(old['registration']),'unchanged ABI and entire exact preregistered library set')
 need(type(v['callable_object_id'])is int and v['callable_object_id']>0,'actual worker-local callable identity, not cross-process address qualification')
 need(len(v['rows'])==len(v['before'])==12,'complete12 before/after receipts')
 for kind,refs in(('row',v['rows']),('before',v['before'])):
  for i,r in enumerate(refs):need(Path(r['path'])==root/('%s-%02d.pt'%(kind,i)),'exact ordered raw pathname');C.checked(r)
 need(sum(r['bytes']for r in v['rows']+v['before'])==v['raw_bytes']and v['raw_bytes']+newref['bytes']<=CAP,'entire serialized calibration charged32MiB')
 need(v['worker_reference']['pass_gate']is True and v['worker_diagnostic_only']is True and v['independent_consumer_pending']is True,'worker report diagnostic only')
 return v
def consume(t,C,newref,oldref,sr,rank):
 import calibrate_conv118 as K
 own=C.obj(sr);own_module(C,own,K);v=validate(C,newref,oldref,sr,rank);rows=[]
 for rr,br in zip(v['rows'],v['before']):
  row=t.load(C.checked(rr),map_location='cpu',weights_only=False);pre=t.load(C.checked(br),map_location='cpu',weights_only=False)
  need(tuple(row['before'].shape)==(2*row['batch']+3,3,2560),'original model calibration full2560 channel whole cache')
  need(pre['output']is None and all(pre[k]==row[k]for k in('batch','step','activation')),'original before-call chronology')
  for key in('inputs','weight','indices','before'):
   a,b=pre[key],row[key];need(a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)),'original saved before-call bits '+key)
  rows.append(row)
 report=K.consume(t,rows,require_native_metadata=True);need(report['pass_gate'],'independent original12 numerical/state/inactive gates')
 return dict(abi_ref=newref,old_abi_ref=oldref,rank=rank,independently_recomputed=report,raw_bytes=v['raw_bytes'],model_ready=False)
