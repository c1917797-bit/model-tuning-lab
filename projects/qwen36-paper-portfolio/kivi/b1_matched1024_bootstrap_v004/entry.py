"""Read-only plan for the explicit MAIN-owned common host. No controller here."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import screen_contract as c
def plan(output,port,run):
 output=Path(output)
 c.need(output.is_absolute()and not output.exists()and ".."not in output.parts,"new independent screen parent")
 dense=c.native_argv(port,"kivi_firstdecode_bootstrap.FirstDecodeWorker")
 candidate=c.native_argv(port,"kivi_firstdecode_bootstrap.FirstDecodeWorker")
 c.matched_argv(dense,candidate)
 return dict(schema="kivi.b1-matched1024-preparation/v1",common=c.COMMON,protocol=c.PROTOCOL,algorithm_delta=c.ALGORITHM_DELTA,
  input_digest=__import__("hashlib").sha256(c.canonical(c.prompt())).hexdigest(),
  stages=[dict(arm=arm,output=str(output/arm),budget=c.BUDGET,native_argv=argv,
   algorithm_env={"QWEN36_KIVI_SCREEN_ARM":arm},requests=c.rows(run))for arm,argv in(("dense",dense),("candidate",candidate))],
  producer_prerequisite=c.PRODUCER,whole_source=c.WHOLE,raw_source=c.RAW,
  execution_available=True,required_runtime_binding="host_run.py requires exact own software-stage plus actual018 whole/raw originals",
  C16_verified=False,FULL_verified=False,performance_accepted=False,model_ready=False,run_authority=False)
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--plan",action="store_true");p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250)
 p.add_argument("--run",default="screen001");p.add_argument("--predecessor-arguments",type=Path)
 a=p.parse_args(argv)
 if not(a.execute or a.plan):print(json.dumps(dict(enabled=False,NPU=False,run_authority=False)));return 0
 c.need(a.output is not None,"explicit new independent output")
 result=plan(a.output,a.port,a.run)
 if a.execute:
  c.need(a.predecessor_arguments is not None,"actual018 whole/raw original arguments required before any device action")
  from screen_predecessor import replay
  replay(json.loads(a.predecessor_arguments.read_bytes()))
  raise ValueError("Use the explicit MAIN-owned host_run.py command and fresh actual resource admission; this plan never launches")
 print(json.dumps(result,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
