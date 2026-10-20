"""Reopen immutable model evidence; a diagnostic pass is not final success."""
import argparse,hashlib,json
from pathlib import Path

def ref(path):
 path=Path(path);b=path.read_bytes()
 return dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(reference):
 assert ref(reference['path'])==reference,('Ref3 mismatch',reference['path'])
 return json.loads(Path(reference['path']).read_bytes())
def need(value,label):
 if not value:raise ValueError(label)
def audit(root):
 root=Path(root);result_path=root/'RESULT.json'
 if not result_path.exists():
  return dict(state='running',output=str(root),final_success=False)
 result=json.loads(result_path.read_bytes());sr=result['source'];source=read(sr)
 facts=dict(result=ref(result_path),source=sr,primary=result['primary'],
  secondary=result['secondary'],source_unchanged=result['source_before']==result['source_after'],
  elapsed=result['elapsed'],cleanup_seconds=result['cleanup_spent'])
 if result['primary']is not None or result['secondary']:
  return dict(state='failed',facts=facts,final_success=False)
 need(facts['source_unchanged'],'source bytes before/after mismatch')
 need(result['scheduler_committed']is False and result['model_ready']is False,'retain diagnostic scope')
 attribution_path=root/'cpu-consumer/ATTRIBUTION.json'
 attribution=json.loads(attribution_path.read_bytes())
 need(attribution['source']==sr and attribution['diagnostic_complete']is True,'same-source complete independent diagnostic')
 need(attribution['component_checks_pass']is True and attribution['actual_all4_retirement']is True and
      attribution['actual64_layers_per_rank']is True and
      attribution['independent_actual_MTP_TP4_vocabulary_join']is True,'all original independent component/identity gates')
 need(attribution['scheduler_committed']is False and attribution['model_ready']is False and
      attribution['whole_numerical_qualified']is False and attribution['whole_numerical_threshold']is None,
      'diagnostic must not be relabelled whole-model/production qualification')
 need(len(attribution['ranks'])==4,'four independently consumed rank reports')
 reports=[];all_greedy=True;fa_passed=0;gdn_passed=0
 for rank,rr in enumerate(attribution['ranks']):
  value=read(rr);need(value['source']==sr,'rank report same source');report=value['report']
  need(report['component_checks_pass']is True and report['accepted_path_writeback_restore_pass']is True,'rank component/writeback gates')
  need(len(report['rows'])==64,'all64 layers per rank')
  all_greedy=all_greedy and report['greedy_identity_pass']
  for row in report['rows']:
   if row['kind']=='fa':
    need(all(v['pointwise_pass']for v in row['attention'].values()),'original FA FP32/FP64 bounds')
    fa_passed+=1
   else:
    need(row['kind']=='gdn'and row['FP32_output']['passed']and row['U']['passed']and
         row['P']['passed']and all(x['passed']for x in row['local_states'])and
         row['conv']['output_bound_pass']and row['conv']['state_bitwise'],'original GDN/conv bounds')
    gdn_passed+=1
  reports.append(dict(rank=rank,report=rr,raw=value['raw'],
   greedy_identity_pass=report['greedy_identity_pass'],whole_discrepancies=report['whole_discrepancies']))
 need(fa_passed==64 and gdn_passed==192,'all rank/layer numerical frames')
 for arm in ('dense','cpu-preflight','cpu-consumer'):
  cleanup=json.loads((root/arm/'cleanup.json').read_bytes())
  need(cleanup['stopped']and cleanup['retained']and not cleanup['errors'],'all owned containers released and retained')
 return dict(state='diagnostic-complete',facts=facts,attribution=ref(attribution_path),
  fa_frames_passed=fa_passed,gdn_frames_passed=gdn_passed,
  original_component_limits_unchanged=True,greedy_smoke_identity=all_greedy,
  complete_selected_cache_writeback_restore=True,actual_four_rank_request_retirement=True,
  reports=reports,whole_model_tensor_qualification=False,
  real_generation_scheduler_commit=False,formal_tasks=False,formal_paired_performance=False,
  final_success=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--save')
 a=p.parse_args();value=audit(a.output)
 if a.save:
  dest=Path(a.save)
  with dest.open('x')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(value,indent=2,allow_nan=False))
if __name__=='__main__':main()

