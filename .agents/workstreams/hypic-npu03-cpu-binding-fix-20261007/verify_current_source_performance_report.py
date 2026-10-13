#!/usr/bin/env python3
"""Read-only numerical/command replay for the current4429 scoped report.

Not a generic prose proof, HYPIC quality acceptance, or full Skill acceptance.
The manual obligation review is recorded separately in the case supplement.
"""
import hashlib
import json
import re
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REPORT = HERE / "HYPIC_CURRENT_SOURCE_PERFORMANCE_FINAL_20261013.md"
AGGREGATE = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/current4429-performance-20261013-audit.json")
AGG_SHA = "67ba6cf14fc9bed993acbdf421eb438f22d56957f3e56baad170a4bb871e53fe"
SOURCE = "4429e35177979c874bf053ab29789e4773f39b22"
ORDER = (("no-cache","screen"),("hypic-only","screen"),("hypic-only","repeat2"),
         ("no-cache","repeat2"),("no-cache","repeat3"),("hypic-only","repeat3"))
METRICS = (("Weighted TPOT (ms/token)","tpot_weighted_ms",1),
           ("TPOT P95 (ms/token)","tpot_p95_ms",1),
           ("TTFT P95 (s)","ttft_p95_ms",1000),
           ("Output throughput (token/s)","output_tokens_per_second",1),
           ("Batch duration (s)","benchmark_duration_s",1))

def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(text, header):
    lines = text.splitlines()
    require(lines.count(header) == 1, "table header missing or duplicated: "+header)
    i = lines.index(header)+2
    out=[]
    while i < len(lines) and lines[i].startswith("|"):
        out.append(lines[i]);i+=1
    return out

def review_text(text, a):
    require(a["source_commit"] == SOURCE and a["all_six_phases_valid"] is True,
            "campaign identity")
    require(a["quality_decision"] == "REJECT_OR_QUALIFY" and
            a["deployment_allowed"] is False, "quality boundary")
    require([(p["arm"],p["phase"]) for p in a["phases"]] == list(ORDER), "phase order")
    per = {arm:[p["metrics"] for p in a["phases"] if p["arm"]==arm]
           for arm in ("no-cache","hypic-only")}
    expected=[]
    for i,name in enumerate(("screen","repeat2","repeat3")):
        b,c=per["no-cache"][i],per["hypic-only"][i]
        expected.append(f"| {name} | {b['tpot_weighted_ms']:.4f} | {c['tpot_weighted_ms']:.4f} | {100*(c['tpot_weighted_ms']/b['tpot_weighted_ms']-1):.4f}% | {b['ttft_p95_ms']/1000:.4f} | {c['ttft_p95_ms']/1000:.4f} | {b['output_tokens_per_second']:.4f} / {c['output_tokens_per_second']:.4f} |")
    require(rows(text,"| Round | G1 TPOT ms | G2 TPOT ms | TPOT relative change | G1 TTFT P95 s | G2 TTFT P95 s | G1/G2 throughput token/s |")==expected,
            "per-round table mismatch")
    expected=[]
    for i,name in enumerate(("screen","repeat2","repeat3")):
        b,c=per["no-cache"][i],per["hypic-only"][i]
        expected.append(f"| {name} | {b['tpot_p95_ms']:.4f} | {c['tpot_p95_ms']:.4f} | {b['benchmark_duration_s']:.4f} | {c['benchmark_duration_s']:.4f} |")
    require(rows(text,"| Round | G1 TPOT P95 ms | G2 TPOT P95 ms | G1 batch duration s | G2 batch duration s |")==expected,
            "remaining per-round metrics missing or mismatched")
    expected=[]
    for label,key,scale in METRICS:
        b=[p[key]/scale for p in per["no-cache"]]
        c=[p[key]/scale for p in per["hypic-only"]]
        mb,mc=statistics.median(b),statistics.median(c)
        expected.append(f"| {label} | {statistics.mean(b):.4f} ± {statistics.stdev(b):.4f} | {statistics.mean(c):.4f} ± {statistics.stdev(c):.4f} | {mb:.4f} | {mc:.4f} | {100*(mc/mb-1):.4f}% |")
    require(rows(text,"| Metric | G1 mean ± sample SD | G2 mean ± sample SD | G1 median | G2 median | Median relative change |")==expected,
            "aggregate table mismatch")
    expected=[f"| {p['arm']}/{p['phase']} | {p['guard_samples']} | {p['result_sha256']} |"
              for p in a["phases"]]
    require(rows(text,"| Phase | Guard samples | arm-result SHA256 |")==expected,
            "receipt table mismatch")
    commands=re.findall(r"^TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py .*--action run$",text,re.M)
    require(commands==[f"TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm {arm} --phase {phase} --action run" for arm,phase in ORDER],
            "historical commands mismatch")
    require(sum(p["guard_samples"] for p in a["phases"])==1006, "guard count changed")
    require(a["strict_hot_coverage"]=={"verified":120,"expected":120,"decision":"PASS"},
            "activation changed")
    required = (SOURCE,AGG_SHA,"Fixed output1024","input32768","concurrency16",
                "240 scored responses and12 warmups","1006 continuous isolation",
                "All120 candidate scored requests","REJECT_OR_QUALIFY",
                "deployment_allowed=false","not a confidence interval",
                "No failed/excluded scored request","unrecorded transport retries",
                "No new profile","component-level saved-time cause unproven",
                "full independent tokenizer-byte",
                "driver/firmware/toolchain matrix is not established",
                "explicitly authorized this speed-only supplement",
                "not zeros or automatically satisfied requirements",
                "six-phase speed measurement, not all Paper-to-Ascend",
                "do not rerun completed roots","No additional performance or quality run",
                "No foreign task or physical4–7 was modified",
                "main/remote synchronization","23 regressions,15 improvements")
    for marker in required:
        require(marker in text,"claim boundary missing: "+marker)
    for marker in ("TBD","TODO","待补充","<measured>","<hash>","<exact"):
        require(marker not in text,"placeholder: "+marker)
    return {"report_tables":4,"historical_commands":6,"performance_phases":6,
            "quality_decision":"REJECT_OR_QUALIFY","new_device_work":False}

