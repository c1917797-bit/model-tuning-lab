import importlib.util,json,shutil,subprocess,sys,tempfile,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import common116 as C,predecessor118t as R

def fixture(root):
 def put(n,v):p=root/n;C.write(p,v);return C.ref(p)
 sr=put('SOURCE.json',dict(schema='bole.tree-fa-owned-source/v118c',prepared_only=False))
 frames=[dict(path='/software-unopened-frame-'+str(i),bytes=1,sha256='a'*64)for i in range(12)]
 capture=put('CAPTURE.json',dict(schema='bole.actual-native-conv-capture/v118c',source=sr,operator_executed=True,records=frames,before_records=frames))
 stage=put('STAGE.json',dict(schema='bole.tree-stage/v118c',source=sr,primary=None,NPU=True,qualified=False,result=capture))
 no=put('NUMERIC.json',dict(schema='bole.tree-owned/v118c',source=sr,primary=None,secondary=[],stopped_retained=True,physical=[4],logical=0,result=stage))
 result=put('ATTR.json',dict(schema='bole.native-conv-independent/v118c',source=sr,actual_capture=capture,pass_gate=True,native_SD_chronology_pass=True,rows=[{}for _ in range(12)],records=frames,before_records=frames,qualified=False,model_ready=False,BOLE_model_ready=False))
 co=put('CPU.json',dict(schema='bole.tree-owned-CPU/v118c',source=sr,primary=None,secondary=[],resource_release_verified=True,stopped_retained=True,numeric_owner=no,stage_ref=stage,stage_result=result))
 return dict(actual_118c=dict(source=sr,numeric_owner=no,consumer_owner=co,stage=stage,capture=capture,consumer=result))

class Tests(unittest.TestCase):
 def test_real_predecessor_reader_serialized_chain_and_bad_owner(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);m=fixture(root);self.assertTrue(R.join(C,m)['native_chronology_pass'])
   co=C.obj(m['actual_118c']['consumer_owner']);co['numeric_owner']=m['actual_118c']['consumer_owner'];C.write(root/'WRONG.json',co)
   m['actual_118c']['consumer_owner']=C.ref(root/'WRONG.json')
   with self.assertRaises(ValueError):R.join(C,m)

 def test_actual_owner_eight_rows_firstfault_and_wrong_count(self):
  import owner116 as O
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);file=root/'raw.pt';file.write_bytes(b'explicit software raw reference');rr=C.ref(file);sr=rr;ar=rr;pr=rr
   rows=[dict(case=c,mode=m,raw=rr,before=rr,primary={'error':'unsupported TND fixture'})for c in range(4)for m in(0,1)]
   inner=dict(schema='bole.paged-tree-stage/v1',source=sr,NPU=True,qualified=False,rows=rows);C.write(root/'INNER.json',inner)
   outer=dict(schema='bole.tree-stage/v118t',source=sr,authority=ar,plan=pr,primary=None,NPU=True,qualified=False,result=C.ref(root/'INNER.json'))
   self.assertEqual(O.receive(outer,sr,ar,pr),outer) # preserve actual unsupported-domain evidence for receiver
   inner['rows']=rows[:-1];C.write(root/'BAD.json',inner);outer['result']=C.ref(root/'BAD.json')
   with self.assertRaises(ValueError):O.receive(outer,sr,ar,pr)

 def test_declared_split_source_and_real_cli_builders(self):
  template=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)/'deployed';root.mkdir();m=dict(template,root=str(root),prepared_only=False,profile='paged',output_root=str(Path(d)/'output'/'paged'))
   refs={}
   for n in template['files']:
    dest=root/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/n,dest);refs[n]=C.ref(dest)
   shutil.copyfile(P/'SOURCE_TEMPLATE.json',root/'SOURCE_TEMPLATE.json');m['files']=refs;m['prepared_template']=C.ref(root/'SOURCE_TEMPLATE.json');C.write(root/'SOURCE_MANIFEST.json',m);sr=C.ref(root/'SOURCE_MANIFEST.json')
   # Real isolated -I process imports common116 and validates every own file and template in its actual split directory.
   code="import sys,json;sys.path.insert(0,sys.argv[1]);import common116 as C,run116 as R,types;m=C.source(json.loads(sys.argv[2]));a=types.SimpleNamespace(stage='sourceaudit',source_ref=sys.argv[2]);v=R.command(a);assert v[3]==str(__import__('pathlib').Path(sys.argv[1])/'owner116.py');print(len(m['files']))"
   z=subprocess.run([sys.executable,'-I','-B','-c',code,str(root),json.dumps(sr)],capture_output=True,text=True,timeout=15)
   self.assertEqual(z.returncode,0,z.stderr);self.assertEqual(int(z.stdout),len(refs))
   (root/'adapter.py').unlink()
   z=subprocess.run([sys.executable,'-I','-B','-c',code,str(root),json.dumps(sr)],capture_output=True,text=True,timeout=15)
   self.assertNotEqual(z.returncode,0)

if __name__=='__main__':unittest.main()
