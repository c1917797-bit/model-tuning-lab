"""MAIN finite serial025 CPU owner. Default OFF. No model/NPU dispatch exists."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import main_quiescence as Q


def memory_view(H,pid,expected):
    version,group,mount,chain=H.hierarchy(pid,'memory');rows=[];finite=[]
    for path in chain:
        name='memory.max'if version==2 else'memory.limit_in_bytes';file=path/name
        if not file.is_file():C.need(path==Path(mount),'actual ancestor memory control missing');continue
        text=file.read_text().strip();limit=None if text=='max'else int(text)
        if limit is not None:finite.append(limit)
        usage_file=path/('memory.current'if version==2 else'memory.usage_in_bytes')
        swap=path/('memory.swap.max'if version==2 else'memory.memsw.limit_in_bytes')
        rows.append(dict(path=str(path),limit=text,usage_bytes=int(usage_file.read_text())if usage_file.is_file()else None,
            swap_limit=swap.read_text().strip()if swap.is_file()else None))
    C.need(finite and min(finite)==expected,'actual guest plus all ancestors admit exact finite memory cap')
    return dict(version=version,cgroup=group,ancestors=rows,effective_bytes=min(finite))


def host_binding(S,ctl,pid,uid,namespace_module,*,guest=None,HE=False):
    proc=Path('/proc')/str(pid);status=(proc/'status').read_text();stat=(proc/'stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    cg=(proc/'cgroup').read_text();nspid=[int(v)for line in status.splitlines()if line.startswith('NSpid:')for v in line.split()[1:]]
    uids=[int(v)for line in status.splitlines()if line.startswith('Uid:')for v in line.split()[1:]]
    C.need(ctl.cid in cg and nspid and uids==[uid]*4 and fields[0]!='Z','actual exact live owned cgroup/namespace/uid')
    if guest is not None:C.need(nspid[-1]==guest['pid']and int(fields[19])==guest['start_ticks'],'actual child strong lifetime namespace mapping')
    argv=[v.decode()for v in(proc/'cmdline').read_bytes().split(b'\0')if v]
    if HE:
        # env-i resolves python3 using the frozen PATH. Compare the actual loaded
        # binary with the first executable in that PATH inside the same pinned root.
        F=namespace_module;namespaces=F.namespace_id(proc)
        rootfd=os.open(proc/'root',os.O_RDONLY|os.O_DIRECTORY);expected_fd=actual_fd=None
        C.need(F.identity(os.fstat(rootfd))==namespaces['root'],'pinned actual HE namespace root FD')
        expected=None
        try:
            for directory in('/usr/local/sbin','/usr/local/bin','/usr/sbin','/usr/bin','/sbin','/bin'):
                try:fd,canonical=F.root_open(rootfd,directory+'/python3')
                except FileNotFoundError:continue
                try:proof=F.file_proof(fd)
                except ValueError:os.close(fd);continue
                expected_fd=fd;expected=canonical;break
            C.need(expected_fd is not None,'actual frozen PATH resolves a real Python executable')
            actual_fd=os.open(proc/'exe',os.O_RDONLY)
            actual=F.file_proof(actual_fd);C.need(actual==F.file_proof(expected_fd),'actual HE loaded executable matches whole namespace PATH binary')
            C.need(F.namespace_id(proc)==namespaces,'same actual HE namespaces/root throughout binary probe')
            program=dict(expected_namespace_executable=expected,actual_namespace_executable=os.readlink(proc/'exe'),executable=actual,namespaces=namespaces)
        finally:
            for fd in(actual_fd,expected_fd,rootfd):
                if fd is not None:os.close(fd)
        C.need(argv==['python3','-I','-B','/source/he_worker.py','--controls','--capsule-sha256',ctl.stage['capsule_ref']['sha256']],
               'actual fixed HE controls process, no task execution entry')
    else:
        program=namespace_module.verify(proc,Path('/proc')/str(ctl.inspect()[0]['State']['Pid']),'/usr/local/python3.12.13/bin/python3')
        C.need(len(argv)>4 and argv[1:3]==['-I','-B']and argv[3]==str(P/'cpu_steps.py'),'actual private owned CPU child executable/entry')
    cpu=S.H.cpu_view(pid);C.need(cpu['effective_cpus']==[145]and cpu['effective_capacity']==1,'actual CPU145/oneCPU guest and ancestor quotas')
    memory=memory_view(S.H,pid,2*C.GIB if HE else 8*C.GIB)
    C.need((proc/'stat').read_text().split(')')[-1].split()[19]==fields[19]and(proc/'cgroup').read_text()==cg,'same live owned process across full host probe')
    return C.write(ctl.out/'PROCESS-BINDING.json',dict(container_id=ctl.cid,host_pid=pid,guest_pid=nspid[-1],
        nspid=nspid,start_ticks=int(fields[19]),uid=uid,status=status,cgroup=cg,argv=argv,
        program=program,cpu=cpu,memory=memory,guest_start=guest,Devices=[]))


def observe_cpu(ctl,label,initial=False):
    # Original025 actual NPU/HBM/FD/protected/resource guards always run first.
    r=ctl.observe(label,initial=initial)
    return Q.observe(ctl,r,ctl._main_quiescence_ref)


def child(C,c,S,H,ctl,inputs_ref,mode,seconds,namespace_module,extra=()):
    args=[str(P/'cpu_steps.py'),'--execute','--inputs-ref',json.dumps(inputs_ref),'--mode',mode,'--output',str(ctl.out),*extra]
    command=[S.DOCKER,'exec',ctl.cid,c.PY,'-I','-B',*args]
    start=time.monotonic();deadline=start+min(seconds,ctl.remaining(cap=seconds));binding=None;next_observe=start+5
    with(ctl.out/'child.stdout').open('x')as so,(ctl.out/'child.stderr').open('x')as se:
        process=subprocess.Popen(ctl.wrapper(command),stdout=so,stderr=se,cwd=c.ROOT)
    ctl.server=process;ctl.server_argv=command
    started=ctl.out/('CHILD-START-'+mode+'.json')
    while process.poll()is None:
        C.need(time.monotonic()<deadline,'finite CPU child; no retry')
        if binding is None and started.is_file():
            guest=C.obj(C.ref(started));matches=[]
            for path in Path('/proc').iterdir():
                if not path.name.isdigit():continue
                try:
                    if ctl.cid not in(path/'cgroup').read_text():continue
                    status=(path/'status').read_text();ids=[int(v)for line in status.splitlines()if line.startswith('NSpid:')for v in line.split()[1:]]
                    if ids and ids[-1]==guest['pid']:matches.append(int(path.name))
                except(FileNotFoundError,ProcessLookupError):continue
            C.need(len(matches)==1,'one actual live CPU child host mapping')
            binding=host_binding(S,ctl,matches[0],0,namespace_module,guest=guest)
        if time.monotonic()>=next_observe:
            observe_cpu(ctl,mode+'-running');next_observe=time.monotonic()+5
        ctl.remaining(cap=seconds);time.sleep(.2)
    terminal=C.write(ctl.out/'CPU-CHILD-TERMINAL.json',dict(requested_argv=command,actual_host_argv=ctl.wrapper(command),
        host_cli_pid=process.pid,exit_code=process.returncode,stdout=C.ref(ctl.out/'child.stdout'),stderr=C.ref(ctl.out/'child.stderr'),
        elapsed_seconds=time.monotonic()-start,process_binding=binding))
    C.need(process.returncode==0 and binding is not None,'actual finite CPU child and live identity probe must succeed')
    report=C.ref(ctl.out/('CHILD-'+mode+'.json'));v=C.obj(report)
    C.need(v['inputs_ref']==inputs_ref and v['readset_before']==v['readset_after']and v['NPU']is False
           and v['task_score_produced']is False and v['model_executed']is False,'actual source-stable CPU software child')
    return dict(terminal=terminal,report=report,binding=binding,inspect_ref=ctl.inspect()[1])


def create_cpu(c,S,ctl,source,readset,tokenizer):
    sys.modules['external025'].prepare(ctl.out)
    mounts={str(P):(str(P),False),str(ctl.out):(str(ctl.out),True),'/adakv-results':(str(ctl.out),True)}
    guest_assets={r['guest']['path']:r['host']['path']for r in tokenizer}
    for guest,host in guest_assets.items():mounts[guest]=(host,False)
    for reference in readset:
        path=reference['path']
        if Path(path).is_relative_to(P)or path in guest_assets.values():continue
        C.need(not Path(path).is_relative_to(ctl.out),'no readonly alias shadows current owned RW leaf')
        mounts[path]=(path,False)
    ctl.expected=dict(cid=None,name=ctl.name,image=C.IMAGE,arm='cpu-preflight',source=source,
        host_sha256=c.sha(S.__file__),guest_cpus=[145],mounts=mounts)
    derived=N.cpu_profile(C,ctl.cpu)
    ctl.cpu_only_profile_ref=C.write(ctl.out/'DERIVED_CPU_PROFILE.json',derived)
    C.need(ctl.expected['guest_cpus']==derived['actual_helper_cpus'],'explicit actual CPU145 branch independent of original TP4 first guest')
    old,_=ctl.call('unique-name',[S.DOCKER,'ps','-a','--filter','name=^/'+ctl.name+'$','--format','{{.ID}}'])
    C.need(not old['stdout'].strip(),'new exact owned CPU name, never retry/reuse')
    for src,_ in mounts.values():C.need(Path(src).exists(),'actual exact immutable input/owned output mount')
    ctl.create_owned({'safety_host.py':c.sha(S.__file__)})
    x,_=ctl.inspect();C.need(not x['State']['Running']and x['State']['Pid']==0,'fresh stopped CPU init')
    ctl.call('start',[S.DOCKER,'start',ctl.cid],cap=30);x,ir=ctl.inspect()
    C.need(x['State']['Running']and not x['State']['OOMKilled'],'actual live CPU init')
    view=S.H.cpu_view(x['State']['Pid']);C.need(view['effective_capacity']==1 and view['effective_cpus']==[145],'actual original CPU cgroup')
    C.write(ctl.out/'INIT_CPU.json',view);C.write(ctl.out/'INIT_MEMORY.json',memory_view(S.H,x['State']['Pid'],8*C.GIB))
    return ir


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group()
    g.add_argument('--execute',action='store_true');g.add_argument('--source-audit',action='store_true');p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"task_score_produced":false}');return 0
    C.need(a.inputs_ref,'explicit prepared owner inputs');ir=json.loads(a.inputs_ref);x=C.inputs(ir)
    on=C.basis(x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref'])
    C.need(x['helper_refs']==N.helper_refs(C,on),'complete exact original helper declaration, no missing guard source')
    readset,tokenizer=C.task_readset(x['task_source_unbound_ref'],host=True)
    prior_owner=C.obj(x['G1_owner_ref'])
    releases=[prior_owner['summary'][key]for key in('CPU_release','model_release','independent_release')]
    readset=[*readset,*C.tokenizer_sources(x,host=True),*x['tokenizer_runtime_copy_refs'],*Q.readset(x['main_quiescence_ref'],authority_ref=x['authority_ref']),*x['files'].values(),*x['helper_refs'],ir,x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref'],*releases]
    for r in readset:C.checked(r)
    if a.source_audit:print(json.dumps(dict(inputs_ref=ir,readset_files=len(readset),weight_hashes_performed=False,NPU=False,resources_admitted=False)));return 0
    C.need(os.environ.get('BOLE_TASK_CPU_MAIN_ENABLE')=='1','MAIN explicit CPU-only owner opt-in')
    argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'fresh actual -I/-B owner CLI')
    C.need(166 in os.sched_getaffinity(0),'actual source-bound root CPU166 available');os.sched_setaffinity(0,{166})
    _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go-child AS contract');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
    start=time.monotonic();C.authority(x['authority_ref'],3600);out=Path(x['output_root']);owned=[];summary={};primary=None
    before={r['path']:r['sha256']for r in readset};after={};phase='namespace'
    with N.open_namespace(C,x,on)as(c,S,H,proof):
        out.mkdir(mode=0o700);C.write(out/'PRIVATE_NAMESPACE.json',proof);joint=H.Joint(start);protected=None
        F=C.load(on['files']['frontend_namespace131r18.py'],'_task_cpu_original_namespace_program')
        def ctl_for(role,HE_stage=None,bound=None):
            nonlocal protected
            leaf=out/role;C.need(not leaf.exists()and leaf.parent==out,'one new exact phase leaf');leaf.mkdir(mode=0o700)
            if HE_stage is None:ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start)
            else:
                import he_owned
                sys.path.insert(0,x['task_packet_root']);import he_policy
                ctl=he_owned.create_class(C,c,S,H,joint,he_policy)(argparse.Namespace(output_dir=leaf),start,HE_stage,bound)
            ctl._main_quiescence_ref=x['main_quiescence_ref']
            ctl.protected=protected;owned.append(ctl);observe_cpu(ctl,role+'-admission',initial=True);protected=ctl.protected
            return ctl
        def close(ctl):
            r=ctl.cleanup();ctl._task_closed=True;v=c.obj(r)
            C.need(v['stopped']is True and v['retained']is True and v['errors']==[],'every actual phase stopped-retained before next admission')
            return r
        try:
            phase='cpu-preflight';ctl=ctl_for(phase);create_cpu(c,S,ctl,x['task_source_unbound_ref'],readset,tokenizer)
            summary['CPU']=child(C,c,S,H,ctl,ir,'import-probe',300,F)
            summary['CPU_release']=close(ctl)
        except BaseException as e:
            primary=dict(phase=phase,error=repr(e),traceback=traceback.format_exc());C.write(out/'FIRST-FAULT.json',primary)
        finally:
            for ctl in reversed(owned):
                if ctl.cid and not getattr(ctl,'_task_closed',False):
                    ctl.primary=primary
                    try:ctl.cleanup()
                    except BaseException as e:joint.secondary.append(repr(e))
                joint.secondary.extend(ctl.secondary)
            try:
                for r in readset:after[r['path']]=C.ref(C.checked(r))['sha256']
            except BaseException as e:joint.secondary.append('source/input-after '+repr(e))
            joint.secondary.extend(S.formal_time_failures(joint.deadline))
            if joint.cleanup_used>180:joint.secondary.append('joint owned cleanup180 exceeded')
            passed=primary is None and not joint.secondary and before==after
            result_value=dict(schema='bole.actual-finite-task-CPU-owner/v2',inputs_ref=ir,summary=summary,main_quiescence_ref=x['main_quiescence_ref'],
                quiescence_observations=[r for ctl in owned for r in getattr(ctl,'_main_quiescence_observations',[])],
                primary=primary,secondary=joint.secondary,source_input_before=before,source_input_after=after,
                phase_seconds=3600,cleanup_seconds=180,cleanup_spent=joint.cleanup_used,elapsed_seconds=time.monotonic()-start,
                source_image_CPU_owner_software_controls_verified=False,diagnostic_only=True,tokenizer_probe=x['tokenizer_probe'],
                tokenizer_import_diagnostic_completed=passed,actual_host_argv=argv,
                model_executed=False,HTTP_executed=False,task_score_produced=False,model_ready=False,
                performance_ready=False,formal_accuracy_accepted=False,NPU=False)
    # Publish success only AFTER all original module objects/globals were restored.
    result_value['private_namespace_restored_by_identity']=True
    result=C.write(out/'RESULT.json',result_value)
    print(json.dumps(dict(result_ref=result,software_controls_verified=False,diagnostic_only=True,diagnostic_completed=passed,model_ready=False,NPU=False)),flush=True)
    return 0 if passed else 3


if __name__=='__main__':raise SystemExit(main())
