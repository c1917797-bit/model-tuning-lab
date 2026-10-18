"""Pure CPU owner boundary controls; these never create a process or device."""
import ast
import copy
import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import common as C
import owner as O
import cpu_owner as U


def function(filename,name):
    tree=ast.parse((HERE/filename).read_bytes())
    return next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name==name)


def fixture():
    cid='a'*64;mounts={'/exact/input':('/exact/input',False),'/exact/output':('/adakv-results',True)}
    env={'ASCEND_RT_VISIBLE_DEVICES':'','TORCH_DEVICE_BACKEND_AUTOLOAD':'0'}
    child=['-I','-B','/exact/cpu_guest.py'];name='actual-fixed-owner';guest=145
    host=dict(Privileged=False,ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],
              Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,CpusetCpus=str(guest),PidsLimit=256,
              IpcMode='private',NetworkMode='none',LogConfig={'Type':'none'},Devices=[],
              DeviceRequests=[],DeviceCgroupRules=[],PortBindings={})
    config=dict(Labels={'qwen36.owner':U.OWNER},Env=[k+'='+v for k,v in env.items()],
                Entrypoint=['/bin/bash'],Cmd=['-c',U.CANN_WRAPPER,'boletree116',U.PY,*child])
    value=dict(Id=cid,Image=C.IMAGE,Name='/'+name,Config=config,HostConfig=host,ExecIDs=[],
               Mounts=[dict(Source=k,Destination=v[0],RW=v[1])for k,v in mounts.items()],
               State={'OOMKilled':False})
    return value,(cid,mounts,env,guest,name,child)


