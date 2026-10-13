"""Serial physical5 stage over exact031; no cohort or graph permissions."""
import hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
DONOR={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/R118/mxr-y16-serial-single5-numeric-owner-v1-031/host.py','bytes':11330,'sha256':'63687e5c1ba0ed33b3adc14e16cc767817a3384edde392d8c319a60a990858f4'}
BINDING={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/R156/mxr-diag16-build-binding-v1-038/binding.py','bytes':1713,'sha256':'f76dc98098d138f7b30e8f8d18745a60b1cbba9a7ef1d7e020635be380892b02'}
def runtime():
 p=Path(BINDING['path']);raw=p.read_bytes()
 if len(raw)!=BINDING['bytes']or hashlib.sha256(raw).hexdigest()!=BINDING['sha256']:raise ValueError('whole new private binding source')
 s=importlib.util.spec_from_file_location('_mxr036_exact_binding035',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v.view('numeric',P,DONOR)
def main():
 if not any(flag in sys.argv for flag in('--execute','--source-audit-only')):print(json.dumps(dict(enabled=False,NPU=False)));return 0
 return runtime().main()
if __name__=='__main__':raise SystemExit(main())
