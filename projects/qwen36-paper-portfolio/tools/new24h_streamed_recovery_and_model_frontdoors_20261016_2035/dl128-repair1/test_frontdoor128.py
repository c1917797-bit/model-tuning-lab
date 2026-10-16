"""Future-receipt SHAPE fixture, never persisted or passed off as actual data."""
import copy,hashlib,json,os,sys,unittest,tempfile
from unittest.mock import patch
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import receiver128 as R,io128 as IO
import test_receiver128 as _software
_TEMPS=[]
def fixture():
 _,m,o,_=_software.Controls().fixture();bundle=json.loads((P/'FAULT_FIXTURE128.json').read_bytes())['bundle'];er=bundle['refs']
 def fr(label,path=None):return dict(path=path or '/SOFTWARE_ONLY128/'+label+'.json',bytes=1,sha256=hashlib.sha256(label.encode()).hexdigest())
 special={'source':er['source'],'owner':er['owner'],'producer':er['producer'],'old':er['strict']}
 refs={}
 def rr(label):
  if label not in refs:refs[label]=special.get(label,fr(label))
  return refs[label]
 def convert(x):
  if type(x)is dict:
   if set(x)=={'label'}:return rr(x['label'])
   return{k:convert(v)for k,v in x.items()}
  if type(x)is list:return[convert(v)for v in x]
  return x
 m,o=convert(m),convert(o);docs={}
 key=lambda r:json.dumps(r,sort_keys=True)
 def put(r,v):docs[key(r)]=v
 for label,value in o.items():put(rr(label),value)
 s=o['source'];p=o['producer'];mathroot=er['source']['path'].rsplit('/',1)[0]
 s['files'].update({'entry.py':fr('entry',mathroot+'/entry.py'),'raw_reader_entry.py':fr('rawentry',mathroot+'/raw_reader_entry.py')});m['reviewed_domain_files']=s['files'];o['template']['files']=s['files']
 for j,row in enumerate(p['records']):row.setdefault('raw',fr('raw-%d'%j))
 authority=bundle['small_documents']['owner']['authority'];life=fr('lifecycle');s['lifecycle_source_ref']=life
 p.update(authority=authority,lifecycle=life)
 plan=o['plan'];plan.update(schema='deltalog.fresh-bridge-plan/v2',authority=authority,lifecycle=life,steps=160,physical=5,logical=0,graph=False,phase_seconds=1800,cleanup_seconds=90,output='/SOFTWARE_ONLY128/old/numeric/result')
 for label,doc in bundle['small_documents'].items():put(er[label],copy.deepcopy(doc))
 put(er['source'],s);put(er['producer'],p)
 for v in bundle['inspect'].values():put(v['ref'],v['projection'])
 put(R.FAULT,bundle)
 rt=json.loads((Path(os.environ['SOURCE128_RECOVERY_PREDECESSOR'])/'SOURCE_TEMPLATE.json').read_bytes());put(R.R2_TEMPLATE,rt)
 temp=tempfile.TemporaryDirectory(prefix='receiver128-shape-');_TEMPS.append(temp);rt['root']=Path(temp.name).as_posix()
 base=Path('/SOFTWARE_ONLY128/new-recovery');ownref=fr('new-owner',str(base/'RESULT.json'));rs=fr('new-consumer-source')
 stage_ref=fr('new-stage',str(base/'native/result/STAGE_RESULT.json'));cleanup_ref=fr('new-cleanup',str(base/'native/cleanup-verdict.json'));inspect_ref=fr('new-inspect',str(base/'native/inspect-exited.json'));domain_ref=fr('domain');envelope_ref=fr('new-envelope')
 arm_ref,device_ref,hs_ref=fr('old-arm'),fr('old-device'),fr('old-handshake')
 required=[er['source'],er['producer'],er['owner'],er['strict'],er['numeric_cleanup'],er['consumer_cleanup'],*[x['raw']for x in p['records']],*p['actual_sidecar_records']]
 reader=dict(schema='deltalog.deadpayload-native-bridge-source/v024',prepared_only=False,bound=True,prepared_template=R.R2_TEMPLATE,files=rt['files'],root=rt['root'],producer_source=er['source'],original_source_ref=er['source'],original_producer_ref=er['producer'],original_failed_owner_ref=er['owner'],original_strict_ref=er['strict'],actual_fault_evidence_ref=R.FAULT,original_timeout_seconds=585.6111058300012,allowed_fault='exact-original-domain-TimeoutExpired-shared590',recovery_refs=required,lifecycle_source_ref=life,original_arm_ref=arm_ref,original_device_ref=device_ref,original_handshake_ref=hs_ref,original_plan_ref=p['plan'])
 idx=_software.load(Path(os.environ['SOURCE128_RECOVERY_PREDECESSOR'])/'readset127.py','_128_real_index_fixture')
 unique={v['path']:v for v in required};data=b''.join(idx.encoded(unique[k])for k in sorted(unique));indexpath=Path(temp.name)/'RECOVERY_READSET127.jsonl';indexpath.write_bytes(data)
 parents=sorted({str(__import__('pathlib').PurePosixPath(k).parent)for k in unique})
 descriptor=dict(schema=idx.SCHEMA,index_ref=IO.ref(indexpath),entries=len(unique),parents=parents,parent_count=len(parents));descriptor['index_ref']['path']=indexpath.as_posix()
 reader.pop('recovery_refs');reader['recovery_readset_index']=descriptor
 put(rs,reader)
 cid='c'*64;put(cleanup_ref,dict(cid=cid,errors=[],secondary_guard_cleanup=[],resource_release_verified=True,stopped=True,retained=True,unresolved_active_cid=None))
 owner=dict(schema='deltalog.fresh-bridge-owned-host/v5',source=rs,target_source=rs,stage='cpu',steps=16,physical=[],NPU=False,primary=None,secondary=[],stopped_retained=True,resource_admitted=True,bridge_primitive_gate_pass=False,full_gdn_qualified=False,model_ready=False,result=stage_ref,authority=authority);put(ownref,owner)
 flags=dict(NPU=False,NPU_reexecuted=False,model_ready=False,model_admitted=False,performance_ready=False)
 stage=dict(schema='deltalog.anchor-consumer-CPU-recovery/v127',source=rs,authority=authority,producer_source=er['source'],actual_original_producer=er['producer'],original_failed_owner=er['owner'],preserved_original_strict=er['strict'],actual_fault_evidence=R.FAULT,consumer_envelope=envelope_ref,domain=domain_ref,pass_gate=True,diagnostic_capture_complete=True,domain_checks_pass=True,old_failure_unchanged=True,**flags);put(stage_ref,stage)
 put(envelope_ref,dict(schema='deltalog.anchor-consumer-diagnostic/v127',consumer_source=rs,producer_source=er['source'],producer=er['producer'],preserved_original_strict=er['strict'],domain=domain_ref,original_domain_exit=0,NPU_reexecuted=False,qualification=False,model_admitted=False))
 args=['/usr/local/python3.12.13/bin/python3','-I','-B',rt['files']['entry.py']['path'],'--execute','--stage','cpu-preflight','--source-ref',json.dumps(rs),'--authority-ref',json.dumps(authority),'--lifecycle-ref',json.dumps(life),'--steps','16','--output',str(base/'native/result')]
 cmd=['/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','dldeadbridge024']+args
 parents={Path(r['path']).parent for r in[rs,R.R2_TEMPLATE,*rt['files'].values(),descriptor['index_ref'],*required]};parents.update((Path(rt['root']),Path(er['source']['path']).parent,Path(authority['path']).parent));parents={q for q in parents if not any(v!=q and v in q.parents for v in parents)}
 mounts={str(q):(str(q),False)for q in parents};mounts['/usr/local/Ascend/driver']=('/usr/local/Ascend/driver',False);mounts[str(base/'native')]=(str(base/'native'),True)
 x=dict(Id=cid,Image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',ExecIDs=None,State=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False),HostConfig=dict(Devices=[],DeviceRequests=None,DeviceCgroupRules=None,Privileged=False,NetworkMode='none',Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,CapDrop=['ALL'],SecurityOpt=['no-new-privileges']),Config=dict(Labels={'qwen36.owner':'deltalog-anchor-consumer-recovery-new24h-MAIN-127-repair3','qwen36.stage':'native','deltalog-fresh-bridge.owner-source-sha256':rs['sha256']},Env=['TORCH_DEVICE_BACKEND_AUTOLOAD=0','ASCEND_RT_VISIBLE_DEVICES=','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1'],Cmd=cmd),Mounts=[dict(Destination=d,Source=a,RW=b)for d,(a,b)in mounts.items()])
 put(inspect_ref,dict(exit_code=0,stdout=json.dumps([x])))
 oldcid=bundle['small_documents']['numeric_cleanup']['cid'];tail=['0']*20;tail[19]='42'
 dv=dict(logical=0,physical=5,visible='0',canary=[4.,5.],plan=p['plan'],cgroup=oldcid,pid=1,stat='1 (entry) '+' '.join(tail));put(device_ref,dv)
 aa=['/usr/local/python3.12.13/bin/python3','-I','-B',s['files']['entry.py']['path'],'--execute','--stage','numeric','--source-ref',json.dumps(er['source']),'--authority-ref',json.dumps(authority),'--lifecycle-ref',json.dumps(life),'--steps','160','--output',plan['output'],'--plan-ref',json.dumps(p['plan']),'--cpu-preflight-ref',json.dumps(plan['cpu_preflight'])]
 put(arm_ref,dict(physical=5,pid=123,start_ticks=42,cgroup=oldcid,namespace_pids=[123,1],argv=aa));put(hs_ref,dict(schema='deltalog.fresh-bridge-arm/v2',pid=1,plan_sha256=p['plan']['sha256'],physical=5))
 source_ref=fr('current128-source');ip=dict(schema='deltalog.recovered-component-model-input/v128',receiver_source_ref=source_ref,old_model_template_ref=R.OLD_TEMPLATE,recovery_template_ref=R.R2_TEMPLATE,actual_fault_ref=R.FAULT,recovery_owner_ref=ownref,recovery_cleanup_ref=cleanup_ref,recovery_inspect_ref=inspect_ref,component_cpu_owner_ref=m['component_cpu_owner_ref'])
 class Reader:
  need=staticmethod(IO.need)
  @staticmethod
  def obj(r):return docs[key(r)]
  @staticmethod
  def obj_file(r):
   if r==rt['files']['provenance127.py']:return Path(os.environ['SOURCE128_RECOVERY_PREDECESSOR'])/'provenance127.py'
   if r==rt['files']['readset127.py']:return Path(os.environ['SOURCE128_RECOVERY_PREDECESSOR'])/'readset127.py'
   return None # SHAPE fixture only: real entry uses actual hash-verifying reader.
  @staticmethod
  def streamed(r):return IO.obj_file(r)if r==descriptor['index_ref']else None # Only data existence is fixture-shaped; index parsing/SHA is actual.
 return Reader,m,ip,source_ref,docs,rs,stage_ref,inspect_ref
class Frontdoor(unittest.TestCase):
 def test_actual_function_full_recovery_shape(self):
  C,m,p,s,docs,rs,stage,inspect=fixture()
  with patch.object(R,'streamed',C.streamed):o,prod,r,proof=R.load_recovery(C,m,p,s)
  self.assertIsNotNone(o['primary']);self.assertTrue(r['domain_checks_pass']);self.assertEqual(proof['consumer_source'],rs)
 def test_wrong_device_source_mount_or_CPU_failure_rejects(self):
  for change in ('device','source','mount','failed','stage'):
   C,m,p,s,docs,rs,stage,inspect=fixture();key=lambda r:json.dumps(r,sort_keys=True)
   if change in ('device','source','mount'):
    x=json.loads(docs[key(inspect)]['stdout'])[0]
    if change=='device':x['HostConfig']['Devices']=[{'PathOnHost':'/dev/davinci5'}]
    elif change=='source':x['Config']['Labels']['deltalog-fresh-bridge.owner-source-sha256']='0'*64
    else:x['Mounts'].pop()
    docs[key(inspect)]['stdout']=json.dumps([x])
   elif change=='failed':docs[key(p['recovery_owner_ref'])]['primary']='failed'
   else:docs[key(stage)]['producer_source']={'wrong':'source'}
   with patch.object(R,'streamed',C.streamed),self.assertRaises(ValueError):R.load_recovery(C,m,p,s)
