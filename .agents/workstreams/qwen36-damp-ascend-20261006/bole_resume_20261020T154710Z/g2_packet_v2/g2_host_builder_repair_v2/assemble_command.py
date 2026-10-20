"""Print actual host argv only; never run a builder/container/model."""
import argparse,hashlib,json
from pathlib import Path


def ref(path):
 p=Path(path)
 if not p.is_absolute()or not p.is_file()or any(v.is_symlink()for v in(p,*p.parents)):raise ValueError('ordinary exact CLI operand')
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 for k in('overlay','repair-builder','new-root','output-root'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--executor-sources-json',required=True);a=p.parse_args()
 mr=ref(a.overlay/'MANIFEST.json');original=ref(a.overlay/'prepare_g2.py');consumer=ref(a.overlay/'g2_consumer.py')
 if(mr['bytes'],mr['sha256'])!=(15972,'34119feffb6b8b910177731575a63181b02ef46b1670e2844f0813456a9c6f0d'):raise ValueError('exact frozen original G2 manifest')
 parent=json.loads(Path(mr['path']).read_bytes())['parent_qualification']
 argv=['/usr/bin/python3','-I','-B',ref(a.repair_builder)['path'],'--execute',
  '--parent-source-ref',json.dumps(parent['source']),'--parent-owner-result-ref',json.dumps(parent['owner_result']),
  '--parent-qualification-ref',json.dumps(parent['qualification']),'--consumer-source-ref',json.dumps(consumer),
  '--executor-sources-json',json.dumps(json.loads(a.executor_sources_json)),
  '--advisory-manifest-ref',json.dumps(mr),'--original-builder-ref',json.dumps(original),
  '--overlay',str(a.overlay),'--new-root',str(a.new_root),'--output-root',str(a.output_root)]
 print(json.dumps(dict(schema='bole.G2-portable-builder-actual-host-argv/v2',argv=argv,
   actual_host_execution=False,default_runtime_OFF=True)));return 0


if __name__=='__main__':raise SystemExit(main())
