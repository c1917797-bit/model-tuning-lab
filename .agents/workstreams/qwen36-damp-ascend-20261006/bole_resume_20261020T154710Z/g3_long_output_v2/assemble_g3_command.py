"""Print reviewed actual host preparation argv; create/bind/run nothing."""
import argparse
import json
from pathlib import Path


def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 for key in('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','parent-source-audit-ref',
            'consumer-source-ref','executor-sources-json','advisory-manifest-ref'):p.add_argument('--'+key,required=True)
 for key in('overlay','new-root','output-root'):p.add_argument('--'+key,required=True,type=Path)
 a=p.parse_args()
 if not all(x.is_absolute()for x in(a.overlay,a.new_root,a.output_root)):raise ValueError('absolute actual host paths only')
 argv=['/usr/bin/python3','-I','-B',str(a.overlay/'prepare_g3.py'),'--execute']
 for key in('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','parent-source-audit-ref',
            'consumer-source-ref','executor-sources-json','advisory-manifest-ref'):
  raw=getattr(a,key.replace('-','_'));json.loads(raw);argv+=['--'+key,raw]
 for key in('overlay','new-root','output-root'):argv+=['--'+key,str(getattr(a,key.replace('-','_')))]
 print(json.dumps(dict(argv=argv,execution_performed=False,actual_G2_qualification_required=True,NPU=False)))


if __name__=='__main__':main()
