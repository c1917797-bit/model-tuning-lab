"""Private-module clock overlay; historical017/008 source remains immutable."""
from pathlib import Path
START=1792134133
CUT=1792220533
AUTHORITY={'path':'/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json','bytes':3481,'sha256':'e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28'}
def need(v,m):
 if not v:raise ValueError(m)
def install(H,m):
 need(m['window']=={'start':START,'cutoff':CUT},'exact NEW24H window')
 need(m['authority']==AUTHORITY and m['authority_sha256']==AUTHORITY['sha256'] and m['cutoff_epoch']==CUT,'actual NEW24H authority identity')
 H.START=START;H.CUT=CUT;H.AUTH=Path(AUTHORITY['path']);H.AUTH_SHA=AUTHORITY['sha256']
def transform(text):
 pairs=(('START, CUTOFF = 1791962297, 1792135097',f'START, CUTOFF = {START}, {CUT}'),('facade.CUT = "2026-10-16T07:18:17+00:00"','facade.CUT = "2026-10-17T07:02:13+00:00"'),('AUTH = ROOT / ".agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json"',f'AUTH = Path({AUTHORITY["path"]!r})'))
 out=text
 for old,new in pairs:
  need(out.count(old)==1,'exact generated017 clock source occurrence: '+old);out=out.replace(old,new)
 inverse=out
 for old,new in reversed(pairs):
  need(inverse.count(new)==1,'unique generated clock inverse');inverse=inverse.replace(new,old)
 need(inverse==text,'whole generated controller clock-only inverse')
 return out
