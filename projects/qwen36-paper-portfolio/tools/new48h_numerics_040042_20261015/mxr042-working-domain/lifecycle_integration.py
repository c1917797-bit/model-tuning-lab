"""Call unmodified real lifecycle helper with bounded cold lifecycle fixtures."""
import datetime,hashlib,inspect,types
from pathlib import Path
SHA='4bbd492809c9ba1922fd3885b101f8cc6fe187884703c21e4a2d44acd1444b75'
def check(L):
 path=Path(inspect.getsourcefile(L.owned_exit_identity));b=path.read_bytes()
 if len(b)!=6865 or hashlib.sha256(b).hexdigest()!=SHA:raise ValueError('actual original lifecycle helper source')
 absent=dict(pid=222,reads={k:dict(status='missing')for k in('stat_before','stat_after','cmdline','cgroup')})
 results={}
 for label in('replay','matrix'):
  child=types.SimpleNamespace(pid=333);ctl=types.SimpleNamespace(child=child,child_label=label,cid='fixtureCID',child_started=datetime.datetime(2026,10,15,tzinfo=datetime.timezone.utc),expected_child_argv=['fixture','-I','-B'])
  proof=dict(pid=222,start_ticks=123,argv=ctl.expected_child_argv,cgroup='/docker/fixtureCID');known=dict(child=child,association=L.child_association(ctl),live_proof=proof,live_raw_ref=dict(fixture_only=True));ctl.known_processes={(222,123):known}
  try:accepted=L.owned_exit_identity(ctl,222,absent,absent)is known
  except ValueError:accepted=False
  results[label]=accepted
 if results!={'replay':False,'matrix':True}:raise ValueError('actual inherited child-label contract drift')
 return dict(schema='mxr.actual-lifecycle-cold-integration/v042',source=dict(path=str(path),bytes=len(b),sha256=SHA),fixtures=True,replay_rejected=True,matrix_accepted=True,actual_process_permission_granted=False)
