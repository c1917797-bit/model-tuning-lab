"""Narrow original external policy composition: sole additional exact payload RW.

No rootfs/device/inspect/label predicate is replaced. CPU stages keep one RW.
"""
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def install(E,S,Owned,c,root,safety_ref,payload,ro_roots=()):
 root=Path(root);payload=Path(payload)
 need(root.is_absolute()and payload.is_absolute()and payload.parent.as_posix()=='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061','exact separate payload root')
 original_environment=E.environment
 def environment(e):
  mounts=e['mounts'];nested=mounts.get('/adakv-results/model/capture')
  if nested is None:return original_environment(e)
  need(nested==(payload.as_posix(),True)and mounts.get('/adakv-results')==((root/'candidate').as_posix(),True),'only candidate exact two nested RW mappings')
  need({p for p,w in mounts.values()if w}=={payload.as_posix(),(root/'candidate').as_posix()},'no third RW')
  copy=dict(e,mounts={k:v for k,v in mounts.items()if k!='/adakv-results/model/capture'})
  return original_environment(copy)
 E.environment=environment
 result=E.install(S,Owned,c,root,safety_ref)
 inherited_init=Owned.__init__;inherited_create=S.create_argv;tracked={}
 def init(self,leaf):
  inherited_init(self,leaf);tracked[self.name]=self
  if Path(leaf)==root/'candidate':
   self._external_output_expected['mounts']['/adakv-results/model/capture']=(payload.as_posix(),True)
   environment(self._external_output_expected)
 def create(e):
  need(e['name']in tracked,'exact tracked actual owner')
  ctl=tracked[e['name']]
  for value in ro_roots:
   q=Path(value);need(q.is_absolute()and q.is_dir()and all(not x.is_symlink()for x in(q,*q.parents)),'exact declared RO directory')
   need(q.as_posix()not in e['mounts']or e['mounts'][q.as_posix()]==(q.as_posix(),False),'no RO shadow/downgrade of existing mount')
   e['mounts'][q.as_posix()]=(q.as_posix(),False)
  if Path(ctl.out)==root/'candidate':
   need(payload.is_dir()and all(not p.is_symlink()for p in(payload,*payload.parents)),'reserved ordinary payload exists before create')
   need('/adakv-results/model/capture'not in e['mounts'],'no caller-controlled nested alias')
   e['mounts']['/adakv-results/model/capture']=(payload.as_posix(),True)
  return inherited_create(e)
 Owned.__init__=init;S.create_argv=create
 return dict(result,additional_candidate_mount=dict(host=payload.as_posix(),guest='/adakv-results/model/capture',read_write=True),same_global_workspace_cap_bytes=32*2**30)
