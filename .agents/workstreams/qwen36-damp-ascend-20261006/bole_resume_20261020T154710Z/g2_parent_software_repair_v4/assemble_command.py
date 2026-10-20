"""Print exact NEW-v4 preparation argv only; execute/create nothing."""
import argparse
import hashlib
import json
from pathlib import Path
FAILED_SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v3/SOURCE_BOUND.json',bytes=220181,sha256='91002bf0dbda04826db5a1c4d3264b36da0bfaf4f4464feb50ce8ee05435c874')
FAILED_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v3-CPU/RESULT.json',bytes=240698,sha256='2835f03e31170405c093f900b0d02d3518bffba042e50f2442cb64bda6c6fe96')

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--repair-overlay',type=Path,required=True);p.add_argument('--repair-manifest-ref',required=True)
 p.add_argument('--new-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);a=p.parse_args()
 for path in(a.repair_overlay,a.new_root,a.output_root):
  if not path.is_absolute():raise ValueError('absolute actual host operands')
 mr=json.loads(a.repair_manifest_ref)
 if Path(mr['path'])!=a.repair_overlay/'MANIFEST.json':raise ValueError('explicit reviewed actual host manifest path')
 argv=['/usr/bin/python3','-I','-B',str(a.repair_overlay/'prepare_g2_parent_v4.py'),'--execute',
  '--failed-source-ref',json.dumps(FAILED_SOURCE),'--failed-owner-result-ref',json.dumps(FAILED_OWNER),
  '--repair-manifest-ref',a.repair_manifest_ref,'--repair-overlay',str(a.repair_overlay),
  '--new-root',str(a.new_root),'--output-root',str(a.output_root)]
 print(json.dumps(dict(schema='bole.G2-parent-software-repair-host-argv/v4',argv=argv,
  actual_execution=False,original214_plus28_fresh_rerun_required=True,prospective_cases=258,NPU=False)))

if __name__=='__main__':main()