def main():
    pins={
      ".agents/skills/paper-to-ascend-reporting/SKILL.md":"7902b3f9c96ebd6b77a35b328333ad3834fe4a9f",
      ".agents/skills/paper-to-ascend-reporting/references/report-template.md":"40582e499b5589893524df3b74aabfeebe040f8c"}
    for path,blob in pins.items():
        require(subprocess.check_output(["git","rev-parse","origin/main:"+path],cwd=REPO,text=True).strip()==blob,
                "main reporting contract moved")
    require(sha(AGGREGATE)==AGG_SHA,"aggregate hash drift")
    a=json.loads(AGGREGATE.read_text())
    import current_source_performance_20261013 as c
    actual=[c.audit_one(*pair) for pair in ORDER]
    require([{k:v for k,v in p.items() if k!="normalized_spec"} for p in actual]==a["phases"],
            "independent phase audit drift")
    require(all(p["normalized_spec"]==actual[0]["normalized_spec"] for p in actual),"one-switch drift")
    for p in a["phases"]:
        root=Path(p["root"]); contract=json.loads((root/"contract.json").read_text())
        command=json.loads((root/"benchmark-command.json").read_text())
        argv=command["argv"]
        cfg=contract["benchmark_config"]
        for key in ("input_tokens","output_tokens","requests","concurrency","warmup_requests"):
            flag="--"+key.replace("_","-")
            require(argv.count(flag)==1 and argv[argv.index(flag)+1]==str(cfg[key]),
                    "benchmark command/contract drift: "+key)
        require(("--require-hot-path" in argv)==(p["arm"]=="hypic-only"),"benchmark activation option")
        for key in ("benchmark_sha256","request_id_adapter_sha256"):
            require(command[key]==contract[key],"benchmark byte identity drift")
        release=json.loads((root/p["arm"]/"service-stop.json").read_text())
        require(all(release[k] is True for k in ("container_removed","owned_npus_released","port_released")),
                "exact release not proved")
    result=review_text(REPORT.read_text(),a)
    result.update({"report_sha256":sha(REPORT),"aggregate_sha256":AGG_SHA,
                   "main_skill_blob":pins[".agents/skills/paper-to-ascend-reporting/SKILL.md"],
                   "scope":"Current4429 descriptive report only; historical r13 gaps unchanged",
                   "manual_review_not_replaced_by_text_markers":True})
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
