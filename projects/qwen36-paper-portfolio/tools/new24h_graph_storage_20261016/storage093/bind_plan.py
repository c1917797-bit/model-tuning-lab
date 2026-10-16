"""No remote calls: bind three actual not_found observation Refs, never exit data."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import sealed_storage093 as S
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--unavailable-ref',action='append');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=S.read(sr);S.need(m['schema']=='deltalog.closed-storage-source/v093'and m['files']['bind_plan.py']==S.ref(__file__),'source-bound plan binder');rr=[json.loads(x)for x in(a.unavailable_ref or[])];S.need(rr==[m['files']['evidence/operation-notfound-observed.json']],'exact actual three-operation not_found snapshot Ref');S.unavailable(rr[0])
 out=Path(a.output);S.need(out.is_absolute()and not out.exists()and out.parent.is_dir(),'unique absolute owned output');v=dict(schema='deltalog.storage-terminal-plan/v093',source=sr,operation_terminal_refs=[None]*3,operation_unavailable_ref=rr[0],historical_operation_receipt_unavailable=True,historical_operation_exit_claimed=False)
 with out.open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 print(json.dumps(S.ref(out)));return 0
if __name__=='__main__':raise SystemExit(main())
