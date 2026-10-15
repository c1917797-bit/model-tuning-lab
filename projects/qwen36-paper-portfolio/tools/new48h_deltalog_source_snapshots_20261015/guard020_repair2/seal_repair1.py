"""Generate LF immutable repair delivery; require data dependencies explicitly."""
import ast,hashlib,json,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));from input_contract import EXPECTED,require
B=P.parent/'deltalog-regression137-guard-new48h-20261015-020-physical4'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-regression137-guard-new48h-v1-020-physical4-repair1'
def ref(p,path=None):
 b=p.read_bytes();return dict(path=path or str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def put(n,v):
 b=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();assert b'\r'not in b;(P/n).write_bytes(b)
if '--execute'not in sys.argv:print('disabled');raise SystemExit()
m=json.loads((B/'SOURCE_MANIFEST.json').read_bytes());oldroot=m['root'];oldsr=ref(B/'SOURCE_MANIFEST.json',oldroot+'/SOURCE_MANIFEST.json')
names=[n for n in m['files']if n.endswith('.py')and n!='seal_physical4.py']+['ORIGINAL020_SOURCE.json','input_contract.py','test_input_contract.py','seal_repair1.py']
# Root/output/owner identity are data-only remaps; no runtime mathematical source changes.
for n in ('host.py',):
 b=(B/n).read_bytes();b=b.replace(b'MAIN-020-physical4',b'MAIN-020-physical4-repair1');(P/n).write_bytes(b)
for n in names:
 b=(P/n).read_bytes().replace(b'\r\n',b'\n');(P/n).write_bytes(b);assert b'\r'not in b
 if n.endswith('.py'):ast.parse(b)
m['root']=ROOT;m['files']={n:ref(P/n,ROOT+'/'+n)for n in names};m['files']['REGRESSION_INPUTS.json']=EXPECTED
require(m,lambda r:None)
m['outputs']={k:v.replace('guard020-physical4-','guard020-physical4-repair1-')for k,v in m['outputs'].items()}
m['input_dependency_repair']=dict(original_failed_source=oldsr,missing_key='REGRESSION_INPUTS.json',original016_ref=EXPECTED,math_changed=False)
put('SOURCE_MANIFEST.json',m);sr=ref(P/'SOURCE_MANIFEST.json',ROOT+'/SOURCE_MANIFEST.json')
cmd=json.loads((B/'COMMANDS.json').read_bytes())
def change(v):
 if isinstance(v,dict):return sr if v==oldsr else{k:change(x)for k,x in v.items()}
 if isinstance(v,list):return[change(x)for x in v]
 if isinstance(v,str):return v.replace(oldroot,ROOT).replace(oldsr['sha256'],sr['sha256']).replace('guard020-physical4-','guard020-physical4-repair1-').replace('ACTUAL_BOUND_020_PHYSICAL4_SHA256','ACTUAL_BOUND_020_PHYSICAL4_REPAIR1_SHA256')
 return v
put('COMMANDS.json',change(cmd))
r=subprocess.run([sys.executable,'-I','-B','-m','unittest','discover','-s',str(P),'-p','test*.py'],capture_output=True,text=True);assert r.returncode==0,r.stderr
from verify_mapping import verify
put('INVERSE_PROOF.json',verify())
put('LOCAL_TEST_RESULT.json',dict(full_discover=r.stderr,NPU=False,sameimage=False))
fs=[dict(path=n,text=(P/n).read_bytes().decode())for n in names+['SOURCE_MANIFEST.json','COMMANDS.json','LOCAL_TEST_RESULT.json','INVERSE_PROOF.json']];assert all('\r'not in f['text']for f in fs)
put('BYTE_EXACT_DELIVERY.json',dict(schema='awmcp.source-text-payload/v1',root=ROOT,files=fs));payload=json.loads((P/'BYTE_EXACT_DELIVERY.json').read_bytes());assert all(f['text'].encode()==(P/f['path']).read_bytes()for f in payload['files'])
print(json.dumps(sr));print(json.dumps(ref(P/'BYTE_EXACT_DELIVERY.json')))
