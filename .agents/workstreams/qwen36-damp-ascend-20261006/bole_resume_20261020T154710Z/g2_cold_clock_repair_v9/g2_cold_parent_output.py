"""Retain/run exact original G2 software child with explicit guest-alias export.
No original G2 function/argv is edited. No cached pass is accepted.
"""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import sourceio as C


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def parse(raw):
    def pairs(rows):
        out={}
        for k,v in rows:
            C.need(k not in out,'unique parent software JSON keys');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError(v)))


def extract(data,parent_ref,parent):
    C.need(type(data)is bytes,'complete retained parent bytes');found=[]
    for line in data.splitlines():
        try:value=parse(line)
        except(UnicodeDecodeError,ValueError):continue
        if type(value)is dict and value.get('schema')=='bole.G2-explicit-combined-software-gate/v1':found.append(value)
    C.need(len(found)==1,'one exact source-owned G2 combined software result, never trailing-line inference')
    value=found[0];scope=parent['service_software_scope']
    C.need(value['source']==parent_ref and type(value['tests'])is int and value['tests']==parent['service_required_sameimage_software_cases']and value['historical_cases']==scope['parent_exact_cases']and value['current_cases']==scope['new_current_cases']and value['all_tests_passed']is True and value['NPU']is False and value['actual_scheduler_executed']is False and value['model_ready']is False and value['source_validated']['source_validated']is True,'all actual original parent source/count/current/historical/devicefree gates')
    metadata=value['actual_installed_metadata'];C.need(metadata['source']==parent_ref and metadata['NPU']is False and metadata['actual_model_constructed']is False and metadata['actual_batch_constructed']is False and metadata['actual_scheduler_executed']is False and metadata['actual_torch_context_class_checked']is True and len(metadata['classes'])==len(metadata['complete_native_sources_compiled'])==6 and all(r['full_source_compiled']is True and r['import_executed']is False for r in metadata['complete_native_sources_compiled']),'actual complete original installed metadata classes and native source compile gates')
    reference=parent['files']['parent_software_output.py'];spec=importlib.util.spec_from_file_location('_task_exact_original_G2_parent_gate',C.checked(reference));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original=value['parent_software_result'];module.summary(C,canonical(original)+b'\n',parent_source=scope['parent_source'],expected_tests=scope['parent_exact_cases'])
    C.need(set(value['parent_software_evidence'])=={'terminal','stdout','stderr','extraction'},'complete actual original nested raw/terminal/extraction references')
    return value


def alias_exports(value,alias,actual):
    alias=Path(alias);actual=Path(actual);mapping={}
    C.need(alias.is_dir()and actual.is_dir()and alias.samefile(actual),'actual same-device/inode declared original-parent output alias')
    def visit(x):
        if type(x)is dict:
            if set(x)=={'path','bytes','sha256'}and Path(x['path']).is_relative_to(alias):
                old=C.checked(x);new=actual/old.relative_to(alias);nr=C.ref(new)
                C.need((nr['bytes'],nr['sha256'])==(x['bytes'],x['sha256'])and new.samefile(old),'whole original guest-alias evidence re-exported as exact actual host file')
                st=new.stat();mapping[x['path']]=dict(original_guest_ref=x,actual_host_ref=nr,same_device_inode=[st.st_dev,st.st_ino]);return
            for v in x.values():visit(v)
        elif type(x)in(tuple,list):
            for v in x:visit(v)
    visit(value)
    C.need(len(mapping)==4,'all four unique original nested parent evidence refs joined, no missing/cached exported streams')
    return list(mapping.values())


def run(source_ref):
    m=C.obj(source_ref);C.need(C.ref(__file__)==m['files']['g2_cold_parent_output.py'],'exact source-bound retained parent runner');parent_ref=m['g2_cold_clock_v9']['parent_source'];parent=C.obj(parent_ref);alias=Path(parent['output_root'])/'cpu-preflight'
    options=[Path(m['output_root'])/'cpu-preflight',Path(m['output_root']+'-CPU')/'cpu-preflight']
    matches=[p for p in options if p.is_dir()and p.samefile('/adakv-results')]
    C.need(len(matches)==1 and alias.is_dir()and alias.samefile(matches[0]),'one exact current owned RW phase plus declared original G2 guest alias')
    actual=matches[0];root=actual/'G2-V9-PARENT-V8-SOFTWARE';C.need(not root.exists(),'fresh actual full parent rerun; no cached PASS or overwrite');root.mkdir()
    stdout=root/'STDOUT.raw';stderr=root/'STDERR.raw';entry=C.checked(parent['files']['service_entry.py'])
    C.need(entry==Path(parent['root'])/'service_entry.py','exact original bound G2 entry')
    argv=[sys.executable,'-I','-B',str(entry),'--software'];env={k:v for k,v in os.environ.items()if not k.startswith('BOLE_')}
    start=time.monotonic();returncode=None;timed_out=False;fault=None;pid=None
    try:
        with stdout.open('xb')as so,stderr.open('xb')as se:
            process=subprocess.Popen(argv,env=env,stdout=so,stderr=se,start_new_session=True);pid=process.pid
            try:returncode=process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(process.pid,signal.SIGKILL);returncode=process.wait(timeout=10)
            finally:so.flush();os.fsync(so.fileno());se.flush();os.fsync(se.fileno())
    except BaseException as error:fault=repr(error)
    terminal=C.write(root/'TERMINAL.json',dict(schema='bole.actual-G2-v9-parent-v8-software-terminal/v1',source_ref=source_ref,parent_source_ref=parent_ref,actual_argv=argv,child_pid=pid,returncode=returncode,timed_out=timed_out,primary=fault,stdout=C.ref(stdout),stderr=C.ref(stderr),elapsed_seconds=time.monotonic()-start,original_parent_argv_unchanged=True,cached_PASS_reused=False,actual_parent_guest_alias=str(alias),actual_host_output=str(actual)))
    C.need(fault is None and returncode==0 and not timed_out,'fresh original G2 full software child failed, raw/terminal retained')
    C.need(stdout.stat().st_size+stderr.stat().st_size<=32*2**20,'bounded complete parent streams, never truncate to pass')
    value=extract(stdout.read_bytes(),parent_ref,parent);exports=alias_exports(value['parent_software_evidence'],alias,actual)
    result=C.write(root/'EXTRACTION.json',dict(schema='bole.actual-G2-v9-parent-v8-software-extraction/v1',source_ref=source_ref,parent_source_ref=parent_ref,terminal_ref=terminal,stdout_ref=C.ref(stdout),stderr_ref=C.ref(stderr),original_summary=value,original_guest_evidence_to_actual_host_refs=exports,exact_original_gates_rechecked=True,original_G2_and_G1_controls_really_rerun=True,NPU=False))
    return value,dict(terminal_ref=terminal,stdout_ref=C.ref(stdout),stderr_ref=C.ref(stderr),extraction_ref=result)


def parent_alias(C,sr,leaf,readset,source_root):
    m=C.obj(sr);parent=C.obj(m['g2_cold_clock_v9']['parent_source']);alias=Path(parent['output_root'])/'cpu-preflight'
    C.need(alias.is_absolute()and alias!=leaf and not alias.is_relative_to(source_root)and not any(Path(r['path']).is_relative_to(alias)for r in readset),'one exact original-parent CPU alias cannot hide immutable evidence')
    return {str(alias):(str(leaf),True)}
