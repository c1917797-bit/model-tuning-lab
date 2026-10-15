"""Compare preserved actual017 sources and exact B010 ABI call; no device."""
import argparse,ast,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent/'qwen36_deltalog_service'
KEEP=('binding.py','contract.py','layout_controls.py','runtime_helpers.py','transform.py')
def main():
 p=argparse.ArgumentParser();p.add_argument('--old-root',required=True,type=Path);a=p.parse_args()
 for n in KEEP:assert(P/n).read_bytes()==(a.old_root/n).read_bytes(),'unchanged original017 '+n
 def call(path):
  tree=ast.parse(path.read_bytes());xs=[x for x in ast.walk(tree)if isinstance(x,ast.Call)and ast.unparse(x.func)=='_OP'];assert len(xs)==1;return ast.dump(xs[0],include_attributes=False)
 assert call(P/'runtime.py')==call(a.old_root/'runtime.py'),'unchanged B010 argument/ordering/production math ABI'
 assert hashlib.sha256((P/'primitives.py').read_bytes()).hexdigest()=='1b9a2e53ce137f319ca5939be6e21fa293735edd363cdc37f7b438626e985470','exact audited021 dead-payload fix'
 print({'preserved017_sources':KEEP,'B010_actual_call_unchanged':True,'exact021':True,'NPU':False})
if __name__=='__main__':main()
