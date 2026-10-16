"""Source-only explicit CPU profile proposal; not installed by any owner."""
import ast,hashlib
SHA='1df9ce6cac75b68e0f8781c40a2445887a00494941c9cde9488abafe735ab07c'
def transform(raw):
 if len(raw)!=40280 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('exact original v7 pipeline')
 text=raw.decode('utf8');tree=ast.parse(text);lane=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Lane');call=next(n for n in lane.body if isinstance(n,ast.FunctionDef)and n.name=='call')
 lines=text.splitlines(keepends=True);method=''.join(lines[call.lineno-1:call.end_lineno])
 if method.count('-180')!=1:raise ValueError('one original work-reserve literal')
 altered=method.replace('-180','-90')
 result=''.join(lines[:call.lineno-1])+altered+''.join(lines[call.end_lineno:])
 if inverse(result)!=raw:raise ValueError('exact wholebody clock inverse')
 return result
def inverse(text):
 tree=ast.parse(text);lane=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Lane');call=next(n for n in lane.body if isinstance(n,ast.FunctionDef)and n.name=='call')
 lines=text.splitlines(keepends=True);method=''.join(lines[call.lineno-1:call.end_lineno])
 if method.count('-90')!=1:raise ValueError('one declared CPU cleanup reserve')
 return(''.join(lines[:call.lineno-1])+method.replace('-90','-180')+''.join(lines[call.end_lineno:])).encode('utf8')
