"""Thin immutable source/delta transport serializer, no runtime actions."""
import ast,base64,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair1'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair2'
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 import sys
 sys.path.insert(0,str(P));import storage_bridge093 as S
 prior=json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes());oldroot=prior['root'];m=json.loads(json.dumps(prior).replace(oldroot,ROOT));m['root']=ROOT;m['storage093_source_ref']=S.SOURCE093;m['storage_seal_evidence_ref']=None;m['storage_seal_generation_ref']=None
 m['storage_policy']['sealed_terminal_compatibility']='093 actual existing8 only; six closed phases immutable; old069 numericalFAIL unchanged; independent088 prepared identity'
 changed=('bind052.py','host.py','run052.py');added=('storage_bridge093.py','test088r2.py','HANDOFF088R2.md','seal088r2.py');files={};copies=[];patch=[]
 for n,r in list(m['files'].items()):
  if r['path'].startswith(ROOT+'/'):
   b=(P/n).read_bytes();files[n]=b;m['files'][n]=ref(ROOT+'/'+n,b)
   if n not in changed:assert b==(OLD/n).read_bytes(),n;copies.append(dict(relative=n,source=prior['files'][n],target=m['files'][n]))
 for n in added:
  b=(P/n).read_bytes();files[n]=b;m['files'][n]=ref(ROOT+'/'+n,b)
 for n in changed:patch.extend(difflib.unified_diff((OLD/n).read_text().splitlines(True),(P/n).read_text().splitlines(True),fromfile='R1/'+n,tofile='R2/'+n))
 for n,b in files.items():
  assert b'\r'not in b and b.endswith(b'\n'),n
  if n.endswith('.py'):ast.parse(b)
 raw=enc(m);(P/'SOURCE_TEMPLATE.json').write_bytes(raw);tr=ref(ROOT+'/SOURCE_TEMPLATE.json',raw)
 priorcmd=json.loads((OLD/'COMMANDS088R1.json').read_bytes());commands={}
 for phase,row in priorcmd['commands'].items():
  argv=[x.replace(oldroot,ROOT).replace('SAME088R1','SAME088R2')for x in row['argv']];argv[argv.index('--template-ref')+1]=json.dumps(tr,separators=(',',':'))
  if phase=='bind':
   argv[argv.index('--build-ref')+1]=json.dumps(m['reviewed_split_build_ref'],separators=(',',':'))
   argv[argv.index('--storage-seal-evidence-ref')+1]=json.dumps(S.EVIDENCE093,separators=(',',':'))
   au=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/DL061_STORAGE_AUTHORITY_20261016.json',bytes=1213,sha256='3b58d42555147db06874fa4db36ada8b95474af4f3153fc89b73e4b7779d6f6c');argv[argv.index('--storage-authority-ref')+1]=json.dumps(au,separators=(',',':'))
  commands[phase]=dict(argv=argv,executable_now=False,reason='actual035 predecessor, fresh CPU resources/same088R2 receipts required; storage093 not mathematicalPASS')
 cb=enc(dict(template_ref=tr,commands=commands,qualification=False,graph_supported=False,existing093seal8=S.GENERATION8,seal_creation_prohibited=True));(P/'COMMANDS088R2.json').write_bytes(cb)
 extra={'SOURCE_TEMPLATE.json':raw,'COMMANDS088R2.json':cb,'COPY_MAP088R2.json':enc(copies),'CHANGED088R2.patch':''.join(patch).encode()}
 for n,b in extra.items():(P/n).write_bytes(b)
 payload=dict(files,**extra);bb=enc(dict(schema='deltalog.eager-storage088R2-source-delivery/v1',root=ROOT,prepared_only=True,READY=False,files=[dict(relative=n,**ref(ROOT+'/'+n,b),base64=base64.b64encode(b).decode())for n,b in sorted(payload.items())]));(P/'BYTE_EXACT088R2.json').write_bytes(bb);print(json.dumps(dict(template=tr,delivery=ref(str(P/'BYTE_EXACT088R2.json'),bb),files=len(payload),changed=list(changed),added=list(added))))
if __name__=='__main__':main()
