"""Synthetic diagnostic/schema/source tests. No network/device/container/eval run."""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import probe_evidence as E
import main_quiescence as Q
import diagnostic_host as D
import he_policy as H
import he_runtime_probe as Probe
import lock_evidence as L
import network_evidence as V


def observation():
    return dict(schema='bole.actual-HE-runtime-isolation-diagnostic/v3',capsule_sha256='c'*64,
        interpreter=dict(version='synthetic fixture',version_info=[3,9,0,'final',0],implementation='cpython',executable='/usr/bin/python3'),
        environment=dict(ASCEND_VISIBLE_DEVICES='',HOME='/tmp'),conditions=dict(ASCEND_VISIBLE_DEVICES_empty=True,
            HOME_tmp=True,sys_class_interfaces_loopback_only=False),sys_class_net_names=['eth0','lo'],
        proc_self_net_dev='Inter-| Receive | Transmit\n lo: 0 0\n',net_namespace_link='net:[123]',
        network_details=details_fixture(['eth0','lo']),original_runtime_guard=dict(called=True,passed=False,error='ValueError: actual no-network namespace'),
        diagnostic_only=True,evaluator_executed=False,generated_code_executed=False,task_score_produced=False,
        full_software_qualification_accepted=False,network_safety_accepted=False,NPU=False)


def lock_fixture():
    path='/exact/MAIN_ADMISSION.lock';identity=dict(device_major=0,device_minor=45,inode=1001)
    line='1: FLOCK ADVISORY WRITE 90 00:2d:1001 0 EOF'
    return dict(schema=L.SCHEMA,policy_ref=dict(path='/exact/policy',bytes=1,sha256='a'*64),lock_path=path,
        owner_pid=90,owner_start_ticks=123,file_identity=identity,
        proc_locks_matching_lines=[line],proc_locks_bytes=len(line)+1,proc_locks_sha256='b'*64,
        inherited_fds=[dict(fd=3,link=path,file_identity=identity,regular_file=True,fdinfo='pos:\t0\nlock:\t'+line+'\n')],
        acquired_or_released_lock=False,capture_phase='before-sandbox-create',captured_monotonic=1.5)


def details_fixture(names):
    rows=[]
    for i,name in enumerate(names):
        ordinary=name=='bonding_masters'
        attributes={key:dict(ok=True,text='0\n',error=None)for key in V.ATTRIBUTES}
        if ordinary:attributes={key:dict(ok=False,text=None,error=dict(type='NotADirectoryError',errno=20))for key in V.ATTRIBUTES}
        else:attributes['carrier']=dict(ok=False,text=None,error=dict(type='OSError',errno=22))
        rows.append(dict(name=name,lstat=dict(mode=0o100644 if ordinary else 0o120777,device=5,inode=100+i),
            is_symlink=not ordinary,is_dir=not ordinary,symlink_target=None if ordinary else '../../devices/virtual/net/'+name,
            attributes=attributes))
    return dict(schema='bole.actual-HE-readonly-network-details/v1',sys_entries=rows,
        proc_routes={key:dict(ok=True,text='',error=None)for key in V.ROUTES},guest_process=dict(pid=1,start_ticks=555),
        interpretation_performed=False,network_safety_accepted=False)


def namespace_fixture():
    def row(pid,ticks,inode):return dict(pid=pid,start_ticks=ticks,link='net:['+str(inode)+']',file_identity=dict(device=4,inode=inode))
    return dict(schema='bole.actual-HE-host-guest-netns-observation/v1',container_id='d'*64,
        bound_guest_host_pid=501,bound_guest_start_ticks=555,
        namespaces=dict(owner=row(90,123,999),host_init=row(1,1,999),guest=row(501,555,123)),
        comparisons=dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False),
        setns_performed=False,sockets_or_ioctls_performed=False,network_safety_accepted=False)


