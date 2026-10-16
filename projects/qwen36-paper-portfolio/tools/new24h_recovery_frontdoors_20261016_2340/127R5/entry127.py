"""Consumer-only domain diagnostic. No NPU and no owner promotion API."""
import argparse,hashlib,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from timing_transform127r5 import transform
from audit_transform127r4 import Memo
import codec_transform130

def checked(ref):
 if set(ref)!={'path','bytes','sha256'}:raise ValueError('exact Ref3')
 p=Path(ref['path'])
 if not p.is_absolute() or p.is_symlink():raise ValueError('ordinary absolute input')
 with p.open('rb') as f:
  before=os.fstat(f.fileno());data=f.read();after=os.fstat(f.fileno())
 signature=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 if signature(before)!=signature(after) or signature(after)!=signature(p.stat()):raise ValueError('stable input')
 if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('exact input bytes')
 return data

def obj(ref):return json.loads(checked(ref))

def prepare(source_ref,producer_source_ref,producer_ref,strict_ref):
 own=obj(source_ref)
 if own.get('consumer_contract_schema')!='deltalog.anchor-consumer-source/v127':raise ValueError('consumer source schema')
 # No binding can be approved until original terminal failure is classified.
 if own.get('bound') is not True:raise ValueError('pending original terminal category and recovery authorization')
 if own['producer_source']!=producer_source_ref:raise ValueError('separate exact original producer source')
 for name,ref in own['files'].items():
  if Path(ref['path']).name!=name:raise ValueError('declared source leaf')
  checked(ref)
 m=obj(producer_source_ref);producer=obj(producer_ref);strict=obj(strict_ref)
 if producer['source']!=producer_source_ref or producer['primary'] is not None or producer['steps']!=160:raise ValueError('complete original NPU producer')
 if len(producer['records'])!=328 or len(producer['actual_sidecar_records'])!=351:raise ValueError('exact681 retained raw references')
 if strict['source']!=producer_source_ref:raise ValueError('preserved original strict source')
 data=checked(m['files']['run_consumer088.py']);text=transform(data)
 return own,m,text

def main():
 ap=argparse.ArgumentParser(allow_abbrev=False)
 ap.add_argument('--execute',action='store_true')
 for name in ('consumer-source-ref','producer-source-ref','producer-ref','strict-ref','output'):
  ap.add_argument('--'+name,required=True)
 a=ap.parse_args()
 if not a.execute:print('disabled; no numerical execution');return 0
 sr,ps,pr,st=map(json.loads,(a.consumer_source_ref,a.producer_source_ref,a.producer_ref,a.strict_ref))
 own,m,text=prepare(sr,ps,pr,st)
 # Original __file__/imports/manifest/readset and every numerical predicate remain intact.
 target=m['files']['run_consumer088.py']['path']
 sys.path.insert(0,str(Path(target).parent))
 import torch
 codec_transform130.install(torch,m['files']['raw_codec.py'],lambda r:Path(r['path']) if checked(r) else None)
 output=Path(a.output)
 if not output.is_absolute() or not output.parent.is_dir() or output.exists():raise ValueError('fresh output')
 sys.argv=[target,'--execute','--source-ref',json.dumps(ps),'--producer-ref',json.dumps(pr),'--output',str(output)]
 namespace={'__name__':'anchor_recovery127','__file__':target,'_memo_factory127r4':Memo}
 exec(compile(text,target+'#anchors-only127','exec'),namespace)
 code=namespace['main']()
 # Original report is preserved unchanged. This envelope is not v035 owner/PASS.
 envelope=dict(schema='deltalog.single-read-audit-reuse-consumer-diagnostic/v127-repair5',consumer_source=sr,
  producer_source=ps,producer=pr,preserved_original_strict=st,reader_contract='single-open130 + completed-invocation-audit131; same original mathematical gates',
  domain=dict(path=str(output),bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest()),
  original_domain_exit=code,NPU_reexecuted=False,qualification=False,model_admitted=False)
 ep=output.with_name(output.name+'.consumer127.json')
 with ep.open('x',encoding='utf-8',newline='\n') as f:json.dump(envelope,f,sort_keys=True,allow_nan=False)
 return code
if __name__=='__main__':raise SystemExit(main())
