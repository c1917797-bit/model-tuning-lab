"""Current NEW24H authority only; historical receipt clocks are not reset."""
import hashlib,json
from pathlib import Path
START,CUT=1792134133,1792220533
REF=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json',bytes=3481,sha256='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28')
def validate(reference,body):
 if reference!=REF or(len(body),hashlib.sha256(body).hexdigest())!=(REF['bytes'],REF['sha256']):raise ValueError('exact published NEW24H authority bytes/ref')
 a=json.loads(body)
 if a['schema']!='ascend.paper-portfolio.new24h-authority/v1'or(a['start_epoch'],a['cutoff_epoch'])!=(START,CUT)or a['hours']!=24 or a['hardware']['physical_npus']!=[4,5,6,7]or a['hardware']['protected_npus']!=[0,1,2,3]or a['automatic_extension']is not False:raise ValueError('frozen independent NEW24H authority, not historical timestamps')
 return a
def verify(reference):return validate(reference,Path(reference['path']).read_bytes())
