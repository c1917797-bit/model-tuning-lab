"""MAIN bounded binding/audit/Devices[] execution of the reviewed revision4 only."""
import hashlib,json,subprocess,time
from pathlib import Path
W=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");R=W/'mxr48_complete_successor_prepare_v1/revision4/prepared-source'
D=W/'renew24_20261023T073553Z'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
T=dict(path=str(R/'SOURCE_TEMPLATE.json'),bytes=41781,sha256='90b84ad6833b67c361483774a991e398b87f980a47aebb36106752c8b3556aa0')
assert ref(Path(T['path']))==T
M=json.loads(Path(T['path']).read_text());review=D/'MXR_CTX4_MAIN_REVIEW.json'
rv=json.loads(review.read_text());assert rv['source_file_refs']==M['files'] and rv['prepared_template_ref']==T and rv['decision']=='approve'
a=dict(schema='mxr.MAIN-reviewed-context-successor-authority/v1',approved=True,preparation_window_ref=M['preparation_window_ref'],prepared_template_ref=T,source_root=str(R),outputs=M['outputs'],physical=[6],protected=[0,1,2,3],start_epoch=1792740953,cutoff_epoch=1792827353,resources=M['resources'],MAIN_review_ref=ref(review))
ar=save(D/'MXR_CTX4_MAIN_AUTHORITY.json',a)
records=[]
cmd=['/usr/bin/python3','-I','-B',str(R/'prepare_successor.py'),'--bind','--template-ref',json.dumps(T),'--authority-ref',json.dumps(ar)]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
records.append(dict(stage='bind',argv=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
save(D/'MXR_CTX4_ACTUAL_BIND.json',records[-1]);assert r.returncode==0,records[-1]
cmds=json.loads((R/'COMMANDS.json').read_text())
for stage,cap in [('audit',120),('cpu',620)]:
 cmd=cmds[stage];start=time.monotonic()
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=cap)
 record=dict(stage=stage,argv=cmd,returncode=r.returncode,elapsed=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr)
 rr=save(D/('MXR_CTX4_ACTUAL_'+stage.upper()+'.json'),record)
 print(json.dumps(dict(stage=stage,returncode=r.returncode,elapsed=record['elapsed'],record=rr,stderr_tail=r.stderr[-1800:])),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
print(json.dumps(dict(Devices=[],NPU=False,cpu_result=str(Path(M['outputs']['CPU'])/'RESULT.json'))))
