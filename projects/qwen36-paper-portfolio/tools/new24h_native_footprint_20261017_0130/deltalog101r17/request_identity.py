"""Pinned actual660 completion/header/engine identity expressions, no API import."""
import ast,hashlib,types
from pathlib import Path
P=Path(__file__).resolve().parent
PINS={'completion_serving_v023.py':'c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7','engine_serving_v023.py':'38b242a091b2b4502a58b7d9b8a274ac17611b383fecc30e9b714f5da9c8dc75'}
def identities(header):
 if not isinstance(header,str)or not header:raise ValueError('explicit unique HTTP header')
 trees={}
 for n,h in PINS.items():
  b=(P/'dependencies'/n).read_bytes()
  if hashlib.sha256(b).hexdigest()!=h:raise ValueError('actual660 request identity source')
  trees[n]=ast.parse(b)
 base=next(x for x in ast.walk(trees['engine_serving_v023.py'])if isinstance(x,ast.FunctionDef)and x.name=='_base_request_id');base.decorator_list=[]
 module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),base],type_ignores=[]);ast.fix_missing_locations(module);ns={};exec(compile(module,'<actual660-base-request-id>','exec'),ns)
 create=next(x for x in ast.walk(trees['completion_serving_v023.py'])if isinstance(x,ast.AsyncFunctionDef)and x.name=='_create_completion')
 assigns=[next(x for x in ast.walk(create)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id==n for t in x.targets))for n in('request_id','request_id_item')]
 ctx=dict(self=types.SimpleNamespace(_base_request_id=ns['_base_request_id']),raw_request=types.SimpleNamespace(headers={'X-Request-Id':header}),request=types.SimpleNamespace(request_id='unused'),i=0)
 exec(compile(ast.Module(body=assigns,type_ignores=[]),'<actual660-completion-ID-expressions>','exec'),ctx)
 calls=[x for x in ast.walk(create)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='generate']
 if not any(len(x.args)>2 and isinstance(x.args[2],ast.Name)and x.args[2].id=='request_id_item'for x in calls):raise ValueError('actual engine generate ID seam')
 return dict(http_header=header,response_id=ctx['request_id'],passed_request_id=ctx['request_id_item'])
