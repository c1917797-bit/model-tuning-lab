
"""Default-OFF read-only copy of two exact captured framework sources."""
import argparse,hashlib,json,os,resource,subprocess,time
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
ROOT=T/'gdn_matched_v5_installed_sources_v2'
DISC=dict(path=str(T/'GDN_MATCHED_V5_INSTALLED_SOURCE_DISCOVERY.json'),bytes=3416,sha256='f4b867e777e2931ece27f2926a2475dbe499e67a28ec32f97c80e7c1248dd3d9')
SR=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v5/SOURCE_BOUND.json',bytes=117604,sha256='f5308ea9d74e92293fd00a73f156a324fab064bfb2dcca3997728054deff4831')
RR=dict(path='/opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v5/RESULT.json',bytes=238251,sha256='8bad263436d441dd1e84d0147788bd9ff2d04ccf77cb86f55c8335e41d0b5bd0')
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
EXACT=[
 dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py',bytes=16312,sha256='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'),
 dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/solve_tril.py',bytes=14809,sha256='2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0')]
def need(v,s):
 if not v:raise ValueError(s)
def canonical_inspect(i):
 z=dict(i);rows=i['Mounts'];need(len({r['Destination']for r in rows})==len(rows),'complete unique mount destinations');z['Mounts']=sorted(rows,key=lambda r:r['Destination']);return z
def ref(p):
 p=Path(p);a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable whole source hash')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj(r):
 a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'whole exact Ref2/Ref3')
 return json.loads(Path(r['path']).read_bytes())
def put(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 return ref(p)
def child_unlimited():
 resource.setrlimit(resource.RLIMIT_AS,(resource.RLIM_INFINITY,resource.RLIM_INFINITY))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--controller-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false,"resources_admitted":false}');return 0
 need(a.controller_ref and json.loads(a.controller_ref)==ref(__file__),'exact reviewed metadata copy controller')
 os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'original Go child hard AS infinity');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 start=time.monotonic();d=obj(DISC);m=obj(SR);v=obj(RR)
 need(d['source']==SR and d['model_result']==RR and d['missing_count']==2 and d['missing_total_bytes']==31121 and[r['ref']for r in d['missing_exact_source_refs']]==EXACT and all(len(r['origins'])==8 and r['matching_host_readset_paths']==[]for r in d['missing_exact_source_refs']),'complete exact two all-four captured framework source projections')
 need(v['primary']is None and v['secondary']==[]and v['source_before']==v['source_after'],'actual completed original model')
 release_ref=v['summary']['model_release'];release=obj(release_ref);need(release['stopped']is True and release['retained']is True and release['errors']==[],'only original stopped-retained model owner')
 leaf=Path(release_ref['path']).parent;owned_ref=ref(leaf/'OWNED.json');own=obj(owned_ref);cid=own['cid']
 need(own['source']==SR and own['image']==IMAGE and cid==release['container'],'original source-owned image/CID')
 saved_after_ref=ref(release['after_inspect']['path']);saved=obj(saved_after_ref);original=json.loads(saved['stdout'])[0]
 def run(argv):
  remaining=600-(time.monotonic()-start);need(remaining>0,'one finite600 metadata copy clock')
  q=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=min(60,remaining),preexec_fn=child_unlimited)
  need(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss<=512*1024,'actual Go-child RSS remains within512MiB')
  need(q.returncode==0,'bounded readonly Docker copy/inspect completed '+q.stderr)
  return q
 def inspect():
  q=run(['/usr/bin/docker','inspect',cid]);need(len(q.stdout.encode())<=4*2**20,'complete inspect within4MiB, never truncate');items=json.loads(q.stdout);need(len(items)==1,'one exact original stopped container')
  i=items[0];s=i['State'];need(i['Id']==cid and i['Image']==IMAGE and s['Running']is False and s['Pid']==0 and s['OOMKilled']is False and not i.get('ExecIDs'),'actual stopped original owner PID0/noOOM/emptyExecIDs')
  for k in('Id','Image','State','Mounts','HostConfig','Config'):need(canonical_inspect(i)[k]==canonical_inspect(original)[k],'saved original owner metadata still exact '+k)
  return i,dict(bytes=len(q.stdout.encode()),sha256=hashlib.sha256(q.stdout.encode()).hexdigest())
 need(not ROOT.exists()and ROOT.parent==T,'exclusive new metadata source-copy leaf');before,before_wire=inspect();ROOT.mkdir(mode=0o700);rows=[]
 for index,wanted in enumerate(EXACT):
  name=('chunk'if index==0 else'solve_tril')+'_image_copy.txt';temporary=ROOT/(name+'.partial');final=ROOT/name
  q=run(['/usr/bin/docker','cp',cid+':'+wanted['path'],str(temporary)])
  need(temporary.is_file()and not temporary.is_symlink()and temporary.stat().st_size==wanted['bytes'],'exact single ordinary copied source size')
  r=ref(temporary);need(r['sha256']==wanted['sha256']and r['bytes']==wanted['bytes'],'captured all-four source whole-byte hash equals same stopped image copy')
  os.chmod(temporary,0o400);temporary.rename(final);host=ref(final);need(host['bytes']==wanted['bytes']and host['sha256']==wanted['sha256'],'frozen source bytes after mode/rename')
  rows.append(dict(guest_ref=wanted,host_ref=host,origins=d['missing_exact_source_refs'][index]['origins'],copy_argv=['/usr/bin/docker','cp',cid+':'+wanted['path'],str(temporary)],exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,content_equal=True))
 need(sum(r['host_ref']['bytes']for r in rows)==31121 and sum(p.stat().st_size for p in ROOT.iterdir())==31121,'exact31121 source bytes; no temporary copies remain')
 after,after_wire=inspect();need(canonical_inspect(after)==canonical_inspect(before),'complete original stopped container metadata unchanged across readonly copies')
 for r in rows:need(ref(r['host_ref']['path'])==r['host_ref'],'each frozen copy independently reopened')
 result=dict(schema='bole.GDN-matched-v5-exact-installed-source-projections/v1',controller_ref=ref(__file__),discovery_ref=DISC,source=SR,model_result=RR,image=IMAGE,original_owned_ref=owned_ref,original_model_release_ref=release_ref,original_after_inspect_ref=saved_after_ref,cid=cid,rows=rows,source_copy_bytes=31121,full_current_inspect_before=before_wire,full_current_inspect_after=after_wire,all_stopped_PID0_before_after=True,full_container_metadata_before_after_equal=True,actual_child_maxrss_KiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,elapsed=time.monotonic()-start,phase_seconds=600,source_files_byte_equal_to_all4_saved_framework_refs=True,container_started=False,container_exec_performed=False,container_created=False,resources_admitted=False,original_source_or_image_modified=False,mapped_ELF_identity_qualified=False,current_live_NPU_identity_reobserved=False,raw_numerical_replayed=False,model_ready=False,formal_success=False,NPU=False)
 rr=put(ROOT/'PROJECTIONS.json',result);print(json.dumps(dict(projection_ref=rr,source_copy_bytes=31121,rows=len(rows),stopped_original_unchanged=True,resources_admitted=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
