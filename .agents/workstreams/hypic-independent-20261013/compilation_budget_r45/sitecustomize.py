"""Explicit R45 bootstrap; disabled observation imports no inference code."""
import os
_graph=os.environ.get("INDEPENDENT_GRAPH_HYPIC","0")
_compile=os.environ.get("INDEPENDENT_COMPILATION_BUDGET","0")
if _graph not in("0","1")or _compile not in("0","1")or(_compile=="1"and _graph!="1"):
 raise SystemExit("R45_INVALID_EXPLICIT_ACTIVATION")
if _graph=="1":
 try:
  if _compile=="1":
   from graph_candidate import worker_loader as _loader
   if not callable(getattr(_loader,"_compilation_budget_enabled",None)):
    raise ValueError("R45 worker-loader integration is not source-bound")
  from component_budget_r38.patch import enable
  _remove_compilation_bootstrap=enable()
 except BaseException as error:
  import sys
  print("R45_BOOTSTRAP_FAILED: "+type(error).__name__+": "+str(error),file=sys.stderr,flush=True)
  raise SystemExit(171)from error
