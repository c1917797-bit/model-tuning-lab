import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
from pair_metrics122 import arm,metadata_delta
class Controls(unittest.TestCase):
 def test_01_real_cold_entries(self):
  for n in('bind122.py','host_validation.py','health_guest122.py','host_pair.py','server_entry.py'):
   for flags in([],['--help']):
    z=subprocess.run([sys.executable,'-I','-B',str(P/n),*flags],capture_output=True,text=True);self.assertEqual(z.returncode,0,z.stderr)
 def test_02_common_actual_cli(self):
  import server_entry as S
  a=S.command();self.assertNotIn('--async-scheduling',a)
  for key,val in(('--max-model-len','4096'),('--max-num-batched-tokens','2048'),('--max-num-seqs','1'),('--mamba-cache-mode','none')):self.assertEqual(a[a.index(key)+1],val)
  self.assertEqual(a.count('--no-async-scheduling'),1);self.assertIn('--enforce-eager',a);self.assertIn('--no-enable-prefix-caching',a)
  import types
  from unittest.mock import patch
  p=P/'dependencies/benchmark_shared_prefix.py';self.assertEqual(A.ref(p)['sha256'],'cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822')
  s=importlib.util.spec_from_file_location('_122_exact_original_HTTP_driver',p);v=importlib.util.module_from_spec(s)
  with patch.dict(sys.modules,{s.name:v}):s.loader.exec_module(v)
  with patch.object(sys,'argv',[str(p),'--base-url','http://127.0.0.1:8230','--model','qwen36-mxr-eager','--input-tokens','2048','--prefix-tokens','1024','--output-tokens','1024','--requests','2','--concurrency','1','--warmup-requests','2']):
   args=v._parse_args();self.assertEqual((args.requests,args.warmup_requests,args.output_tokens),(2,2,1024))
 def response(self,count=2):
  return dict(config=dict(input_tokens=2048,prefix_tokens=1024,output_tokens=1024,requests=count,concurrency=1,warmup_requests=2,ignore_eos=True),summary=dict(benchmark_duration_s=10.,output_tokens_per_second=1024*count/10,failed=0,successful=count,fixed_output_verified=True),results=[dict(index=i,ok=True,output_tokens=1024,requested_output_tokens=1024,ttft_ms=10.,duration_s=3.)for i in range(count)])
 def test_03_actual_HTTP_metrics(self):
  metric,calls=arm(self.response(),2);self.assertEqual(calls,2046);self.assertEqual(metric['throughput'],204.8)
 def test_04_partial_or_nonfixed_HTTP_refused(self):
  for change in(lambda x:x['results'].pop(),lambda x:x['results'][0].update(output_tokens=1023),lambda x:x['summary'].update(benchmark_duration_s=0),lambda x:x['config'].update(concurrency=16)):
   x=self.response();change(x)
   with self.assertRaises(ValueError):arm(x,2)
 def snapshots(self):
  b=dict(pid=1,prefixes={str(i):dict(candidate=7,finished_steps=9,materialized_slots=2,native=1)for i in range(48)});a=copy.deepcopy(b)
  for r in a['prefixes'].values():r.update(candidate=2053,finished_steps=2057,materialized_slots=4)
  return b,a
 def test_05_actual_metadata_calls(self):
  b,a=self.snapshots();self.assertEqual(len(metadata_delta(b,a,2046,2)),48)
 def test_06_metadata_not_HTTP_blind_multiply(self):
  b,a=self.snapshots()
  for key in('candidate','finished_steps','materialized_slots','native'):
   wrong=copy.deepcopy(a);wrong['prefixes']['0'][key]+=1
   with self.assertRaises(ValueError):metadata_delta(b,wrong,2046,2)
 def health(self):
  sr={'only':'software-positive'};o=dict(schema='deltalog.production-health-owned/v122',source=sr,primary=None,secondary=[],released=True)
  r=dict(schema='deltalog.production-health-equivalence/v122',source=sr,production_source=sr,production_qualification=sr,NPU=True,all_model216_decode_bitwise=True,all320_flush_bitwise=True,valid_health=dict(all_finite=True),dead_nan_pass=True,invalid_live_sticky=True,invalid_output_sticky=True,rows=[dict(batch=b,step=s,flush_bitwise=True)for b in(1,16)for s in range(160)],model_rows=[dict(raw=dict(path='/software/'+str(i)),decode_bitwise=True)for i in range(216)],health_scope='observed decode outputs and materialized logical states; not all cache/aux cells',qualified=False,performance=False)
  r.update(invalid_health=dict(all_finite=False),output_negative_health={k:dict(all_finite=False,outside_timing=True)for k in('NaN','Inf')});return o,r,sr
 def test_07_typed_health_source_positive(self):
  o,r,s=self.health();A.health_gate(o,r,s,s,s)
 def test_08_Meta_or_partial_health_never_admitted(self):
  for change in(lambda o,r:o.update(primary='failed'),lambda o,r:r.update(NPU=False),lambda o,r:r['rows'].pop(),lambda o,r:r.update(invalid_live_sticky=False),lambda o,r:r.update(production_source={})):
   o,r,s=self.health();change(o,r)
   with self.assertRaises(ValueError):A.health_gate(o,r,s,s,s)
  sr=dict(software=True);o=dict(schema='deltalog.production-owned-single-pair/v122',source=sr,primary=None,secondary=[],source_before={'a':'sha'},source_after={'a':'sha'},arms=[{},{}]);r=dict(schema='deltalog.actual-single-pair-independent/v122',source=sr,smoke_pair=True,acceptance=False,formal_three_rounds=False);A.smoke_gate(o,r,sr)
  for key,value in(('primary','failed'),('secondary',['failed']),('source_after',{})):
   bad=copy.deepcopy(o);bad[key]=value
   with self.assertRaises(ValueError):A.smoke_gate(bad,r,sr)
  with tempfile.TemporaryDirectory()as td:
   path=Path(td)/'original025.json';path.write_bytes(b'{}');actual=A.ref(path);r2={k:v for k,v in actual.items()if k!='bytes'};self.assertEqual(A.original025_ref3(r2),actual)
   with self.assertRaises(ValueError):A.original025_ref3(dict(actual,bytes=1))
 def test_09_pending_source_refused_before_imports(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'source.json';p.write_text(json.dumps(dict(schema='deltalog.actual-production-pair-source/v122',root=str(P),default_enabled=False,prepared_only=True)))
   with self.assertRaises(ValueError):A.source(A.ref(p),pair=True)
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());m['root']=str(P);m['files']={n:A.ref(P/n)for n in m['files']};t=root/'template.json';t.write_bytes(json.dumps(m).encode());tr=json.dumps(A.ref(t));out=P/'_SOFTWARE_MUST_NOT_PUBLISH.json'
   z=subprocess.run([sys.executable,'-I','-B',str(P/'bind122.py'),'--execute','--template-ref',tr,'--production-source-ref',tr,'--production-qualification-ref',tr,'--output',str(out)],capture_output=True,text=True)
   self.assertNotEqual(z.returncode,0);self.assertIn('actual106 bound source',z.stderr);self.assertFalse(out.exists())
 def test_10_real_helper_atomic_no_overwrite(self):
  from snapshot_publication import publish
  # This exact existing publisher uses Linux directory fsync. Windows executes
  # only its no-overwrite source contract, Linux same-image does real syscalls.
  if sys.platform=='linux':
   with tempfile.TemporaryDirectory()as td:
    p=Path(td)/'x.json';publish(p,dict(done=True));self.assertEqual(json.loads(p.read_bytes()),dict(done=True))
    with self.assertRaises(ValueError):publish(p,dict(done=False))
  else:
   import snapshot_publication as S
   self.assertIn('os.link(',Path(S.donor().__file__).read_text())
 def test_11_declared_current_runtime(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
  for n,r in m['files'].items():self.assertEqual(A.ref(P/n),dict(r,path=str(P/n)))
  self.assertEqual(m['software_cases'],12);self.assertEqual(m['window'],dict(start=1792134133,cutoff=1792220533));self.assertEqual(m['resource']['RAM_initial_GiB'],56.5)
  import external025 as E,owned_substrate as S
  safety=(P/'dependencies/original025_safety_host.py').read_bytes();host=(P/'dependencies/original025_host_once.py').read_bytes();derived,pairs=E.derive(safety);self.assertEqual(len(pairs),4)
  body,changes=S.derive_host(host);self.assertEqual(len(changes),3);self.assertIn(b'self.deadline=start+3600',body)
  with self.assertRaises(ValueError):E.derive(safety+b'\n')
  with self.assertRaises(ValueError):S.derive_host(host+b'\n')
 def test_12_actual_pairflow_guard_chain(self):
  tree=ast.parse((P/'host_pair.py').read_bytes());text=(P/'host_pair.py').read_text();self.assertIn('actual full release before changing arm',text);self.assertIn('pair_consume.py',text);self.assertIn('policy_snapshot(c,ctl',text)
  consumer=(P/'pair_consume.py').read_text();self.assertIn('validate_delta(',consumer);self.assertIn('metadata_delta(',consumer);self.assertIn('A.qualify(sr)',consumer)
  source=(P/'health_guest122.py').read_text();self.assertIn("for row in A.model_inputs(m)",source);self.assertIn("raw['after'][i]",source);self.assertIn("f['after'][n]",source)
  # Execute the REAL pair consumer and real106 live-reader together. Only the
  # unavailable external qualification is a clearly software-only shadow;
  # no actual certificate/owner is published by this contract control.
  import types,contextlib
  from unittest.mock import patch
  import pair_consume as C
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());pm=m['production_template']['files'];lp=Path(pm['live106.py']['path'])if sys.platform=='linux'else P.parent/'deltalog-production-new24h-106-repair5/live106.py';qp=lp.parent/'qualification106.py'
  self.assertEqual(A.ref(lp)['sha256'],pm['live106.py']['sha256']);self.assertEqual(A.ref(qp)['sha256'],pm['qualification106.py']['sha256'])
  qs=importlib.util.spec_from_file_location('_122_software_actualQ106',qp);Q=importlib.util.module_from_spec(qs);qs.loader.exec_module(Q)
  with patch.dict(sys.modules,{'qualification106':Q}):
   ls=importlib.util.spec_from_file_location('_122_software_actualLive106',lp);L=importlib.util.module_from_spec(ls);ls.loader.exec_module(L)
  sr={'software-only':True};q={'software-only-qualification':True};lib={'software-library':True};manifest=dict(production_source_ref=sr,production_qualification_ref=q)
  b0,a0=self.snapshots();before=[];after=[]
  for pid in range(1,5):
   common=dict(schema='deltalog.production-worker/v106',source_ref=sr,qualification_ref=q,mode='bounded-production',tensor_capture=False,native_peer=False,graph=False,async_scheduling=False,PDC=False,synchronization_outside_timing=True,tensor_snapshot=False,receipt_trigger='SIGUSR1 outside timed client interval',health=dict(outside_timing=True,all_finite=True,rows={'software':dict(finite=True,observations=1)}),actual_common_precision=dict(matmul_allow_hf32=False,conv_allow_hf32=False),mapped_rows=['software-mapped-proof'],library=lib,actual_core_id=7,actual_target='software.Target',proc_stat='1 (software) '+' '.join(['S']+['0']*18+['42']),cgroup='software-not-actual')
   for rows,base,ordinal in((before,b0,1),(after,a0,2)):
    z=copy.deepcopy(common);z.update(pid=pid,ordinal=ordinal,prefixes=copy.deepcopy(base['prefixes']))
    for r in z['prefixes'].values():r.update(self_id=pid,arena={'software':1},core_id=7)
    rows.append(z)
  @contextlib.contextmanager
  def context(unused):yield {'live106':L},{}
  inputs=dict(measured=2,warmups=2,shared_prefix_tokens=1024,prompts=[[0]*2048 for _ in range(4)])
  with patch.object(A,'qualify',return_value=(manifest,q)),patch.object(A,'context',context),patch.object(Q,'qualify',return_value=q),patch.object(Q,'source',return_value=dict(library_ref=lib)):
   report=C.consume(self.response(),self.response(),inputs,inputs,before,after,sr,2);self.assertEqual(len(report['observed_worker_delta']),4);self.assertFalse(report['acceptance'])
   wrong=copy.deepcopy(after);wrong[0]['health']['all_finite']=False
   with self.assertRaises(ValueError):C.consume(self.response(),self.response(),inputs,inputs,before,wrong,sr,2)
if __name__=='__main__':unittest.main()
