import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import recovery_io as C,plan as R
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');p.add_argument('--terminal-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 C.need(a.template_ref and a.terminal_ref,'explicit immutable template and actual failed terminal Ref3')
 tr=json.loads(a.template_ref);terminal=json.loads(a.terminal_ref)
 # Full actual failure/readset proof is checked before any new write.
 proof=R.bind(C,terminal);m=C.obj(tr)
 C.need(tr==C.ref(P/'SOURCE_TEMPLATE.json')and m['root']==str(P)and m['prepared_only']is True,'exact deployed immutable prepared recovery source')
 for r in m['files'].values():C.checked(r)
 authority=C.obj(m['authority_ref']);C.need(authority['start_epoch']==1792226600 and authority['cutoff_epoch']==1792313000,'exact current user authority')
 pr=C.write(P/'RECOVERY_PLAN.json',proof);m['recovery_plan_ref']=pr;m['prepared_template']=tr;m['prepared_only']=False
 sr=C.write(P/'SOURCE_BOUND.json',m);R.consume(C,pr);print(json.dumps(sr));return 0
if __name__=='__main__':raise SystemExit(main())
