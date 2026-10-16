"""Explicit new authorization; old compile/022 certificates are historical only."""
import hashlib,json,time
from pathlib import Path
START,CUT=1792134133,1792220533
AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json',bytes=3481,sha256='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28')
def require_current(r,obj,*,now=None):
 if r!=AUTH:raise ValueError('exact new24h authority Ref required, not old48h')
 a=obj(r);t=time.time()if now is None else now
 if not(a['schema']=='ascend.paper-portfolio.new24h-authority/v1'and a['start_epoch']==START and a['cutoff_epoch']==CUT and START<=t<CUT-2880):raise ValueError('fixed new24h/unchanged whole owner2880 budget')
 return a
