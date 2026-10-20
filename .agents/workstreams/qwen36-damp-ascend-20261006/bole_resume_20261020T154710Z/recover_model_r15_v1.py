"""Adopt an exact live BOLE container after control-plane owner loss.
Original operation terminal remains unknown; no duplicate model/server launch.
"""
import argparse,datetime,hashlib,json,math,os,resource,subprocess,sys,time,traceback
from pathlib import Path
P=Path("/opt/host/vnf/austinov/bole-model-fa64-fp16-20261020T154710Z-r15");sys.path.insert(0,str(P))
import contract090 as C,owned_ref131r7 as owned_ref
from owned_substrate import load
from owned_create import create
from worker_snapshot_owner import snapshot
OUT=Path("/opt/host/vnf/austinov/run-bole-model-fa64-fp16-20261020T154710Z-r15")
SR={"path":"/opt/host/vnf/austinov/bole-model-fa64-fp16-20261020T154710Z-r15/SOURCE_BOUND.json","bytes":75343,"sha256":"9fc47a77bdc82682273d4b484a026be2858ccac37c06b4a447fe76ca22939d8b"}
ORIGINAL_OPERATION="exec-00000000000019c8"
CID="c741f3460589aaf3158a883164cd248b869d27aca47ffec5e0847ccafe3aafe3"

def proc(pid):
 p=Path("/proc")/str(pid)
 try:
  text=(p/"stat").read_text();tick=int(text[text.rfind(")")+2:].split()[19])
  return dict(pid=pid,start_ticks=tick,cgroup=(p/"cgroup").read_text(),
              argv=[x.decode("utf8","strict") for x in (p/"cmdline").read_bytes().split(b"\0")if x])
 except (FileNotFoundError,ProcessLookupError):return None

class ExistingProcess:
 def __init__(self,identity):self.identity=identity;self.pid=identity["pid"];self.returncode=None
 def poll(self):
  now=proc(self.pid)
  if now is None:return "TERMINATED_EXIT_UNKNOWN"
  if(now["start_ticks"],now["cgroup"])!=(self.identity["start_ticks"],self.identity["cgroup"]):
   return "IDENTITY_CHANGED_EXIT_UNKNOWN"
  return None
 def wait(self,timeout):
  until=time.monotonic()+timeout
  while self.poll()is None:
   if time.monotonic()>=until:raise TimeoutError("owned prior server PID still present")
   time.sleep(.1)
  return None

