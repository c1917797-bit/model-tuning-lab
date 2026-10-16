"""Byte serialization only, no experiment execution."""
import base64,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-native-prefill-cpu-preflight-new24h-v1-083'
OLD=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-state-drift-cpu-new24h-20261016-074-repair2')
GUEST=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-native-prefill-counterfactual-new24h-079')
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def ref(path,b):return dict(path=path,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 old=json.loads((OLD/'SOURCE_MANIFEST.json').read_bytes());gm=json.loads((GUEST/'SOURCE_MANIFEST.json').read_bytes());gr=ref(gm['root']+'/SOURCE_MANIFEST.json',(GUEST/'SOURCE_MANIFEST.json').read_bytes())
 names=['owned_cpu.py','cpu_entry.py','test_preflight083.py','HANDOFF.md','seal083.py'];files={n:(P/n).read_bytes()for n in names}
 for n,b in files.items():
  if b'\r'in b or not b.endswith(b'\n'):raise ValueError('LF-only '+n)
 diff=''.join(difflib.unified_diff((OLD/'owned_cpu.py').read_text().splitlines(True),(P/'owned_cpu.py').read_text().splitlines(True),fromfile='actual074R2/owned_cpu.py',tofile='083/owned_cpu.py')).encode();(P/'DONOR_DIFF.patch').write_bytes(diff);files['DONOR_DIFF.patch']=diff
 m=dict(schema='deltalog.native-prefill-cpu-source/v083',root=ROOT,default_enabled=False,authority_ref=gm['authority_ref'],guest_source=gr,files={n:ref(ROOT+'/'+n,b)for n,b in files.items()},donor=old['files']['owned_cpu.py'],resource=old['resource'],NPU=False,qualification=False,actual_sameimage=False)
 raw=data(m);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw)
 argv=['/usr/bin/python3','-I','-B',ROOT+'/owned_cpu.py'];common=['--source-ref',json.dumps(sr,separators=(',',':'))];c=dict(source=sr,default_off=argv,source_audit=argv+['--source-audit']+common,execute=argv+['--execute']+common+['--host-cpu','MAIN_HOST_CPU','--guest-cpu','MAIN_DISJOINT_GUEST_CPU','--output','/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-prefill083-MAIN-20261016-001'],actual_sameimage=False,NPU=False)
 cb=data(c);(P/'COMMANDS.json').write_bytes(cb);files.update({'SOURCE_MANIFEST.json':raw,'COMMANDS.json':cb})
 b=data(dict(schema='deltalog083.source-only-byteexact/v1',root=ROOT,files=[dict(relative=n,**ref(ROOT+'/'+n,v),base64=base64.b64encode(v).decode())for n,v in sorted(files.items())]));(P/'BYTE_EXACT_DELIVERY.json').write_bytes(b);print(json.dumps(dict(source=sr,delivery=ref(str(P/'BYTE_EXACT_DELIVERY.json'),b),files=len(files))))
if __name__=='__main__':main()
