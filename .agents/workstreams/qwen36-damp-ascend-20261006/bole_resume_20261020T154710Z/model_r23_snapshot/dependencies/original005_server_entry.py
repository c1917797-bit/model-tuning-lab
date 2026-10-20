"""Same-eager candidate/dense exact server CLI. MAIN retains ownership/cleanup."""
import argparse,json,os,sys
from pathlib import Path
def original_command(port):
 return [sys.executable,'-m','vllm.entrypoints.openai.api_server','--model','/models/Qwen3.6-27B','--served-model-name','qwen36-mxr-eager','--host','127.0.0.1','--port',str(port),'--data-parallel-size','1','--tensor-parallel-size','4','--max-model-len','40960','--max-num-batched-tokens','40960','--max-num-seqs','16','--gpu-memory-utilization','0.9','--no-enable-prefix-caching','--enforce-eager','--trust-remote-code','--async-scheduling']
def command(port):
 from cap48_provider import explicit_lazy_argv
 return explicit_lazy_argv(original_command(port))
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--role',choices=('dense','candidate'));p.add_argument('--port',type=int,default=8230);p.add_argument('--qualification-ref');p.add_argument('--source-ref');p.add_argument('--receipt-root');a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 if a.role is None or a.port!=8230:raise ValueError('frozen role/port')
 if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='0,1,2,3':raise ValueError('MAIN actual physical4--7 tological0--3 required')
 if any(key.startswith(('VLLM_PROFILER','TORCH_PROFILER'))for key in os.environ):raise ValueError('profiling off before formal comparison')
 need_absent=('MXR_CAPTURE_ENABLE','MXR_CAPTURE_SOURCE_REF','MXR_CAPTURE_ROOT')
 if any(os.environ.get(k)for k in need_absent):raise ValueError('no diagnostic capture in production')
 env=dict(os.environ,VLLM_PLUGINS='ascend',MXR_OBSERVERLESS_ENABLE='0',PYTHONPATH=str(Path(__file__).resolve().parent)+os.pathsep+os.environ.get('PYTHONPATH',''))
 if a.role=='candidate':
  if not(a.qualification_ref and a.source_ref and a.receipt_root):raise ValueError('actual full-GDN/multistep/32768/Event source-bound qualification and owned receipts required')
  env.update(VLLM_PLUGINS='ascend,mxr_observerless',MXR_OBSERVERLESS_ENABLE='1',MXR_Y16_EXPERIMENT_ENABLE='1',MXR_OBSERVERLESS_QUALIFICATION_REF=a.qualification_ref,MXR_OBSERVERLESS_SOURCE_REF=a.source_ref,MXR_OBSERVERLESS_RECEIPT_ROOT=a.receipt_root)
 os.execve(sys.executable,command(a.port),env)
if __name__=='__main__':raise SystemExit(main())


