"""Print exact NEW-v5 preparation argv only; execute/create nothing."""
import argparse
import hashlib
import json
from pathlib import Path
FAILED_SOURCE={'path': '/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v4/SOURCE_BOUND.json', 'bytes': 328177, 'sha256': 'c20ff6d58e8ac9a44f20060f96b20c71c56ebaa4425eb33590f77e35644b0877'}
FAILED_OWNER={'path': '/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v4-CPU/RESULT.json', 'bytes': 335666, 'sha256': '23360c6e8b079e3d2ab98bfcb399d8ce789928fdea0c27b0db5f5da14ac09e44'}

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--repair-overlay',type=Path,required=True);p.add_argument('--repair-manifest-ref',required=True)
 p.add_argument('--new-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);a=p.parse_args()
 for path in(a.repair_overlay,a.new_root,a.output_root):
  if not path.is_absolute():raise ValueError('absolute actual host operands')
 mr=json.loads(a.repair_manifest_ref)
 if Path(mr['path'])!=a.repair_overlay/'MANIFEST.json':raise ValueError('explicit reviewed actual host manifest path')
 argv=['/usr/bin/python3','-I','-B',str(a.repair_overlay/'prepare_g2_control_v5.py'),'--execute',
  '--failed-source-ref',json.dumps(FAILED_SOURCE),'--failed-owner-result-ref',json.dumps(FAILED_OWNER),
  '--repair-manifest-ref',a.repair_manifest_ref,'--repair-overlay',str(a.repair_overlay),
  '--new-root',str(a.new_root),'--output-root',str(a.output_root)]
 print(json.dumps(dict(schema='bole.G2-parent-control-ref-repair-host-argv/v5',argv=argv,
  actual_execution=False,original214_plus42_fresh_rerun_required=True,prospective_cases=258,NPU=False)))

if __name__=='__main__':main()
