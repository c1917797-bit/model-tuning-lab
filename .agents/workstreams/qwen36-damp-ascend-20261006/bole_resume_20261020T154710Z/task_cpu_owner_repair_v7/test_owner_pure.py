"""Pure schema/resource/stop-authority controls. No host/Docker/NPU/code execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import cpu_host as O
import he_owned as E


def packet_root():
    p=P/'task_packet'
    return p if p.is_dir()else P.parent/'task_decoder_scorer'


class Source(unittest.TestCase):
    def test_exact_frozen_packet_unchanged(self):
        self.assertEqual(C.packet(packet_root())['sha256'],C.PACKET_SHA)

    def test_new_authority_budget_no_extension(self):
        with tempfile.TemporaryDirectory()as tmp:
            ref=C.write(Path(tmp)/'synthetic-clock',dict(start_epoch=0,cutoff_epoch=200))
            with patch.object(C.time,'time',return_value=100):
                C.authority(ref,99)
                with self.assertRaises(ValueError):C.authority(ref,100)

    def test_default_OFF_and_help_no_accelerator_import(self):
        for name in('prepare_owner','cpu_steps','cpu_host'):
            for extra in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/(name+'.py')),*extra],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,(name,extra,r.stderr))
                if not extra:self.assertIs(json.loads(r.stdout)['enabled'],False)

    def test_no_toplevel_runner_or_torch_import(self):
        for f in P.glob('*.py'):
            tree=ast.parse(f.read_bytes())
            for node in tree.body:
                if isinstance(node,ast.Import):names=[a.name for a in node.names]
                elif isinstance(node,ast.ImportFrom):names=[node.module or'']
                else:continue
                self.assertFalse(any(n.split('.')[0]in{'torch','torch_npu','vllm','vllm_ascend','runner'}for n in names))


class Resource(unittest.TestCase):
    def memory(self,limit):
        temp=tempfile.TemporaryDirectory();root=Path(temp.name);parent=root/'parent';child=parent/'child';child.mkdir(parents=True)
        for p,v in((parent,str(16*C.GIB)),(child,str(limit))):
            (p/'memory.max').write_text(v);(p/'memory.current').write_text('1234');(p/'memory.swap.max').write_text('0')
        H=types.SimpleNamespace(hierarchy=lambda pid,ctl:(2,'synthetic',str(root),[child,parent]))
        return temp,H

    def test_actual_memory_chain_exact_guest_cap(self):
        t,H=self.memory(8*C.GIB)
        try:self.assertEqual(O.memory_view(H,123,8*C.GIB)['effective_bytes'],8*C.GIB)
        finally:t.cleanup()

    def test_insufficient_effective_memory_rejected(self):
        t,H=self.memory(4*C.GIB)
        try:
            with self.assertRaises(ValueError):O.memory_view(H,123,8*C.GIB)
        finally:t.cleanup()

    def test_original_observation_failure_is_not_bypassed(self):
        def fail(*a,**k):raise ValueError('synthetic original actual FD conflict')
        with self.assertRaisesRegex(ValueError,'actual FD'):
            O.observe_cpu(types.SimpleNamespace(observe=fail),'synthetic')

    def test_derived_CPU145_can_be_original_reserve_without_mutating_original(self):
        a=dict(host_cpu=166,guest_cpus=[0,1,2,3],reserve_cpus=[144,145],host_cpu_budget=1,guest_cpu_budget=4,reserve_cpu_budget=2,common_finite_capacity=None)
        before=copy.deepcopy(a);derived=N.cpu_profile(C,a)
        self.assertEqual(a,before);self.assertEqual(derived['original025_allocation'],a)
        self.assertEqual(derived['actual_helper_cpus'],[145]);self.assertEqual(derived['derived_reserve_cpus'],[144,0])
        self.assertEqual(derived['unused_main_guest_cpus'],[1,2,3]);self.assertIs(derived['global_CPU_idleness_measured'],False)

    def test_derived_profile_rejects_CPU145_outside_actual_original_pool(self):
        a=dict(host_cpu=166,guest_cpus=[0,1,2,3],reserve_cpus=[144,146],host_cpu_budget=1,guest_cpu_budget=4,reserve_cpu_budget=2,common_finite_capacity=7)
        with self.assertRaises(ValueError):N.cpu_profile(C,a)

    def test_derived_profile_preserves_sevenCPU_capacity_and_reserve2(self):
        a=dict(host_cpu=166,guest_cpus=[0,1,2,3],reserve_cpus=[144,145],host_cpu_budget=1,guest_cpu_budget=4,reserve_cpu_budget=2,common_finite_capacity=6)
        with self.assertRaises(ValueError):N.cpu_profile(C,a)
        a['common_finite_capacity']=7;a['reserve_cpu_budget']=1
        with self.assertRaises(ValueError):N.cpu_profile(C,a)

    def test_original7CPU_profile_remains_required_in_source(self):
        # Read supplied exact original025 function only; never import its host controller.
        donor=P.parents[1]/'g1_review_v2/safety_host.py'
        if not donor.is_file():self.skipTest('local exact donor fixture only; runtime reads original Ref')
        body=donor.read_bytes();self.assertEqual((len(body),hashlib.sha256(body).hexdigest()),N.ORIGINAL['safety_host.py'])
        node=next(n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef)and n.name=='cpu_admission')
        scope={'c':types.SimpleNamespace(require=C.need)};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual025-cpu-admission','exec'),scope)
        def view(cap,cpus,quota):return dict(effective_capacity=cap,effective_cpus=cpus,quota_ancestors=[dict(key='same-ancestor',capacity=quota)])
        host=view(1,[166],7);daemon=view(7,[145,146,147,148,149,150,166],7)
        value=scope['cpu_admission'](host,daemon)
        self.assertEqual(value['host_cpu'],166);self.assertEqual(value['guest_cpus'][0],145)
        self.assertEqual(value['reserve_cpu_budget'],2)
        daemon['quota_ancestors'][0]['capacity']=6
        with self.assertRaises(ValueError):scope['cpu_admission'](host,daemon)


class HEStopAuthority(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0,str(packet_root()));import he_policy
        self.policy=he_policy
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        stage=C.write(root/'stage',dict(source_root='/public/source',suite_root='/public/suite',input_root='/public/inputs',
            capsule_ref=dict(sha256='b'*64)))
        class Base:
            def __init__(self,a,start):self.out=a.output_dir;self.cid=None;self.cpu=dict(host_cpu=166,guest_cpus=[145,146,147,148],reserve_cpus=[149,150])
        H=types.SimpleNamespace(controller=lambda *args:Base)
        c=types.SimpleNamespace(sha=lambda path:C.ref(path)['sha256'],canonical=C.canonical)
        S=types.SimpleNamespace(__file__=str(P/'he_owned.py'),DOCKER='/usr/bin/docker')
        cls=E.create_class(C,c,S,H,None,he_policy)
        out=root/'run-bole-task-cpu-synthetic'/'he-controls';out.mkdir(parents=True)
        self.he=cls(types.SimpleNamespace(output_dir=out),0,stage,dict(sha256='synthetic'))
        self.he.cid='c'*64;self.he.expected['cid']=self.he.cid
        command=self.he.command;args=command[command.index(C.IMAGE)+1:]
        self.value=dict(Id=self.he.cid,Image=C.IMAGE,Name='/'+self.he.name,Path='/usr/bin/env',Args=args,
            Config=dict(Image=C.IMAGE,Entrypoint=['/usr/bin/env'],Cmd=args,User='65534:65534',WorkingDir='/tmp'),
            HostConfig=dict(Runtime='runc',NetworkMode='none',IpcMode='private',PidMode='',UTSMode='',Privileged=False,
                ReadonlyRootfs=True,Memory=2*C.GIB,MemorySwap=2*C.GIB,NanoCpus=10**9,PidsLimit=64,Tmpfs={'/tmp':he_policy.TMPFS},
                Devices=[],DeviceRequests=None,DeviceCgroupRules=None,VolumesFrom=None,Links=None,PortBindings={},ExtraHosts=None,
                CapAdd=None,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],CpusetCpus='',
                Ulimits=[dict(Name='nofile',Soft=128,Hard=128),dict(Name='fsize',Soft=8388608,Hard=8388608)]),
            Mounts=[dict(Source='/public/'+n,Destination='/'+n,RW=False,Type='bind',Propagation='rprivate')for n in('source','suite','inputs')],
            State=dict(Running=False,Pid=0,OOMKilled=False))
        self.he.call=lambda *args,**kwargs:(dict(stdout=json.dumps([self.value])),None)

    def tearDown(self):self.temp.cleanup()

    def test_exact_stopped_owned_container_can_cleanup(self):
        self.he.inspect(cleanup=True);self.assertTrue(self.he._cleanup_stopped)
        self.assertEqual(self.he._cleanup_owned_identity[0],self.he.cid)

    def test_OOM_outcome_does_not_lose_safe_stop_authority(self):
        self.value['State']['OOMKilled']=True
        self.he.inspect(cleanup=True)
        self.assertTrue(self.he._cleanup_stopped)

    def test_prestart_update_success_persistence_failure_still_cleanup(self):
        self.value['HostConfig']['CpusetCpus']='145'
        self.assertFalse(self.he.affinity_updated);self.he.inspect(cleanup=True)

    def test_postcommit_CPU_drift_rejected(self):
        self.he.affinity_updated=True
        with self.assertRaises(ValueError):self.he.inspect(cleanup=True)

    def test_foreign_CID_rejected(self):
        self.value['Id']='d'*64
        with self.assertRaises(ValueError):self.he.inspect(cleanup=True)

    def test_npu_runtime_or_device_rejected(self):
        self.value['HostConfig']['Runtime']='ascend'
        with self.assertRaises(ValueError):self.he.inspect(cleanup=True)
        self.value['HostConfig']['Runtime']='runc';self.value['HostConfig']['Devices']=[dict(PathOnHost='/dev/davinci4')]
        with self.assertRaises(ValueError):self.he.inspect(cleanup=True)

    def test_writable_secret_mount_rejected(self):
        self.value['Mounts'][0]['RW']=True
        with self.assertRaises(ValueError):self.he.inspect(cleanup=True)

    def test_create_argv_remains_exact_frozen_HE_policy(self):
        self.assertNotIn('--cpuset-cpus',self.he.command)
        self.assertEqual(self.he.command,self.policy.argv(self.he.name,C.IMAGE,'/public/source','/public/suite','/public/inputs','b'*64,'controls'))


if __name__=='__main__':unittest.main()
