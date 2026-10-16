"""Host-only counter observer. No runtime/model/algorithm hooks are installed."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import formal_r15_tp4 as controller
import independent_formal_workload as workload
from native_pdc_metrics import fetch_metrics,observe_full40
HERE=Path(__file__).resolve().parent
LOGGER="/vllm-workspace/vllm/vllm/v1/metrics/loggers.py"
LOGGER_SHA="ce2a0535d2b2b69e4368f34b692dac081be764e8d0eadab4f791b1afdcf43df4"
NAMES={"native_pdc_metrics.py","formal_pdc_metrics_tp4.py","audit_native_pdc_metrics_terminal.py"}

def check_contract(c):
    if (c.get("performance_group")not in ("G2","G4")
            or c.get("enable_prefix_caching")is not True
            or c.get("formal_performance")is not True
            or c.get("physical_npus")!=[0,1,2,3] or c.get("tp")!=4):
        raise ValueError("explicit nativePDC formal TP4 group required")
    spec=c.get("native_pdc_metrics",{})
    if spec.get("official_logger_sha256")!=LOGGER_SHA or set(spec.get("source_sha256",{}))!=NAMES:
        raise ValueError("prospective native counter observer binding required")
    for n,h in spec["source_sha256"].items():
        if hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=h:raise ValueError("observer source drift")
    if hashlib.sha256((HERE/"formal_r15_tp4.py").read_bytes()).hexdigest()!=c["controller_sha256"]:
        raise ValueError("unchanged controller identity required")

def run(c,contract_path):
    check_contract(c);original=workload.run_full40
    def observed(*args,**kwargs):
        raw=Path(c["raw_root"]);start=json.loads((raw/"service-start.json").read_text())
        cid=start["container_id"];meta=controller.inspect(cid)
        if (meta["Id"]!=cid or meta["Image"]!=c["image"]
                or meta["Config"]["Labels"].get("model-tuning-lab.task")!=c["task_id"]):
            raise ValueError("exact owned source target mismatch")
        actual=subprocess.check_output(["docker","exec",cid,"sha256sum",LOGGER],text=True,timeout=10).split()[0]
        if actual!=LOGGER_SHA:raise ValueError("actual official counter producer source drift")
        identity={"schema":"native-pdc-metrics/v1","container_id":cid,"image":c["image"],
                  "contract_sha256":hashlib.sha256(Path(contract_path).read_bytes()).hexdigest(),
                  "official_logger_sha256":actual,"observer_sources":c["native_pdc_metrics"]["source_sha256"],
                  "scope":"host-only pre/post full40 observation, no polling during original measured call"}
        return observe_full40(original,args,kwargs,fetch=lambda:fetch_metrics(c["port"]),
            guard=kwargs["guard"],save=lambda receipt:controller.write(raw,"native-pdc-observation.json",receipt),
            identity=identity)
    workload.run_full40=observed
    try:return controller.run_contract(c)
    finally:workload.run_full40=original

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--run",action="store_true");a=p.parse_args()
    c=json.loads(Path(a.contract).read_text());check_contract(c)
    if a.run:run(c,a.contract)
    else:print(json.dumps({"configuration_valid":True,"device_run":False}))
