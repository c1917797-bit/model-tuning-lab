"""Actual original predicates with software records, never runtime qualification."""
import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_recover120_test',P/'recover.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)


class Controls(unittest.TestCase):
 def setUp(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());self.m=m
  owner=m['original_owner_source_ref']
  if sys.platform=='linux':owned=R.obj(owner);path=owned['files']['owned_analysis.py']
  else:path=R.ref(P.parent/'mxr-r5-prefill-analysis-owned-new24h-120-analysis1/owned_analysis.py')
  self.O=R.load(path,'_actual_original120analysis_predicate')
 def fixture(self,root):
  O=self.O;ar=self.m['original_owner_source_ref'];q=self.m['original_analysis_source_ref'];old=R.obj(ar)if sys.platform=='linux'else json.loads((P.parent/'mxr-r5-prefill-analysis-owned-new24h-120-analysis1/SOURCE_MANIFEST.json').read_bytes())
  own=copy.deepcopy(old);cases=[dict(case_id=str(i))for i in range(3)]
  p=root/'fixture-guest.json';p.write_bytes(json.dumps(dict(cases=cases)).encode());own['guest_source']=R.ref(p)
  software=dict(source=ar,tests=22,passed=True,NPU=False,actual_data_consumed=False)
  analysis=dict(schema='mxr.prefill-source-and-round-cell-analysis/v120-analysis1',source=q,stage_ref=own['actual_stage_ref'],NPU=False,qualification=False,performance=False,task=False,reference_validity_resolved=False,cases=[dict(case=c,tiles=[{}]*384,qualification=False)for c in cases],original_consumer=dict(source=own['guest_source'],candidate_anchor_bitwise=True,old_R5_FAIL_preserved=True))
  # The guest report Ref keeps its real container path. It is never rewritten.
  hostreport=root/R.NAMES['analysis'];hostreport.write_bytes(json.dumps(analysis).encode());hr=R.ref(hostreport);gr=dict(hr,path='/adakv-results/ANALYSIS120A1.json')
  receipt=dict(schema='mxr.prefill-analysis-owned-child/v120-analysis1',source=ar,analysis_source=q,stage_ref=own['actual_stage_ref'],analysis_ref=gr,software=software,NPU=False,qualified=False)
  required=[ar,*own['files'].values(),q,own['guest_source'],own['actual_stage_ref'],own['actual_attribution_ref'],own['actual_CPU_owner_ref']]
  mounts={r['path']:(r['path'],False)for r in required};mounts[str(root)]=('/adakv-results',True)
  env=dict(ASCEND_RT_VISIBLE_DEVICES='',ASCEND_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR='/adakv-results',HOME='/adakv-results')
  child=['-I','-B',own['files']['analysis_entry.py']['path'],'--execute','--source-ref',json.dumps(ar),'--stage-ref',json.dumps(own['actual_stage_ref']),'--output','/adakv-results/ANALYSIS120A1.json'];name='software-only-cpu';argv=O.create_argv(7,mounts,env,name,child);cid='a'*64
  inspect=dict(Id=cid,Image=O.IMAGE,Name='/'+name,ExecIDs=None,Config=dict(Labels={'qwen36.owner':O.OWNER},Env=[k+'='+v for k,v in env.items()],Entrypoint=[O.PY],Cmd=child),HostConfig=dict(Privileged=False,ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*O.GIB,MemorySwap=8*O.GIB,NanoCpus=10**9,CpusetCpus='7',PidsLimit=256,IpcMode='private',NetworkMode='none',LogConfig={'Type':'none'},Devices=[],DeviceRequests=[],DeviceCgroupRules=[],PortBindings={}),Mounts=[dict(Source=s,Destination=d,RW=w)for s,(d,w)in mounts.items()],State=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False))
  parent=dict(schema='mxr.prefill-analysis-owned-CPU/v120-analysis1',source=ar,guest_source=own['guest_source'],stage_ref=own['actual_stage_ref'],primary=R.FAILURE,secondary=[],resource_release_verified=True,stopped_retained=True,Devices=[],NPU=False,qualified=False,cid=cid)
  data=dict(analysis=analysis,receipt=receipt,software=software,parent=parent,inspect=inspect,create=argv,cid=dict(cid=cid,name=name))
  for key,name in R.NAMES.items():
   if key!='analysis':(root/name).write_bytes(json.dumps(data[key]).encode())
  refs={key:R.ref(root/name)for key,name in R.NAMES.items()}
  return own,ar,q,refs,data
 def test_01_positive_alias_and_old_parent_FAIL_preserved(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);args=self.fixture(root);before={k:R.ref(v['path'])for k,v in args[3].items()};out=R.validate(self.O,*args,root)
   self.assertTrue(out['transport_recovery_valid']);self.assertFalse(out['original_parent_pass']);self.assertFalse(out['qualification']);self.assertEqual(out['original_guest_analysis_ref']['path'],'/adakv-results/ANALYSIS120A1.json');self.assertEqual(before,{k:R.ref(v['path'])for k,v in args[3].items()})
 def test_02_bad_guestalias_hash_and_extraRW_reject(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);args=self.fixture(root)
   for mutate in(lambda d:d['receipt']['analysis_ref'].update(path='/tmp/ANALYSIS120A1.json'),lambda d:d['receipt']['analysis_ref'].update(sha256='0'*64),lambda d:d['inspect']['Mounts'].append(dict(Source='/foreign',Destination='/foreign',RW=True)),lambda d:d['inspect']['Mounts'][-1].update(Destination='/wrong')):
    z=copy.deepcopy(args);mutate(z[-1])
    with self.assertRaises(ValueError):R.validate(self.O,*z,root)
 def test_03_wrong_source_missingcoverage_and_fakequalification_reject(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);args=self.fixture(root)
   for mutate in(lambda d:d['receipt'].update(source={}),lambda d:d['analysis']['cases'].pop(),lambda d:d['analysis'].update(qualification=True),lambda d:d['software'].update(tests=21)):
    z=copy.deepcopy(args);mutate(z[-1])
    with self.assertRaises(ValueError):R.validate(self.O,*z,root)
 def test_04_unknown_parentfailure_or_live_or_OOM_reject(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);args=self.fixture(root)
   for mutate in(lambda d:d['parent'].update(primary='unrelated failure'),lambda d:d['parent'].update(primary=None),lambda d:d['inspect']['State'].update(Running=True),lambda d:d['inspect']['State'].update(OOMKilled=True),lambda d:d['inspect'].update(ExecIDs=['x']),lambda d:d['cid'].update(cid='b'*64)):
    z=copy.deepcopy(args);mutate(z[-1])
    with self.assertRaises(ValueError):R.validate(self.O,*z,root)
 def test_05_actual_file_ref_change_detected(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);args=self.fixture(root);R.checked(args[3]['analysis']);(root/'ANALYSIS120A1.json').write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'bytes/SHA'):R.checked(args[3]['analysis'])
 def test_06_actual_I_cold_default_and_help(self):
  for flags in([],['--help']):
   out=subprocess.run([sys.executable,'-I','-B',str(P/'recover.py'),*flags],capture_output=True,text=True);self.assertEqual(out.returncode,0,out.stderr)


if __name__=='__main__':unittest.main()
