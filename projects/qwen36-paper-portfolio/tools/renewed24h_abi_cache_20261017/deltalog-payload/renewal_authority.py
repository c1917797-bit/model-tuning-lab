"""New-window read-only revalidation; never rewrites historical capture authority."""
import ast,hashlib,json,time,types
from pathlib import Path
START,CUT=1792226600,1792313000
AUTHORITY=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/RENEW24H_AUTHORITY_20261017_084320.json',bytes=3012,sha256='cdba34641b429a6132e7af5a6a88a93b63faf7d0834a9313a8b948e2a4907b6d')
REUSE=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/RENEW24H_ARTIFACT_REUSE_SCOPE_20261017_084320.json',bytes=2467,sha256='442cb693c1724834238779a0179b2667776f2d2f2ce5c48ee63850f18dcc3d7c')
BASE23=dict(path='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/STORAGE_LEDGER061.23.json',bytes=4169,sha256='7bacf26df76b47d53963fc054c91b38384716c7d9901938087f329dc288c23d0')
OLD="need(latest(K)==BASE and time.time()<1792220533,'ledger/cutoff stable through final verification')"
NEW="need(latest(K)==BASE,'historical ledger stable through renewed verification');_renewed_authority_check()"

def require(v,m):
 if not v:raise ValueError(m)

def check():
 p=Path(AUTHORITY['path']);b=p.read_bytes()
 require(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents))and len(b)==AUTHORITY['bytes']and hashlib.sha256(b).hexdigest()==AUTHORITY['sha256'],'exact renewed authority')
 a=json.loads(b)
 require(a['schema']=='ascend.paper-portfolio.explicit-renewed24h/v1'and a['start_epoch']==START and a['cutoff_epoch']==CUT and a['old_window_immutable']['not_retroactive']is True and a['resource_limits']['original_storage_limits_unchanged']is True,'explicit nonretroactive renewed scope')
 q=Path(REUSE['path']);rb=q.read_bytes()
 require(not any(x.is_symlink()for x in(q,*q.parents))and len(rb)==REUSE['bytes']and hashlib.sha256(rb).hexdigest()==REUSE['sha256'],'exact historical reuse authority')
 reuse=json.loads(rb)
 require(reuse['schema']=='ascend.renewed24h.historical-artifact-reuse/v1'and reuse['base_authority']==AUTHORITY and reuse['start_epoch']==START and reuse['cutoff_epoch']==CUT and reuse['qualification']is False and reuse['storage']['original_authority_kept_as_legacy_ledger_identity']is True,'source-bound nonpromoting historical reuse')
 require(START<=time.time()<CUT,'renewed reader current window')
 return dict(authority=AUTHORITY,reuse_authority=REUSE,historical_ledger_ref=BASE23,start_epoch=START,cutoff_epoch=CUT,historical_capture_unchanged=True,numeric_qualified=False)