class Diagnostics(unittest.TestCase):
    def parse(self,v):return E.parse_probe(E.INTERPRETER_MARKER+json.dumps(v['interpreter'])+'\n'+E.MARKER+json.dumps(v),'c'*64)
    def test_guard_failure_is_an_observation_never_network_or_full_qualification(self):
        v=self.parse(observation());self.assertIs(v['original_runtime_guard']['passed'],False)
        self.assertIs(v['network_safety_accepted'],False);self.assertIs(v['full_software_qualification_accepted'],False)
    def test_each_of_three_actual_condition_values_independently_checked(self):
        for key in('ASCEND_VISIBLE_DEVICES_empty','HOME_tmp','sys_class_interfaces_loopback_only'):
            v=observation();v['conditions'][key]=not v['conditions'][key]
            with self.assertRaises(ValueError,msg=key):self.parse(v)
    def test_extra_environment_or_qualification_claim_rejected(self):
        for key,value in(('environment',dict(ASCEND_VISIBLE_DEVICES='',HOME='/tmp',UNRELATED='forbidden-output')),
                           ('network_safety_accepted',True),('evaluator_executed',True)):
            v=observation();v[key]=value
            with self.assertRaises(ValueError):self.parse(v)
    def test_missing_duplicate_or_wrong_source_observation_rejected(self):
        text=E.MARKER+json.dumps(observation())
        with self.assertRaises(ValueError):E.parse_probe('', 'c'*64)
        with self.assertRaises(ValueError):E.parse_probe(text+'\n'+text,'c'*64)
        with self.assertRaises(ValueError):E.parse_probe(text,'d'*64)
    def test_probe_calls_only_original_runtime_never_evaluator_or_worker_run(self):
        tree=ast.parse((P/'he_runtime_probe.py').read_bytes())
        attrs=[n.func.attr for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
        self.assertIn('runtime',attrs);self.assertNotIn('run',attrs);self.assertNotIn('evaluate_functional_correctness',attrs)
        names=[n.func.id for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)]
        self.assertFalse({'eval','exec'}&set(names))
    def test_original_resource_helpers_and_guard_files_frozen(self):
        expected=C.obj(C.ref(P/'PREVIOUS_CPU_EXPECTED.json'));self.assertEqual(C.ref(P/'PREVIOUS_CPU_EXPECTED.json')['sha256'],C.PREVIOUS_EXPECTED_SHA)
        for name,key in(('task_contract.py','original_task_contract'),('he_policy.py','original_he_policy')):
            a=C.ref(P/name);self.assertEqual((a['bytes'],a['sha256']),(expected[key]['bytes'],expected[key]['sha256']))
        old=P.parent/'task_cpu_owner_qualification_v10'
        if old.is_dir():
            for name in('owner_namespace.py','he_owned.py'):self.assertEqual((P/name).read_bytes(),(old/name).read_bytes())
    def test_actual_CPU3_records_are_explicit_data_not_admission_flags(self):
        v=C.obj(C.ref(P/'CPU3_ACTUAL_ENTRIES.json'));self.assertEqual(len(v['entries']),3)
        self.assertIs(v['actual_runtime_success_inferred'],False)
        self.assertEqual([e['owned_ref']['bytes']for e in v['entries']],[209038,266560,329260])
        for e in v['entries']:
            self.assertEqual(set(e),{'owned_ref','source_ref','cid','profile'});self.assertEqual(e['profile'],Q.CPU3_PROFILE)
    def test_loaded_runtime_guard_source_pin_rejects_mutated_code(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'runtime_fixture.py';source='def runtime():\n    return True\n';p.write_text(source)
            scope={};exec(compile(source,str(p),'exec'),scope);f=scope['runtime']
            Probe.original_guard(f,p,'runtime')
            f.__code__=f.__code__.replace(co_consts=(None,False))
            with self.assertRaises(ValueError):Probe.original_guard(f,p,'runtime')

    def test_top_level_guard_rejects_nested_or_duplicate_same_name(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'runtime_fixture.py'
            for source in('def outer():\n    def runtime():\n        return True\n    return runtime\n',
                           'def runtime():\n    return True\ndef runtime():\n    return True\n'):
                p.write_text(source);scope={};exec(compile(source,str(p),'exec'),scope)
                f=scope['outer']()if'outer'in scope else scope['runtime']
                with self.assertRaises(ValueError):Probe.original_guard(f,p,'runtime')

    def test_guard_uses_only_cross_version_top_level_code_names(self):
        tree=ast.parse((P/'he_runtime_probe.py').read_bytes())
        attributes={n.attr for n in ast.walk(tree)if isinstance(n,ast.Attribute)}
        self.assertNotIn('co_qualname',attributes);self.assertIn('co_name',attributes)
        self.assertIn('__qualname__',attributes);self.assertIn('co_consts',attributes)

    def test_interpreter_receipt_is_bounded_actual_data_not_version_gate(self):
        for version in([3,9,2,'final',0],[3,12,13,'final',0]):
            v=observation();v['interpreter']['version_info']=version;self.parse(v)
        for replacement in(dict(version_info=[3,9]),dict(executable='x'*2049),dict(version_info=[3,9,0,'unknown',0])):
            v=observation();v['interpreter'].update(replacement)
            with self.assertRaises(ValueError):self.parse(v)
        v=observation()
        with self.assertRaises(ValueError):E.parse_probe(E.MARKER+json.dumps(v),'c'*64)
        text=E.INTERPRETER_MARKER+json.dumps(dict(v['interpreter'],executable='/different'))+'\n'+E.MARKER+json.dumps(v)
        with self.assertRaises(ValueError):E.parse_probe(text,'c'*64)

    def test_precreate_inherited_lock_joins_actual_pid_inode_fd_and_kernel_row(self):
        v=lock_fixture();self.assertEqual(L.validate(v,v['policy_ref'],v['lock_path']),v)
        for key,replacement in(('owner_pid',91),('owner_start_ticks',0),('acquired_or_released_lock',True),
                                ('capture_phase','after-create'),('proc_locks_matching_lines',[])):
            w=copy.deepcopy(v);w[key]=replacement
            with self.assertRaises(ValueError,msg=key):L.validate(w,v['policy_ref'],v['lock_path'])
        for key,replacement in(('link','/another/MAIN_ADMISSION.lock'),('fdinfo','pos:\t0\n'),('regular_file',False)):
            w=copy.deepcopy(v);w['inherited_fds'][0][key]=replacement
            with self.assertRaises(ValueError,msg=key):L.validate(w,v['policy_ref'],v['lock_path'])

    def test_kernel_lock_parser_rejects_foreign_read_waiting_posix_and_partial(self):
        value=lock_fixture();pid=value['owner_pid'];identity=value['file_identity'];line=value['proc_locks_matching_lines'][0]
        self.assertTrue(L.matching(line,pid,identity))
        for bad in(line.replace('WRITE','READ'),line.replace('FLOCK','POSIX'),line.replace('90','91',1),
                   line.replace('1001','1002'),line.replace(' 0 EOF',' 1 EOF'),line.replace(' FLOCK',' -> FLOCK')):
            self.assertFalse(L.matching(bad,pid,identity),bad)

    def test_lock_capture_never_acquires_and_precedes_create_with_original_cold_clock(self):
        tree=ast.parse((P/'lock_evidence.py').read_bytes())
        calls={n.func.attr if isinstance(n.func,ast.Attribute)else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call)and isinstance(n.func,(ast.Attribute,ast.Name))}
        self.assertFalse({'flock','lockf','fcntl','acquire','release'}&calls)
        host=(P/'diagnostic_host.py').read_text()
        self.assertLess(host.index("summary['inherited_lock_ref']="),host.index('live,_=ctl.create_start()'))
        self.assertLess(host.index('entry_start=time.monotonic()'),host.index('x=C.inputs(ir)'))
        self.assertIn('start=entry_start',host);self.assertIn('90+180<entry_start+3600',host)

    def test_network_file_vs_interface_receipts_keep_os_errors_without_whitelisting(self):
        value=details_fixture(['bonding_masters','erspan0','lo']);V.validate_details(value,['bonding_masters','erspan0','lo'])
        self.assertIs(value['sys_entries'][0]['is_dir'],False)
        self.assertEqual(value['sys_entries'][0]['attributes']['flags']['error']['errno'],20)
        self.assertEqual(value['sys_entries'][1]['attributes']['carrier']['error']['errno'],22)
        self.assertIs(value['network_safety_accepted'],False)

    def test_network_details_require_every_entry_attribute_and_proc_file(self):
        base=details_fixture(['eth0','lo'])
        for mode in('missing-entry','wrong-symlink','missing-attribute','fake-success','missing-route','claim-safe'):
            value=copy.deepcopy(base)
            if mode=='missing-entry':value['sys_entries'].pop()
            elif mode=='wrong-symlink':value['sys_entries'][0]['is_symlink']=False
            elif mode=='missing-attribute':value['sys_entries'][0]['attributes'].pop('iflink')
            elif mode=='fake-success':value['sys_entries'][0]['attributes']['carrier']['ok']=True
            elif mode=='missing-route':value['proc_routes'].pop('ipv6_route')
            else:value['network_safety_accepted']=True
            with self.assertRaises(ValueError,msg=mode):V.validate_details(value,['eth0','lo'])

    def test_readonly_file_capture_retains_enoent_and_enforces_size(self):
        with tempfile.TemporaryDirectory()as tmp:
            path=Path(tmp)/'fixture';self.assertEqual(Probe.read_detail(path,8)['error']['errno'],2)
            path.write_text('0x80\n');self.assertEqual(Probe.read_detail(path,8),dict(ok=True,text='0x80\n',error=None))
            path.write_text('x'*9)
            with self.assertRaises(ValueError):Probe.read_detail(path,8)

    def test_actual_namespace_identity_join_rejects_stale_guest_owner_and_wrong_inode(self):
        binding=dict(container_id='d'*64,host_pid=501,guest_pid=1,start_ticks=555)
        V.validate_namespaces(namespace_fixture(),binding,observation(),90,123)
        for mode in('guest-start','owner-start','guest-pid','wrong-link','wrong-comparison'):
            value=namespace_fixture()
            if mode=='guest-start':value['namespaces']['guest']['start_ticks']+=1
            elif mode=='owner-start':value['namespaces']['owner']['start_ticks']+=1
            elif mode=='guest-pid':value['namespaces']['guest']['pid']+=1
            elif mode=='wrong-link':value['namespaces']['guest']['link']='net:[124]'
            else:value['comparisons']['guest_equals_owner']=True
            with self.assertRaises(ValueError,msg=mode):V.validate_namespaces(value,binding,observation(),90,123)

    def test_namespace_equality_is_reported_without_becoming_safety_acceptance(self):
        binding=dict(container_id='d'*64,host_pid=501,guest_pid=1,start_ticks=555);value=namespace_fixture()
        for role in('owner','host_init'):
            value['namespaces'][role]['link']='net:[123]';value['namespaces'][role]['file_identity']['inode']=123
        value['comparisons']={k:True for k in value['comparisons']}
        V.validate_namespaces(value,binding,observation(),90,123)
        self.assertIs(value['network_safety_accepted'],False)

    def test_network_observation_source_has_no_active_network_or_namespace_operations(self):
        for name in('he_runtime_probe.py','network_evidence.py'):
            tree=ast.parse((P/name).read_bytes())
            calls={n.func.attr if isinstance(n.func,ast.Attribute)else n.func.id for n in ast.walk(tree)
                if isinstance(n,ast.Call)and isinstance(n.func,(ast.Attribute,ast.Name))}
            self.assertFalse({'socket','ioctl','setns','unshare','connect','send','sendto','recv','recvfrom','setsockopt'}&calls)
        host=(P/'diagnostic_host.py').read_text();self.assertIn('V.capture_namespaces(C.obj',host)

    def test_v3_prerequisite_pins_actual_v2_failure_condition_and_full_source_inventory(self):
        expected=C.obj(C.ref(P/'PREVIOUS_DIAGNOSTIC_EXPECTED.json'))
        self.assertEqual(C.ref(P/'PREVIOUS_DIAGNOSTIC_EXPECTED.json')['sha256'],C.PREVIOUS_DIAGNOSTIC_EXPECTED_SHA)
        self.assertEqual(len(expected['actual_refs']),11);self.assertEqual(len(expected['source_files']),14)
        self.assertEqual(expected['actual_refs']['RESULT.json']['sha256'],'6fc2dd28ea5991449fc787535eac989d0924cec1924e3c5aba7278f566fdf7e5')
        self.assertEqual(expected['actual_refs']['READBACK.json']['sha256'],'ed286c06a247283280f2fe70c55f2152b28c0ba474eb615b085fe089f4722694')
        self.assertIs(expected['qualified'],False)
        text=(P/'prepare_diagnostic.py').read_text();self.assertIn('previous-diagnostic-owner-ref',text)
        self.assertIn('previous-diagnostic-independent-ref',text)

    def test_diagnostic_subclass_changes_only_the_actual_entry_token(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);stage=C.write(root/'stage',dict(source_root='/public/source',suite_root='/public/suite',
                input_root='/public/inputs',capsule_ref=dict(sha256='c'*64)))
            class Base:
                def __init__(self,a,start):self.out=a.output_dir;self.cid=None
            fakeH=types.SimpleNamespace(controller=lambda *args:Base)
            fakeC=types.SimpleNamespace(sha=lambda path:C.ref(path)['sha256'])
            fakeS=types.SimpleNamespace(__file__=str(P/'he_owned.py'),DOCKER='/usr/bin/docker')
            cls=D.diagnostic_class(fakeC,fakeS,fakeH,None)
            out=root/'run-bole-task-cpu-probe'/'he-runtime-diagnostic';out.mkdir(parents=True)
            actor=cls(types.SimpleNamespace(output_dir=out),0,stage,dict(synthetic=True))
            original=H.argv(actor.name,C.IMAGE,'/public/source','/public/suite','/public/inputs','c'*64,'controls')
            self.assertEqual([(a,b)for a,b in zip(original,actor.command)if a!=b],
                             [('/source/he_worker.py','/source/he_runtime_probe.py')])
            self.assertEqual(len(original),len(actor.command));self.assertIs(actor.expected['create_argv'],actor.command)

    def test_all_five_diagnostic_CLIs_default_OFF_and_help(self):
        for n in('prepare_diagnostic','prepare_registry','diagnostic_host','probe_evidence','he_runtime_probe'):
            for args in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/(n+'.py')),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,(n,r.stderr))
                if not args:self.assertIs(json.loads(r.stdout)['enabled'],False)


if __name__=='__main__':unittest.main()
