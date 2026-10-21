"""Original API runpy entry with actual assignment observer installed first."""
import argparse,json,os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
import g1_contract as G1


def environment(base,sr,receipt):
 e=dict(base);C.need(not any(k.startswith(('VLLM_PROFILER','TORCH_PROFILER'))for k in e),'no profiling')
 for k in list(e):
  if k.startswith(('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_')):e.pop(k)
 m=C.obj(sr)
 e.update(VLLM_PLUGINS='ascend,dense_opportunity090,bole_mtp_load_receipt111,bole_three_node131',
  BOLE111_MTP_LOAD_AUDIT_ENABLE='1',BOLE111_MTP_SOURCE_REF=json.dumps(m['installed_sources']['qwen_mtp']),
  BOLE111_MTP_LOAD_RECEIPT_ROOT=str(receipt),DENSE_OPPORTUNITY090_ENABLE='1',DENSE_OPPORTUNITY090_SOURCE_REF=json.dumps(sr),
  DENSE_OPPORTUNITY090_RECEIPT_ROOT=str(receipt),BOLE_THREE_NODE_MODEL_ENABLE='1',BOLE_MODEL_OBJECT_AUDIT_ENABLE='1',
  BOLE_MTP_TREE_CAPTURE_ENABLE='1',BOLE_PAGED_TREE_ENABLE='1',BOLE_MODEL_SOURCE_REF=json.dumps(sr),
  BOLE_MODEL_RAW_ROOT=str(receipt),PYTHONPATH=str(P)+os.pathsep+e.get('PYTHONPATH',''))
 if m.get('service_experiment')is not None:
  C.need(m['service_experiment']==G1.SCOPE,'exact bounded service scope')
  e.pop('BOLE_CONTINUOUS_SERVICE_ENABLE',None)
  e[G1.FLAG]='1'
  e['BOLE_G3_STREAM_CHANNEL_PATH']=m['stream_channel_contract_path']
 C.need(str(receipt)==m['model_receipt_root'],'actual guest physical output, not alias')
 return e


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--receipt-root',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr)
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3'and a.receipt_root.is_dir(),'genuine owned TP4/receipt leaf')
 args=C.server_command();C.write(a.receipt_root/'SERVER_COMMAND.json',dict(source=sr,argv=args,BOLE_diagnostic=True,native_MTP=True,num_speculative_tokens=8,actual_cache_memory_config=C.cache_memory_config(args,m),scheduler_committed=False,model_ready=False))
 os.environ.update(environment(os.environ,sr,a.receipt_root))
 import identity_journal
 identity_journal.install_frontend(sr)
 sys.argv=[args[2],*args[3:]]
 runpy.run_module(args[2],run_name='__main__')
 return 0


if __name__=='__main__':raise SystemExit(main())
