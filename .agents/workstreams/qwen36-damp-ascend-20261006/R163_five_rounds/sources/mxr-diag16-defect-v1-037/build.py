"""No-device source-bound compile; exact old TriInverse flags, no Torch import."""
import argparse,ast,hashlib,importlib.util,json,os,posixpath,shutil,subprocess,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent
CUT=1792002456
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>0,'strict actual Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary immutable file');b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'whole pinned bytes');return b
def flags(raw,author,pto):
 need(hashlib.sha256(raw).hexdigest()=='23bbe505d415e1e9992cb7e7686046da07fedde00b3831c64309be285cb9bfd4','exact original compile.py')
 f=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)and n.name=='compile_tri_inverse');rows=[n for n in f.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='flags'for x in n.targets)];need(len(rows)==1,'one actual TriInverse flags list')
 ns=dict(os=types.SimpleNamespace(path=posixpath),MEMORY_MODEL='MEMORY_BASE',AICORE_ARCH='dav-2201',_KERNEL_INCLUDE=posixpath.join(str(author),'kernels/pto/include'),PTO_LIB_PATH=str(pto))
 result=eval(compile(ast.Expression(rows[0].value),'<actual-compile-tri-inverse-flags>','eval'),ns)
 need(result==['-fPIC','-shared','-xcce','-DMEMORY_BASE','-O2','-std=c++17','-I'+ns['_KERNEL_INCLUDE'],'-I'+posixpath.join(str(pto),'include'),'--npu-arch=dav-2201'],'no extra or altered compiler flags')
 return result
def headers(root):
 root=Path(root);need(root.is_absolute()and root.is_dir()and not root.is_symlink(),'exact PTO include root')
 rows={}
 for p in sorted(root.rglob('*')):
  need(not p.is_symlink(),'PTO symlink source not admitted')
  if p.is_file():rows[str(p)]=ref(p)
 need(rows,'actual nonempty PTO header closure');return rows
def source(sr):
 m=json.loads(checked(sr));need(m['schema']=='mxr.y16.compensated-source/v1'and m['root']==str(P)and m['default_enabled']is False and m['window']==dict(start=1791916056,cutoff=CUT),'explicit current private source')
 for r in[*m['files'].values(),*m['dependencies'].values()]:checked(r)
 dr=m['files']['derive.py'];s=importlib.util.spec_from_file_location('_mxr025_source_derivation',dr['path']);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
 generated,_=D.sources(checked(m['dependencies']['author_impl']),checked(m['dependencies']['author_entry']),m['dependencies']['derive028'])
 for name,raw in generated.items():need(raw==checked(m['files'][name]),'full actual source derivation/inverse, no foreign kernel edits')
 return m
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--source-audit-only',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit_only):print(json.dumps(dict(enabled=False,build=False,NPU=False)));return 0
 sr=json.loads(a.source_ref);m=source(sr)
 if a.source_audit_only:need('torch'not in sys.modules and'torch_npu'not in sys.modules,'source audit must remain stdlib only');print(json.dumps(dict(source=sr,readset=[sr,*m['files'].values(),*m['dependencies'].values()],whole_derivation_inverse_verified=True,build=False,NPU=False,resource_admitted=False)));return 0
 need(os.environ.get('MXR_Y16_BUILD_ENABLE')=='1'and not list(Path('/dev').glob('davinci*'))and'torch'not in sys.modules and'torch_npu'not in sys.modules and time.time()+270<=CUT,'MAIN Devices[] no-device build with full180+90 window')
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists()and not a.output.is_symlink(),'sole absent build, no compiler cache reuse')
 before=headers(Path(m['pto_root'])/'include');compiler=shutil.which('bisheng');nm=shutil.which('nm');need(compiler and nm,'actual same-image installed bisheng/nm required')
 compiler_ref=ref(Path(compiler).resolve());nm_ref=ref(Path(nm).resolve());a.output.mkdir(mode=0o700);so=a.output/'libmxr_diag16_defect_MEMORY_BASE.so';nm_argv=[nm,'-D','--defined-only',str(so)]
 argv=[compiler,*flags(checked(m['dependencies']['compile_py']),m['author_root'],m['pto_root']),str(P/'tri_inverse_y16.cpp'),'-o',str(so)]
 error=None;symbols=None;secondary=[];after={}
 try:
  with(a.output/'compile.stdout').open('xb')as out,(a.output/'compile.stderr').open('xb')as err:
   subprocess.run(argv,stdout=out,stderr=err,timeout=180,check=True)
  with(a.output/'nm.stdout').open('xb')as out,(a.output/'nm.stderr').open('xb')as err:subprocess.run(nm_argv,stdout=out,stderr=err,timeout=15,check=True)
  symbols=(a.output/'nm.stdout').read_bytes().decode('utf8',errors='strict')
  need(all(name in symbols.split()for name in('call_mxr_y16_control','call_mxr_y16_compensated')),'both unique actual host ABI exports')
 except BaseException as e:error=e
 try:
  for r in[*m['files'].values(),*m['dependencies'].values()]:checked(r)
  after=headers(Path(m['pto_root'])/'include');need(before==after and compiler_ref==ref(Path(compiler).resolve())and nm_ref==ref(Path(nm).resolve()),'entire actual compiler/PTO closure unchanged')
 except BaseException as e:
  if error is None:error=e
  else:secondary.append(repr(e))
 body=dict(schema='mxr.y16.compensated-build/v1',source=sr,status='compiled_no_device'if error is None else'FAILED',argv=argv,compiler=compiler_ref,nm=nm_ref,nm_argv=nm_argv,library=ref(so)if so.is_file()else None,symbols=symbols,compile_stdout=ref(a.output/'compile.stdout')if(a.output/'compile.stdout').is_file()else None,compile_stderr=ref(a.output/'compile.stderr')if(a.output/'compile.stderr').is_file()else None,nm_stdout=ref(a.output/'nm.stdout')if(a.output/'nm.stdout').is_file()else None,nm_stderr=ref(a.output/'nm.stderr')if(a.output/'nm.stderr').is_file()else None,header_refs_before=before,header_refs_after=after,error=repr(error)if error else None,secondary=secondary,Devices=[],NPU=False,matrix_gate_pass=False,graph_qualified=False,model_ready=False,performance_ready=False,task_ready=False)
 path=a.output/'BUILD.json'
 with path.open('x',encoding='utf8')as h:json.dump(body,h,sort_keys=True,allow_nan=False);h.write('\n')
 print('MAIN_MXR_Y16_BUILD '+json.dumps(ref(path)),flush=True)
 if error:raise error
 return 0
if __name__=='__main__':raise SystemExit(main())
