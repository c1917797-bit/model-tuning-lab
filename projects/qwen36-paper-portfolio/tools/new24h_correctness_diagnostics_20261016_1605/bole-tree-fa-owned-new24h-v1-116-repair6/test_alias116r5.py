import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C
from test116 import fixture
import ticket116 as T
def make(root,mutate=None):
 sr,m=fixture(root);m['output_root']=str(root/'out');C.write(root/'AUTH.json',dict(start_epoch=1792134133,cutoff_epoch=1792220533));m['authority_ref']=C.ref(root/'AUTH.json');C.write(root/'SOURCE.json',m);sr=C.ref(root/'SOURCE.json')
 cpu=Path(m['output_root'])/'cpu';pre=cpu/'preflight';pre.mkdir(parents=True)
 abi=dict(schema='bole.actual-FIA-installed-ABI/v115',source=sr,NPU=False,Devices=[],no_device_fds=True,operator_executed=False,operator='npu::npu_fused_infer_attention_score',argument_names=list(T.REQUIRED),header_ref=m['header_ref'],overload='',schema_family={'':'software serialized ABI fixture'},actual_schema='software serialized ABI fixture');C.write(pre/'ACTUAL_FIA_ABI.json',abi)
 alias=dict(C.ref(pre/'ACTUAL_FIA_ABI.json'),path='/adakv-results/preflight/ACTUAL_FIA_ABI.json')
 stage=dict(schema='bole.tree-CPU-stage/v116',source=sr,NPU=False,primary=None,actual_meta={'pass_gate':True},actual_abi_ref=alias);cid='a'*64
 inspect=dict(Id=cid,Image=m['image'],ExecIDs=None,State=dict(Running=False,Pid=0,ExitCode=0,OOMKilled=False),HostConfig=dict(ReadonlyRootfs=True,Privileged=False,Devices=[],DeviceRequests=[],DeviceCgroupRules=[]),Config=dict(Labels={'qwen36.owner':'bole-tree-CPU116R6'},Cmd=['-I','-B',m['files']['cpu116.py']['path'],'--execute','--source-ref',json.dumps(sr,separators=(',',':')),'--output','/adakv-results/preflight']),Mounts=[dict(Source=str(cpu),Destination='/adakv-results',RW=True,Type='bind')])
 if mutate:mutate(stage,inspect)
 C.write(pre/'STAGE_RESULT.json',stage);C.write(cpu/'FINAL_INSPECT.json',inspect)
 owner=dict(schema='bole.tree-owned-CPU/v116',source=sr,primary=None,secondary=[],resource_release_verified=True,stopped_retained=True,stage_ref=None,Devices=[],NPU=False,cid=cid,stage_result=C.ref(pre/'STAGE_RESULT.json'));C.write(cpu/'RESULT.json',owner)
 return sr,C.ref(cpu/'RESULT.json'),pre
class Tests(unittest.TestCase):
 def test_actual_I_ticket_fullentry_serialized_guest_alias(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);sr,owner,pre=make(root);out=root/'TICKET.json';r=subprocess.run([sys.executable,'-I','-B',str(P/'ticket116.py'),'--execute','--source-ref',json.dumps(sr),'--cpu-owner-ref',json.dumps(owner),'--output',str(out)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);ticket=json.loads(out.read_bytes());self.assertEqual(ticket['actual_abi_ref'],C.ref(pre/'ACTUAL_FIA_ABI.json'));self.assertEqual(T.consume(C.ref(out),sr,owner),ticket)
 def test_wrong_mount_hash_path_and_source(self):
  mutations=[lambda s,x:x['Mounts'][0].update(Source='/wrong'),lambda s,x:s['actual_abi_ref'].update(sha256='0'*64),lambda s,x:s['actual_abi_ref'].update(path='/adakv-results/preflight/OTHER.json'),lambda s,x:s.update(source={'wrong':True}),lambda s,x:x['State'].update(Pid=99),lambda s,x:x['Mounts'].append(dict(Source='/x',Destination='/adakv-results/preflight',RW=False,Type='bind'))]
  for mutate in mutations:
   with tempfile.TemporaryDirectory()as d:
    sr,owner,_=make(Path(d),mutate)
    with self.assertRaises((ValueError,FileNotFoundError)):T.from_cpu(sr,owner)
 def test_guest_numeric_and_consumer_no_cpu_alias(self):
  import ast
  guest=(P/'guest116.py').read_text(encoding='utf8');self.assertIn("a.output.mkdir();out=a.output",guest)
  owner=(P/'owner116.py').read_text(encoding='utf8');self.assertIn("'--output',str(childout)",owner);self.assertIn("mounts[str(self.output)]=(str(self.output),True)",owner)
  consumer=(P/'owned_cpu116.py').read_text(encoding='utf8');self.assertIn('mounts[rawroot]=(rawroot,False)',consumer)
 def test_actual_selector_under_guest_TMPDIR(self):
  import ast
  tree=ast.parse((P/'ticket116.py').read_bytes());node=next(n for n in ast.walk(tree)if isinstance(n,ast.If)and isinstance(n.test,ast.Compare)and any(isinstance(v,ast.Constant)and v.value=='/adakv-results/preflight/ACTUAL_FIA_ABI.json'for v in ast.walk(n.test)))
  code=compile(ast.Expression(body=node.test),'actual from_cpu discriminator','eval')
  paths={'/adakv-results/preflight/ACTUAL_FIA_ABI.json':True,'/adakv-results/tmp123/ABI.json':False,'/adakv-results/tmp123/preflight/ACTUAL_FIA_ABI.json':False,'/adakv-results/preflight/OTHER.json':False,'/adakv-results2/preflight/ACTUAL_FIA_ABI.json':False}
  for path,expected in paths.items():self.assertEqual(eval(code,{'abi_ref':{'path':path}}),expected)

if __name__=='__main__':unittest.main()
