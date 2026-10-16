"""MAIN-only read-only observation; creates only exact new evidence leaf."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C,closed_overlay088r6 as O
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 C.window(__import__('window056').AUTH);tr=json.loads(a.template_ref);C.need(C.ref(P/'SOURCE_TEMPLATE.json')==tr,'own exact template');m=C.obj(tr)
 for r in m['files'].values():C.checked(r)
 print(json.dumps(O.capture(C,m,tr,O.ROOT/'seal-evidence088R6-MAIN-001')));return 0
if __name__=='__main__':raise SystemExit(main())
