import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr=json.loads(a.template_ref);m=A.obj(tr);A.need(m['prepared_only']is True and m['root']==str(P),'prepared source-only audit')
 for n,r in m['files'].items():A.need(A.ref(P/n)==r,'own source namespace/bytes')
 for r in m['dependencies']:A.checked(r)
 A.checked(m['authority_ref']);A.need(m['resource']['RAM_initial_GiB']==56.5 and m['resource']['opt_initial_GiB']==40.5,'original075 cap48 budgets')
 print(json.dumps(dict(schema='deltalog.pair-source-audit/v122',source=tr,files=len(m['files']),NPU=False,resources_admitted=False,actual_qualification=False)));return 0
if __name__=='__main__':raise SystemExit(main())