class OwnerControls(unittest.TestCase):
    def test_01_exact_npu_donor(self):
        raw=(HERE/'DONOR_NPU_OWNER.py').read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),
                         (16858,'a5bf934cd7e749aa3b630da2039969a2d8e3cce52d4c0756a52e73299edc543d'))

    def test_02_exact_cpu_donor(self):
        raw=(HERE/'DONOR_CPU_OWNER.py').read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),
                         (16387,'6159466bc6347ab6f28c18537cc9dcc6fee37db0bb288e94652b32e6c8288812'))

    def test_03_original_resource_helpers(self):
        for new,old,names in [('owner.py','DONOR_NPU_OWNER.py',('exact_methods','device_proof','scan','storage_check')),
                              ('cpu_owner.py','DONOR_CPU_OWNER.py',('docker_argv','create_argv','inspect_owned','output_scan','storage_check'))]:
            for name in names:
                self.assertEqual(ast.dump(function(new,name)),ast.dump(function(old,name)))

    def test_04_complete_inverse_controller(self):
        text=ast.get_source_segment((HERE/'owner.py').read_text(),function('owner.py','controller'))
        changes=[(";d.START=C.START;d.CUT=C.CUT",''),
                 ("own['controller_files']","own['files']"),
                 ("BOLE_FIA_FIXED_FRAME_ENABLE='1'","BOLE_PAGED_TREE_ENABLE='1'"),
                 ("schema='bole.fia-replay-plan/v1'","schema='bole.tree-plan/v118t'"),
                 (",work_deadline=min(C.CUT-180,time.time()+560,a.whole_epoch_deadline-180)",''),
                 ("own['files']['guest.py']","own['files']['guest116.py']"),
                 ("'bole-fia-fixed-'+str(time.time_ns())","'boletree116-'+str(time.time_ns())"),
                 ("schema='bole.fia-replay-arm/v1'","schema='bole.tree-arm/v118t'"),
                 ("HERE/'owner.py'","HERE/'owner116.py'")]
        for before,after in changes:
            self.assertIn(before,text);text=text.replace(before,after)
        self.assertEqual(ast.dump(ast.parse(text).body[0]),ast.dump(function('DONOR_NPU_OWNER.py','controller')))

    def test_05_device_free_create_command(self):
        args=U.create_argv(145,{}, {},'fixture',['-I','-B','/f.py'])
        self.assertFalse(any(x.startswith('--device')for x in args))
        self.assertEqual(args[args.index('--memory')+1],str(8*2**30))
        self.assertEqual(args[args.index('--memory-swap')+1],str(8*2**30))
        self.assertEqual(args[args.index('--cpus')+1],'1')
        self.assertIn(C.IMAGE,args)

    def test_06_cpu_exact_inspect_pass(self):
        value,args=fixture();self.assertIs(U.inspect_owned(value,*args),value)

    def test_07_cpu_memory_rejected(self):
        value,args=fixture();value['HostConfig']['Memory']+=1
        with self.assertRaises(ValueError):U.inspect_owned(value,*args)

    def test_08_cpu_npu_device_rejected(self):
        value,args=fixture();value['HostConfig']['Devices']=[{'PathOnHost':'/dev/davinci4'}]
        with self.assertRaises(ValueError):U.inspect_owned(value,*args)

    def test_09_foreign_cid_rejected(self):
        value,args=fixture();value['Id']='b'*64
        with self.assertRaises(ValueError):U.inspect_owned(value,*args)

    def test_10_wrong_cpu_rejected(self):
        value,args=fixture();value['HostConfig']['CpusetCpus']='144'
        with self.assertRaises(ValueError):U.inspect_owned(value,*args)

    def test_11_extra_write_mount_rejected(self):
        value,args=fixture();value['Mounts'][0]['RW']=True
        with self.assertRaises(ValueError):U.inspect_owned(value,*args)

    def test_12_oom_rejected(self):
        value,args=fixture();value['State']['OOMKilled']=True
        with self.assertRaises(ValueError):U.inspect_owned(value,*args)

    def test_13_full_npu_cutoff(self):
        with patch.object(C,'authority',return_value={}),patch.object(C.time,'time',return_value=C.CUT-900):
            with self.assertRaises(ValueError):C.window({},whole=900)
        with patch.object(C,'authority',return_value={}),patch.object(C.time,'time',return_value=C.CUT-900-.01):
            C.window({},whole=900)

    def test_14_full_cpu_cutoff(self):
        with patch.object(C,'authority',return_value={}),patch.object(C.time,'time',return_value=C.CUT-1000):
            with self.assertRaises(ValueError):C.window({},whole=1000)

    def test_15_baseline_failure_cannot_intervene(self):
        outer=dict(schema='bole.fia-replay-stage/v1',source=1,authority=2,plan=3,
                   primary=None,NPU=True,qualified=False,result=4)
        inner=dict(schema='bole.fia-original-replay-and-parameter-probe/v1',source=1,
                   qualified=False,diagnostic_complete=True,baseline_gate_pass=False,
                   intervention_executed=True,replay_qualified=False)
        with patch.object(O,'obj',return_value=inner):
            with self.assertRaises(ValueError):O.receive(outer,1,2,3)

    def test_16_qualification_never_promoted(self):
        outer=dict(schema='bole.fia-replay-stage/v1',source=1,authority=2,plan=3,
                   primary=None,NPU=True,qualified=True,result=4)
        with self.assertRaises(ValueError):O.receive(outer,1,2,3)

    def test_17_docker_wrapper_only_actual_docker(self):
        with self.assertRaises(ValueError):U.docker_argv(['/bin/sh'])
        self.assertEqual(U.docker_argv(['/usr/bin/docker','inspect','x']),
                         ['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker','inspect','x'])

    def test_18_no_duplicate_ref_identity(self):
        with self.assertRaises(ValueError):
            C.dedup([dict(path='/x',bytes=1,sha256='a'*64),dict(path='/x',bytes=2,sha256='a'*64)])

    def test_19_control_skip_rejected(self):
        import cpu_guest
        with self.assertRaises(ValueError):cpu_guest.control_count('Ran 20 tests in 0.01s\n\nOK (skipped=1)\n')

    def test_20_ambiguous_control_count_rejected(self):
        import cpu_guest
        with self.assertRaises(ValueError):cpu_guest.control_count('Ran 19 tests in 0.01s\nRan 20 tests in 0.01s\n\nOK\n')


