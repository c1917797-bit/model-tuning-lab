"""Submit one finite BOLE owner outside the AgentWeb service cgroup."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
P=Path("/opt/host/vnf/austinov/bole-g1-two-request-20261020T154710Z-v1")
ROOT=Path("/opt/host/vnf/austinov/bole-g1-owned-units-20261020T154710Z-v1")
SOURCE={"path":"/opt/host/vnf/austinov/bole-g1-two-request-20261020T154710Z-v1/SOURCE_BOUND.json","bytes":104107,"sha256":"845c1a86741a9b014e910256f847f45dd2dbbe0c81afec9abec07579fe6f1ca1"}
OUT="/opt/host/vnf/austinov/run-bole-g1-two-request-20261020T154710Z-v1"
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 ap=argparse.ArgumentParser();ap.add_argument("phase",choices=["cpu","model"]);a=ap.parse_args()
 assert ref(SOURCE["path"])==SOURCE
 ROOT.mkdir(exist_ok=True)
 unit="bole-g1-v1-"+a.phase+"-20261020t154710z"
 record=ROOT/(a.phase+"-SUBMITTED.json");assert not record.exists()
 args=["/usr/bin/systemd-run","--quiet","--unit="+unit,
  "--property=Type=exec","--property=RemainAfterExit=yes","--property=Restart=no",
  "--property=RuntimeMaxSec=3900","--property=TimeoutStopSec=180","--property=KillSignal=SIGTERM",
  "--property=CPUAffinity=166","--property=MemoryMax=512M",
  "--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab",
  "--property=StandardOutput=append:"+str(ROOT/(a.phase+".stdout")),
  "--property=StandardError=append:"+str(ROOT/(a.phase+".stderr")),
  "/usr/bin/env","BOLE_MODEL131_MAIN_ENABLE=1","DENSE090_EXTERNAL_OUTPUT_ENABLE=1",
  "/usr/bin/python3","-I","-B",str(P/"host_service.py"),"--execute"]
 if a.phase=="cpu":args+=["--cpu-only"]
 args+=["--source-ref",json.dumps(SOURCE),"--output",OUT+("-CPU"if a.phase=="cpu"else"")]
 assert not Path(OUT+("-CPU"if a.phase=="cpu"else"")).exists()
 r=subprocess.run(args,capture_output=True,text=True,timeout=30)
 event=dict(schema="bole.finite-owned-unit-submission/v1",unit=unit+".service",source=SOURCE,
  phase=a.phase,argv=args,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,
  phase_seconds=3600,cleanup_seconds=180,runtime_max_seconds=3900,
  restart="no",independent_of_agentweb=True,controller=ref(__file__))
 with record.open("x")as f:json.dump(event,f,sort_keys=True);f.write("\n")
 print(json.dumps(event))
 if r.returncode:raise SystemExit(r.returncode)
if __name__=="__main__":main()
