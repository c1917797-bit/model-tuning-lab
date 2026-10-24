"""Execute actual rendered Trace classes and every actual capture trace call."""
import ast,hashlib,json,os,resource,sys,types
from pathlib import Path
from unittest.mock import patch
os.sched_setaffinity(0,{145});resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20))
p=Path(__file__).parent
ns=dict(__file__=str(p/'prepare_successor.py'),__name__='_v6_source')
exec(compile((p/'prepare_successor.py').read_bytes(),ns['__file__'],'exec'),ns)
b=ns['render']();ns['inverse'](b);files=b['files'];root=Path(b['manifest']['root'])
prev=json.loads((p.parent/'mxr_three_tile_rounding_prepare_v5_20261024/prepared-source/SOURCE_MANIFEST.json').read_bytes())
changed=[n for n,data in files.items()if n not in prev['files']or data!=Path(prev['files'][n]['path']).read_bytes()]
assert set(changed)=={'event_host.py','event_software.py','prepare_successor.py','successor_bindings.py','rounding_capture.py','rounding_stage_trace.py','trace_contract_check.py'},changed
oldcap=Path(prev['files']['rounding_capture.py']['path']).read_text()
newcap=files['rounding_capture.py'].decode()
assert newcap.replace('from rounding_stage_trace import Trace','from wu_stage_trace import Trace',1)==oldcap
assert files['wu_stage_trace.py']==Path(prev['files']['wu_stage_trace.py']['path']).read_bytes()
assert files['wu_cpu_fixture.py']==Path(prev['files']['wu_cpu_fixture.py']['path']).read_bytes()
assert b['manifest']['resources']==prev['resources']and b['manifest']['window']==prev['window']
original=Path.read_bytes
def read_bytes(path):
    if path==root/'rounding_capture.py':return files['rounding_capture.py']
    return original(path)
saved={n:sys.modules.get(n)for n in('wu_stage_trace','rounding_stage_trace','trace_contract_check')}
try:
    for name in saved:
        module=types.ModuleType(name);module.__file__=str(root/(name+'.py'))
        exec(compile(files[name+'.py'],module.__file__,'exec'),module.__dict__)
        sys.modules[name]=module
    with patch.object(Path,'read_bytes',read_bytes):
        result=sys.modules['trace_contract_check'].check(dict(fixture=True))
finally:
    for name,value in saved.items():
        if value is None:sys.modules.pop(name,None)
        else:sys.modules[name]=value
assert result['positive_calls']==6 and result['negative_controls']==15,result
soft=ast.parse(files['event_software.py'])
calls=[n for n in ast.walk(soft)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='check_trace_contract']
assert len(calls)==1
print(json.dumps(dict(passed=True,trace_contract=result,same_image_hook=True,changed_files=changed,whole_source_inverse=True,
 Torch=False,NPU=False,source_materialized=False,
 refs=[dict(path=str(f),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())for f in sorted(p.iterdir())if f.is_file()])))
