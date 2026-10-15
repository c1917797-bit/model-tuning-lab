"""Both roles same sync/eager/common optimizations; MAIN owns service."""
import argparse,json,os,sys
from pathlib import Path
def command(port):
 from cap48_provider import explicit_lazy_argv
 return explicit_lazy_argv([sys.executable,'-m','vllm.entrypoints.openai.api_server','--model','/models/Qwen3.6-27B','--served-model-name','qwen36-dl-sync','--host','127.0.0.1','--port',str(port),'--data-parallel-size','1','--tensor-parallel-size','4','--max-model-len','40960','--max-num-batched-tokens','40960','--max-num-seqs','16','--gpu-memory-utilization','0.9','--no-enable-prefix-caching','--mamba-cache-mode','none','--enforce-eager','--trust-remote-code','--no-async-scheduling'])
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--role',choices=('dense','candidate'));p.add_argument('--port',type=int,default=8230)
 for k in('source-ref','qualification-ref','receipt-root'):p.add_argument('--'+k)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 if a.port!=8230 or a.role is None or os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='0,1,2,3':raise ValueError('actual frozen role/port/devices')
 if any(k.startswith(('VLLM_PROFILER','VLLM_TORCH_PROFILER','TORCH_PROFILER'))for k in os.environ):raise ValueError('profiling OFF')
 env=dict(os.environ,VLLM_PLUGINS='ascend',QWEN36_DELTALOG_SCREEN033_ENABLE='0',PYTHONPATH=str(Path(__file__).resolve().parent)+os.pathsep+os.environ.get('PYTHONPATH',''))
 for key in list(env):
  if key.startswith(('MXR_CAPTURE','QWEN36_DELTALOG_TENSOR026','QWEN36_DELTALOG_TRACE025'))or key in('QWEN36_DELTALOG_AUDIT','QWEN36_DELTALOG_SERVICE023_ENABLE','QWEN36_DELTALOG_ENABLE','QWEN36_DELTALOG_FRESH_ENABLE','QWEN36_DELTALOG_MIXED_ENABLE'):env.pop(key)
 if a.role=='candidate':
  if not all((a.source_ref,a.qualification_ref,a.receipt_root)):raise ValueError('actual source/numeric032/production qualification required')
  env.update(VLLM_PLUGINS='ascend,qwen36_deltalog_screen033',QWEN36_DELTALOG_SCREEN033_ENABLE='1',QWEN36_DELTALOG_SCREEN033_MODE='performance-screen-only',QWEN36_DELTALOG_SCREEN033_SOURCE_REF=a.source_ref,QWEN36_DELTALOG_SCREEN033_QUALIFICATION_REF=a.qualification_ref,QWEN36_DELTALOG_SCREEN033_RECEIPT_ROOT=a.receipt_root,QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE='1')
 os.execve(sys.executable,command(a.port),env)
if __name__=='__main__':raise SystemExit(main())
