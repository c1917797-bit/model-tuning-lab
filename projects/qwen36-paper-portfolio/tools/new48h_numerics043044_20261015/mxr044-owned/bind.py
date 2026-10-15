"""One-shot bind exact original042 probe; no new numerical qualification."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr=json.loads(a.template_ref);m=C.obj(tr);C.need(m['root']==str(P)and m['prepared_only']is True and m['default_enabled']is False,'exact new prepared template')
 for r in m['files'].values():C.checked(r)
 component=C.obj(m['component044_source']);C.need(component['actual042_source']==m['owned042_source'],'same042 source bound by frozen044')
 owner=C.obj(component['actual042_owner']);probe=C.obj(owner['probe']);C.need(owner['source']==m['owned042_source']and owner['primary']is None and owner['secondary']==[]and owner['released']is True and owner['cpu_preflight']is False,'actual original042 terminal and exact release')
 C.need(probe['source']==m['owned042_source']and probe['primary']is None and probe['candidate_hits']==18 and len(probe['raws'])==9,'actual042 complete real inputs')
 for r in component['files'].values():C.checked(r)
 for r in probe['raws']:C.checked(r)
 m.update(prepared_only=False,prepared_template=tr,actual042_probe=owner['probe'],actual_owned044_CPU=None,actual_owned044_NPU=None,model_ready=False,performance_ready=False)
 print(json.dumps(dict(source=C.write(P/'SOURCE_MANIFEST.json',m),NPU=False,qualified=False)));return 0
if __name__=='__main__':raise SystemExit(main())
