"""Readonly exact-file closure for MAIN's existing owned singleton controller."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
def checked(r):
 b=Path(r['path']).read_bytes()
 if(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('exact whole Ref3')
 return b
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--selection-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr,selr=map(json.loads,(a.source_ref,a.selection_ref));m=json.loads(checked(sr));selection=json.loads(checked(selr));capture=json.loads(checked(selection['capture_source']));r=capture['files']['prerequisite.py'];s=importlib.util.spec_from_file_location('_saved018_closure_prerequisite',r['path']);R=importlib.util.module_from_spec(s);exec(compile(checked(r),r['path'],'exec'),R.__dict__);passed=R.gate(m['prerequisite_ref'])
 reuse=json.loads(checked(m['reused_source']));rows=[sr,selr,selection['original_report'],selection['capture_source'],m['authority_ref'],m['original_metrics'],m['prerequisite_ref'],m['reused_source'],*m['files'].values(),*m['native_source_refs'],*m['reused'].values(),*reuse['files'].values(),*capture['files'].values(),*capture['dependencies'],*passed['readset']]
 for row in selection['rows']:rows.extend([row['frame'],row['raw']])
 unique={}
 for r in rows:
  checked(r)
  if r['path']in unique and unique[r['path']]!=r:raise ValueError('ambiguous closure')
  unique[r['path']]=r
 if any(n=='torch'or n.startswith(('torch.','torch_npu'))for n in sys.modules):raise ValueError('host closure must not import framework')
 print(json.dumps(dict(schema='mxr.saved-frame-readonly-closure/v042',source=sr,selection=selr,RO_refs=list(unique.values()),NPU=False,READY=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
