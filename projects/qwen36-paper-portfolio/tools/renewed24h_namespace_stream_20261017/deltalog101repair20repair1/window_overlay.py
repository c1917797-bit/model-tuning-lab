"""Private-module clock overlay; historical017/008 source remains immutable."""
from pathlib import Path
START=1792226600
CUT=1792313000
AUTHORITY={'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/RENEW24H_AUTHORITY_20261017_084320.json', 'bytes': 3012, 'sha256': 'cdba34641b429a6132e7af5a6a88a93b63faf7d0834a9313a8b948e2a4907b6d'}
def need(v,m):
 if not v:raise ValueError(m)
def install(H,m):
 need(m['window']=={'start':START,'cutoff':CUT},'exact NEW24H window')
 need(m['authority']==AUTHORITY and m['authority_sha256']==AUTHORITY['sha256'] and m['cutoff_epoch']==CUT,'actual NEW24H authority identity')
 H.START=START;H.CUT=CUT;H.AUTH=Path(AUTHORITY['path']);H.AUTH_SHA=AUTHORITY['sha256']
def transform(text):
 pairs=(('START, CUTOFF = 1791962297, 1792135097',f'START, CUTOFF = {START}, {CUT}'),('facade.CUT = "2026-10-16T07:18:17+00:00"','facade.CUT = "2026-10-18T08:43:20+00:00"'),('AUTH = ROOT / ".agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json"',f'AUTH = Path({AUTHORITY["path"]!r})'))
 out=text
 for old,new in pairs:
  need(out.count(old)==1,'exact generated017 clock source occurrence: '+old);out=out.replace(old,new)
 inverse=out
 for old,new in reversed(pairs):
  need(inverse.count(new)==1,'unique generated clock inverse');inverse=inverse.replace(new,old)
 need(inverse==text,'whole generated controller clock-only inverse')
 return out
