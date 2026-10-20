"""Read-only source-owned prerequisite closure audit; no container/device action."""
import argparse,importlib.util,json
from pathlib import Path


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 path=Path(__file__).with_name('prepare_g2_host_v3.py')
 spec=importlib.util.spec_from_file_location('actual_prereq_builder',path);B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
 print(json.dumps(B.audit_prerequisite_closure(json.loads(a.source_ref))));return 0


if __name__=='__main__':raise SystemExit(main())
