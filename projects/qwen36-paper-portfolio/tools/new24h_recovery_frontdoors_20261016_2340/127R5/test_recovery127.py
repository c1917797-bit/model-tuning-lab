import copy,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import provenance127 as V,entry127 as E,host as H
class RecoveryTests(unittest.TestCase):
 def fixture(self):
  e=json.loads((P/'FAULT_FIXTURE127.json').read_bytes())['bundle'];refs=e['refs']
  docs={json.dumps(refs[k],sort_keys=True):v for k,v in e['small_documents'].items()}
  for x in e['inspect'].values():docs[json.dumps(x['ref'],sort_keys=True)]=x['projection']
  # Only provenance-schema fields are synthesized here. They are NOT raw data,
  # not a numerical PASS and not persisted binding. Runtime binder opens actual
  # remote source/producer and verifies every681 descriptor and recursive blob.
  source=dict(files={'raw_reader_entry.py':dict(path=refs['source']['path'].rsplit('/',1)[0]+'/raw_reader_entry.py')})
  producer=dict(source=refs['source'],primary=None,steps=160,NPU=True,graph=False,records=[dict(raw=dict(path='main-%d'%i))for i in range(328)],actual_sidecar_records=[dict(path='side-%d'%i)for i in range(351)])
  docs[json.dumps(refs['source'],sort_keys=True)]=source;docs[json.dumps(refs['producer'],sort_keys=True)]=producer
  return e,docs
 def validate(self,e,docs):return V.validate(e,lambda r:docs[json.dumps(r,sort_keys=True)])
 def test_actual_fault_documents_shape(self):
  e,d=self.fixture();self.validate(e,d)
 def test_wrong_fault_or_timeout_rejected(self):
  for token in ('TimeoutExpired','585.6111058300012'):
   e,d=self.fixture();log=d[json.dumps(e['refs']['logs'],sort_keys=True)];log['stderr']=log['stderr'].replace(token,'WRONG')
   with self.assertRaises((ValueError,SyntaxError)):self.validate(e,d)
 def test_missing_or_wrong_original_ref_rejected(self):
  e,d=self.fixture();e['refs']['owner']['sha256']='0'*64
  with self.assertRaises(KeyError):self.validate(e,d)
 def test_release_OR_device_mismatch_rejected(self):
  for which in ('running','devices','release','oldsuccess'):
   e,d=self.fixture()
   if which=='running':e['inspect']['consumer']['projection']['state']['Running']=True
   elif which=='devices':e['inspect']['consumer']['projection']['devices']=[{'PathOnHost':'/dev/davinci5'}]
   elif which=='release':d[json.dumps(e['refs']['numeric_cleanup'],sort_keys=True)]['resource_release_verified']=False
   else:d[json.dumps(e['refs']['owner'],sort_keys=True)]['primary']=None
   with self.assertRaises(ValueError):self.validate(e,d)
 def test_incomplete681_rejected(self):
  e,d=self.fixture();d[json.dumps(e['refs']['producer'],sort_keys=True)]['actual_sidecar_records'].pop()
  with self.assertRaises(ValueError):self.validate(e,d)
 def test_host_whole_body_inverse(self):
  edits=json.loads((P/'HOST_EDITS127.json').read_bytes());text=(P/'host.py').read_text(encoding='utf8')
  r4=json.loads((P/'EDITS127R4.json').read_bytes())
  for before,after in reversed(r4['host.py']):
   self.assertEqual(text.count(after),1);text=text.replace(after,before,1)
  text=text.replace('127-repair4','127-repair3').replace('127repair4','127repair3')
  for old,new in reversed(edits['edits']):
   self.assertEqual(text.count(new),1);text=text.replace(new,old)
  donor=Path(os.environ['SOURCE127_DONOR_HOST']).read_bytes()
  self.assertEqual(hashlib.sha256(donor).hexdigest(),edits['donor']['sha256'])
  self.assertEqual(text,donor.decode('utf8').replace('\r\n','\n'))
  self.assertEqual(H.RESERVE,8*1024**3);self.assertEqual(H.HOST_RESERVE,512*1024**2)
 def test_actual_original_host_ARM_entry_construction(self):
  import ast,types
  from pathlib import PurePosixPath
  target=Path(os.environ['SOURCE127_ORIGINAL']).parent
  template=json.loads((target/'SOURCE_TEMPLATE.json').read_bytes());data=(target/'host.py').read_bytes()
  self.assertEqual(hashlib.sha256(data).hexdigest(),template['files']['host.py']['sha256'])
  tree=ast.parse(data);nodes=[n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='args'for x in n.targets)and "root / 'entry.py'"in ast.unparse(n.value)]
  self.assertEqual(len(nodes),1)
  e=json.loads((P/'FAULT_FIXTURE127.json').read_bytes())['bundle'];sr=e['refs']['source'];ar=e['small_documents']['owner']['authority']
  lr=template['lifecycle_source_ref'];pr=dict(path='/fixture/PLAN.json',bytes=1,sha256='1'*64);cpu=dict(path='/fixture/CPU.json',bytes=1,sha256='2'*64)
  root=PurePosixPath(sr['path']).parent;output=str(PurePosixPath(e['refs']['producer']['path']).parent)
  ns=dict(PY=H.PY,root=root,stage='numeric',sr=sr,ar=ar,lr=lr,a=types.SimpleNamespace(steps=160),childout=PurePosixPath(output),json=json)
  argv=eval(compile(ast.Expression(nodes[0].value),'actual-original-host-create','eval'),ns)
  argv+=['--plan-ref',json.dumps(pr,separators=(',',':')),'--cpu-preflight-ref',json.dumps(cpu,separators=(',',':'))]
  source=dict(files={'entry.py':dict(path=str(root/'entry.py'))});producer=dict(source=sr,authority=ar,lifecycle=lr,plan=pr)
  plan=dict(schema='deltalog.fresh-bridge-plan/v2',source=sr,authority=ar,lifecycle=lr,steps=160,physical=5,logical=0,graph=False,phase_seconds=1800,cleanup_seconds=90,output=output,cpu_preflight=cpu)
  cid=e['small_documents']['numeric_cleanup']['cid'];a=dict(physical=5,pid=123,start_ticks=42,cgroup=cid,namespace_pids=[123,1],argv=argv)
  tail=['0']*20;tail[19]='42';dv=dict(logical=0,physical=5,visible='0',canary=[4.,5.],plan=pr,cgroup=cid,pid=1,stat='1 (entry) '+' '.join(tail))
  handshake=dict(schema='deltalog.fresh-bridge-arm/v2',pid=1,plan_sha256=pr['sha256'],physical=5)
  self.assertTrue(V.arm(a,dv,handshake,pr,plan,producer,source,cid))
  a['argv'][3]=str(root/'producer.py')
  with self.assertRaisesRegex(ValueError,'host entry'):V.arm(a,dv,handshake,pr,plan,producer,source,cid)
 def test_budget_not_added_and_stage_has_no_NPU_branch(self):
  text=(P/'entry.py').read_text(encoding='utf8')
  self.assertIn('left=min(V.TIMEOUT,hostcap,CLOCK.child_cap(deadline,profile)',text)
  self.assertIn('1792220533-time.time()-90',text)
  tree=__import__('ast').parse(text)
  self.assertNotIn('torch_npu',text)
  self.assertIn("choices=('cpu-preflight',)",text)
  self.assertLess(V.TIMEOUT,590)
  self.assertIn("policy.require_complete(C,producer,m['original_source_ref'])",text)
  self.assertIn("policy.require_complete(oldC,prod,r['source'])",(P/'bind127.py').read_text())
 def test_actual_I_all_three_entry_parsers(self):
  for name in ('run_recovery.py','bind127.py','entry.py'):
   result=subprocess.run([sys.executable,'-I','-B',str(P/name),'--help'],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertIn('usage:',result.stdout)
 def test_actual_I_ON_wrong_template_ref(self):
  argv=[sys.executable,'-I','-B',str(P/'run_recovery.py'),'--execute','--phase','bind','--template-ref','{}']
  r=subprocess.run(argv,capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('exact reviewed127R1 template',r.stderr)
 def test_declared_split_entry_missing_original_RO_rejected(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td)/'own';root.mkdir()
   for name in ('entry127.py','anchor_transform127.py','audit_transform127r4.py','codec_transform130.py'):(root/name).write_bytes((P/name).read_bytes())
   missing=dict(path=str(Path(td)/'unmounted-target'/'SOURCE_MANIFEST.json'),bytes=1,sha256='0'*64)
   manifest=dict(consumer_contract_schema='deltalog.anchor-consumer-source/v127',bound=True,producer_source=missing,files={})
   mf=root/'SOURCE_MANIFEST.json';mf.write_text(json.dumps(manifest),encoding='utf8')
   sr=dict(path=str(mf),bytes=mf.stat().st_size,sha256=hashlib.sha256(mf.read_bytes()).hexdigest())
   argv=[sys.executable,'-I','-B',str(root/'entry127.py'),'--execute','--consumer-source-ref',json.dumps(sr),'--producer-source-ref',json.dumps(missing),'--producer-ref','{}','--strict-ref','{}','--output',str(root/'never.json')]
   r=subprocess.run(argv,capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertIn('FileNotFoundError',r.stderr);self.assertIn('unmounted-target',r.stderr)
   self.assertFalse((root/'never.json').exists())
if __name__=='__main__':unittest.main()
