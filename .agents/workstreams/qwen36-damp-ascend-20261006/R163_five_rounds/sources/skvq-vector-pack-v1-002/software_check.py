"""Actual CPU full affine bytes + exact source inverse; not target/NPU evidence."""
import hashlib,importlib.util,itertools,json,os,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
ORIGINAL=Path('C:/Users/Huawei/AppData/Local/Temp/skvq-r118-preparation/writer-full-v1-003/writer.py')
ORACLE=Path('C:/Users/Huawei/AppData/Local/Temp/skvq-task-domain-math-20261012-002/donors/writer_byte_oracle.py')
DONOR=Path('C:/Users/Huawei/AppData/Local/Temp/skvq-task-domain-math-20261012-002/donors/device_writer.py')
CHANGES=[('self.pack_factors=tuple(factors[j]for j in range(8//bits))','self.pack_factors=tuple(factors[j]for j in range(8//bits))\n        self.pack_factor_bank=factors.view(1,1,8//bits)'),("'packed':empty((16,w),torch.int32),'shifted':empty((16,w),torch.int32)","'packed':empty((16,w),torch.int32),'weighted':empty((16,w,n),torch.int32)"),("g['ints'].zero_();g['ints_live'].copy_(g['norm']);g['packed'].zero_()\n            for j in range(n):\n                t.mul(g['ints3'][:,:,j],self.r.pack_factors[j],out=g['shifted'])\n                t.add(g['packed'],g['shifted'],out=g['packed'])","g['ints'].zero_();g['ints_live'].copy_(g['norm'])\n            t.mul(g['ints3'],self.r.pack_factor_bank,out=g['weighted'])\n            t.sum(g['weighted'],dim=2,dtype=t.int32,out=g['packed'])")]
def inverse(original,derivative):
 if hashlib.sha256(original).hexdigest()!='05df54778201e4b350524d03a9588cbcfe277382d1183bc7e50d927797a61866':raise ValueError('original fixed source')
 text=derivative.decode()
 for old,new in reversed(CHANGES):
  if text.count(new)!=1:raise ValueError('unique packing delta')
  text=text.replace(new,old)
 if text.encode()!=original:raise ValueError('complete byte inverse, no other algorithm/control change')
 return True
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
class Layout:
 def __init__(self,axis):self.permutation=tuple(reversed(range(256)));self.starts=(0,63,128,193,256)if axis=='K'else(0,1,71,190,256);self.smooth=(1.,)*256;self.clip=.95
 def validate(self):
  if sorted(self.permutation)!=list(range(256)):raise ValueError('source-explicit component layout')
 def obj(self):return dict(permutation=list(self.permutation),starts=list(self.starts),smooth=list(self.smooth),clip=self.clip)
def matrix(torch,writer):
 need=lambda v:None if v else (_ for _ in()).throw(ValueError('whole independent affine bytes'))
 oracle={};raw=ORACLE.read_bytes();need(hashlib.sha256(raw).hexdigest()=='deea191c19694ecb961f17f291eba5a3fdd8298f862a12dbed860e7d73c03b70');exec(compile(raw,str(ORACLE),'exec',dont_inherit=True),oracle)
 device=torch.device('cpu');cells=0
 for dtype,kind in((torch.bfloat16,'bfloat16'),(torch.float16,'float16')):
  for bits in(2,4):
   layouts={a:Layout(a)for a in('K','V')};pool={}
   for axis,l in layouts.items():
    width=sum((z-a+8//bits-1)//(8//bits)for a,z in zip(l.starts,l.starts[1:]))
    pool[axis]={n:torch.empty(shape,dtype=dt,device=device)for n,shape,dt in (('payload',(16,40960,width),torch.uint8),('scales',(16,40960,4),dtype),('zero_points',(16,40960,4),dtype),('edges',(16,133,256),dtype))}
   r=writer.WriterResources(torch,pool,layouts,DONOR.read_bytes(),dtype=dtype,device=device,bits=bits)
   for b in range(1,17):
    seed=torch.linspace(-.9,.7,b*256,dtype=dtype).reshape(b,256);plan=writer.BoundWriter(r,None,None,None,None,None,None,b,False,None);plan.s['seed'].copy_(seed)
    input_bytes=seed.contiguous().view(torch.uint8).numpy().tobytes()
    for axis in('K','V'):
     plan.quantize(axis);o=plan.s['axis'][axis];observed={n:o[k].contiguous().view(torch.uint8).numpy().tobytes()for n,k in(('payload','payload'),('scales','scales'),('zero_points','zeros'))};need(observed==oracle['encode_scalar'](input_bytes,layouts[axis].obj(),bits,kind));cells+=1
   del plan,r,pool
 return cells
class Controls(unittest.TestCase):
 def test01_full_inverse(self):self.assertTrue(inverse(ORIGINAL.read_bytes(),(P/'writer.py').read_bytes()))
 def test02_inverse_extra_change_rejected(self):
  with self.assertRaises(ValueError):inverse(ORIGINAL.read_bytes(),(P/'writer.py').read_bytes()+b'changed=1\n')
 def test03_exhaustive512_integer_bytes(self):
  import torch
  for bits in(2,4):
   n=8//bits;qs=list(itertools.product(range(1<<bits),repeat=n));x=torch.tensor(qs,dtype=torch.int32);f=torch.tensor([1<<(bits*(n-1-j))for j in range(n)],dtype=torch.int32);out=torch.empty(256,dtype=torch.int32);torch.sum(torch.mul(x,f),dim=1,dtype=torch.int32,out=out)
   scalar=[sum(v<<(bits*(n-1-j))for j,v in enumerate(q))for q in qs];self.assertEqual(out.tolist(),scalar);self.assertEqual(sorted(out.tolist()),list(range(256)))
 def test04_real128_cpu_affine_cells(self):
  import torch
  torch.set_num_threads(1);m=load(P/'writer.py','_vector_original_CPU_writer');prior=os.environ.get(m.ENV);os.environ[m.ENV]='1'
  try:self.assertEqual(matrix(torch,m),128)
  finally:
   if prior is None:os.environ.pop(m.ENV,None)
   else:os.environ[m.ENV]=prior
 def test05_default_off(self):
  self.assertIn("need(os.environ.get(ENV)=='1','fixed writer defaults OFF')",(P/'writer.py').read_text())
def run(m):
 global ORIGINAL,ORACLE,DONOR
 ORIGINAL=Path(m['original_writer']['path']);ORACLE=Path(m['oracle']['path']);DONOR=Path(m['donor']['path'])
 for r in(m['original_writer'],m['oracle'],m['donor']):
  b=Path(r['path']).read_bytes()
  if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('complete actual donor source')
 result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Controls).run(result)
 if not(result.testsRun==5 and not result.errors and not result.failures and not result.skipped):raise ValueError(repr(dict(tests=result.testsRun,errors=result.errors,failures=result.failures)))
 return dict(tests=5,affine_CPU_cells=128,exhaustive_integer_words=512,NPU=False,source_inverse_complete=True)
if __name__=='__main__':unittest.main()

