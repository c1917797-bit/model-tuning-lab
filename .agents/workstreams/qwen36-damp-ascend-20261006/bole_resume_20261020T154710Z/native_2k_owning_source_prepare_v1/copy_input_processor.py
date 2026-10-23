"""Explicit one-file copy from the exact own stopped-retained V7; no exec/start."""
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
CID='2e941d42dcc8c05bd1d16e2a84305b7181caa64f4914dc44b61c201a0b5f7bbe'
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
ORIGINAL=Path('/opt/host/vnf/austinov/run-bole-reduction-ON-v7-startup_20261022T215000Z')
SOURCE='/vllm-workspace/vllm/vllm/v1/engine/input_processor.py'
SHA='c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15'
DEST=HERE/'dependencies/input_processor.py'
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(ref(r['path'])==r,'whole historical Ref3');return json.loads(Path(r['path']).read_bytes())
def mounts(a):
 need(type(a)is list and len({m['Destination']for m in a})==len(a),'unique complete mount destinations')
 return {m['Destination']:m for m in a}
def call(argv):
 need(argv[:2]==['/usr/bin/docker','inspect']or argv[:2]==['/usr/bin/docker','cp'],'only narrow readonly inspect/copy')
 q=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
 need(q.returncode==0,'exact stopped owner operation failed: '+q.stderr[:1000])
 return dict(requested_argv=argv,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr)
def inspect(owner,saved):
 receipt=call(['/usr/bin/docker','inspect',CID]);rows=json.loads(receipt['stdout']);need(len(rows)==1,'one actual inspected own container');a=rows[0]
 need(a['Id']==owner['cid']==CID and a['Image']==owner['image']==IMAGE and a['Name']=='/'+owner['name'],'exact own historical CID/image/name')
 need(a['State']==saved['State']and a['State']['Pid']==0 and a['State']['Running']is False and a['State']['Status']=='exited'and a['State']['OOMKilled']is False,'same stopped retained owner, no new process')
 need(mounts(a['Mounts'])==mounts(saved['Mounts'])and a['Config']==saved['Config']and a['HostConfig']==saved['HostConfig'],'complete saved/current config/security/mount equality; order only normalized')
 need({m['Destination']:(m['Source'],m['RW'])for m in a['Mounts']}=={k:tuple(v)for k,v in owner['mounts'].items()},'all actual mounts match own source declaration')
 need(not any(SOURCE==m['Destination']or SOURCE.startswith(m['Destination'].rstrip('/')+'/')for m in a['Mounts']),'requested image-only source is not covered by a bind/volume override')
 return receipt,a
def run():
 need(DEST.parent.is_dir()and not DEST.exists()and not DEST.is_symlink(),'new unique dependency target; no overwrite')
 for p in(DEST.parent,*DEST.parent.parents):need(not p.is_symlink(),'ordinary source dependency directory')
 ownerref=ref(ORIGINAL/'dense/OWNED.json');cleanupref=ref(ORIGINAL/'dense/cleanup.json');resultref=ref(ORIGINAL/'RESULT.json')
 owner=obj(ownerref);cleanup=obj(cleanupref);result=obj(resultref)
 need(owner['source']==result['source']and cleanup['container']==CID and cleanup['stopped']is True and cleanup['retained']is True and cleanup['errors']==[],'same actual own source and stopped retained cleanup')
 obj(owner['source'])
 raw=Path(cleanup['after_inspect']['path']).read_bytes()
 need(hashlib.sha256(raw).hexdigest()==cleanup['after_inspect']['sha256'],'saved whole post-cleanup inspect hash')
 savedrecord=json.loads(raw);need(savedrecord['exit_code']==0 and savedrecord['requested_argv']==['/usr/bin/docker','inspect',CID],'saved actual inspect operation')
 saved=json.loads(savedrecord['stdout']);need(len(saved)==1,'one saved stopped owner')
 before,b=inspect(owner,saved[0])
 copied=call(['/usr/bin/docker','cp',CID+':'+SOURCE,str(DEST)])
 need(DEST.is_file()and not DEST.is_symlink()and ref(DEST)['sha256']==SHA,'copied exact whole input_processor bytes')
 after,a=inspect(owner,saved[0])
 need(a['State']==b['State']and mounts(a['Mounts'])==mounts(b['Mounts']),'copy never started/changed own owner')
 DEST.chmod(0o444)
 def summarize(r,inspected):
  body=r['stdout'].encode();return dict(requested_argv=r['requested_argv'],exit_code=r['exit_code'],stdout_bytes=len(body),stdout_sha256=hashlib.sha256(body).hexdigest(),
   actual_state=inspected['State'],actual_image=inspected['Image'],actual_cid=inspected['Id'],complete_saved_Config_HostConfig_equal=True,
   complete_unique_mounts_equal=True,mount_count=len(inspected['Mounts']))
 return dict(schema='native2k.actual-stopped-own-source-copy/v1',cid=CID,image=IMAGE,source_runtime_path=SOURCE,source_runtime_ref=dict(ref(DEST),path=SOURCE),host_copy_ref=ref(DEST),
  owner_ref=ownerref,cleanup_ref=cleanupref,result_ref=resultref,historical_source_ref=owner['source'],saved_after_inspect_ref=ref(cleanup['after_inspect']['path']),
  before=summarize(before,b),copy=copied,after=summarize(after,a),container_start_create_exec=False,NPU=False,new_authority=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--copy-source-only',action='store_true');a=p.parse_args()
 if not a.copy_source_only:print('{"enabled":false,"NPU":false}');return 0
 print(json.dumps(run(),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
