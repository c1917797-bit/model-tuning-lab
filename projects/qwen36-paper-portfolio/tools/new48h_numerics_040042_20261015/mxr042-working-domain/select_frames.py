"""Freeze original report-order first failed and first passed real layer; CPU IO only."""
import argparse,hashlib,json
from pathlib import Path
REPORT_SHA='2c34b9b80b4653eb8344aefcf73f472fce8f6a30023b444dbc88f31698c96465'
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_absolute()and not p.is_symlink()and ref(p)==r,'exact ordinary Ref3');return p.read_bytes()
def select(report_ref):
 need(report_ref['sha256']==REPORT_SHA,'actual failed016 rank0 report pin');v=json.loads(checked(report_ref));need(v['schema']=='mxr.observerless-once-GDN-independent/v1'and len(v['rows'])==48 and v['gdn_frame_gate_pass']is False,'actual failed wholeGDN report, not missing-module result')
 failed=[x for x in v['rows']if not x['pass_gate']];passed=[x for x in v['rows']if x['pass_gate']];need(failed,'actual numerical failed row')
 need(not passed,'actual report all48 failed; do not invent passing control')
 partial=[x for x in v['rows']if x['output']['pass']and not x['state']['pass']];need(partial,'actual output-pass/state-fail control')
 chosen=[]
 for layer in (16,40):
  matches=[x for x in v['rows']if x['prefix']=='language_model.model.layers.%d.linear_attn'%layer];need(len(matches)==1,'fixed nontrivial heldout layer metadata');chosen.append(('nontrivial_heldout_layer%d'%layer,matches[0]))
 rows=[]
 for role,row in chosen:
  notes=[]
  for p in sorted(Path(v['worker_root']).glob('frame-*/FRAME.json')):
   n=json.loads(p.read_bytes())
   if n['prefix']==row['prefix']and n['raw']==row['raw']:notes.append((ref(p),n))
  need(len(notes)==1,'exact unique original FRAME/source/raw association');nr,n=notes[0];checked(row['raw'])
  need(n['source']==v['capture_source']and n['pid']==v['pid']and n['candidate_delta']==1,'actual candidate producer chain')
  rows.append(dict(role=role,prefix=row['prefix'],frame=nr,raw=row['raw'],original_metrics=row))
 witness=dict(rows[0],role='initial_state_rounding_witness',transform='zero_q_k_v_g_beta_initial_FP32_1.003');rows.append(witness)
 return dict(schema='mxr.saved-frame-fixed-selection/v042',original_report=report_ref,capture_source=v['capture_source'],run_id=v['run_id'],rows=rows,has_passing_control=False,selection='layers16/40 not used for027/041 calibration, not globally unseen; third row transformed initial-state witness is calibration only',repeats=3,NPU=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--report-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(a.report_ref and a.output and not a.output.exists(),'explicit new frozen selection');v=select(json.loads(a.report_ref))
 with a.output.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 print(json.dumps(ref(a.output)));return 0
if __name__=='__main__':raise SystemExit(main())
