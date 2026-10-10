"""Fresh actual Devices[] input-plan+NumPy24 CLI closure; no Torch/native import."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import writer_contract as C
def run(expected,whole_ref,out):
    source=C.source(expected);C.need("torch"not in sys.modules and"torch_npu"not in sys.modules and
      not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),
      "actual Devices[] CPU before ANY NPU")
    out=Path(out);C.need(out.is_dir()and not(out/"CPU_RESULT.json").exists(),"actual existing unique CPU work")
    from writer_inputs import make_plan
    plan_dir=C.new_output(out/"plan");plan=C.publish(plan_dir/"INPUT_PLAN.json",make_plan(whole_ref,source))
    from numpy_preflight import run as parity
    numpy_ref=parity(expected,plan,out/"NUMPY_PREFLIGHT.json")
    return C.publish(out/"CPU_RESULT.json",dict(schema="skvq.actual-writer.cpu/v1",status="ACTUAL_INPUT_PLAN_NUMPY24_COMPLETE",
      source_ref=source,calibration_whole_ref=whole_ref,input_plan_ref=plan,numpy_ref=numpy_ref,Devices_empty=True,**C.scopes()))
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--calibration-whole-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.calibration_whole_ref_json and a.output,"actual descriptor/new owned work")
    print(json.dumps(run(a.source_manifest_sha256,json.loads(Path(a.calibration_whole_ref_json).read_bytes()),a.output),sort_keys=True))
if __name__=="__main__":main()
