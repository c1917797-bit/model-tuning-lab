"""Only read completed exact short-arm evidence. Never launch an owner."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cleanup_summary import read_cleanup_summary
ON={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2/SOURCE_BOUND.json","bytes":1503149,"sha256":"a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f"}
OFF={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/bound-short-OFF-v2/SOURCE_BOUND.json","bytes":1503858,"sha256":"ee9c2633dd33ccf449dd881d65e6100d478bc4439b4e966bf19961b69e2c2b70"}
sys.path.insert(0,str(Path(ON['path']).parent))
import compare_state_digest as R
def host(sr):
 m=R.obj(sr);out=Path(m['output_root']);rr=R.ref(out/'RESULT.json');v=R.obj(rr,8*2**20)
 R.need(v['schema']=='bole.actual-three-node-model-owned/v131' and v['source']==sr and v['cpu_only'] is False and v['primary'] is None and v['secondary']==[] and v['source_before']==v['source_after'],'completed exact host; no partial stream promotion')
 R.need(v['phase_seconds']==3600 and v['cleanup_seconds']==180 and 0<=v['cleanup_spent']<=180 and 0<v['elapsed']<=3600,'original bounded whole phase and cleanup')
 summary=v['summary'];refs=[rr]
 for k in ('CPU_release','model_release'):
  expected=out/('cpu-preflight/cleanup.json' if k=='CPU_release' else 'dense/cleanup.json')
  ref,rel=read_cleanup_summary(summary[k],expected)
  R.need(rel['stopped'] is True and rel['retained'] is True and not rel['errors'],'real stopped retained owner release')
  refs.append(ref)
 R.need(len(summary['worker_snapshots'])==4 and all(x['source_ref']==sr and x['native_core'] is True and x['native_inverse'] is True and x['allow_hf32'] is False for x in summary['worker_snapshots']),'native barrier and real restored workers')
 R.need(summary['streaming_validation']['arm_state_receipts_verified'] is True,'host actual arm consumer completed')
 return m,out,refs
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 R.need(a.output.is_absolute() and a.output.parent.is_dir() and not a.output.exists(),'fresh exclusive final output')
 am,ap,ar=host(ON);bm,bp,br=host(OFF)
 R.need(R.ref(R.__file__)==am['files']['compare_state_digest.py'],'exact independent reader')
 result=R.compare(ON,OFF,ap/'dense/receipts',bp/'dense/receipts',
  R.ref(ap/'dense/performance-client/HTTP_RESULT.json'),R.ref(bp/'dense/performance-client/HTTP_RESULT.json'))
 result.update(actual_hosts_complete=True,actual_owner_cleanup_complete=True,host_readset=ar+br,
  comparison_entry=R.ref(__file__),original_partial_G3_evidence_not_promoted=True)
 with a.output.open('xb')as f:f.write((json.dumps(result,sort_keys=True)+'\n').encode())
 print(json.dumps(dict(result=R.ref(a.output),state_digest_equal=True,formal_performance=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())


