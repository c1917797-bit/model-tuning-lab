"""Exact017 Owned controller reuse; new source/run identity, no new safety."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import owner_overlay as O
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--postconsume-input-ref');a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=O.current(sr)
 import firstdecode_refs as FR
 post_ref=json.loads(a.postconsume_input_ref)if a.postconsume_input_ref else None
 post_refs=[]
 if post_ref is not None:post,post_refs=FR.post(O,m,post_ref);O.need(post['model_source']==sr,'same actual model source')
 active_output=m['postconsumer_output_root']if post_ref is not None else m['output_root']
 # Complete exact017 source and donor scopes stay RO. No controller bypass.
 for r in m['dependencies']:O.obj_file(r)
 H=module(O.obj_file(m['host017_ref']),'_dl025_original017_host')
 import window_overlay as W
 O.obj_file(W.AUTHORITY);W.install(H,m)
 original_adapt=H.adapt
 def adapted(text,s,p):
  result,pairs=original_adapt(text,s,p)
  result=W.transform(result)
  before=result;extra=[]
  from packet_contract import OUTPUT
  O.need(m['output_root']==OUTPUT,'only exact registered model opt output')
  OUTPUT=active_output
  for old,new in (('lowbit/deltalog-service-empirical-owned-v1-017','lowbit/'+HERE.name),('OUT = PREP / "lowbit/run-deltalog-service-empirical-main-NEW48H_017_001"','OUT = Path('+json.dumps(OUTPUT)+')'),('need(free >= S.RESERVE + (S.WORKSPACE if initial else 0), "actual Docker root storage reserve")','_EXTERNAL.docker_gate(self, S, free, initial)')):
   O.need(result.count(old)==1,'single registered017 deployment/output delta');result=result.replace(old,new);extra.append((old,new))
  inverse=result
  for old,new in reversed(extra):O.need(inverse.count(new)==1,'unique overlay inverse');inverse=inverse.replace(new,old)
  O.need(inverse==before,'whole017 resource/controller delta inverse')
  return result,pairs
 H.HERE=HERE;H.DEPLOY=HERE;H.OUT=Path(active_output);H.adapt=adapted
 original_leaf=H.leaf
 def leaf(name):
  if (HERE/name).is_file():return module(HERE/name,'_dl025_'+name[:-3])
  return module(O.obj_file(m['owner017_files'][name]),'_dl025_donor_'+name[:-3])
 H.leaf=leaf
 H.source=lambda digest:O.current(dict(path=str(HERE/'SOURCE_MANIFEST.json'),bytes=(HERE/'SOURCE_MANIFEST.json').stat().st_size,sha256=digest))
 refs=[sr,*m['files'].values(),*m['dependencies'],*FR.refs(O,m),*post_refs]
 for r in O.transitive_refs(m):O.obj_file(r)
 refs.extend(O.transitive_refs(m))
 bridge=O.model_gate(m);pr=m['bridge024_owner_ref']
 h,pairs=H.bind(sr,pr,refs)
 h._EXTERNAL=leaf('external_output_policy.py')
 if a.source_audit:
  O.need('torch'not in sys.modules and'torch_npu'not in sys.modules,'host source-only')
  print(json.dumps(dict(source=sr,NPU=False,source_checked=True,model_ready=False,actual_owned_controller=m['host017_ref'],pending=m['pending'])));return 0
 H.protect_cleanup(h)
 original_safety=h.safety
 def safety(source_ref,policy,started):
  base,S,Owned,state=original_safety(source_ref,policy,started)
  # Original017 has already installed the source-bound cap32 provider BEFORE
  # stage_resources captures its private globals; create/inspect also see32.
  O.need(S.MEM==32*base.GIB and S.HOST_MEM==512*1024**2 and S.RESERVE==8*base.GIB,'same32 create/inspect/resources with original host/reserve')
  state['stage_resource_contract'].update(model_initial_GiB=40.5,model_guest_GiB=32,actual_model_guest_GiB=32,host_GiB=.5,reserve_GiB=8)
  # Install only now, before run_owned constructs its first Owned object.
  import firstdecode_output_policy as FD,model_snapshot_budget as B
  extra=FR.payload_roots(O,m)
  if post_ref is not None:extra=extra+(m['output_root'],B.LEAF.as_posix())
  state['external_output_policy']=FD.install(h._EXTERNAL,S,Owned,base,h.OUT,m['ownership_observation_refs']['safety'],B.LEAF,extra)
  return base,S,Owned,state
 h.safety=safety
 original_child=h.child
 def child(ctl,c,label,*args,**kwargs):
  result=original_child(ctl,c,label,*args,**kwargs)
  if label=='DL-cold-source':
   cp=c.obj(c.ref(ctl.out/'CPU.json'));receipt=leaf('ipc_receipt.py')
   receipt.check(cp,sr,c.obj,c.ref(ctl.out/'IPC_CONTROLS.json'))
  return result
 h.child=child
 import firstdecode_owner as FD
 h._SNAPSHOT=FD.lease(O,m,sr)
 if post_ref is None:h.run=lambda source_ref,started:leaf('run_owned.py').run(h,source_ref,pr,started)
 else:h.run=lambda source_ref,started:leaf('postconsume_recipe.py').run(h,source_ref,pr,started,post_ref)
 O.need(HERE==Path(m['root']),'actual reviewedLinux deployment only')
 return h.main(['--execute','--source-sha256',sr['sha256']])
if __name__=='__main__':raise SystemExit(main())
