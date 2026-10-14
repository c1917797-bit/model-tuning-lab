"""Audit saved case artifacts only. Does not execute CPU/NPU mathematics."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def require(x,m):
 if not x:raise ValueError(m)
def main():
 if '--execute' not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--evidence-root',type=Path,required=True);a=p.parse_args()
 index=json.loads((P/'EVIDENCE.json').read_bytes());values={}
 for r in index['files']:
  f=a.evidence_root/r['name'];require(f.is_file()and not f.is_symlink(),'ordinary exact evidence file');b=f.read_bytes()
  require(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'immutable artifact '+r['name']);values[r['name']]=json.loads(b)
 g=values['GE005_ACTUAL_ATTRIBUTION.json'];rank0=next(x for x in g['rows']if x['rank']==0)
 require(all(rank0['metrics'][k]['frob_relative']>.002 and rank0['metrics'][k]['pass']is False for k in('NPU','CPU_FP32','CPU_FP64')),'domain failure replicated across backends')
 c=values['GE007_ACTUAL_CONSUMPTION.json'];require(c['complete']and len(c['rows'])==16 and set(c['passing_configs'])=={'N3S11','N3S15'}and not c['model_ready'],'CPU qualification is not model success')
 o=values['GE008_ACTUAL_OWNER_RESULT.json'];n=values['GE008_ACTUAL_NUMERIC_RESULT.json']
 require(o['matrix_gate_pass']is False and o['independent_consumer']is None and o['secondary'],'retain owner failure')
 require(n['matrix_gate_pass']is True and len(n['actual_matmul_dispatch'])==324 and n['model_ready']is False,'saved component pass does not override owner/model verdict')
 require(all(len(x['repeats'])==3 and all(y['metric']['pass']and y['FP32_BF16_deterministic']for y in x['repeats'])for x in n['rows']),'actual complete rank-repeat evidence')
 d=values['DL_CPU54_ACTUAL_DECOMPOSITION.json'];t=d['CPU_full54_trajectory']
 require(t['steps']==54 and all(t['input_last_bitwise'].values())and t['actual_native_CPU64_relative_l2']<2e-7 and t['actual_candidate_CPU64_relative_l2']>.29,'independent recorded native/candidate separation')
 require(all(h['candidate_CPU64_rel']>.4 for h in t['perhead'][:3])and all(h['candidate_CPU64_rel']<2e-7 for h in t['perhead'][3:]),'shared-head localization')
 require(d['causal_attribution_final']is False,'localization is not completed kernel-causality proof')
 b=values['DL_KDMA006_ACTUAL_BUILD_RESULT.json'];require(b['primary']is None and b['Devices']==[]and b['numeric_qualified']is False and b['original_a369_source_identity_verified']is False,'compiled library is not numerical repair')
 require(len(b['commands'])==5 and [x['arm']for x in b['artifacts']]==['baseline','kdma']and all(x['exit_code']==0 and x['error']is None for x in b['commands']),'complete build, not partial005')
 require(index['MXR056']['owned_pid_proven']is False,'pending mapping association must stay unproved')
 print(json.dumps(dict(saved_artifact_audit=True,NPU_executed=False,numerical_reexecuted=False,model_qualified=False,paper_failed=False)));return 0
if __name__=='__main__':raise SystemExit(main())
