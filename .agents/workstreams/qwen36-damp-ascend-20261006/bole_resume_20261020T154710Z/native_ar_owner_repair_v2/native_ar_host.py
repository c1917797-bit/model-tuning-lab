"""Default-OFF MAIN finite nativeAR TP4 reference smoke over actual025 authority.

Only the unchanged controller creates/stops exact owned containers. No signals
are sent to AR workers. Original numerical/observer source is never rewritten.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true')
    p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not a.inputs_ref:p.error('actual source-bound INPUTS Ref required')
    root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('_native_ar_controller_common',str(root/'ar_owner_common.py'))
    C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    ir=json.loads(a.inputs_ref);x=C.obj(ir)
    C.need(x['schema']=='bole.native-ar-owner-inputs/v1'and C.ref(__file__)==x['files']['native_ar_host.py']and
           C.ref(C.__file__)==x['files']['ar_owner_common.py'],'exact reviewed controller/common source')
    m,on,readset=C.readset(x,installed=False);C.checked(ir);readset+=[ir]
    if a.source_audit:print(json.dumps(dict(inputs=ir,source=x['AR_source'],readset=len(readset),NPU=False,resources_admitted=False)));return 0
    C.need(os.environ.get('BOLE_NATIVE_AR_MAIN_ENABLE')=='1','MAIN explicit native AR owner opt-in')
    argv=[v.decode('utf8','strict')for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'actual private -I/-B host CLI')
    namespace=C.load(x['files']['ar_host_namespace.py'],'_native_ar_host_namespace')
    B=C.load(x['files']['ar_snapshot_bindings.py'],'_native_ar_snapshot_bindings')
    out=Path(x['output_root']);sr=x['AR_source'];P=Path(m['root'])
    # The namespace adapter creates no container and cannot skip existing gates.
    with namespace.open_namespace(C,x,on)as(c,S,H,namespace_proof):
        import owned_create,identity_owner
        start=time.monotonic();authority=C.obj(x['authority'])
        C.need(time.time()+3600<=authority['cutoff_epoch'],'whole original3600 fits actual authority before admission')
        host=S.H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host['effective_cpus'])})
        _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original restored Go-child AS contract')
        resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
        out.mkdir(mode=0o700);joint=H.Joint(start);owned=[];primary=None;summary={}
        before={r['path']:r['sha256']for r in readset};phase=dict(name='setup',ordinal=0)
        C.write(out/'PRIVATE_HOST_NAMESPACE.json',namespace_proof)
        def mark(name):phase.update(name=name,ordinal=phase['ordinal']+1)
        def ctl_for(role,extra=()):
            mark(role+'-admit');leaf=H.fresh_leaf(out/role);H.outputs(leaf);(leaf/'receipts').mkdir()
            ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start);owned.append(ctl)
            ctl.observe(role+'-admission',initial=True)
            owned_create.create(c,S,ctl,sr,[*readset,*extra],'cpu-preflight'if role!='dense'else'dense',P)
            return ctl
        def child(ctl,label,args,seconds):
            return H.child(ctl,label,args,seconds,observe=ctl.expected['arm']!='cpu-preflight')
        def close(ctl):
            mark(ctl.out.name+'-stop-retain');r=ctl.cleanup();ctl._native_ar_closed=True;v=c.obj(r)
            C.need(v['stopped']is True and v['retained']is True and v['errors']==[],'actual exact owned retained release')
            return r
        def spawn(ctl,args,label):
            command=c.docker_argv(ctl.cid,args)
            with(ctl.out/(label+'.stdout')).open('x')as so,(ctl.out/(label+'.stderr')).open('x')as se:
                proc=subprocess.Popen(ctl.wrapper(command),stdout=so,stderr=se,cwd=c.ROOT)
            return proc,command
        try:
            cpu=ctl_for('cpu-preflight')
            summary['sameimage_child']=child(cpu,'AR-SOURCE-PREFLIGHT',[x['files']['ar_sameimage_preflight.py']['path'],
                '--execute','--inputs-ref',json.dumps(ir),'--output',str(cpu.out/'PREFLIGHT.json')],300)
            report=C.obj(C.ref(cpu.out/'PREFLIGHT.json'))
            C.need(report['inputs']==ir and report['source']==sr and report['Devices']==[] and
                   report['source_preflight_pass']is True and report['NPU']is False,'actual sameimage source preflight before TP4')
            summary['sameimage']=C.ref(cpu.out/'PREFLIGHT.json');summary['sameimage_release']=close(cpu)
            # Original c.model streams and hashes actual /cache checkpoint paths.
            mark('actual-full-checkpoint');c.model(c.MODEL_REF)
            ctl=ctl_for('dense')
            canary=on['files']['guest_canary.py']
            summary['canary_child']=child(ctl,'CANARY',[canary['path'],'--output',str(ctl.out/'CANARY.json')],180)
            C.need(c.obj(c.ref(ctl.out/'CANARY.json'))['rows']==[dict(logical=i,values=[4.,5.])for i in range(4)],
                   'original all4 tiny actual canary; not model qualification')
            mark('native-ar-server');ctl.server_started=H.utc()
            ctl.server,ctl.server_argv=spawn(ctl,[m['files']['native_ar_server.py']['path'],'--execute',
                '--source-ref',json.dumps(sr)],'server')
            until=time.monotonic()+min(900,ctl.remaining(cap=900))
            while True:
                C.need(ctl.server.poll()is None and time.monotonic()<until,'finite actual AR startup, no retry')
                ctl.observe('native-ar-startup')
                command=c.docker_argv(ctl.cid,['-c',"import urllib.request;assert urllib.request.urlopen('http://127.0.0.1:8230/health',timeout=2).status==200"])
                result=ctl.h.run(ctl.wrapper(command),min(4,ctl.remaining(cap=4)));c.write(ctl.out/('health-%d.json'%time.time_ns()),result)
                if result['exit_code']==0:break
                time.sleep(1)
            mark('native-ar-two-requests')
            ctl.client,ctl.client_argv=spawn(ctl,[m['files']['pair_entry.py']['path'],'--execute',
                '--source-ref',json.dumps(sr),'--variant','native_AR','--variant-source-ref',json.dumps(sr),
                '--inputs-ref',json.dumps(x['frozen_inputs']),'--output',str(ctl.out),'--base-url','http://127.0.0.1:8230'],'client')
            until=time.monotonic()+min(1800,ctl.remaining(cap=1800))
            while ctl.client.poll()is None:
                C.need(ctl.server.poll()is None and time.monotonic()<until,'finite native AR HTTP/retirement client')
                ctl.observe('native-ar-two-request');time.sleep(.2)
            summary['client_terminal']=C.write(ctl.out/'CLIENT-TERMINAL.json',dict(actual_argv=ctl.client_argv,
                exit_code=ctl.client.returncode,stdout=C.ref(ctl.out/'client.stdout'),stderr=C.ref(ctl.out/'client.stderr')))
            C.need(ctl.client.returncode==0,'actual AR HTTP failed; terminal retained')
            receipt=ctl.out/'receipts'
            mark('existing-ar-snapshots-no-signal');snapshots,snapshot_refs,bindings=B.bind(C,c,ctl,sr,receipt)
            journals=[C.ref(v)for v in sorted(receipt.glob('IDENTITY-*.json'))]
            http_ref=C.ref(ctl.out/'HTTP_RESULT.json');http=C.obj(http_ref);response=C.obj(http['rows'][0]['response'])
            assignments=[C.obj(r)['event']for r in journals if C.obj(r)['role']=='frontend'and
                         C.obj(r)['event']['before_request_id']==response['id']+'-0']
            C.need(len(assignments)==1,'actual native AR assigned frontend event')
            frontend=identity_owner.frontend(c,S,ctl,assignments[0])
            summary['frontend_binding']=C.write(ctl.out/'FRONTEND_BINDING.json',frontend)
            observed,inspect_receipt=ctl.inspect();raw=C.obj(inspect_receipt)['stdout']
            C.need(json.loads(raw)==[observed],'complete actual unmodified inspect array')
            with(ctl.out/'DOCKER-INSPECT.json').open('x')as f:f.write(raw)
            # Read initial exec environment WHILE its real bound frontend lives.
            guest=frontend['guest'];expected=C.write(ctl.out/'FRONTEND-GUEST-PROCESS.json',guest)
            command=c.docker_argv(ctl.cid,[m['files']['launch_profile.py']['path'],'--execute','--source-ref',json.dumps(sr),
                '--variant','native_AR','--owned-process-ref',json.dumps(expected),'--output',str(ctl.out/'INITIAL-LAUNCH-PROFILE.json')])
            _,summary['initial_profile_child']=ctl.call('AR-initial-only-environment',command,cap=30)
            ranks=[]
            for rank in range(4):
                rr=C.ref(receipt/('NATIVE-AR-RANK-%d.json'%rank));rv=C.obj(rr)
                C.need(rv['schema']=='bole.actual-native-ar-worker-receipt/v1'and rv['source']==sr and
                       rv['rank']==rank and rv['primary']is None,'actual native AR frozen rank capture')
                C.checked(rv['raw']);ranks.append(dict(receipt=rr,raw=rv['raw']))
            bundle=dict(schema='bole.actual-four-rank-native-ar-inputs/v1',source=sr,http=http_ref,journal=journals,
                snapshots=snapshots,snapshot_refs=snapshot_refs,host_bindings=bindings,ranks=ranks,frontend_binding=frontend,
                docker_inspect_ref=C.ref(ctl.out/'DOCKER-INSPECT.json'),server_command_ref=C.ref(receipt/'SERVER_COMMAND.json'),
                model_manifest_ref=m['model_manifest_ref'],launch_profile_ref=C.ref(ctl.out/'INITIAL-LAUNCH-PROFILE.json'),
                launch_profile_semantics='exec-initial-only; not current os.environ after in-process update',
                worker_signal_sent=False)
            summary['model_release']=close(ctl)
            ar_bundle_ref=C.write(out/'NATIVE-AR-BUNDLE.json',bundle)
            onbundle=dict(C.obj(x['G1_bundle']),docker_inspect_ref=x['G1_docker_inspect'],
                server_command_ref=x['G1_server_command'],model_manifest_ref=m['model_manifest_ref'],
                launch_profile_ref=x['G1_initial_profile'],launch_profile_semantics='exec-initial-only; not current os.environ')
            onbundle_ref=C.write(out/'BOLE-BUNDLE.json',onbundle)
            pair_ref=C.write(out/'PAIR-INPUTS.json',dict(schema='bole.actual-native-ar-bole-pair-inputs/v1',
                source=sr,scope=m['scope'],native_AR=ar_bundle_ref,BOLE=onbundle_ref,inputs_ref=x['frozen_inputs'],model_ready=False))
            extra=[]
            def collect(v):
                if type(v)is dict:
                    if set(v)in({'path','bytes','sha256'},{'path','sha256'}):C.checked(v);extra.append(C.ref(v['path']))
                    else:
                        for z in v.values():collect(z)
                elif type(v)is list:
                    for z in v:collect(z)
            collect(bundle);collect(onbundle);collect(pair_ref)
            collect([ar_bundle_ref,onbundle_ref,summary['model_release']])
            collect([r['response']for r in http['rows']])
            consumer=ctl_for('cpu-consumer',extra=extra)
            summary['independent_child']=child(consumer,'PAIR-INDEPENDENT',[x['files']['consume_pair_entry.py']['path'],
                '--execute','--owner-inputs-ref',json.dumps(ir),'--pair-inputs-ref',json.dumps(pair_ref),
                '--output',str(consumer.out)],900)
            summary['independent']=C.ref(consumer.out/'ATTRIBUTION.json');value=C.obj(summary['independent'])
            C.need(value['source']==sr and value['native_AR_reference_smoke_pass']is True and value['bounded_pair_pass']is False
                   and value['matched_common_plugin_effects_gate_pending']is True and value['model_ready']is False,
                   'bounded actual native reference only; common effects and model qualification remain pending')
            summary['independent_release']=close(consumer)
        except BaseException as e:
            primary=dict(error=repr(e),traceback=traceback.format_exc(),phase=dict(phase))
            C.write(out/'FIRST-FAULT.json',primary)
        finally:
            for ctl in reversed(owned):
                if ctl.cid and not getattr(ctl,'_native_ar_closed',False):
                    ctl.primary=primary
                    try:ctl.cleanup()
                    except BaseException as e:joint.secondary.append(repr(e))
                joint.secondary.extend(ctl.secondary)
            after={}
            try:
                for r in readset:C.checked(r);after[r['path']]=r['sha256']
            except BaseException as e:joint.secondary.append('source-after '+repr(e))
            joint.secondary.extend(S.formal_time_failures(joint.deadline))
            if joint.cleanup_used>180:joint.secondary.append('original joint cleanup180 exceeded')
            rr=C.write(out/'RESULT.json',dict(schema='bole.actual-native-ar-finite-owner/v1',inputs=ir,source=sr,
                primary=primary,secondary=joint.secondary,summary=summary,source_before=before,source_after=after,
                private_namespace=namespace_proof,phase_seconds=3600,cleanup_seconds=180,cleanup_spent=joint.cleanup_used,
                elapsed=time.monotonic()-start,actual_host_argv=argv,worker_signal_sent=False,
                native_AR_reference_smoke_pass=primary is None and not joint.secondary and before==after,
                bounded_pair_pass=False,matched_common_plugin_effects_gate_pending=True,model_ready=False,
                task_ready=False,performance_ready=False,E2E_measured=False,formal_success=False))
            print(json.dumps(dict(result=rr,model_ready=False,formal_success=False)),flush=True)
        return 3 if primary or joint.secondary or before!=after else 0


if __name__=='__main__':raise SystemExit(main())
