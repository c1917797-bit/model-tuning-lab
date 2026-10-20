"""Retain exact fresh parent software output before strict summary extraction."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SCHEMA='bole.g1-cold-aggregate-software/v1'
FILES=('service_entry.py','host_service.py','service_client.py','consume_service.py','server090.py')


def summary(C,data,*,parent_source,expected_tests):
    C.need(type(data)is bytes,'original complete parent stdout bytes')
    matches=[]
    def nonfinite(value):raise ValueError('nonfinite JSON constant '+value)
    for ordinal,line in enumerate(data.decode('utf-8',errors='replace').splitlines(),1):
        try:value=json.loads(line,parse_constant=nonfinite)
        except(ValueError,TypeError):continue
        if type(value)is dict and value.get('schema')==SCHEMA:matches.append((ordinal,value))
    C.need(len(matches)==1,'exactly one original parent software summary, never missing/duplicate or an arbitrary log line')
    line,value=matches[0]
    C.need(value['source']==parent_source and type(value['tests'])is int and
        value['tests']==expected_tests==214 and value['all_tests_passed']is True and
        value['complete_readset_audited']is True and value['NPU']is False and
        value['actual_scheduler_executed']is False and value['model_ready']is False,
        'exact actual parent source/214/all-pass/complete-readset/device-free gates')
    expected=[dict(file=name,mode=mode,exit_code=0)for name in FILES for mode in([],['--help'])]
    C.need(value['actual_cold_cli']==expected and
        all(type(v['exit_code'])is int for v in value['actual_cold_cli']),
        'all ten original exact cold/defaultOFF/help CLI checks really completed')
    metadata=value['actual_installed_metadata']
    C.need(metadata['schema']=='bole.service-installed-class-protocol-devicefree/v1'and
        metadata['source']==parent_source and metadata['NPU']is False and
        metadata['actual_model_constructed']is False and metadata['actual_batch_constructed']is False and
        metadata['actual_scheduler_executed']is False and metadata['model_ready']is False and
        metadata['actual_torch_context_class_checked']is True and
        metadata['actual_runtime_method_guards_required_after_real_load']is True and
        len(metadata['classes'])==len(metadata['complete_native_sources_compiled'])==6 and
        all(row['full_source_compiled']is True and row['import_executed']is False
            for row in metadata['complete_native_sources_compiled']),
        'original actual installed metadata/source/full-native-compile gates, no model execution inferred')
    return value,line


def owned_output(C,m,*,alias=Path('/adakv-results')):
    """Join the two exact existing mounts created by unchanged owned_create.

    Return the actual host-path mount, so retained Refs are independently
    reopenable by the host rather than incorrectly labelled guest-alias Refs.
    """
    alias=Path(alias)
    C.need(alias.is_dir()and not any(p.is_symlink()for p in(alias,*alias.parents)),
        'actual existing ordinary owned guest output alias')
    candidates=[Path(m['output_root'])/'cpu-preflight',Path(m['output_root']+'-CPU')/'cpu-preflight']
    matches=[p for p in candidates if p.is_dir()and
        not any(x.is_symlink()for x in(p,*p.parents))and p.samefile(alias)]
    C.need(len(matches)==1,'one actual host-path output mount matches existing RW guest output alias; never a readonly-source fallback')
    path=matches[0];stat=path.stat()
    return path,dict(schema='bole.actual-existing-owned-guest-output-alias/v4',
        guest_alias=str(alias),actual_host_path_mount=str(path),same_device_inode=[stat.st_dev,stat.st_ino],
        actual_samefile=True,source_directory_used=False)


def run(C,*,source_ref,parent_source_ref,expected_tests,evidence_root=Path('/adakv-results'),output_binding=None,timeout=120):
    """Production root is the existing exact-owned guest RW output mount.

    Controlled tests may pass their own new temporary output leaf. No source or
    prerequisite directory is used as a fallback. No old PASS is accepted.
    """
    m=C.obj(parent_source_ref);entry=C.checked(m['files']['service_entry.py'])
    C.need(entry==Path(m['root'])/'service_entry.py'and
        m['service_required_sameimage_software_cases']==expected_tests==214,
        'exact original parent executable and214 declared controls')
    root=Path(evidence_root)
    C.need(root.is_absolute()and root.is_dir()and
        not any(p.is_symlink()for p in(root,*root.parents)),'existing ordinary exact-owned guest RW output root')
    leaf=root/'PARENT-G1-SOFTWARE';leaf.mkdir(mode=0o700)
    stdout=leaf/'stdout';stderr=leaf/'stderr';terminal=leaf/'TERMINAL.json'
    argv=[sys.executable,'-I','-B',str(entry),'--software']
    env={k:v for k,v in os.environ.items()if not k.startswith('BOLE_')}
    started=time.monotonic();primary=None;returncode=None;timed_out=False;pid=None
    try:
        with stdout.open('xb')as so,stderr.open('xb')as se:
            process=subprocess.Popen(argv,env=env,stdout=so,stderr=se);pid=process.pid
            try:returncode=process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;process.kill();returncode=process.wait(timeout=5)
                raise ValueError('bounded exact parent software child timeout; complete raw retained')
            finally:
                so.flush();os.fsync(so.fileno());se.flush();os.fsync(se.fileno())
    except BaseException as error:primary=repr(error)
    # Preserve stdout/stderr and observed terminal data before any gate/parser.
    # An owner-level external kill can prevent this final receipt; raw streams
    # already write directly to the owned persistent leaf throughout execution.
    value=dict(schema='bole.actual-fresh-parent-software-terminal/v4',source=source_ref,
        parent_source=parent_source_ref,argv=argv,child_pid=pid,returncode=returncode,
        timed_out=timed_out,primary=primary,elapsed=time.monotonic()-started,
        stdout=C.ref(stdout),stderr=C.ref(stderr),complete_streams_retained=True,
        reused_cached_PASS=False,actual_output_binding=output_binding,NPU=False)
    terminal_ref=C.write(terminal,value)
    C.need(primary is None and returncode==0 and timed_out is False,
        'fresh exact parent software process failed; terminal/raw retained '+json.dumps(terminal_ref))
    prior,line=summary(C,stdout.read_bytes(),parent_source=parent_source_ref,expected_tests=expected_tests)
    extraction=C.write(leaf/'EXTRACTION.json',dict(schema='bole.unique-exact-parent-software-extraction/v4',
        source=source_ref,parent_source=parent_source_ref,terminal=terminal_ref,
        stdout=value['stdout'],stderr=value['stderr'],summary_line=line,summary=prior,
        exactly_one_expected_schema=True,complete_original_gates_checked=True,
        non_JSON_lines_retained=True,reused_cached_PASS=False,NPU=False))
    return prior,dict(terminal=terminal_ref,stdout=value['stdout'],stderr=value['stderr'],extraction=extraction)
