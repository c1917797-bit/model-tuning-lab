#!/usr/bin/env python3
"""Postbind unchanged one-pair lifecycle/E2E screen to the NEW all-T prerequisite."""
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
import contract as c

def check_bindings(arms,identities,checked_ref,inputs):
    for name in ("dense","candidate"):
        arm=arms[name];ir=identities[name]["ref"];ident=identities[name]["value"]
        c.require(arm.get("schema")=="kvbp.service-arm/v1" and arm.get("arm")==name and
                  arm.get("prepare_only") is False and arm.get("identity_sha256")==ir["sha256"] and
                  ident.get("evidence",{}).get("all_T_kernel_prerequisite")==checked_ref,
                  "both actual ARM/identity raw bytes bind same NEW all-T prerequisite")
        c.require(arm.get("checked_split_prerequisite")==inputs["split_checked"]["checked"] and
                  arm.get("consumer_source_manifest")==inputs["split_manifest"] and
                  arm.get("native_gate_kind")=="split-kernel-prerequisite" and
                  arm.get("formal_performance_authorized") is False and
                  arm.get("task_accuracy_verified") is False,"old split labels/scopes not rewritten")
    c.require(identities["dense"]["ref"]!=identities["candidate"]["ref"],"fresh independent identities for sequential TP4 arms")

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--enable",action="store_true")
    for n in ("packet","inputs","checked","dense-identity","candidate-identity"):
        p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
    for n in ("dense-arm","candidate-arm","dense-client","candidate-client","old-pair-output","output"):
        p.add_argument("--"+n)
    a=p.parse_args(argv)
    if not a.enable:
        print(json.dumps(dict(status="OFF",launches_npu=False,formal_performance_authorized=False)));return 0
    c.require(os.environ.get("KVBUFFER_ALL_T_DIAGNOSTIC")=="1","explicit MAIN diagnostic screen opt-in")
    names=("packet","inputs","checked","dense_identity","candidate_identity")
    c.require(all(getattr(a,n) and getattr(a,n+"_sha256") for n in names) and
              all(getattr(a,n) for n in ("dense_arm","candidate_arm","dense_client","candidate_client","old_pair_output","output")),
              "all original prerequisite/identity/arm/client outputs")
    refs={n:dict(path=getattr(a,n),sha256=getattr(a,n+"_sha256")) for n in names}
    inputs=c.obj(refs["inputs"]);checked=c.validate_complete(inputs,refs["packet"],enabled=True)
    checked["input_ref"]=refs["inputs"]
    c.require(c.obj(refs["checked"])==checked,"original all-T prerequisite replay")
    packet,_=c.sources(refs["packet"]);before=dict(packet["dependencies"])
    arms={k:c.obj(c.actual_ref(Path(getattr(a,k+"_arm"))/"ARM.json")) for k in ("dense","candidate")}
    ids={k:dict(ref=refs[k+"_identity"],value=c.obj(refs[k+"_identity"])) for k in ("dense","candidate")}
    check_bindings(arms,ids,refs["checked"],inputs)
    output=Path(a.output);oldout=Path(a.old_pair_output)
    c.require(not output.exists() and not oldout.exists() and output.parent==oldout.parent and
              Path("/kvbuffer-results") in output.resolve().parents,"new distinct bounded pair outputs, no overwrite")
    compare=c.PROJECT/"tools/service/compare.py"
    c.require(c.digest(c.read_file(str(compare)))==before[str(compare)],"original comparison source")
    command=[sys.executable,"-B",str(compare)]
    for k in ("dense_arm","candidate_arm","dense_client","candidate_client"):
        command+=["--"+k.replace("_","-"),getattr(a,k)]
    command+=["--output",str(oldout)]
    streams={n:output.with_name(output.name+"."+n) for n in ("stdout","stderr")}
    original_error=None;returncode=None
    try:
        with streams["stdout"].open("xb") as out,streams["stderr"].open("xb") as err:
            r=subprocess.run(command,cwd=str(c.ROOT),stdout=out,stderr=err,check=False)
        returncode=r.returncode
        c.require(returncode==0,"original comparison subprocess failed; retain raw report/streams")
        pair=c.obj(c.actual_ref(oldout))
        c.require(pair.get("schema")=="kvbp.same-eager-pair/v1" and
                  pair.get("status")=="matched_screen_complete" and pair.get("rounds")==1 and
                  pair.get("quality_evaluated") is False and pair.get("graph_service_validated") is False,
                  "actual unchanged complete one-pair lifecycle screen, not final acceptance")
        c.require(all(c.digest(c.read_file(p))==h for p,h in before.items()),"source drift after actual pair consumer")
        result=dict(schema="kvbp.all-T-bound-P1-screen/v1",status="actual_pair_bound_to_all_T_kernel_prerequisite",
                    prerequisite=refs["checked"],input_ref=refs["inputs"],source_packet=refs["packet"],
                    old_pair=c.actual_ref(oldout),identities={k:ids[k]["ref"] for k in ids},
                    arm_reports={k:c.actual_ref(Path(getattr(a,k+"_arm"))/"ARM.json") for k in arms},
                    original_command=command,returncode=returncode,
                    stdout=c.actual_ref(streams["stdout"]),stderr=c.actual_ref(streams["stderr"]),
                    rounds=1,component_batches=list(range(1,17)),legacy_report_rewritten=False,
                    source_after=before,scope="P1 actual lifecycle/performance screen; not three-round or quality acceptance")
        result.update({k:False for k in c.FALSE_SCOPE})
        c.write_new(output,result);print(json.dumps(dict(report=c.actual_ref(output),service_ready=False)));return 0
    except BaseException as primary:
        original_error=repr(primary)
        try:
            c.write_new(output.with_name(output.name+".failure.json"),
                        dict(original_error=original_error,command=command,returncode=returncode,
                             stdout=None if not streams["stdout"].exists() else c.actual_ref(streams["stdout"]),
                             stderr=None if not streams["stderr"].exists() else c.actual_ref(streams["stderr"]),
                             old_pair=None if not oldout.exists() else c.actual_ref(oldout),no_retry=True,
                             service_ready=False))
        except BaseException as secondary:print("KVBP_PAIR_SECONDARY "+repr(secondary),file=sys.stderr)
        raise
if __name__=="__main__":raise SystemExit(main())
