"""DEFAULT OFF same-image Devices[] preflight: actual23 CLI tests and actual TRAIN builder.
Only MAIN-owned host dispatch runs this file. No NPU or model launch here.
"""
import argparse,ast,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
HERE=Path(__file__).resolve().parent
ORDER=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-tp4-qkv-loader-order-v1-001")
sys.path.insert(0,str(BASE))
from io_contract import require,publish_json,reference
def run(out):
    require(not list(Path("/dev").glob("davinci*")) and not any(Path("/dev",x).exists() for x in ("devmm_svm","hisi_hdc")),"actual Devices[] all compute/control nodes absent")
    require(os.environ.get("MAIN_SKVQ_CPU_ENABLE")=="1","explicit MAIN CPU only opt-in")
    out=Path(out);results=[]
    import current_contract as C
    C.configure(os.environ["SKVQ_CURRENT_MANIFEST_SHA256"])
    source=C.source()
    depcmd=[sys.executable,"-I","-B",str(HERE/"input_dependency.py"),"--execute","--source-manifest-sha256",source["sha256"],"--output",str(out/"INPUT_DEPENDENCY.json")]
    depchild=subprocess.run(depcmd,capture_output=True,text=True,timeout=120,cwd=HERE)
    publish_json(out/"INPUT_DEPENDENCY_CLI.json",dict(argv=depcmd,exit_code=depchild.returncode,stdout=depchild.stdout,stderr=depchild.stderr))
    require(depchild.returncode==0,"actual source-bound dependency/all9-first-record preflight before build/NPU")
    depref=reference(out/"INPUT_DEPENDENCY.json")
    publish_json(out/"INPUT_DEPENDENCY_REF.json",depref)
    for p in Path(__file__).resolve().parent.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
    for root,name,want in ((HERE,"SOFTWARE_TESTS_15.py",15),(ORDER,"SOFTWARE_TESTS.py",8)):
        for p in root.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
        cmd=[sys.executable,"-B",str(root/name)]
        start=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=90,cwd=root)
        r=dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed=time.monotonic()-start,source=reference(root/name))
        publish_json(out/("TESTS-"+str(want)+".json"),r)
        require(p.returncode==0 and ("Ran "+str(want)+" tests") in p.stderr,"actual CLI full expected test count; no planned PASS")
        results.append(r)
    require("torch" not in sys.modules and "torch_npu" not in sys.modules,"stdlib software parent")
    publish_json(out/"ACTUAL23.json",dict(status="ACTUAL23_CLI_SOFTWARE_ONLY",total=23,results=results,native_ready=False))
    cmd=[sys.executable,"-I","-B",str(HERE/"input_entry.py"),"--execute","--source-manifest-sha256",source["sha256"],"--dependency-ref-json",str(out/"INPUT_DEPENDENCY_REF.json"),"--output",str(out/"run-skvq-train-inputs-001-main")]
    env=dict(os.environ,QWEN36_SKVQ_INPUT_BUILD_ENABLE="1",ASCEND_RT_VISIBLE_DEVICES="")
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=480,env=env,cwd=BASE)
    publish_json(out/"INPUT_BUILDER_CLI.json",dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
    require(p.returncode==0,"actual nine TRAIN/hash/tokenizer builder; retain failure, no download/retry")
    cmd=[sys.executable,"-B",str(BASE/"consume_inputs.py"),"--input",str(out/"run-skvq-train-inputs-001-main/INPUTS.json"),"--output",str(out/"INPUTS_CONSUMED.json")]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=120,cwd=BASE)
    publish_json(out/"INPUT_CONSUMER_CLI.json",dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
    require(p.returncode==0,"actual independent token byte/source consumer")
    # Only actual declared SchedulerConfig here: ModelConfig registry and full config touch HAL.
    import engine_config
    config=publish_json(out/"ACTUAL_ENGINE_CONFIG.json",engine_config.construct())
    import rpc_extension as rpc
    rpc_ref=publish_json(out/"ACTUAL_RPC_PREFLIGHT.json",rpc.preflight(source))
    return publish_json(out/"CPU_COMPLETE.json",dict(actual_named_rpc_preflight_ref=rpc_ref,input_dependency_ref=depref,actual_engine_config=config,status="ACTUAL23_AND_REAL_TRAIN_INPUTS_CONSUMED",actual23=reference(out/"ACTUAL23.json"),inputs=reference(out/"run-skvq-train-inputs-001-main/INPUTS.json"),consumer=reference(out/"INPUTS_CONSUMED.json"),model_launched=False,native_ready=False))
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,model_launched=False,native_ready=False)));return
    require(a.output,"explicit host-created phase directory");print(json.dumps(run(a.output)))
if __name__=="__main__":main()
