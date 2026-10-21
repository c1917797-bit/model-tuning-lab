"""Print an exact source-preparation argv; never execute it."""
import argparse,json
from pathlib import Path
KEYS=('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','consumer-source-ref','executor-sources-json','advisory-manifest-ref','parent-source-audit-ref','cold-handoff-layer-ref')
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--assemble',action='store_true')
 for key in KEYS:p.add_argument('--'+key)
 for key in('overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
 a=p.parse_args()
 if not a.assemble:print('{"enabled":false,"execution_performed":false,"NPU":false}');return 0
 if not all(v is not None for k,v in vars(a).items()if k!='assemble'):raise ValueError('all explicit reviewed actual operands required')
 if not all(getattr(a,k).is_absolute()for k in('overlay','new_root','output_root')):raise ValueError('absolute source/packet/output paths')
 for key in KEYS:json.loads(getattr(a,key.replace('-','_')))
 argv=['/usr/bin/python3','-I','-B',str(a.overlay/'prepare_g3.py'),'--execute']
 for key in KEYS:argv.extend(('--'+key,getattr(a,key.replace('-','_'))))
 for key in('overlay','new-root','output-root'):argv.extend(('--'+key,str(getattr(a,key.replace('-','_')))))
 print(json.dumps(dict(argv=argv,execution_performed=False,actual_G2_qualification_required=True,exact_cold_layer_required=True,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
