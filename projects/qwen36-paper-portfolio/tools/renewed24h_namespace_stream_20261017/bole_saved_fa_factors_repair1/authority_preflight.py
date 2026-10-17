import argparse,ast,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C
def validate(value):
 C.need(value['schema']=='ascend.paper-portfolio.explicit-renewed24h/v1'and value['start_epoch']==1792226600 and value['cutoff_epoch']==1792313000,'exact renewed authority schema and unchanged epochs')
 return value
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--authority-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 r=json.loads(a.authority_ref);m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());C.need(r==m['authority_ref'],'exact actual authority Ref3');validate(C.obj(r));print('{"authority_checked":true,"resources_admitted":false}');return 0
if __name__=='__main__':raise SystemExit(main())
