"""All four saved ranks serially, using original exact failed-owner plan.

This child completes input attribution even when old numeric gates are false.
It cannot promote the old owner, paper, model, lifecycle or performance scope.
"""
import argparse,gc,json,os,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import recovery_io as C,plan as R,diagnose as D

def run(t,source_ref,plan_ref,out):
 own=C.obj(source_ref);proof=R.consume(C,plan_ref)
 C.need(own['recovery_plan_ref']==plan_ref and own['prepared_only']is False and
        own['schema']=='bole.r17-fa-input-diagnostic-source/v1','actual bound own source and original failed-owner proof')
 for r in own['files'].values():C.checked(r)
 reports=[]
 for rank,pair in enumerate(proof['ranks']):
  receipt=C.obj(pair['receipt'])
  C.need(receipt['source']==R.SOURCE and receipt['primary']is None and receipt['rank']==rank and receipt['raw']==pair['raw'],
         'original complete same-source producer/rank/raw join')
  exported=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False)
  C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and exported['logical_tensor_bytes']<=2**30,'original complete bounded primitive export')
  raw=exported['payload'];C.need(raw['source']==R.SOURCE and raw['rank']==rank,'exact original actual captured rank/source')
  report=D.diagnose(t,raw);report.update(source=source_ref,original_source=R.SOURCE,original_raw=pair['raw'],producer=pair['receipt'],rank=rank)
  data=(json.dumps(report,sort_keys=True,allow_nan=False)+'\n').encode();C.need(len(data)<=16*2**20,'scalar attribution cap16MiB/rank')
  with(out/('RANK-%d.json'%rank)).open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  reports.append(C.ref(out/('RANK-%d.json'%rank)))
  del raw,exported,report;gc.collect()
 result=dict(schema='bole.r17-independent-FA-input-attribution/v1',source=source_ref,plan=plan_ref,
  original_source=R.SOURCE,failed_owner=R.OWNER,rank_reports=reports,diagnostic_complete=True,
  ranks_completed=4,original_numeric_failures_unchanged=True,qualified=False,original_owner_pass=False,
  native_snapshot_status=proof['native_snapshot_status'],live_frontend_binding_status='missing-not-reconstructed',
  lifecycle_qualified=False,whole_numerical_qualified=False,model_ready=False,scheduler_committed=False,performance_ready=False,
  diagnostic_does_not_require_original_FA_gate_pass=True)
 return C.write(out/'ATTRIBUTION.json',result)

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 C.need(a.source_ref and a.plan_ref and a.output is not None,'complete typed actual source/plan/output')
 sr=json.loads(a.source_ref);own=C.obj(sr);pr=json.loads(a.plan_ref)
 C.need(a.output==Path(own['output_root'])/'consumer'and a.output.is_dir()and all(not x.is_symlink()for x in(a.output,*a.output.parents)),'sole exact admitted consumer output, no alias')
 C.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not os.environ.get('ASCEND_RT_VISIBLE_DEVICES')and not os.environ.get('ASCEND_VISIBLE_DEVICES')and not list(Path('/dev').glob('davinci*')),'actual Devices[] CPU no visibility or NPU FD')
 try:
  import torch as t
  t.set_num_threads(1)
  C.need(not hasattr(t,'npu')or not t.npu.is_initialized(),'no NPU initialization')
  print(json.dumps(run(t,sr,pr,a.output)));return 0
 except BaseException as e:
  C.write(a.output/'FAILURE.json',dict(source=sr,primary=repr(e),traceback=traceback.format_exc(),qualified=False,NPU=False));raise
if __name__=='__main__':raise SystemExit(main())
