"""Stdlib-only graph-stage source and prior-eager admission."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
CANDIDATE = BASE.parent
PROJECT = CANDIDATE.parents[1]
REPO = PROJECT.parents[1]
FROZEN_TESTS = CANDIDATE / "tests"
PRIOR_RUNTIME_SHA = "e1cf89a658f389ff45f681ced2ff376a2ef4c66cbfbb61095194d9bc597a232a"
PRIOR_REPORT_SHA = "47c6120134ba788ff3e4a40f949aba1de9ae052726745437482a0bcbc3a71444"
PRIOR_LIBRARY_SHA = "ad6d01068d8cb122abc58da874dad5c4bd0dbd90402d30b5feb0155a86c92c8b"
GATE_CONTRACT_SHA = "b49b8113b77f2318d434fbca5beedbcc23b5a186b291e479c2cf1bd428b217a0"
STEPS, IDENTICAL_REPEATS, WARMUPS = 160, 8, 3
VARIANTS = ("SR1_perHv_permutations", "power2_perHv_permutations")
API_SOURCE = "projects/qwen36-deltalog/tools/deltalog_candidate_npu_probe.py"
API_SOURCE_SHA = "a0ea94634efc732f409a3f09cc7faf8fa2db07b8ab4da92a73352301371e9ef2"
METADATA_SOURCE = "projects/damp-ascend/tests/packed_recurrence_gate.py"
METADATA_SOURCE_SHA = "f3aff86e743cd40217ad19d1de383390fbbcb4ff30672893144d75c16009bf76"
OWN_NAMES = ("graph_contract.py", "graph_protocol.py", "run_graph_gate.py", "test_software_contract.py")

def require(value, message):
    if not value: raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text())

def old_contract():
    require(sha(FROZEN_TESTS/"gate_contract.py")==GATE_CONTRACT_SHA, "frozen gate contract drift")
    sys.path.insert(0, str(FROZEN_TESTS))
    import gate_contract
    require(Path(gate_contract.__file__).resolve()==(FROZEN_TESTS/"gate_contract.py").resolve(),
            "unexpected imported gate_contract")
    return gate_contract

def graph_source_bindings(args):
    old = old_contract()
    require(old.sha(args.runtime_manifest)==PRIOR_RUNTIME_SHA, "old runtime13 must remain frozen")
    bindings = old.source_bindings(args)
    require(bindings["library_sha256"]==PRIOR_LIBRARY_SHA, "only actual eager-correct production v3 SO admitted")
    path = old.checked_file(args.graph_runtime_manifest,args.graph_runtime_manifest_sha256)
    require(path==(BASE/"runtime_manifest.json").resolve(), "wrong NEW graph runtime manifest")
    manifest = read_json(path)
    names = {str((BASE/n).relative_to(REPO)) for n in OWN_NAMES}
    names.update((API_SOURCE,METADATA_SOURCE))
    require(manifest.get("schema")=="damp_integer_compaction_graph_runtime_v1" and
            set(manifest.get("sources",{}))==names, "exact graph6 separate runtime source set")
    for name,digest in manifest["sources"].items():
        p=(REPO/name).resolve()
        require(REPO in p.parents and sha(p)==digest, "graph dependency drift "+name)
    require(manifest["sources"][API_SOURCE]==API_SOURCE_SHA and
            manifest["sources"][METADATA_SOURCE]==METADATA_SOURCE_SHA, "graph API/metadata source identity")
    bindings["graph_runtime_sources"]=manifest["sources"]
    bindings["graph_runtime_manifest_sha256"]=sha(path)
    return bindings

def eager_admission(report, bindings):
    require(report.get("schema")=="damp_integer_compaction_npu_gate_v1" and
            report.get("status")=="restricted_numerical_pass" and
            report.get("namespace")=="qwen36_damp_integer_compaction_v1" and
            report.get("stage")=="restricted" and report.get("steps")==STEPS and
            report.get("matrix_class")=="full-160" and report.get("npu_executed") is True,
            "actual four-case160step restricted NPU acceptance required")
    require(report.get("limits")=={"state":1e-5,"output":0.00303} and
            report.get("versions",{}).get("actual_runtime_soc")=="Ascend910B4",
            "prior exact numerical limits/real SoC required")
    previous=report.get("bindings",{})
    for key in ("compiled_sources","runtime_sources","source_manifest_sha256",
                "runtime_manifest_sha256","build_receipt_sha256","library_sha256"):
        require(previous.get(key)==bindings.get(key), "prior eager/current binding mismatch "+key)
    expected={(b,v) for b in (1,16) for v in VARIANTS}
    seen=set()
    for case in report.get("cases",[]):
        key=(case.get("batch"),case.get("variant"))
        require(case.get("stage")=="restricted" and key in expected and key not in seen and
                case.get("status")=="passed" and len(case.get("steps",[]))==STEPS,
                "missing/duplicate/incomplete prior restricted case")
        for index,step in enumerate(case["steps"]):
            require(step.get("step")==index+1 and step.get("passed") is True and
                    step.get("guards") and all(x is True for x in step["guards"].values()),
                    "prior eager failed step/guard")
        seen.add(key)
    require(seen==expected, "all B1/B16 x SR1/power2 scopes required")
    return {"sha256":PRIOR_REPORT_SHA,"status":report["status"],"cases":len(seen),
            "scope":"restricted eager only; not general SR or graph acceptance"}

def metadata_cases(batch, slots):
    require(batch in (1,16) and slots==batch+3, "only admitted B1/B16 slots")
    good_lens=[0]+[1]*batch
    good_ids=list(range(batch))
    result=[]
    for label,value in (("prefix_nonzero",1),("prefix_negative",-1)):
        lens=list(good_lens); lens[0]=value
        result.append((label,lens,list(good_ids)))
    for label,value in (("zero_length",0),("multi_token_length",2),("negative_length",-1)):
        lens=list(good_lens); lens[-1]=value
        result.append((label,lens,list(good_ids)))
    for label,value in (("negative_slot",-1),("out_of_range_slot",slots),
                        ("int32max_slot",2147483647),("int32min_slot",-2147483648)):
        ids=list(good_ids); ids[-1]=value
        result.append((label,list(good_lens),ids))
    if batch==16:
        ids=list(good_ids); ids[-1]=ids[0]
        result.append(("duplicate_slots_last",list(good_lens),ids))
        result.append(("cumulative_lengths_not_native_ABI",list(range(batch+1)),list(good_ids)))
    return result

def semantic_metadata_valid(lens, ids, batch, slots):
    return (len(lens)==batch+1 and len(ids)==batch and lens[0]==0 and
            all(x==1 for x in lens[1:]) and len(set(ids))==batch and
            all(type(x) is int and 0<=x<slots for x in ids))

def validate_frozen_evidence(args, bindings):
    old=old_contract()
    p=old.checked_file(args.eager_report,PRIOR_REPORT_SHA)
    require(args.eager_report_sha256==PRIOR_REPORT_SHA, "pre-registered actual eager report hash only")
    admission=eager_admission(read_json(p),bindings)
    admission["path"]=str(p)
    return admission
