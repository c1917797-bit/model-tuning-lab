"""R18 full40 timed audit; numerical Canary is a separate immutable prerequisite."""
import json,hashlib
from pathlib import Path
from audit_r18_terminal_base import audit_r18_base as audit_full40
from audit_r16_performance import validate_timed_mode
from audit_r17_transfer_performance import validate_transfer_mode

def audit_timed_partition(events,manifest,*,enabled):
    forbidden={"c1_packed_wave_shadow_checked","c1_first_divergence_capture",
               "c1_private_material_transfer_verified","prompt_snapshot_opportunity",
               "native_decode_batch_shadow_checked"}
    if any(e.get("event")in forbidden for e in events):
        raise ValueError("diagnostic overhead present in timed arm")
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    groups=[e for e in events if e.get("event")=="c1_packed_wave_prepared"]
    done=[e for e in events if e.get("event")=="compact_gdn_body_composed"]
    if not enabled:
        if installs or groups or done:raise ValueError("algorithm event in native arm")
        return dict(enabled=False,groups=0,completed=0)
    if len(installs)!=4 or len({e.get("pid") for e in installs})!=4 or any(
            e.get("manifest_sha256")!=manifest or e.get("c1_partitioned_render")is not True
            or e.get("c1_performance_mode")is not True or e.get("c1_first_divergence")is not False
            or e.get("c1_layer_shadow_validation")is not False for e in installs):
        raise ValueError("exact four-worker timed partition installation required")
    pids={e["pid"] for e in installs};rank_pids={};selected={}
    def identity(e):
        rank=e.get("rank");pid=e.get("pid")
        if (type(rank)is not int or not 0<=rank<4 or pid not in pids
                or e.get("manifest_sha256")!=manifest or type(e.get("step"))is not int
                or e["step"]<=0 or not isinstance(e.get("layer"),str)):
            raise ValueError("actual timed rank/PID/source/step/layer required")
        if rank in rank_pids and rank_pids[rank]!=pid:raise ValueError("worker mapping drift")
        rank_pids[rank]=pid
        return rank,pid,e["step"],e["layer"]
    for e in groups:
        key=identity(e)
        if key in selected:raise ValueError("duplicate partition group")
        if (e.get("state_schedule")!="partitioned" or type(e.get("state_passes"))is not int
                or e["state_passes"]not in (1,2) or e.get("actual_slot_commit")!="not_started"):
            raise ValueError("actual partition schedule required")
        if any(type(e.get(k))is not int or e[k]<1 for k in
               ("windows","packed_tokens","state_window_visits","state_token_visits")):
            raise ValueError("strict partition counts required")
        if e["windows"]!=e["state_window_visits"] or e["packed_tokens"]!=e["state_token_visits"]:
            raise ValueError("repeated or missing live window/token")
        ids=e.get("requests",[])
        if not ids or len(set(ids))!=len(ids):raise ValueError("unique actual group IDs required")
        selected[key]=set(ids)
    for e in done:
        key=identity(e)
        if e.get("request_id")not in selected.get(key,set()) or e.get("finite")is not True:
            raise ValueError("completed request not joined to exact partition")
    if set(rank_pids)!=set(range(4)) or len(set(rank_pids.values()))!=4 or not done:
        raise ValueError("complete actual four-worker partition proof required")
    return dict(enabled=True,groups=len(groups),completed=len(done),workers=rank_pids)

def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());base=cp.parent
    report=audit_full40(cp,live_release=live_release)
    mp=base/c["successor_manifest"];mh=hashlib.sha256(mp.read_bytes()).hexdigest()
    cfg=json.loads((base/json.loads(mp.read_text())["config"]).read_text())
    validate_timed_mode(c,cfg)
    mode=validate_transfer_mode(c,cfg)
    sources=c.get("baseline_host_source_sha256") or c.get("cache_diagnostic",{}).get("source_sha256",{})
    if sources.get(c["successor_manifest"])!=mh:
        raise ValueError("common timed manifest binding absent")
    enabled=c["performance_group"]=="G3"
    if cfg.get("c1_partitioned_render")is not enabled:raise ValueError("timed arm partition configuration mismatch")
    events=[]
    for p in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
        events.extend(json.loads(x) for x in p.read_text().splitlines())
    if enabled and c["cache_diagnostic"]["compact_manifest"]!=c["successor_manifest"]:
        raise ValueError("different active timed manifest")
    for e in events:
        if e.get("event")=="compact_hypic_hooks_installed" and (
                e.get("c1_async_material_transfer")is not (mode=="async")
                or e.get("c1_async_material_verify")is not False
                or e.get("prefill_prompt_snapshot")is not True
                or type(e.get("prompt_snapshot_probe_batches"))is not int
                or e["prompt_snapshot_probe_batches"]!=0):
            raise ValueError("worker timed transfer/snapshot mode mismatch")
    report["partition"]=audit_timed_partition(events,mh,enabled=enabled)
    report["scope"]="one R18 full40 timed arm; matched/repeated performance,fullquality,lifecycle separate"
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))