def main():
 global c,S,H
 sr=SR;m=C.source(sr);import bind_model
 readset=bind_model.readset(sr)+m["dependencies"]
 controller_ref=C.ref(__file__)
 control=OUT/"recovery-controller-v1";control.mkdir(exist_ok=False)
 expected=json.loads((OUT/"dense/OWNED.json").read_text())
 C.need(expected["cid"]==CID and expected["source"]==sr,"exact original CID/source")
 for q in Path("/proc").iterdir():
  if q.name.isdigit():
   x=proc(int(q.name))
   if x and str(P/"host090.py")in x["argv"]:raise ValueError("original host controller still live; no parallel adoption")
 observations=sorted(q for q in (OUT/"dense").glob("observation-*.json")if "raw"not in q.name)
 C.need(observations,"original prelaunch observation required")
 original=C.obj(C.ref(observations[0]))
 old_parent=original["resources"]["host_cpu"]["process"]
 start=old_parent["start_ticks"]/os.sysconf("SC_CLK_TCK")
 C.need(0<time.monotonic()-start<3300,"original budget retained, no clock reset")
 os.sched_setaffinity(0,{166})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,"original host AS wrapper")
 resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 c,S,H,pairs=load(OUT);joint=H.Joint(start)
 cpu_cleanup=json.loads((OUT/"cpu-preflight/cleanup.json").read_text())
 C.need(cpu_cleanup["stopped"]and cpu_cleanup["retained"]and not cpu_cleanup["errors"],"original CPU owner released")
 gap=(OUT/"cpu-preflight/cleanup.json").stat().st_mtime-(OUT/"cpu-preflight/CPU-CHILD.json").stat().st_mtime
 prior_cleanup_charge=max(30,math.ceil(gap)+2)
 C.need(prior_cleanup_charge<150,"shared180 cleanup reserve remains")
 joint.cleanup_used=prior_cleanup_charge
 ctl=H.controller(S,joint)(argparse.Namespace(output_dir=OUT/"dense"),start)
 ctl.cid=CID;ctl.name=expected["name"];ctl.expected={k:v for k,v in expected.items()if k not in("create_receipt","sources")}
 ctl.source=expected["sources"];ctl.cpu=original["resources"]["cpu_allocation"];ctl.protected=original["protected0_3"]
 matches=[]
 for q in Path("/proc").iterdir():
  if q.name.isdigit():
   x=proc(int(q.name))
   if x and str(P/"server090.py")in x["argv"]and CID in x["cgroup"]:
    C.need("--source-ref"in x["argv"]and json.loads(x["argv"][x["argv"].index("--source-ref")+1])==sr,"exact prior server source argv")
    matches.append(x)
 C.need(len(matches)==1,"one exact original live server")
 server_identity=matches[0]
 btime=int(next(l.split()[1]for l in Path("/proc/stat").read_text().splitlines()if l.startswith("btime ")))
 ctl.server_started=datetime.datetime.fromtimestamp(btime+server_identity["start_ticks"]/os.sysconf("SC_CLK_TCK"),datetime.timezone.utc)
 ctl.server=ExistingProcess(server_identity);ctl.server_argv=["EXISTING-SERVER",str(server_identity["pid"])]
 owned=[ctl];summary={};primary=None;phase=dict(phase="recovery",step="adopt",ordinal=0)
 before={r["path"]:r["sha256"]for r in readset}
 a=argparse.Namespace(output=OUT)
 def mark(name,step):
  phase.update(phase=name,step=step,ordinal=phase["ordinal"]+1)
  if step in("client-terminal-receipt","independent-report-read","cleanup-close"):print(json.dumps(phase),flush=True)
 def child(owner,label,args,limit):
  return H.child(owner,label,args,limit,observe=owner.expected["arm"]!="cpu-preflight")
 def spawn(owner,args,label):
  argv=c.docker_argv(owner.cid,args)
  so=(owner.out/(label+".stdout")).open("x");se=(owner.out/(label+".stderr")).open("x")
  pr=subprocess.Popen(owner.wrapper(argv),stdout=so,stderr=se,cwd=c.ROOT);so.close();se.close();return pr,argv
 def close(owner):
  mark(owner.expected["arm"],"cleanup-close");r=owner.cleanup();owner._pair_closed=True
  v=c.obj(r);C.need(v["stopped"]and v["retained"]and not v["errors"],"exact recovered owned release")
  return r
 def ctl_for(role,cpu=False,extra=()):
  leaf=H.fresh_leaf(OUT/role);H.outputs(leaf);(leaf/"receipts").mkdir()
  owner=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start);owned.append(owner)
  owner.observe(role+"-admission",initial=True)
  create(c,S,owner,sr,[*readset,*extra],"cpu-preflight"if cpu else role,P)
  return owner
 try:
   current,ir=ctl.inspect()
   C.need(current["State"]["Running"]and not current["State"]["OOMKilled"],"original model owner still running")
   C.need(not(OUT/"dense/CLIENT-TERMINAL.json").exists()and not(OUT/"dense/HTTP_RESULT.json").exists(),"client not previously completed; never duplicate")
   adopted=C.write(control/"ADOPTION.json",dict(schema="bole.exact-live-owner-adoption/v1",controller=controller_ref,source=sr,
    original_operation=ORIGINAL_OPERATION,original_operation_status="not_found",original_exit=None,original_parent=old_parent,
    server=server_identity,inspect=ir,prior_cleanup_conservative_charge=prior_cleanup_charge,
    original_phase_start_monotonic=start,original_phase_deadline_monotonic=start+3600,kernel_boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip()))
   summary["adoption"]=adopted;print("ADOPTED "+json.dumps(adopted),flush=True)
   while True:
    C.need(ctl.server.poll()is None,"original server identity lost")
    ctl.observe("recovered-startup")
    argv=c.docker_argv(ctl.cid,["-c","import urllib.request;assert urllib.request.urlopen('http://127.0.0.1:8230/health',timeout=2).status==200"])
    r=ctl.h.run(ctl.wrapper(argv),min(4,ctl.remaining(cap=4)))
    c.write(control/("health-"+str(time.time_ns())+".json"),r)
    if r["exit_code"]==0:break
    time.sleep(1)
   from load_consumer114 import consume as consume_load
   mark('dense-startup','mtp-load-read');load_rows=[C.obj(owned_ref.file_ref(C,c,f))for f in sorted((ctl.out/'receipts').glob('MTP-LOAD-*.json'))]
   mark('dense-startup','mtp-load-consume');load_proof=consume_load(load_rows,report['actual_checkpoint_mtp_names'],m['installed_sources']['qwen_mtp'],m['files']['load_receipt111.py']);summary['MTP_load']=C.write(ctl.out/'MTP-LOAD-CONSUMPTION.json',load_proof)
   summary['MTP_load_receipts']=[owned_ref.file_ref(C,c,f)for f in sorted((ctl.out/'receipts').glob('MTP-LOAD-*.json'))]
   ctl.client,ctl.client_argv=spawn(ctl,[str(P/'smoke_client.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(ctl.out)],'model-smoke')
   until=time.monotonic()+min(900,ctl.remaining(cap=900))
   while ctl.client.poll()is None:
    mark('model-smoke','client-server-poll');C.need(ctl.server.poll()is None and time.monotonic()<until,'one bounded actual model smoke client');mark('model-smoke','protected-observation');ctl.observe('model-smoke');time.sleep(.2)
   mark('model-smoke','client-terminal-receipt');summary['actual_client_terminal']=C.write(ctl.out/'CLIENT-TERMINAL.json',dict(actual_argv=ctl.client_argv,exit_code=ctl.client.returncode,stdout=owned_ref.file_ref(C,c,ctl.out/'model-smoke.stdout'),stderr=owned_ref.file_ref(C,c,ctl.out/'model-smoke.stderr')))
   C.need(ctl.client.returncode==0,'actual HTTP client failed; preserved terminal/stdout/stderr precede all aggregate assertions')
   mark('model-smoke','worker-snapshot');rows,bindings=snapshot(c,ctl,ctl.out/'receipts','AFTER-MODEL')
   C.need(len(rows)==4 and all(v['schema']=='dense.native-worker-snapshot/v090'and v['source_ref']==sr and v['native_core']is v['native_inverse']is True and v['allow_hf32']is False for v in rows),'all4 actual restored native class/precision proof')
   C.need({v['pid']for v in rows}=={v['pid']for v in load_rows},'source-bound MTP loader and actual worker lifetimes')
   summary['worker_bindings']=C.write(ctl.out/'WORKER_BINDINGS.json',bindings)
   mark('model-smoke','rank-receipt-read');receiptroot=ctl.out/'receipts';ranks=[];calibration_readset=[]
   for rank in range(4):
    receipt=owned_ref.file_ref(C,c,receiptroot/('BOLE-TREE-RANK-%d.json'%rank));rv=c.obj(receipt)
    C.need(rv['rank']==rank and rv['source']==sr,'actual rank/source capture')
    C.checked(rv['raw']);ranks.append(dict(receipt=receipt,raw=rv['raw']))
    import model_calibration131r12 as MC
    MC.own_module(C,m,MC)
    oldabi=C.obj(m['actual118c']['capture'])['actual_device_abi_ref']
    cv=MC.validate(C,rv['model_calibration_ref'],oldabi,sr,rank)
    calibration_readset.extend([rv['model_calibration_ref'],*cv['rows'],*cv['before']])
   journals=[owned_ref.file_ref(C,c,p)for p in sorted(receiptroot.glob('IDENTITY-*.json'))]
   http_ref=owned_ref.file_ref(C,c,ctl.out/'HTTP_RESULT.json');http=C.obj(http_ref);response=C.obj(http['rows'][0]['response'])
   assignments=[C.obj(r)['event']for r in journals if C.obj(r)['role']=='frontend'and C.obj(r)['event']['before_request_id']==response['id']+'-0']
   C.need(len(assignments)==1,'one actual source-bound assignment event')
   import identity_owner
   mark('model-smoke','frontend-identity');frontend_binding=identity_owner.frontend(c,S,ctl,assignments[0])
   bundle=dict(schema='bole.actual-four-rank-model-inputs/v1',source=sr,http=http_ref,journal=journals,snapshots=rows,host_bindings=bindings,ranks=ranks,frontend_binding=frontend_binding)
   summary['model_release']=close(ctl)
   bundle['recovery_controller']=controller_ref
   bundle_ref=C.write(a.output/'RECOVERY-CONSUMER-INPUTS-v1.json',bundle)
   extra=[bundle_ref,bundle['http'],*journals,*[r for pair in ranks for r in pair.values()]]
   extra.extend(r['response']for r in C.obj(bundle['http'])['rows'])
   extra.extend(calibration_readset)
   consumer=ctl_for('cpu-consumer-recovery-v1',cpu=True,extra=extra)
   summary['independent_child']=child(consumer,'INDEPENDENT',[str(P/'consume_model.py'),'--execute','--source-ref',json.dumps(sr),'--inputs-ref',json.dumps(bundle_ref),'--output',str(consumer.out)],900)
   mark('consumer','independent-report-read');summary['independent']=owned_ref.file_ref(C,c,consumer.out/'ATTRIBUTION.json');value=c.obj(summary['independent'])
   C.need(value['source']==sr and value['diagnostic_complete']is True and value['component_checks_pass']is True and value['model_ready']is False and value['scheduler_committed']is False,'independent component gates and complete whole diagnostic, never model qualification')
   summary['independent_release']=close(consumer)
 except BaseException as error:
  primary=repr(error)
  C.write(control/"FIRST-FAULT.json",dict(error=primary,traceback=traceback.format_exc(),phase=phase,source=sr))
 finally:
  for owner in reversed(owned):
   if owner.cid and not getattr(owner,"_pair_closed",False):
    owner.primary=primary
    try:owner.cleanup()
    except BaseException as e:joint.secondary.append(repr(e))
   joint.secondary.extend(owner.secondary)
  after={}
  try:
   for r in readset:C.checked(r);after[r["path"]]=r["sha256"]
  except BaseException as e:joint.secondary.append("source-after "+repr(e))
  if joint.cleanup_used>180:joint.secondary.append("shared cleanup180 exceeded")
  joint.secondary.extend(S.formal_time_failures(joint.deadline))
  result=dict(schema="bole.recovered-model-component-stage/v1",source=sr,controller=controller_ref,
   original_operation=ORIGINAL_OPERATION,original_exit=None,original_result_missing=not(OUT/"RESULT.json").exists(),
   primary=primary,secondary=joint.secondary,summary=summary,source_before=before,source_after=after,
   cleanup_charge_seconds=joint.cleanup_used,phase_start_monotonic=start,phase_deadline_monotonic=start+3600,
   model_ready=False,scheduler_committed=False,formal_performance=False,task_accuracy=False)
  rr=C.write(control/"RESULT.json",result);print("RECOVERY_RESULT "+json.dumps(rr),flush=True)
 return 3 if primary or joint.secondary or before!=after else 0
if __name__=="__main__":raise SystemExit(main())
