"""One exact common native005 CLI; only candidate production106 is added."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
def command():
 p=P/'dependencies/original005_server_entry.py';A.need(A.ref(p)['sha256']=='ac0931cb9f17a93ae923c7cbfd1a92e757d376a417c1ed910b134f984216d080','original005 builder')
 s=importlib.util.spec_from_file_location('_dl122_native005',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);args=v.original_command(8230)
 args.remove('--async-scheduling');args+=['--no-async-scheduling','--mamba-cache-mode','none','--load-format','safetensors','--safetensors-load-strategy','lazy','--model-loader-extra-config','{"enable_multithread_load":false}']
 for k,n in(('--max-model-len','4096'),('--max-num-batched-tokens','2048'),('--max-num-seqs','1')):args[args.index(k)+1]=n
 return args
def environment(sr,receipt,arm,base):
 m,_=A.qualify(sr);e=dict(base);A.need(arm in('dense','candidate'),'actual arm')
 A.need(not any(k.startswith(('VLLM_PROFILER','VLLM_TORCH_PROFILER','TORCH_PROFILER'))for k in e),'profiling OFF')
 A.need(all(e.get(k)in(None,'','0')for k in('QWEN36_DELTALOG_TENSOR026_ENABLE','QWEN36_DELTALOG_TRACE025_ENABLE','MXR_CAPTURE_ENABLE','MXR_ONCE_CORRECTNESS_ENABLE')),'no diagnostic observer')
 with A.context(m)as(v,pm):
  selected=v['qualification106'].environment(m['production_source_ref'],m['production_qualification_ref'],receipt,arm=='candidate')
  e.update(selected);plugins=['ascend','dl_pair_policy122']
  # Sole common entry explicitly boots CANN in EACH interpreter and then
  # invokes exact106 register only for candidate; no unordered plugin install.
  # Same common policy first in both arms; source106 unchanged and separately pinned.
  e.update(VLLM_PLUGINS=','.join(plugins),DL122_COMMON_ENABLE='1',DL122_PAIR_SOURCE_REF=json.dumps(sr),DL122_RECEIPTS=str(receipt),DL122_ARM=arm,PYTHONPATH=str(P)+':'+pm['root']+':'+e.get('PYTHONPATH',''))
 return e
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--role',choices=('dense','candidate'));p.add_argument('--source-ref');p.add_argument('--receipt-root');p.add_argument('--port',type=int,default=8230);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 A.need(a.port==8230 and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3','owned TP4 physical4-7 only')
 sr=json.loads(a.source_ref);m=A.source(sr,pair=True);cann=A.bootstrap_cann(m)
 e=environment(sr,Path(a.receipt_root),a.role,dict(os.environ));e['PYTHONPATH']=cann+':'+e['PYTHONPATH'];os.execve(sys.executable,command(),e)
if __name__=='__main__':raise SystemExit(main())
