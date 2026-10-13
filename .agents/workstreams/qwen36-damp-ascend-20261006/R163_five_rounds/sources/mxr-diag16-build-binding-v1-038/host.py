"""Build stage cold entry; no new controller. MAIN admission required."""
import hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
DONOR={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/R118/mxr-y16-device-free-build-owner-v1-030/host.py','bytes':9447,'sha256':'9afe435ff2c1c18c22b33b56398777f3ab1d37a3e3223bfd8c944c99232cd136'}
def prepare(sr,started):return runtime().prepare(sr,started)
def runtime():
 path=P/'binding.py';raw=path.read_bytes()
 if len(raw)!=1713 or hashlib.sha256(raw).hexdigest()!='f76dc98098d138f7b30e8f8d18745a60b1cbba9a7ef1d7e020635be380892b02':raise ValueError('whole source-bound binding038')
 s=importlib.util.spec_from_file_location('_mxr035_explicit_binding',path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v.view('build',P,DONOR)
def main():
 if not any(flag in sys.argv for flag in('--execute','--source-audit-only')):print(json.dumps(dict(enabled=False,Devices=[],NPU=False)));return 0
 return runtime().main()
if __name__=='__main__':raise SystemExit(main())
