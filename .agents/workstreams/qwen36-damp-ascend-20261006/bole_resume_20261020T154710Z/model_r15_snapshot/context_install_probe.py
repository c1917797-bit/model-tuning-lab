"""Actual complete install executes to native group boundary; no fake device."""
import contextlib,json,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C,model_smoke as M,context_adapter as A,worker_bootstrap as W
class NativeBoundary(Exception):pass
def boundary():raise NativeBoundary()
def main():
 m=dict(runtime_sources=dict(contextlib=C.ref(contextlib.__file__)),files={n:C.ref(P/n)for n in('context_identity.py','context_adapter.py','worker_bootstrap.py')})
 with tempfile.TemporaryDirectory()as td:
  sr=C.write(Path(td)/'SOURCE.json',m)
  try:M.install(None,None,None,C,source_ref=sr,component_refs=None,get_forward_context=None,get_attention_context=None,enter_context=A.enter,native_get_tp_group=boundary,publish=W.publish)
  except NativeBoundary:pass
  else:raise AssertionError('actual native boundary not reached')
 assert not any(n=='vllm_ascend'or n.startswith('vllm_ascend.')or n=='torch_npu'or n.startswith('torch_npu.')for n in sys.modules),'no backend imported by cold source frontdoor'
 print(json.dumps(dict(actual_install_source_frontdoor_pass=True,original_enter_body_preserved=True,NPU=False,backend_imported=False)))
if __name__=='__main__':main()
