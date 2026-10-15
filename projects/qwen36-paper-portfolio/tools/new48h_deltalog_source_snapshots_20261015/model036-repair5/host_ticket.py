"""Exact017 Owned controller reuse; new source/run identity, no new safety."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import owner_overlay as O
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=O.current(sr)
 # Complete exact017 source and donor scopes stay RO. No controller bypass.
 for r in m['dependencies']:O.obj_file(r)
 H=module(O.obj_file(m['host017_ref']),'_dl025_original017_host')
 original_adapt=H.adapt
 def adapted(text,s,p):
  result,pairs=original_adapt(text,s,p)
  before=result;extra=[]
  for old,new in (('lowbit/deltalog-service-empirical-owned-v1-017','lowbit/'+HERE.name),('lowbit/run-deltalog-service-empirical-main-NEW48H_017_001',Path(m['output_root']).relative_to(H.LOW.parent).as_posix())):
   O.need(result.count(old)==1,'single registered017 deployment/output delta');result=result.replace(old,new);extra.append((old,new))
  inverse=result
  for old,new in reversed(extra):O.need(inverse.count(new)==1,'unique overlay inverse');inverse=inverse.replace(new,old)
  O.need(inverse==before,'whole017 resource/controller delta inverse')
  return result,pairs
 H.HERE=HERE;H.DEPLOY=HERE;H.OUT=Path(m['output_root']);H.adapt=adapted
 original_leaf=H.leaf
 def leaf(name):
  if (HERE/name).is_file():return module(HERE/name,'_dl025_'+name[:-3])
  return module(O.obj_file(m['owner017_files'][name]),'_dl025_donor_'+name[:-3])
 H.leaf=leaf
 H.source=lambda digest:O.current(dict(path=str(HERE/'SOURCE_MANIFEST.json'),bytes=(HERE/'SOURCE_MANIFEST.json').stat().st_size,sha256=digest))
 refs=[sr,*m['files'].values(),*m['dependencies']]
 for r in O.transitive_refs(m):O.obj_file(r)
 refs.extend(O.transitive_refs(m))
 bridge=O.model_gate(m);pr=m['bridge024_owner_ref']
 h,pairs=H.bind(sr,pr,refs)
 if a.source_audit:
  O.need('torch'not in sys.modules and'torch_npu'not in sys.modules,'host source-only')
  print(json.dumps(dict(source=sr,NPU=False,source_checked=True,model_ready=False,actual_owned_controller=m['host017_ref'],pending=m['pending'])));return 0
 H.protect_cleanup(h)
 h.run=lambda source_ref,started:leaf('run_owned.py').run(h,source_ref,pr,started)
 O.need(HERE==Path(m['root']),'actual reviewedLinux deployment only')
 return h.main(['--execute','--source-sha256',sr['sha256']])
if __name__=='__main__':raise SystemExit(main())
