#!/usr/bin/env python3
"""Stdlib-only graph/metadata source contract; never imports Torch or dispatches."""
import ast
import copy
import json
from pathlib import Path
from graph_contract import (BASE, STEPS, IDENTICAL_REPEATS, WARMUPS, VARIANTS,
    metadata_cases,semantic_metadata_valid,eager_admission,require,PRIOR_LIBRARY_SHA)

def main():
    checks=[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    for name in ("graph_contract.py","graph_protocol.py","run_graph_gate.py",__file__):
        p=Path(name) if Path(name).is_absolute() else BASE/name
        ast.parse(p.read_text())
        check("AST_"+p.name,True)
    text=(BASE/"graph_protocol.py").read_text()
    tree=ast.parse(text)
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    capture=ast.unparse(functions["capture_one"])
    withs=[n for n in ast.walk(functions["capture_one"]) if isinstance(n,ast.With)]
    check("one_explicit_capture_context",len(withs)==1)
    capture_calls=[ast.unparse(n.func) for n in ast.walk(withs[0]) if isinstance(n,ast.Call)]
    check("capture_only_graph_and_decode",set(capture_calls)=={"torch.npu.graph","candidate.decode"})
    check("capture_no_prepare_H2D_or_oracle",
          not any(x in capture for x in ("candidate.prepare","native_step","torch.tensor","copy_(")))
    replay=ast.unparse(functions["replay"])
    check("replay_sync_before_dispatch",replay.index("torch.npu.synchronize()")<replay.index("graph.replay()"))
    copying=ast.unparse(functions["_copy"])
    check("copies_followed_by_sync",copying.index("dst.copy_(src)")<copying.index("torch.npu.synchronize()"))
    case=ast.unparse(functions["graph_case"])
    check("separate_warmup_arena","warm = [nd(getattr(initial, n))" in case)
    check("eight_reset_identical_repeats",IDENTICAL_REPEATS==8 and "range(IDENTICAL_REPEATS)" in case)
    check("160_changed_own_feedback",STEPS==160 and "golden = evidence['packed']" in case)
    check("three_warmups_checked",WARMUPS==3 and "'warmup_' + str(i + 1) + '_numerical_guard'" in case)
    for node in ast.walk(tree):
        if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            check("no_ops_reassignment_"+str(node.lineno),
                  all("torch.ops" not in ast.unparse(t) for t in targets))
    for batch,count in ((1,9),(16,11)):
        slots=batch+3
        negatives=metadata_cases(batch,slots)
        check("negative_count_B"+str(batch),len(negatives)==count)
        check("negative_labels_unique_B"+str(batch),len({x[0] for x in negatives})==count)
        check("valid_metadata_B"+str(batch),semantic_metadata_valid([0]+[1]*batch,list(range(batch)),batch,slots))
        for label,lens,ids in negatives:
            check("negative_semantic_"+str(batch)+"_"+label,
                  not semantic_metadata_valid(lens,ids,batch,slots))
            check("negative_shape_"+str(batch)+"_"+label,len(lens)==batch+1 and len(ids)==batch)
    for batch in (0,2,15,17):
        try:metadata_cases(batch,batch+3)
        except ValueError:check("unsupported_B"+str(batch),True)
        else:check("unsupported_B"+str(batch),False)
    invalid=ast.unparse(functions["invalid_turn"])
    check("malformed_full_state_unchanged","(5, 6, 7)" in invalid and "complete_state_bitwise_unchanged" in invalid)
    check("malformed_all_inputs_unchanged","every_input_bitwise_unchanged" in invalid)
    check("malformed_NaN_output_guard","torch.isnan(cpu_output).all()" in invalid)
    check("raw_evidence_precedes_assert","observe(gate, label, dispatch, args)" in invalid)
    check("no_candidate_seeded_golden","golden = initial.clone()" in case and "golden = cpu_packed" not in text)
    # A pure synthetic receipt tests validators; it is NOT a NPU report.
    bindings={k:"fixture_"+k for k in ("compiled_sources","runtime_sources","source_manifest_sha256",
        "runtime_manifest_sha256","build_receipt_sha256","library_sha256")}
    report={"schema":"damp_integer_compaction_npu_gate_v1","status":"restricted_numerical_pass",
        "namespace":"qwen36_damp_integer_compaction_v1","stage":"restricted","steps":160,
        "matrix_class":"full-160","npu_executed":True,"limits":{"state":1e-5,"output":0.00303},
        "versions":{"actual_runtime_soc":"Ascend910B4"},"bindings":bindings,"cases":[]}
    for batch in (1,16):
        for variant in VARIANTS:
            report["cases"].append({"batch":batch,"variant":variant,"stage":"restricted","status":"passed",
                "steps":[{"step":i+1,"passed":True,"guards":{"immutable":True}} for i in range(160)]})
    check("synthetic_admission_validator",eager_admission(report,bindings)["cases"]==4)
    bads=[]
    for key,value in (("status","failed"),("npu_executed",False),("steps",159),("stage","general")):
        r=copy.deepcopy(report);r[key]=value;bads.append((key,r))
    r=copy.deepcopy(report);r["cases"].pop();bads.append(("missing_case",r))
    r=copy.deepcopy(report);r["cases"].append(copy.deepcopy(r["cases"][0]));bads.append(("duplicate",r))
    r=copy.deepcopy(report);r["cases"][0]["steps"][45]["guards"]["immutable"]=False;bads.append(("guard",r))
    r=copy.deepcopy(report);r["bindings"]["library_sha256"]="wrong";bads.append(("library",r))
    r=copy.deepcopy(report);r["limits"]["state"]=1e-4;bads.append(("threshold",r))
    for label,r in bads:
        try:eager_admission(r,bindings)
        except ValueError:check("bad_admission_"+label,True)
        else:check("bad_admission_"+label,False)
    primary=(BASE/"run_graph_gate.py").read_text()
    check("audit_before_torch_import",primary.index("if args.audit_only:")<primary.index("import torch\n"))
    check("no_graph_autofallback","silent eager substitute" in primary and "DAMP_RUN_GRAPH_GATE_V1" in primary)
    print(json.dumps({"schema":"damp_graph_gate_software_v1","status":"pass","checks":len(checks),
        "check_names":checks,"npu_executed":False,"graph_supported":False,
        "scope":"stdlib AST/admission/metadata checks only; not actual capture or NPU evidence"}))
if __name__=="__main__":main()
