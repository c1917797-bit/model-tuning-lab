"""Device-free source and actual private generator import controls; no tokenizer mock."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
P=Path(__file__).resolve().parent
OLD=P.parent/'bole_textonly_v8_prepare_20261024'/'prepared-source-short8-v8'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
 A=load(P/'adapt_input_preflight.py','_input_adapter_control')
 names=('hypic32k_input.py','benchmark_shared_prefix.py','performance_service_client.py','preflight114.py')
 old={n:(OLD/n).read_bytes()for n in names}
 out,delta=A.adapt(old);assert A.inverse(out,delta)==old
 assert set(delta)=={'hypic32k_input.py','preflight114.py','input_preflight.py'}
 original=ast.parse(old['hypic32k_input.py']);derived=ast.parse(out['hypic32k_input.py'])
 funcs=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,ast.FunctionDef)}
 assert funcs(original)==funcs(derived)
 assert out['benchmark_shared_prefix.py']==old['benchmark_shared_prefix.py']
 bad=dict(old);bad['benchmark_shared_prefix.py']+=b' '
 try:A.adapt(bad)
 except ValueError:pass
 else:raise AssertionError('wrong generator bytes accepted')
 bad=dict(old);bad['performance_service_client.py']=old['performance_service_client.py'].replace(b"'/models/Qwen3.6-27B'",b"'/models/wrong'")
 try:A.adapt(bad)
 except ValueError:pass
 else:raise AssertionError('wrong checkpoint accepted')
 # Real original private import: complete actual generator body and dataclasses, no fake module.
 name='_bole_current_hypic32k_generator';prior=sys.modules.get(name);had=name in sys.modules
 try:
  spec=importlib.util.spec_from_file_location(name,OLD/'benchmark_shared_prefix.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m
  exec(compile(old['benchmark_shared_prefix.py'],str(OLD/'benchmark_shared_prefix.py'),'exec'),m.__dict__)
  assert callable(m._build_prompts)and callable(m._tokens_at_least)
 finally:
  if had:sys.modules[name]=prior
  else:sys.modules.pop(name,None)
 assert (name in sys.modules)==had and (not had or sys.modules[name]is prior)
 pf=ast.parse(out['preflight114.py']);run=next(n for n in pf.body if isinstance(n,ast.FunctionDef)and n.name=='run')
 assert any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='actual_input_run'for n in ast.walk(run))
 assert b'local_files_only=True'in out['input_preflight.py']
 assert b'120'in (OLD/'host_service.py').read_bytes()
 for n,b in out.items():compile(b,n,'exec')
 print(json.dumps(dict(source_controls=7,whole_input_functions_unchanged=True,real_generator_import=True,
  actual_tokenizer_execution=False,pending='same-image original120-second CPU child; full42-case generation',
  NPU=False)))
if __name__=='__main__':main()
