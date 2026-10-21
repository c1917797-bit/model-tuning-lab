from pathlib import Path
import base64,hashlib,json
P=Path(__file__).resolve().parent;S=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11');O=S.with_name('run-'+S.name);R=O/'dense/receipts/STREAM'
def ref(p):
 p=Path(p);assert p.is_file()and not any(q.is_symlink()for q in(p,*p.parents));b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
records={}
def add(name,path):
 b=path.read_bytes();records[name]=dict(actual_ref=ref(path),base64=base64.b64encode(b).decode())
for n in ('g2_consumer.py','g2_channel.py','sourceio.py'):add('SOURCE/'+n,S/n)
for pat in ('ACK-RANK-*-000000.json','FRAME-RANK-*-000000.json','FRAME-RANK-*-000001.json','REPORT-RANK-*-000000.json','REPORT-RANK-0-000001.json','CHANNEL.json','STREAM_CONSUMER_EXIT.json'):
 for p in sorted(R.glob(pat)):add('STREAM/'+p.name,p)
add('HOST-FIRST-FAULT.json',O/'HOST-FIRST-FAULT.json')
v=dict(schema='bole.actual-v11-ACK-serialization-failure-fixture/v1',source_ref=ref(S/'SOURCE_BOUND.json'),failed_model_ref=ref(O/'RESULT.json'),cleanup_refs={r:ref(O/r/'cleanup.json')for r in('cpu-preflight','candidate','cpu-consumer','dense')},records=records,numerical_model_qualification=False)
assert v['failed_model_ref']==dict(path=str(O/'RESULT.json'),bytes=1072961,sha256='cddfa40ed93a663b5a34102121db4c7bb64df7b92282e18b49c94cc241a0861c')
(P/'ACTUAL_ACK_FIXTURE.json').write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
