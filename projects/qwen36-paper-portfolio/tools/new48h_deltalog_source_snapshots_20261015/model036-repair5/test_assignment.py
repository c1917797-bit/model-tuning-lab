"""Actual InputProcessor body plus original assignment oracle; CPU fixtures."""
import ast,copy,hashlib,json,pathlib,tempfile,types,unittest
import identity_events as I
P=pathlib.Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def event(self,passed):
  source=P/'dependencies/input_processor_v023.py';self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),'c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15')
  fn=copy.deepcopy(next(n for n in ast.walk(ast.parse(source.read_bytes()))if isinstance(n,ast.FunctionDef)and n.name=='assign_request_id'));fn.decorator_list=[]
  node=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fn],type_ignores=[]);ast.fix_missing_locations(node);ns=dict(envs=types.SimpleNamespace(VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=False),random_uuid=lambda:'abcdef0123456789');exec(compile(node,str(source),'exec'),ns)
  r=types.SimpleNamespace(request_id=passed,external_req_id=None);ns['assign_request_id'](r)
  return dict(schema='vllm023.actual-assignment/v1',before_request_id=passed,before_external_req_id=None,after_request_id=r.request_id,after_external_req_id=r.external_req_id,disable_request_id_randomization=False,source_sha256='c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15',identity=dict(pid=1,start_ticks=1,cgroup='/fixture'))
 def check(self,mutation=None,header='a'):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);(root/'identity026').mkdir();sr={'software-fixture':True};cid='a'*64;assigned=[];servers=['cmpl-'+header,'cmpl-b']
   for sid in servers:
    e=self.event(sid+'-0')
    if mutation:mutation(e)
    assigned.append(e['after_request_id']);p=root/'identity026'/('assignment-'+hashlib.sha256((sid+'-0').encode()).hexdigest()+'.json');p.write_text(json.dumps(dict(schema='deltalog.actual-identity-event/v026',source=sr,owner_cid=cid,event=e)))
   trajectory=[dict(rank=r,request_ids=[sid+'-0-abcdef01'])for r in range(4)for sid in servers];loaded=[dict(rank=r,actual_host_process=dict(cgroup='/docker/'+cid))for r in range(4)]
   return I.validate_join(root,servers,sr,trajectory,loaded)
 def test_actual_assigned_suffix_join(self):self.assertEqual(len(self.check()),2)
 def test_wrong_header_rejected(self):
  with self.assertRaises(ValueError):self.check(lambda e:e.update(before_request_id='cmpl-other-0'))
 def test_missing_prompt_zero_rejected(self):
  with self.assertRaises(ValueError):self.check(lambda e:e.update(before_request_id=e['before_request_id'][:-2]))
 def test_wrong_but_wellformed_observed_suffix_rejected_by_worker_join(self):
  with self.assertRaises(ValueError):self.check(lambda e:e.update(after_request_id=e['before_request_id']+'-01234567'))
 def test_mixed_requests_rejected(self):
  with self.assertRaises(ValueError):self.check(lambda e:e.update(after_external_req_id='cmpl-another-0'))
 def test_source_drift_rejected(self):
  with self.assertRaises(ValueError):self.check(lambda e:e.update(source_sha256='0'*64))
if __name__=='__main__':unittest.main()
