"""Devices[] CPU145 import diagnostic only. Never full software qualification."""
import argparse
import json
import os
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_namespace as N
ENTRY_ENV={k:os.environ.get(k)for k in N.TOKENIZER_ENV}
ENTRY_MODULES=sorted(k for k in sys.modules if k.split('.')[0]in{'torch','torch_npu','transformers','tokenizers','vllm','vllm_ascend','triton'})
# Also set the same explicit profile before any subsequent source/helper import.
# Original Docker config MUST already have supplied these before Python startup.
os.environ.update(N.TOKENIZER_ENV)
import owner_common as C


def snapshot():
    stat=Path('/proc/self/stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    return dict(pid=os.getpid(),uid=os.getuid(),euid=os.geteuid(),start_ticks=int(fields[19]),
        affinity=sorted(os.sched_getaffinity(0)),cgroup=Path('/proc/self/cgroup').read_text(),
        status=Path('/proc/self/status').read_text(),executable=os.readlink('/proc/self/exe'),
        actual_python_argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v])


def run(inputs_ref,mode,out):
    x=C.inputs(inputs_ref,host=False);C.need(mode=='import-probe'and x['diagnostic_only']is True,'diagnostic-only source cannot qualify full workflow')
    C.need(ENTRY_ENV==N.TOKENIZER_ENV,'all actual tokenizer env present before Python script/helper imports')
    task=Path(x['task_packet_root']);sys.path.insert(0,str(task));import task_contract as T
    T.cpu_runtime();C.need(os.sched_getaffinity(0)=={145}and out.is_dir(),'actual oneCPU145 Devices[] diagnostic')
    before=snapshot();initial=C.write(out/'CHILD-START-import-probe.json',dict(**before,entry_environment=ENTRY_ENV,entry_related_modules=ENTRY_MODULES))
    readset,_=C.task_readset(x['task_source_unbound_ref'],host=False);readset+=C.tokenizer_sources(x,host=False)
    hashes_before={r['path']:r['sha256']for r in readset}
    import tokenizer_probe
    payload=tokenizer_probe.run(x,T,out)
    after={r['path']:C.ref(C.checked(r))['sha256']for r in readset}
    T.cpu_runtime();C.authority(x['authority_ref']);C.need(after==hashes_before,'unchanged exact source/input across bounded import diagnostic')
    return C.write(out/'CHILD-import-probe.json',dict(schema='bole.actual-task-CPU-child/v1',inputs_ref=inputs_ref,mode=mode,
        start_ref=initial,process_before=before,process_after=snapshot(),readset_before=hashes_before,readset_after=after,payload=payload,
        diagnostic_only=True,source_image_CPU_owner_software_controls_verified=False,model_executed=False,HTTP_executed=False,
        generated_code_executed=False,task_score_produced=False,NPU=False,model_ready=False))


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--mode',choices=('import-probe',))
    p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"software_qualification_accepted":false}');return 0
    C.need(a.mode and a.inputs_ref and a.output,'explicit finite diagnostic owned source/mode/output')
    print(json.dumps(run(json.loads(a.inputs_ref),a.mode,a.output)));return 0


if __name__=='__main__':raise SystemExit(main())
