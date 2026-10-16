"""Dense native only; common HF32OFF, no algorithm/capture plugin."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
def environment(base,sr,receipt):
 e=dict(base);C.need(not any(k.startswith(('VLLM_PROFILER','TORCH_PROFILER'))for k in e),'profiling absent')
 for k in list(e):
  if k.startswith(('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_')):e.pop(k)
 e.update(VLLM_PLUGINS='ascend,dense_opportunity090',DENSE_OPPORTUNITY090_ENABLE='1',DENSE_OPPORTUNITY090_SOURCE_REF=json.dumps(sr),DENSE_OPPORTUNITY090_RECEIPT_ROOT=str(receipt),PYTHONPATH=str(P)+os.pathsep+e.get('PYTHONPATH',''))
 return e
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--receipt-root',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);C.source(sr);C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3'and a.receipt_root.is_dir(),'actual ownedTP4/receiptleaf')
 args=C.server_command();C.write(a.receipt_root/'SERVER_COMMAND.json',dict(source=sr,argv=args,native_only=True,profiling=False));os.execve(sys.executable,args,environment(os.environ,sr,a.receipt_root))
if __name__=='__main__':raise SystemExit(main())
