"""Readonly budget/shape planner, not an execution or qualification launcher."""
import argparse,importlib.util,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--plan',action='store_true');p.add_argument('--cu');a=p.parse_args()
 if not a.plan:print('{"enabled":false,"NPU":false}');return 0
 s=importlib.util.spec_from_file_location('_044plan',Path(__file__).with_name('block_refine.py'));M=importlib.util.module_from_spec(s);s.loader.exec_module(M);cu=json.loads(a.cu);print(json.dumps(dict(M.budget(cu,cu[-1]),NPU=False,qualified=False)));return 0
if __name__=='__main__':raise SystemExit(main())
