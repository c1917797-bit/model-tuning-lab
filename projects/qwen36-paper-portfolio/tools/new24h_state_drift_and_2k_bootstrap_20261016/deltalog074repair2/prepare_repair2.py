"""Mechanical immutable source manifest/commands/delivery formatting only."""
import base64,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=P.parent/'deltalog-state-drift-cpu-new24h-20261016-074-repair1'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-state-drift-cpu-new24h-v1-074-repair2'
def data(v):return(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 m=json.loads((OLD/'SOURCE_MANIFEST.json').read_bytes());oldroot=m['root'];m['root']=ROOT;m['actual_local_tests']=5
 names=['owned_cpu.py','diagnose.py','cpu_entry.py','test_owner074.py','HANDOFF_REPAIR2.md','prepare_repair2.py']
 files={n:(P/n).read_bytes()for n in names}
 for n,b in files.items():
  if b'\r'in b or not b.endswith(b'\n'):raise ValueError('complete LF source '+n)
 for n in ('diagnose.py','cpu_entry.py'):
  if files[n]!=(OLD/n).read_bytes():raise ValueError('diagnostic/math/CPU entry must remain byte-identical')
 m['files']={n:ref(ROOT+'/'+n,b)for n,b in files.items()};m['repair']=dict(scope='Docker-client-only-AS wrapper and original-error preservation; no host budget increase',old_source=ref(oldroot+'/SOURCE_MANIFEST.json',(OLD/'SOURCE_MANIFEST.json').read_bytes()),original_R1_failure_unchanged=True,sameimage_executed=False)
 raw=data(m);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw)
 commands=json.loads((OLD/'COMMANDS_OWNED074.json').read_bytes());commands=json.loads(json.dumps(commands).replace(oldroot,ROOT).replace('run-drift074repair1-','run-drift074repair2-'));commands['source']=sr
 for key in ('execute','sourceaudit'):
  argv=commands[key];argv[argv.index('--source-ref')+1]=json.dumps(sr,separators=(',',':'))
 commands['host_budget_unchanged']='512MiB softAS, original unlimited hard; only exact Docker client prlimit ASunlimited'
 cb=data(commands);(P/'COMMANDS_OWNED074.json').write_bytes(cb)
 patch=''.join(difflib.unified_diff((OLD/'owned_cpu.py').read_text().splitlines(keepends=True),(P/'owned_cpu.py').read_text().splitlines(keepends=True),fromfile='074R1/owned_cpu.py',tofile='074R2/owned_cpu.py')).encode();(P/'RUNTIME_OWNED074.patch').write_bytes(patch)
 files.update({'SOURCE_MANIFEST.json':raw,'COMMANDS_OWNED074.json':cb,'RUNTIME_OWNED074.patch':patch})
 delivery=dict(schema='deltalog.cpu074.source-only-byteexact/v1',root=ROOT,actual_NPU=False,qualification=False,files=[dict(relative=n,**ref(ROOT+'/'+n,b),base64=base64.b64encode(b).decode())for n,b in sorted(files.items())]);db=data(delivery);(P/'BYTE_EXACT_OWNED074.json').write_bytes(db)
 print(json.dumps(dict(source=sr,delivery=ref(str(P/'BYTE_EXACT_OWNED074.json'),db),files=len(files),local_tests=5,sameimage=False,NPU=False)))
if __name__=='__main__':main()
