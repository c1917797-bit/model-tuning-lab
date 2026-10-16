import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('_CF120_owner_test',P/'owned_analysis.py');O=importlib.util.module_from_spec(s);s.loader.exec_module(O)


class Controls(unittest.TestCase):
 def test_01_actual_I_cold_owner_and_entry(self):
  for leaf in('owned_analysis.py','counterfactual_entry.py'):
   for flags in([],['--help']):
    r=subprocess.run([sys.executable,'-I','-B',str(P/leaf),*flags],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_02_exact_existing_resource_functions(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());r=m['controller_donor_source_ref']
  path=Path(O.obj(r)['files']['owned_analysis.py']['path'])if sys.platform=='linux'else P.parent.parent/'mxr-r5-prefill-analysis-owned-new24h-120-analysis1/owned_analysis.py'
  a=ast.parse(path.read_bytes());b=ast.parse((P/'owned_analysis.py').read_bytes())
  for name in('storage_check','docker_argv','output_scan','create_argv','inspect_owned','closure','historical_inputs'):
   get=lambda x:next(n for n in x.body if isinstance(n,ast.FunctionDef)and n.name==name)
   self.assertEqual(ast.dump(get(a)),ast.dump(get(b)))
  text=(P/'owned_analysis.py').read_text();self.assertIn('cleanup_seconds=max(1,min(90',text);self.assertIn("no_overlap(cid)",text);self.assertIn("receive_files(a.output,own,ar,mounts)",text)
 def fixture(self,root):
  ar=dict(path='/software-only-source',bytes=1,sha256='0'*64);cases=[dict(case_id=str(i))for i in range(3)];p=root/'guest.json';p.write_bytes(json.dumps(dict(cases=cases)).encode());gm=O.ref(p)
  own=dict(guest_source=gm,counterfactual_source_ref=ar,actual_stage_ref=ar,actual_analysis_report_ref=ar)
  variants=['baseline','actual_G_only','actual_A_only','actual_A_and_G'];baseline=dict(output_state=dict(output=True,state=True),trace_rows=32,all_trace_fields_bitwise=True,current_original_vs_hook_None=True,historical_tensor_hash_available=False)
  d=dict(schema='mxr.actual-A-G-independent-CPU-counterfactual/v120-analysis3',source=ar,guest_source=gm,actual_stage_ref=ar,prior_analysis_ref=ar,baseline_unchanged=True,old_failures_preserved=True,qualification=False,model=False,performance=False,task=False,NPU=False,reference_validity_resolved=False,variants=variants,cases=[dict(case=c,counterfactual=dict(baseline_identity=copy.deepcopy(baseline),variants={v:dict(chunks=[{}]*32)for v in variants},qualification=False,reference_validity_resolved=False))for c in cases])
  sw=dict(source=ar,tests=12,passed=True,NPU=False,actual_data_consumed=False);target=root/'COUNTERFACTUAL120A3.json';target.write_bytes(json.dumps(d).encode());(root/'SOFTWARE_CONTROLS.json').write_bytes(json.dumps(sw).encode())
  reportref=dict(O.ref(target),path='/adakv-results/COUNTERFACTUAL120A3.json');r=dict(schema='mxr.counterfactual-owned-child/v120-analysis3',source=ar,counterfactual_source=ar,actual_stage_ref=ar,report_ref=reportref,software=sw,NPU=False,qualified=False);(root/'COUNTERFACTUAL_RECEIPT.json').write_bytes(json.dumps(r).encode());return own,ar,d,sw,r
 def test_03_exact_typed_guest_alias_real_inspect_to_receive(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);own,ar,d,sw,r=self.fixture(root);mounts={'/software':('/software',False),str(root):('/adakv-results',True)};env=dict(ASCEND_RT_VISIBLE_DEVICES='');child=['-I','-B','/software/entry.py'];name='software-only';cid='a'*64
   x=dict(Id=cid,Image=O.IMAGE,Name='/'+name,Config=dict(Labels={'qwen36.owner':O.OWNER},Env=['ASCEND_RT_VISIBLE_DEVICES='],Entrypoint=[O.PY],Cmd=child),ExecIDs=None,HostConfig=dict(Privileged=False,ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*O.GIB,MemorySwap=8*O.GIB,NanoCpus=10**9,CpusetCpus='7',PidsLimit=256,IpcMode='private',NetworkMode='none',LogConfig={'Type':'none'},Devices=[],DeviceRequests=[],DeviceCgroupRules=[],PortBindings={}),Mounts=[dict(Source=s,Destination=z,RW=w)for s,(z,w)in mounts.items()],State=dict(OOMKilled=False))
   O.inspect_owned(x,cid,mounts,env,7,name,child);self.assertNotEqual(r['report_ref'],O.ref(root/'COUNTERFACTUAL120A3.json'));O.receive_files(root,own,ar,mounts)
   for key,val in(('path','/wrong/COUNTERFACTUAL120A3.json'),('sha256','1'*64)):
    bad=copy.deepcopy(r);bad['report_ref'][key]=val;(root/'COUNTERFACTUAL_RECEIPT.json').write_bytes(json.dumps(bad).encode())
    with self.assertRaises(ValueError):O.receive_files(root,own,ar,mounts)
   (root/'COUNTERFACTUAL_RECEIPT.json').write_bytes(json.dumps(r).encode())
   with self.assertRaises(ValueError):O.receive_files(root,own,ar,dict(mounts,foreign=('/foreign',True)))
 def test_04_no_fabricated_baseline_or_missing_variants(self):
  with tempfile.TemporaryDirectory()as td:
   own,ar,d,sw,_=self.fixture(Path(td));O.receive_report(d,own,ar,sw)
   for mutate in(lambda z:z.update(qualification=True),lambda z:z['cases'][0]['counterfactual']['baseline_identity'].update(historical_tensor_hash_available=True),lambda z:z['cases'][0]['counterfactual']['baseline_identity']['output_state'].update(state=False),lambda z:z['cases'][0]['counterfactual']['variants'].pop('actual_A_only'),lambda z:z.update(source={})):
    bad=copy.deepcopy(d);mutate(bad)
    with self.assertRaises(ValueError):O.receive_report(bad,own,ar,sw)
 def test_05_exact_current_frontdoor_and_source_closure(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());self.assertEqual(m['software_cases'],O.SOFTWARE_CASES);cmd=O.child_command(m,m['actual_stage_ref']);self.assertEqual(cmd[2],m['files']['counterfactual_entry.py']['path']);self.assertEqual(cmd[-1],'/adakv-results/COUNTERFACTUAL120A3.json')
  text=(P/'owned_analysis.py').read_text();self.assertIn("C.readset(cf)",text);self.assertIn("own['counterfactual_source_ref']",text);self.assertIn('whole1000s',text)
 def test_06_declared_only_controller_readset_missing_and_corrupt_reject(self):
  with tempfile.TemporaryDirectory()as td:
   from unittest.mock import patch
   t=Path(td);host=t/'owned_analysis.py';host.write_bytes(b'original pinned controller')
   manifest=t/'SOURCE.json';manifest.write_bytes(json.dumps(dict(files={'owned_analysis.py':O.ref(host)})).encode())
   actual=dict(controller_donor_source_ref=O.ref(manifest));expected=O.controller_readset(actual)
   self.assertEqual(expected,[actual['controller_donor_source_ref'],O.ref(host)])
   original=O.checked
   for missing in expected:
    def declared(r):
     if r==missing:raise FileNotFoundError('undeclared file-only mount')
     return original(r)
    with patch.object(O,'checked',side_effect=declared):
     with self.assertRaises(FileNotFoundError):O.controller_readset(actual)
   originalhost=host.read_bytes();host.write_bytes(b'corrupt')
   with self.assertRaises(ValueError):O.controller_readset(actual)
   host.write_bytes(originalhost);self.assertEqual(O.controller_readset(actual),expected)


if __name__=='__main__':unittest.main()
