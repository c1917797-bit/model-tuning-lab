import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import stream_closed_tree as S
def write_index(path,root,rows):
 with path.open('w',encoding='utf8',newline='\n')as f:
  f.write('{"files":[')
  for i,row in enumerate(rows):
   if i:f.write(',')
   f.write(json.dumps(row,sort_keys=True))
  f.write('],"root":'+json.dumps(str(root))+'}\n')
 return S.file_ref(path)
def fixture(root):
 (root/'sub').mkdir();(root/'a').write_bytes(b'actual software fixture');(root/'sub/b').write_bytes(b'bounded')
 rows=[]
 for p in sorted(q for q in root.rglob('*')if q.is_file()):
  st=p.stat();rows.append(dict(relative_path=p.relative_to(root).as_posix(),bytes=st.st_size,mtime_ns=st.st_mtime_ns,inode=st.st_ino,device=st.st_dev,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return rows
def process_peak():
 if os.name!='nt':
  import resource
  return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
 import ctypes
 class COUNTERS(ctypes.Structure):_fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
 c=COUNTERS();c.cb=ctypes.sizeof(c);ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
 if not ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(ctypes.windll.kernel32.GetCurrentProcess()),ctypes.byref(c),c.cb):raise OSError('actual local process peak unavailable')
 return c.PeakWorkingSetSize
class Controls(unittest.TestCase):
 def test_full_positive_and_mutation_negative(self):
  with tempfile.TemporaryDirectory()as d:
   base=Path(d);root=base/'leaf';root.mkdir();rows=fixture(root);index=write_index(base/'tree.json',root,rows)
   v=S.verify(index,root);self.assertEqual(v['files'],2);self.assertFalse(v['numeric_qualified'])
   (root/'a').write_bytes(b'changed')
   with self.assertRaises(ValueError):S.verify(index,root)
 def test_bad_schema_ref_truncation_and_coverage(self):
  with tempfile.TemporaryDirectory()as d:
   base=Path(d);root=base/'leaf';root.mkdir();rs=fixture(root)
   for mode in('duplicate','missing','extra','badsha','unknownrow','unknownroot','truncated','wrongref'):
    rows=[dict(x)for x in rs];p=base/'tree.json'
    if mode=='duplicate':rows.append(rows[-1])
    elif mode=='missing':rows.pop()
    elif mode=='extra':(root/'unexpected').write_bytes(b'not indexed')
    elif mode=='badsha':rows[0]['sha256']='0'*64
    elif mode=='unknownrow':rows[0]['unexpected']=True
    index=write_index(p,root,rows)
    if mode=='unknownroot':p.write_text(p.read_text().replace('"root":','"unexpected":'),encoding='utf8');index=S.file_ref(p)
    elif mode=='truncated':p.write_bytes(p.read_bytes()[:-5]);index=S.file_ref(p)
    elif mode=='wrongref':index['sha256']='0'*64
    with self.subTest(mode=mode),self.assertRaises((ValueError,FileNotFoundError)):S.verify(index,root)
    if(root/'unexpected').exists():(root/'unexpected').unlink()
 def test_actual_fresh_process_bounded_135520_index(self):
  p=subprocess.run([sys.executable,'-I','-B',__file__,'--stress'],capture_output=True,text=True,timeout=60)
  self.assertEqual(p.returncode,0,p.stderr);v=json.loads(p.stdout);self.assertEqual(v['rows'],135520);self.assertLess(v['actual_process_peak_bytes'],128*1024**2)
if __name__=='__main__':
 if '--stress'in sys.argv:
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)/'synthetic-not-actual-raw';path=Path(d)/'large-index.json'
   def generated():
    for i in range(135520):yield dict(relative_path='tensor-blobs/'+('%064x'%i)+'.bin',bytes=4096,mtime_ns=1792226600000000000,inode=i,device=1,sha256='%064x'%i)
   index=write_index(path,root,generated());n=sum(1 for _ in S.rows(index,root));print(json.dumps(dict(rows=n,index_bytes=index['bytes'],actual_process_peak_bytes=process_peak(),synthetic_fixture_only=True,qualified=False)))
 else:unittest.main()
