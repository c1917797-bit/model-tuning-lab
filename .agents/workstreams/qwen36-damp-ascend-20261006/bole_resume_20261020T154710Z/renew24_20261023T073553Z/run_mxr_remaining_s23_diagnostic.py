"""MAIN finite serial diagnostic admission; no qualification/performance promotion."""
from pathlib import Path
import hashlib,json,subprocess,time
W=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");D=W/'renew24_20261023T073553Z'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);assert p.is_file()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r;return p
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def run(stage,cmd,cap,shard):
 start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,timeout=cap)
 record=dict(shard=shard,stage=stage,argv=cmd,returncode=r.returncode,elapsed=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr)
 rr=save(D/('MXR_REMAINING_S%d_%s_ACTUAL.json'%(shard,stage.upper())),record)
 print(json.dumps(dict(shard=shard,stage=stage,returncode=r.returncode,record=rr,stderr_tail=r.stderr[-1800:])),flush=True)
 assert r.returncode==0,record['stderr'][-3000:]
first=Path('/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_NPU_001/RESULT.json')
assert ref(first)==dict(path=str(first),bytes=590777,sha256='bf218659bce5202852a1f3546d71360b7d486663cbd9b63d64604ca24f9eec78')
f=json.loads(first.read_text());assert f['primary']is None and f['secondary']==[]
c=json.loads(checked(f['cleanup']).read_text());assert c['stopped']is True and c['retained']is True and c['errors']==[]
g=W/'mxr_remaining_shards_prepare_v1/prepare_remaining.py'
assert ref(g)['sha256']=='9dc19b7e485c5565a6ff5cb0baf4f50685df9d0b6d87615d304f60843c947f48'
ns=dict(__file__=str(g),__name__='_MAIN_checked_remaining_derivation');exec(compile(g.read_bytes(),str(g),'exec'),ns)
ip=W/'mxr_remaining_shards_prepare_v1/materialized/INDEX.json'
assert ref(ip)['sha256']=='3bc761cd66c11edb20f5ff34b9e72e486e87e1938b73884a937c14f87ee0b4b6'
index=json.loads(ip.read_text());assert [x['shard']for x in index['rows']]==[1,2,3]
# MAIN admits the two distinct remaining inputs after actual S1 stop/retain.
s1=Path('/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S1_NPU_001/RESULT.json')
assert ref(s1)==dict(path=str(s1),bytes=594672,sha256='64e9d7c9e18981fdbae41bb60de11dfcf01069b547dc512f963879694306b80f')
sv=json.loads(s1.read_text());assert sv['primary']is None and sv['secondary']==[]
sc=json.loads(checked(sv['cleanup']).read_text());assert sc['stopped']is True and sc['retained']is True and sc['errors']==[]
for row in index['rows'][1:]:
 shard=row['shard'];assert 1792740953<=time.time()and time.time()+1500<=1792827353
 template=row['template_ref'];m=json.loads(checked(template).read_text());R=Path(m['root'])
 generated,files,delta=ns['render'](shard)
 for n,b in files.items():assert (generated/n).read_bytes()==b and (R/n).read_bytes()==b
 for n,r in m['files'].items():assert checked(r)==R/n
 inp=json.loads(checked(m['actual_input_ref']).read_text());assert inp['shard']==shard
 assert m['resources']['physical']==[6]and m['resources']['protected']==[0,1,2,3]
 rv=dict(schema='mxr.MAIN-context-successor-source-review/v1',decision='approve',prepared_template_ref=template,source_file_refs=m['files'],parent_source_ref=m['parent_source_ref'],context_repair_ref=m['context_repair_ref'],preparation_window_ref=m['preparation_window_ref'],resources=m['resources'],math_thresholds_unchanged=True,original97_tests_retained=True)
 rr=save(D/('MXR_S%d_MAIN_REVIEW.json'%shard),rv)
 au=dict(schema='mxr.MAIN-reviewed-context-successor-authority/v1',approved=True,preparation_window_ref=m['preparation_window_ref'],prepared_template_ref=template,source_root=str(R),outputs=m['outputs'],physical=[6],protected=[0,1,2,3],start_epoch=1792740953,cutoff_epoch=1792827353,resources=m['resources'],MAIN_review_ref=rr)
 ar=save(D/('MXR_S%d_MAIN_AUTHORITY.json'%shard),au)
 run('bind',['/usr/bin/python3','-I','-B',str(R/'prepare_successor.py'),'--bind','--template-ref',json.dumps(template),'--authority-ref',json.dumps(ar)],60,shard)
 cmds=json.loads((R/'COMMANDS.json').read_text())
 for stage,cap in [('audit',120),('cpu',630),('numeric',630)]:run(stage,cmds[stage],cap,shard)
 result=Path(m['outputs']['NPU'])/'RESULT.json';v=json.loads(result.read_text());assert v['primary']is None and v['secondary']==[]
 cleanup=json.loads(checked(v['cleanup']).read_text());assert cleanup['stopped']is True and cleanup['retained']is True and cleanup['errors']==[]
 print(json.dumps(dict(shard=shard,terminal=ref(result),qualification=False,model=False,performance=False,task=False)),flush=True)
