"""Bounded no-device observation of the failed002 historical mount replay only."""
import argparse,hashlib,json,os,resource,sys,time
from pathlib import Path
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit")
SOURCE=ROOT/"skvq-capture014-offline-consumer-v1-002"
SHA="cb2a944dfb04c152a5d488c55685ab97db6741bac6ea41b3c7a3b1c33300ae10"
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"NPU":False}));return
    start=time.monotonic()
    if os.environ.get("MAIN_SKVQ_OFFLINE_CPU_ENABLE")!="1":raise ValueError("explicit MAIN CPU opt-in")
    sys.path.insert(0,str(SOURCE))
    import cpu_host as H
    D=H.D
    D.need(time.time()+300<=D.CUT,"unchanged cutoff,300 includes180cleanup")
    source=D.source(SHA);D.original_modules(source)
    import previous_failure as F
    F.inspect()
    R=D.load("_skvq014_offline_cpu_resources",H.binding("resources.py"));R.helper()
    view=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(view["effective_cpus"])})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);D.need(hard==resource.RLIM_INFINITY,"Docker child hardAS")
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard))
    out=H.newroot(a.output);mounts=H.mount_set(out,source)
    Controller=H.control_class(source,R,mounts,H.mount_adapter());ctl=Controller(out)
    ctl.end=min(ctl.end,start+300);result=None
    guest = (
        "import sys,json;from pathlib import Path;"
        "sys.path.insert(0,"+repr(str(SOURCE))+");import offline_contract as D;"
        "source=D.source("+repr(SHA)+");D.original_modules(source);D.cpu_only();"
        "import mount_preflight as M;from previous_failure import HOST_REF;"
        "host=D.obj(HOST_REF);rows=[]\n"
        "for e in host['owned']:\n"
        " mounts={d:(s,bool(rw)) for d,(s,rw) in e['mounts'].items()}\n"
        " v=M.observe(mounts,e['phase'],D.CAPTURE)\n"
        " rows.append(dict(phase=e['phase'],passed=v['passed'],errors=v['errors'],training_passed=v['training']['passed'],mount_count=len(v['mounts'])))\n"
        "print(json.dumps(D.publish("+repr(str(out/"ACTUAL_MOUNT_REPLAY.json"))+",dict(schema='skvq.mount-replay-diagnostic/v1',rows=rows,source=source,Devices_empty=True,numerical_pass=False))),flush=True)\n"
    )
    try:
        H.charge_preflight(ctl,start)
        ctl.create("offline-consumer",False,2*H.GIB)
        cli=ctl.exec("consume-released014",["-c",guest],cap=110)
        result=dict(actual_cli_ref=cli,observation_ref=D.ref(out/"ACTUAL_MOUNT_REPLAY.json"))
    except BaseException as e:ctl.primary=e
    finally:
        try:ctl.cleanup()
        except BaseException as e:ctl.secondary.append(repr(e))
        value=dict(schema="skvq.mount-replay-owned-diagnostic/v1",diagnostic_source=D.ref(__file__),
          guest_program_sha256=hashlib.sha256(guest.encode()).hexdigest(),source=source,
          result=result,owned=ctl.owned,primary=repr(ctl.primary)if ctl.primary else None,
          secondary=ctl.secondary,elapsed=time.monotonic()-start,total_seconds=300,cleanup_included_seconds=180,
          actual_cleanup_seconds=ctl.cleanup_spent,Devices_empty=True,numerical_pass=False)
        print(json.dumps(D.publish(out/"DIAGNOSTIC_HOST_RESULT.json",value)),flush=True)
    if ctl.primary:raise ctl.primary
    D.need(not ctl.secondary and result is not None,"complete diagnostic/release required")
if __name__=="__main__":main()
