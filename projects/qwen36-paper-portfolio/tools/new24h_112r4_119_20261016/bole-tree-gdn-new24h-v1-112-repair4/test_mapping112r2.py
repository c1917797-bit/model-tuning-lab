import ast,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;T=P.parent;donor_path=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())['donor_host']['path'];D=Path(donor_path).parent if sys.platform=='linux'or ':'in donor_path else T/'deltalog-split-scale-numeric-new24h-20261016-069-repair1'
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Tests(unittest.TestCase):
 def test_real_old_scope_refuses4_new_accepts_only4(self):
  old=load(D/'scope_adapter.py','old_scope');new=load(P/'scope_adapter112.py','new_scope')
  with self.assertRaisesRegex(ValueError,'physical5'):old.scoped_cards('numeric',True,4)
  self.assertEqual(new.scoped_cards('numeric',True,4),(4,))
  for bad in (0,1,2,3,5,6,7):
   with self.assertRaises(ValueError):new.scoped_cards('numeric',True,bad)
  self.assertEqual(new.scoped_cards('native',True,4),(4,5,6,7))
 def test_protected_and_actual_transform_unchanged(self):
  a=ast.parse((D/'scope_adapter.py').read_bytes());b=ast.parse((P/'scope_adapter112.py').read_bytes())
  for n in ('ownership_reasons','protected_observation','transform_observe'):
   x=next(v for v in a.body if isinstance(v,ast.FunctionDef)and v.name==n);y=next(v for v in b.body if isinstance(v,ast.FunctionDef)and v.name==n)
   self.assertEqual(ast.dump(x),ast.dump(y))
  m=load(P/'scope_adapter112.py','scope_protection')
  owned=[dict(pid=11,start_ticks=22,cgroup='CID')];protected=[dict(pid=11,start_ticks=22,cgroup='CID')]
  self.assertIn('owned actual PID/start_ticks on protected physical',m.ownership_reasons(protected,owned,'CID',{},[],[]))
 def test_actual_inspect_physical4_and_wrong5_rejected(self):
  h=load(D/'host.py','actual_donor_inspect');h.OWNER='bole-tree-MAIN-112-repair4';cid='a'*64
  a=types.SimpleNamespace(owner_ref={'sha256':'s'},guest_cpu=0,physical_device=4,current_mounts={},current_cmd=['actual'],current_env={'K':'V'})
  x=dict(Id=cid,Image=h.IMAGE,ExecIDs=None,State={'OOMKilled':False},Mounts=[],Config={'Labels':{'qwen36.owner':h.OWNER,'qwen36.stage':'numeric','deltalog-fresh-bridge.owner-source-sha256':'s'},'Cmd':['actual'],'Env':['K=V']},HostConfig=dict(Privileged=False,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,IpcMode='private',ShmSize=2*2**30,PidsLimit=512,CpusetCpus='0',NetworkMode='none',PortBindings=None,Devices=[dict(PathOnHost='/dev/davinci4',PathInContainer='/dev/davinci0')]+[dict(PathOnHost=p,PathInContainer=p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc')],DeviceRequests=None,DeviceCgroupRules=None))
  self.assertIs(h.inspect_owned(x,cid,'numeric',None,None,a),x)
  x['HostConfig']['Devices'][0]['PathOnHost']='/dev/davinci5'
  with self.assertRaisesRegex(ValueError,'singleton'):h.inspect_owned(x,cid,'numeric',None,None,a)
 def test_owner_route_and_cold_entry(self):
  text=(P/'owner112.py').read_text();self.assertIn("adapter=load(own['files']['scope_adapter112.py']",text)
  for literal in ('self.cards=[4]','a.physical_device=4','--device=/dev/davinci4:/dev/davinci0') :self.assertIn(literal,text)
  for n in ('owner112.py','run112.py','owned_cpu112.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['enabled'])
if __name__=='__main__':unittest.main()
