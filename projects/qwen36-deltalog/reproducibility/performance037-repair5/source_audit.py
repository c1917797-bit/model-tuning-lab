"""Pure source closure and syntax gate, not CPU/NPU correctness."""
import argparse,ast,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from qwen36_deltalog_screen import admission as A
def audit(sr):
 m=A.source(sr)
 for name,r in m['files'].items():
  if name.endswith('.py'):compile(Path(r['path']).read_bytes(),r['path'],'exec')
 return m
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);a=p.parse_args();m=audit(json.loads(a.source_ref));print(json.dumps(dict(files=len(m['files']),software_only=True,NPU=False)))
if __name__=='__main__':main()
