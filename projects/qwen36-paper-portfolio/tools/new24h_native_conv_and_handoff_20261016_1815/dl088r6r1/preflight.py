"""No-device source/real-GDN AST inventory, never a numerical admission."""
import argparse,ast,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);p.add_argument('--gdn-ref',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 from qwen36_deltalog_fresh.provider import _obj,_ref
 from qwen36_deltalog_fresh import contract as C
 from qwen36_deltalog_fresh.transform import specialize_core
 sr=json.loads(a.source_ref);m=_obj(sr)
 for r in m['files'].values():
  if _ref(r['path'])!=r:raise RuntimeError('sourceclosure mismatch')
 gr=json.loads(a.gdn_ref)
 if _ref(gr['path'])!=gr or gr['sha256']!=C.GDN_SHA:raise RuntimeError('actualGDN sourcepin')
 text=specialize_core(Path(gr['path']).read_text());tree=ast.parse(text)
 native=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and ast.unparse(n.func)=='torch.ops._C_ascend.npu_recurrent_gated_delta_rule'];routes=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and ast.unparse(n.func)=='_deltalog_route']
 if len(native)!=1 or len(routes)!=2:raise RuntimeError('actualnon-spec consumer rewrite count')
 if 'torch'in sys.modules or 'torch_npu'in sys.modules:raise RuntimeError('no backend/device import allowed in sourceaudit')
 with Path(a.output).open('x')as f:json.dump(dict(schema='deltalog.fresh-provider-source-preflight/v1',source=sr,gdn=gr,non_spec_routes=2,spec_route_retained=1,namespace=C.NAMESPACE,library_sha=C.LIBRARY_SHA,NPU=False,numeric_qualified=False,model_ready=False),f,allow_nan=False)
 return 0
if __name__=='__main__':raise SystemExit(main())
