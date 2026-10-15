"""Mechanical LF/source sealing; no mathematical code generation."""
import ast,hashlib,json,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent
B=P.parent/'deltalog-regression137-guard-new48h-20261015-020-physical4-repair1'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-regression137-guard-new48h-v1-020-physical4-repair2'
def ref(p,path=None):
 b=p.read_bytes();return dict(path=path or str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def put(n,v):
 with (P/n).open('wb')as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
if '--execute'not in sys.argv:print('disabled');raise SystemExit()
m=json.loads((B/'SOURCE_MANIFEST.json').read_bytes());oldroot=m['root'];oldsr=ref(B/'SOURCE_MANIFEST.json',oldroot+'/SOURCE_MANIFEST.json')
names=[n for n,r in m['files'].items()if pathlib.PurePosixPath(r['path']).parent==pathlib.PurePosixPath(oldroot)]+['test_handshake.py','seal_repair2.py']
for n in names:
 b=(P/n).read_bytes().replace(b'\r\n',b'\n');(P/n).write_bytes(b);assert b'\r'not in b
 if n.endswith('.py'):ast.parse(b)
m['root']=ROOT
for n in names:m['files'][n]=ref(P/n,ROOT+'/'+n)
m['outputs']={k:v.replace('guard020-physical4-repair1-','guard020-physical4-repair2-')for k,v in m['outputs'].items()}
m['ownership_visibility_repair']=dict(original_failed_source=oldsr,actual_failed_owner=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl137-guard020-physical4-repair1-numeric-new48h-MAIN-20261015-001/RESULT.json',bytes=1197,sha256='0ab604e15211cb1634a74e53b0fbebe259cebc4c91b965e60a263c4dcd9d9a47'),delta='wait for positive full host proof inside unchanged guest ARM/owner deadline; no self-report-only ARM',math_changed=False)
put('SOURCE_MANIFEST.json',m);sr=ref(P/'SOURCE_MANIFEST.json',ROOT+'/SOURCE_MANIFEST.json')
def change(v):
 if isinstance(v,dict):return sr if v==oldsr else{k:change(x)for k,x in v.items()}
 if isinstance(v,list):return[change(x)for x in v]
 if isinstance(v,str):return v.replace(oldroot,ROOT).replace(oldsr['sha256'],sr['sha256']).replace('guard020-physical4-repair1-','guard020-physical4-repair2-').replace('ACTUAL_BOUND_020_PHYSICAL4_REPAIR1_SHA256','ACTUAL_BOUND_020_PHYSICAL4_REPAIR2_SHA256')
 return v
put('COMMANDS.json',change(json.loads((B/'COMMANDS.json').read_bytes())))
r=subprocess.run([sys.executable,'-I','-B','-m','unittest','discover','-s',str(P),'-p','test*.py'],capture_output=True,text=True);assert r.returncode==0,r.stderr
sys.path.insert(0,str(P));from verify_mapping import verify
put('INVERSE_PROOF.json',verify());put('LOCAL_TEST_RESULT.json',dict(full_discover=r.stderr,NPU=False,sameimage=False))
fs=[dict(path=n,text=(P/n).read_bytes().decode())for n in names+['SOURCE_MANIFEST.json','COMMANDS.json','LOCAL_TEST_RESULT.json','INVERSE_PROOF.json']]
put('BYTE_EXACT_DELIVERY.json',dict(schema='awmcp.source-text-payload/v1',root=ROOT,files=fs))
print(json.dumps(sr));print(json.dumps(ref(P/'BYTE_EXACT_DELIVERY.json')))
