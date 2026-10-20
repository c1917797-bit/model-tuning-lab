"""Scoped host-only MEM32 provider shared by short011 and future pair025.
Does not execute a model, modify source files or change qualification admission.
"""
import hashlib
from pathlib import Path
PINS={22569:'8c83e08318b530c4d022b91bbacd34b12121b3380e1a14d32262c9a3875f6fa7',22338:'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'}
def prepare(S,c):
 p=Path(S.__file__);b=p.read_bytes()
 if PINS.get(len(b))!=hashlib.sha256(b).hexdigest():raise ValueError('actual011/025 immutable source wholebytes')
 if S.MEM!=64*c.GIB or S.RESERVE!=8*c.GIB+512*1024**2 or S.HOST_MEM!=512*1024**2:raise ValueError('exact original resource globals before explicit new cap')
 if S.create_argv.__globals__ is not vars(S) or S.validate_inspect.__globals__ is not vars(S):raise ValueError('create and inspect must share actual safety globals')
 S.MEM=32*c.GIB;S.RESERVE=8*c.GIB
 return dict(schema='mxr.scoped-cap32-provider/v1',original_source=dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()),guest_model_GiB=32,guest_CPU_GiB=8,host_GiB=.5,RAM_reserve_GiB=8,model_initial_GiB=40.5,CPU_initial_GiB=40.5,dense_candidate_common=True,cgroup_OOM_is_failure_not_numerical_PASS=True)
def explicit_lazy_argv(argv):
 flags=['--load-format','--safetensors-load-strategy','--model-loader-extra-config']
 if any(x in argv for x in flags):raise ValueError('no duplicate/ambient load options')
 return list(argv)+['--load-format','safetensors','--safetensors-load-strategy','lazy','--model-loader-extra-config','{"enable_multithread_load":false}']
def bind_pair_load(original_load):
 # Apply ONLY after actual004 owned_substrate.load() has verified original025
 # source/time/context and73GiB original; BEFORE H.controller(S,co) or creation.
 def load():
  c,S,H,pairs=original_load();proof=prepare(S,c)
  H._cap32_source_bound_contract=proof
  return c,S,H,pairs
 return load
def bind_pair_command(original_command):
 # Same binding installed for BOTH dense and candidate server roles.
 return lambda port:explicit_lazy_argv(original_command(port))
