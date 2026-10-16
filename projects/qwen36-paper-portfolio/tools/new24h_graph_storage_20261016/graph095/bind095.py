"""Bind only the already actual051 build; never invent a future result."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common095 as C
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 tr=json.loads(a.template_ref);m=C.obj(tr);C.need(m['root']==str(P)and m['prepared_only']is True,'actual reviewed095 template');[C.checked(r)for r in m['files'].values()];C.window(m)
 v=C.obj(m['build_ref']);C.need(v['source_manifest']==m['kernel_source_ref']and v['primary']is None and v['Devices']==[]and v['NPU']is False,'actual successful051build');C.checked(m['kernel_source_ref'])
 C.need([x['arm']for x in v['artifacts']]==['split_scale_v051','split_scale_sidecar_v051']and all(c['exit_code']==0 and c['error']is None for c in v['commands']),'actual completed both arms')
 for key,row,expect in zip(('production_library','debug_library'),v['artifacts'],m['expected_artifacts']):
  r=row['library'];C.need((r['bytes'],r['sha256'])==(expect['bytes'],expect['sha256']),'exact reviewed artifact');C.checked(r);m[key]=r
 m['prepared_only']=False;m['prepared_template']=tr;C.write(P/'SOURCE_MANIFEST.json',m);print(json.dumps(C.ref(P/'SOURCE_MANIFEST.json')));return 0
if __name__=='__main__':raise SystemExit(main())
