"""Parent-parser source bootstrap only; official plugin loader owns register()."""
import hashlib,importlib.util,sys,types
from pathlib import Path
def prepare(O,m,root):
 r=m['files']['bootstrap101r9.py'];fp=O.obj_file(r)
 s=importlib.util.spec_from_file_location('_r24_parser_source_bootstrap',fp);B=importlib.util.module_from_spec(s);s.loader.exec_module(B)
 roots=B.install(m,root)
 ps=m['firstdecode_contract']['payload_source'];p=O.obj(ps);expected=O.obj_file(p['files']['firstdecode_plugin.py'])
 body=expected.read_bytes();r=p['files']['firstdecode_plugin.py'];O.need((len(body),hashlib.sha256(body).hexdigest())==(r['bytes'],r['sha256']),'exact parent plugin bytes before execution')
 compiled=compile(body,str(expected),'exec',dont_inherit=True)
 name='firstdecode_plugin';previous=sys.modules.get(name)
 O.need(previous is None or Path(previous.__file__).resolve()==expected.resolve(),'parent parser source-qualified payload namespace, no ambient module')
 if previous is None:
  spec=importlib.util.spec_from_file_location(name,expected);first=importlib.util.module_from_spec(spec);sys.modules[name]=first
  try:exec(compiled,first.__dict__)
  except BaseException:
   if sys.modules.get(name)is first:sys.modules.pop(name)
   raise
 else:first=previous
 O.need(Path(first.__file__).resolve()==expected.resolve()and callable(first.register)and callable(first.validate_registration),'actual parent defining plugin source and API')
 defined={x.co_name:x for x in compiled.co_consts if isinstance(x,types.CodeType)}
 for name in('register','validate_registration'):
  f=getattr(first,name)
  O.need(type(f)is types.FunctionType and f.__globals__ is first.__dict__ and f.__code__==defined[name] and f.__qualname__==name and f.__defaults__ is None and not hasattr(f,'__wrapped__'),'whole actual source-defined parent plugin function identity')
 # No direct register(), generic unwrap, loader-cache reset, DSO operation or
 # environment PYTHONPATH injection. Native loader and original validator stay.
 return first
