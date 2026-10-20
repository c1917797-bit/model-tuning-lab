"""Actual donor I/O controls. Linux directory durability is never modeled PASS."""
import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import snapshot_publication as S
P=Path(__file__).resolve().parent

class Tests(unittest.TestCase):
 def test_declared_exact_donor_cold_and_missing_or_mutated_donor_reject(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());r=m['files']['dependencies/publication_common.py'];b=(P/'dependencies/publication_common.py').read_bytes()
  self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],S.DONOR_SHA));self.assertEqual(r['sha256'],S.DONOR_SHA)
  with tempfile.TemporaryDirectory()as td:
   q=Path(td);(q/'dependencies').mkdir();(q/'snapshot_publication.py').write_bytes((P/'snapshot_publication.py').read_bytes());d=q/'dependencies/publication_common.py';d.write_bytes(b)
   code="import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import snapshot_publication as s;assert Path(s.donor().__file__).resolve()==(Path(sys.argv[1])/'dependencies/publication_common.py').resolve()"
   argv=[sys.executable,'-I','-B','-c',code,str(q)]
   actual=subprocess.run(argv,capture_output=True,text=True,timeout=15);self.assertEqual(actual.returncode,0,actual.stderr)
   d.unlink();self.assertNotEqual(subprocess.run(argv,capture_output=True,text=True,timeout=15).returncode,0)
   d.write_bytes(b+b'\n');self.assertNotEqual(subprocess.run(argv,capture_output=True,text=True,timeout=15).returncode,0)

 @unittest.skipIf(os.name=='nt','Linux sameimage mandatory: actual O_DIRECTORY and directory fsync cannot be certified on Windows')
 def test_actual_cold_publish_stage_link_fsync_glob_stdjson_roundtrip(self):
  with tempfile.TemporaryDirectory()as td:
   q=Path(td)
   code="""import sys,json,hashlib,os,stat
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import snapshot_publication as s
root=Path(sys.argv[2]);path=root/'worker-403-snapshot-1.json';value=dict(schema='software-publication-only',pid=403,ordinal=1,qualification=False,text='strict json')
actual=os.fsync;seen=[]
def fsync(fd):
 seen.append('dir'if stat.S_ISDIR(os.fstat(fd).st_mode)else'file');return actual(fd)
os.fsync=fsync
r=s.publish(path,value);assert seen==['file','dir'];assert json.loads(path.read_bytes())==value
raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\\n').encode();assert path.read_bytes()==raw
assert r==dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
visible=list(root.glob('worker-*-snapshot-*.json'));pending=list(root.glob('.worker-403-snapshot-1.json.pending-*'))
assert visible==[path]and len(pending)==1 and pending[0].read_bytes()==raw
assert os.stat(path).st_ino==os.stat(pending[0]).st_ino
try:s.publish(path,value)
except ValueError:pass
else:raise AssertionError('duplicate publication accepted')
assert len(list(root.iterdir()))==2 and path.read_bytes()==raw
print(json.dumps(dict(real_file_and_directory_fsync=True,real_hardlink=True,std_json_roundtrip=True,model_qualified=False)))
"""
   result=subprocess.run([sys.executable,'-I','-B','-c',code,str(P),str(q)],capture_output=True,text=True,timeout=20)
   self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(json.loads(result.stdout)['real_file_and_directory_fsync'])

 def test_existing_destination_nan_and_cap_fail_before_publication(self):
  with tempfile.TemporaryDirectory()as td:
   q=Path(td);dest=q/'worker-403-snapshot-1.json';dest.write_bytes(b'old immutable evidence')
   with self.assertRaises(ValueError):S.publish(dest,{'new':True})
   self.assertEqual(dest.read_bytes(),b'old immutable evidence');self.assertEqual(len(list(q.iterdir())),1)
   for value in({'nan':float('nan')},{'too_large':'x'*(256*1024)}):
    with self.assertRaises(ValueError):S.publish(q/'rejected.json',value)
   self.assertEqual(len(list(q.iterdir())),1)

 def test_real_staging_fsync_then_link_failure_retains_original_bytes(self):
  with tempfile.TemporaryDirectory()as td:
   q=Path(td);dest=q/'worker-403-snapshot-1.json';value={'software_only':True};raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();events=[];real_sync=os.fsync
   def fsync(fd):events.append('file-fsync');return real_sync(fd)
   def rejected(src,target,**kw):events.append('link-attempt');self.assertEqual(Path(src).read_bytes(),raw);raise PermissionError('software injection at OS link; not publisher mock')
   with patch.object(os,'fsync',side_effect=fsync),patch.object(os,'link',side_effect=rejected):
    with self.assertRaises(PermissionError):S.publish(dest,value)
   self.assertEqual(events,['file-fsync','link-attempt']);self.assertFalse(dest.exists());staged=list(q.glob('.worker-403-snapshot-1.json.pending-*'));self.assertEqual(len(staged),1);self.assertEqual(staged[0].read_bytes(),raw)

 def test_write_fsync_or_extent_failure_never_links_and_retains_stage(self):
  with tempfile.TemporaryDirectory()as td:
   q=Path(td);dest=q/'worker-403-snapshot-1.json'
   with patch.object(os,'fsync',side_effect=OSError('software injected file fsync failure')):
    with self.assertRaises(OSError):S.publish(dest,{'software_only':True})
   self.assertFalse(dest.exists());self.assertEqual(len(list(q.glob('.worker-403-snapshot-1.json.pending-*'))),1)
   extent=q/'extent.json'
   with self.assertRaises(ValueError):S.donor().binary(extent,[b'full retained stage'],1)
   self.assertFalse(extent.exists());staged=list(q.glob('.extent.json.pending-*'));self.assertEqual(len(staged),1);self.assertEqual(staged[0].read_bytes(),b'full retained stage')

if __name__=='__main__':unittest.main()
