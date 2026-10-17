import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owner as O
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr=json.loads(a.template_ref);m=O.obj(tr);O.need(m['schema']=='deltalog.measurement-source/v22'and m['prepared_only']is True and m['root']==str(P),'exact deployed reviewed source')
 for r in m['files'].values():O.checked(r)
 O.need(m['files']['owner.py']==O.ref(P/'owner.py'),'exact owner source');O.checked(m['authority_ref'])
 m['prepared_only']=False;m['prepared_template']=tr;out=P/'SOURCE_MANIFEST.json';O.write(out,m);print(json.dumps(O.ref(out)));return 0
if __name__=='__main__':raise SystemExit(main())
