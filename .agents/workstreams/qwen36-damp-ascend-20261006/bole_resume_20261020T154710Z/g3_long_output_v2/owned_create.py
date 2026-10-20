"""Small explicit mount/profile creator over genuine025 create_owned/inspect."""
import json,re
from pathlib import Path
def create(c,S,ctl,sr,readset,role,source_root):
 leaf=ctl.out
 cpu=role in('cpu-preflight','stream-consumer')
 mounts={'/usr/local/Ascend/driver':('/usr/local/Ascend/driver',False),
  '/models/Qwen3.6-27B':('/cache/efim/Qwen3.6-27B',False),
  str(source_root):(str(source_root),False),str(leaf):(str(leaf),True),
  '/adakv-results':(str(leaf),True)}
 if role=='stream-consumer':
  m=c.obj(sr);receipt=Path(m['model_receipt_root']);channel=Path(m['stream_channel_root'])
  mounts={str(source_root):(str(source_root),False),str(receipt):(str(receipt),False),
      str(channel):(str(channel),True),'/adakv-results':(str(channel),True)}
 # Exact immutable file mounts avoid granting broad cache/root reads simply
 # because a standalone prerequisite JSON sits beside experiment outputs.
 for r in readset:
  p=Path(r['path'])
  if p==leaf or leaf in p.parents:raise ValueError('no readonly input shadows ownoutput')
  if source_root not in p.parents:mounts[str(p)]=(str(p),False)
 ctl.expected=dict(cid=None,name=ctl.name,image=c.IMAGE,arm=role,source=sr,
  host_sha256=c.sha(S.__file__),guest_cpus=([145]if cpu else ctl.cpu['guest_cpus']),mounts=mounts)
 if not re.fullmatch('[A-Za-z0-9_-]{1,100}',ctl.name):raise ValueError('new exact bounded name')
 old,_=ctl.call('unique-name',[S.DOCKER,'ps','-a','--filter','name=^/'+ctl.name+'$','--format','{{.ID}}'])
 if old['stdout'].strip():raise ValueError('owned name exists; no reuse/delete')
 for src,rw in mounts.values():
  if not Path(src).exists():raise ValueError('actual exact mount source')
 for node in({}if cpu else S.device_map()):
  if not Path(node).exists():raise ValueError('actual mapped physicalnode')
 ctl.create_owned({'safety_host.py':c.sha(S.__file__)})
 x,ref=ctl.inspect()
 if x['State']['Running']or x['State']['Pid']!=0:raise ValueError('fresh actual stopped owninit')
 ctl.call('start',[S.DOCKER,'start',ctl.cid],cap=60);x,ref=ctl.inspect()
 if not x['State']['Running']or x['State']['Pid']<=0 or x['State'].get('OOMKilled'):raise ValueError('actual live ownedinit')
 cv=S.H.cpu_view(x['State']['Pid'])
 if cv['effective_capacity']!=(1 if cpu else 3)or cv['effective_cpus']!=ctl.expected['guest_cpus']:raise ValueError('actual cpucgroup proof')
 c.write(leaf/'GUEST_CPU.json',cv);return ref