class TicketControls(unittest.TestCase):
    def alias_fixture(self):
        import ticket as T
        def ref(path, data):
            return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        source=ref('/fixture/new/SOURCE_MANIFEST.json',b'same-source')
        root=C.OUTROOT+'/cpu'
        owner_ref=ref(root+'/RESULT.json',b'owner')
        manifest=dict(output_root=C.OUTROOT,image=C.IMAGE,
                      files={'cpu_guest.py':ref('/fixture/new/cpu_guest.py',b'guest')})
        owner=dict(source=source,cid='a'*64,
                   stage_result=ref(root+'/preflight/STAGE_RESULT.json',b'stage'))
        stage={field:ref('/adakv-results/preflight/'+name,name.encode())
               for field,name in T.OUTPUTS.items()}
        mapped={field:dict(value,path=root+'/preflight/'+T.OUTPUTS[field])
                for field,value in stage.items()}
        inspect_ref=ref(root+'/FINAL_INSPECT.json',b'actual-final-inspect-fixture')
        inspect=dict(Id=owner['cid'],Image=C.IMAGE,ExecIDs=[],
            State=dict(Running=False,Pid=0,ExitCode=0,OOMKilled=False),
            HostConfig=dict(Devices=[],DeviceRequests=[],DeviceCgroupRules=[],
                            ReadonlyRootfs=True,Privileged=False),
            Config=dict(Labels={'qwen36.owner':U.OWNER},
                        Cmd=['-I','-B',manifest['files']['cpu_guest.py']['path'],
                             '--execute','--source-ref',__import__('json').dumps(source),
                             '--output','/adakv-results/preflight']),
            Mounts=[dict(Source=root,Destination='/adakv-results',RW=True,Type='bind')])
        return source,manifest,owner_ref,owner,stage,inspect,inspect_ref,mapped

    def resolve(self,fixture):
        import ticket as T
        source,manifest,owner_ref,owner,stage,inspect,inspect_ref,mapped=fixture
        expected={value['path']:value for value in mapped.values()}
        def actual_ref(path):
            self.assertEqual(str(path),inspect_ref['path']);return inspect_ref
        def actual_obj(reference):
            self.assertEqual(reference,inspect_ref);return inspect
        def checked(reference):
            C.need(expected.get(reference['path'])==reference,'exact metadata fixture bytes')
            return Path(reference['path'])
        with patch.object(T.C,'ref',side_effect=actual_ref),patch.object(T.C,'obj',side_effect=actual_obj),patch.object(T.C,'checked',side_effect=checked):
            return T.resolve_outputs(source,manifest,owner_ref,owner,stage)

    def test_21_exact_three_aliases_preserve_original_stage_refs(self):
        fixture=self.alias_fixture();before=copy.deepcopy(fixture[4])
        mapped,inspect_ref=self.resolve(fixture)
        self.assertEqual(mapped,fixture[7]);self.assertEqual(inspect_ref,fixture[6])
        self.assertEqual(fixture[4],before)
        for field in mapped:
            self.assertEqual(mapped[field]['sha256'],before[field]['sha256'])
            self.assertEqual(mapped[field]['bytes'],before[field]['bytes'])

    def test_22_second_rw_and_any_nested_proof_shadow_rejected(self):
        import ticket as T
        for destination,rw in [('/second',True),('/adakv-results/preflight',False),
                               *(('/adakv-results/preflight/'+name,False)for name in T.OUTPUTS.values())]:
            fixture=self.alias_fixture()
            fixture[5]['Mounts'].append(dict(Source='/foreign',Destination=destination,RW=rw,Type='bind'))
            with self.subTest(destination=destination),self.assertRaises(ValueError):self.resolve(fixture)

    def test_23_wrong_cid_owner_source_argv_and_live_state_rejected(self):
        for kind in ('cid','label','source','guest','running','oom','device'):
            fixture=self.alias_fixture();inspect=fixture[5]
            if kind=='cid':inspect['Id']='b'*64
            elif kind=='label':inspect['Config']['Labels']['qwen36.owner']='bole-tree-CPUPAGED118T'
            elif kind=='source':inspect['Config']['Cmd'][5]='{}'
            elif kind=='guest':inspect['Config']['Cmd'][2]='/fixture/old/cpu116.py'
            elif kind=='running':inspect['State']['Running']=True
            elif kind=='oom':inspect['State']['OOMKilled']=True
            else:inspect['HostConfig']['Devices']=[{'PathOnHost':'/dev/davinci4'}]
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.resolve(fixture)

    def test_24_wrong_proof_paths_and_bytes_rejected_for_each_file(self):
        import ticket as T
        scope={'output_root':C.OUTROOT}
        self.assertEqual(T.output_path(scope,Path(C.OUTROOT)/'ABI_TICKET.json'),
                         Path(C.OUTROOT)/'ABI_TICKET.json')
        for target in (Path('/foreign/ABI_TICKET.json'),Path(C.OUTROOT)/'other.json',
                       Path(C.OUTROOT)/'cpu/ABI_TICKET.json'):
            with self.assertRaises(ValueError):T.output_path(scope,target)
        for field in T.OUTPUTS:
            for kind in ('foreign-path','sha','bytes'):
                fixture=self.alias_fixture();reference=fixture[4][field]
                if kind=='foreign-path':reference['path']='/adakv-results/preflight/../other.json'
                elif kind=='sha':reference['sha256']='0'*64
                else:reference['bytes']+=1
                with self.subTest(field=field,kind=kind),self.assertRaises(ValueError):self.resolve(fixture)
        import plan as P
        source=self.alias_fixture()[0]
        manifest=dict(probe_plan_ref={'path':'/fixture/PLAN.json','bytes':1,'sha256':'a'*64},
                      files={'plan.py':{'path':'/fixture/plan.py','bytes':1,'sha256':'b'*64}})
        tensor=dict(shape=[1],stride=[1],dtype='torch.bfloat16',bytes=2,sha256='c'*64)
        branches={}
        for branch in ('tree','native'):
            inputs={'query':copy.deepcopy(tensor),'key':copy.deepcopy(tensor),'value':copy.deepcopy(tensor)}
            if branch=='tree':inputs.update(atten_mask=copy.deepcopy(tensor),block_table=copy.deepcopy(tensor))
            branches[branch]=dict(inputs=inputs,expected_output=copy.deepcopy(tensor),
                original_CPU64_reference=dict(shape=[3,6,256]if branch=='tree'else[1,6,256],
                    stride=[1536,256,1],dtype='torch.float64',
                    bytes=36864 if branch=='tree'else 12288,sha256='d'*64),
                original_parameters=P.call_parameters(branch),
                original_metrics=dict(nodes=[dict(failed_flat_indices=v)for v in
                    ([[],[],[573]]if branch=='tree'else[[573]])]))
        binding=dict(schema='bole.fia-fixed-frame-input-binding/v1',source=source,
            probe_plan_ref=manifest['probe_plan_ref'],original_raw=P.RAW,original_source=P.SOURCE,
            original_rank_report=P.RANK_REPORT,previous_rounding=P.PREVIOUS,
            original_producers=P.PRODUCERS,fixed_cases=P.CASES,actual_saved_inputs_checked=True,
            original_failure_sets_reproduced=True,original_numeric_failures_unchanged=True,
            qualified=False,NPU=False,branches=branches)
        with patch.object(T.C,'load',return_value=P):
            T.validate_inputs(source,manifest,binding)
            for branch in ('tree','native'):
                for kind in ('missing','shape','stride','dtype','bytes','sha'):
                    bad=copy.deepcopy(binding);row=bad['branches'][branch]
                    if kind=='missing':row.pop('original_CPU64_reference')
                    else:
                        reference=row['original_CPU64_reference']
                        if kind=='shape':reference['shape'][0]+=1
                        elif kind=='stride':reference['stride'][-1]=2
                        elif kind=='dtype':reference['dtype']='torch.float32'
                        elif kind=='bytes':reference['bytes']-=8
                        else:reference['sha256']='incomplete'
                    with self.subTest(branch=branch,reference=kind),self.assertRaises(ValueError):
                        T.validate_inputs(source,manifest,bad)


if __name__=='__main__':unittest.main(verbosity=2)
