"""Synchronous pure-consumer import scope; no preload removal or foreign reuse.
Entry rejects owned aliases already present. Exit restores only this invocation's
module registrations/path and fails on mutation of pre-existing registrations.
The original source-qualified loaders and all numerical predicates stay intact.
"""
import json,sys
FIRST_NAMES=("cpu_raw_resources","provider_independent","explicit_geometry",
 "_kivi_firstdecode_source_loader","_kivi_b1_exact_raw_delegate","_mixed_exact_raw023_delegate")
FIRST_PREFIXES=("_kivi_firstdecode_whole_",)
MIXED_NAMES=("_kivi_c16_exact_mixed_whole","_mixed_exact_raw023_delegate",
 "_kivi_mixed_source_loader","provider_independent","explicit_geometry","cpu_raw_resources")
MIXED_PREFIXES=("_mixed_terminal_","_kivi_mixed_release_")
def need(v,m):
 if not v:raise ValueError(m)
def isolated_call(call,scope):
 need(callable(call) and scope in("firstdecode","mixed"),"explicit pure consumer scope")
 names,prefixes=(FIRST_NAMES,FIRST_PREFIXES)if scope=="firstdecode"else(MIXED_NAMES,MIXED_PREFIXES)
 need(not any(n in names or n.startswith(prefixes)for n in sys.modules),
  "consumer namespace already occupied at entry: "+scope)
 registry=sys.modules;before=dict(registry);path=sys.path;original_path=list(path)
 primary=None;answer=None;violation=None
 try:
  answer=call()
  json.dumps(answer,allow_nan=False) # Pure evidence only; no module/Context escapes.
 except BaseException as error:primary=error
 finally:
  changed=[n for n,v in before.items()if n not in registry or registry[n]is not v]
  if sys.modules is not registry or sys.path is not path or changed or list(path)!=original_path:
   violation="consumer changed pre-existing namespace/path: "+repr(changed)
  # Never remove an entry that existed before this invocation. New partial
  # imports are discarded on both successful and exceptional exits.
  for name in tuple(registry):
   if name not in before:del registry[name]
  for name,value in before.items():registry[name]=value
  sys.modules=registry;sys.path=path;path[:]=original_path
 if primary is not None:
  if violation is not None:
   raise ValueError(violation)from primary
  raise primary
 need(violation is None,violation)
 return answer
