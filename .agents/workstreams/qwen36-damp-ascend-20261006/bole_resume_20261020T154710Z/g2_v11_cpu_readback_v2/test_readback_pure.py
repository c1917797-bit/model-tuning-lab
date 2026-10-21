"""Synthetic fail-closed controls; never an actual qualification/result fixture."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import readback_cpu as R


def write(path,value):path.write_text(json.dumps(value));return R.ref(path)


class PureControls(unittest.TestCase):
 def test_strict_JSON_rejects_duplicate_keys_and_nonfinite(self):
    for raw in('{"x":1,"x":2}','{"v":NaN}','{"v":Infinity}'):
        with self.subTest(raw=raw),self.assertRaises(ValueError):R.parse(raw)
 def test_full_Ref_bytes_SHA_and_ordinary_path_required(self):
    with tempfile.TemporaryDirectory()as tmp:
        p=Path(tmp)/'input';p.write_bytes(b'whole raw');r=R.ref(p);self.assertEqual(R.checked(r),p)
        for bad in(dict(r,sha256='0'*64),dict(r,bytes=r['bytes']+1),dict(r,bytes=True),{'path':r['path'],'sha256':r['sha256']}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):R.checked(bad)
        alias=p.with_name('alias');alias.symlink_to(p)
        with self.assertRaises(ValueError):R.ref(alias)
 def test_original_Ref2_normalizes_only_actual_complete_file(self):
    with tempfile.TemporaryDirectory()as tmp:
        p=Path(tmp)/'data';p.write_bytes(b'original');r=R.ref(p)
        self.assertEqual(R.normalize({k:r[k]for k in('path','sha256')}),r)
        with self.assertRaises(ValueError):R.normalize(dict(path=str(p),sha256='0'*64))
 def test_unique_summary_keeps_noise_and_rejects_duplicate_missing(self):
    value=dict(schema='actual-test-only',tests=322);line=json.dumps(value).encode()
    self.assertEqual(R.one(b'noise\n'+line+b'\nnon-JSON tail\n','actual-test-only'),value)
    for raw in(b'noise\n',line+b'\n'+line):
        with self.subTest(raw=raw),self.assertRaises(ValueError):R.one(raw,'actual-test-only')
 def test_actual_raw_zero_skip_and_exact_counts_are_required(self):
    R.zero_skip(b'test_names ... ok\nRan 25 tests in 0.123s\n\nOK\n',25)
    for raw in(b'Ran 24 tests in 1.0s\nOK\n',b'Ran 25 tests in 1.0s\nOK (skipped=1)\n',b'Ran 25 tests in 1.0s\nFAILED (errors=1)\n',b'caller says pass\n'):
        with self.subTest(raw=raw),self.assertRaises(ValueError):R.zero_skip(raw,25)
 def original_c(self):
    root=P.parent.parent/'g1_review_v2';p=root/'model_contract.py'if root.is_dir()else Path('/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-tp4-model-once-v1-025/model_contract.py');body=p.read_bytes();self.assertEqual((len(body),hashlib.sha256(body).hexdigest()),(13660,'82243c277890aef7c24ea5eb5fbfa0658b314a39c01d7b2a7ddf34b2bf363e9f'))
    spec=importlib.util.spec_from_file_location('_readonly_original025_unit',p);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);return c
 def test_actual_original_CANN_child_argv_and_complete_streams_are_reopened(self):
    c=self.original_c()
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);(root/'CPU.stdout').write_bytes(b'complete\n');(root/'CPU.stderr').write_bytes(b'noise\n');cid='a'*64;args=['actual.py','--execute'];argv=c.docker_argv(cid,args)
        self.assertEqual(argv[7:9],[c.PY,'-B'])
        v=dict(child_termination_observed=True,exit_code=0,child_host_pid=123,requested_argv=argv,actual_host_argv=['/usr/bin/prlimit','--as=unlimited','--',*argv],stdout_ref=R.ref(root/'CPU.stdout'),stderr_ref=R.ref(root/'CPU.stderr'))
        r=write(root/'child.json',v);self.assertEqual(R.child(r,c,cid,args,root,'CPU')['value'],v)
        bad=copy.deepcopy(v);bad['requested_argv'][8]='-I';br=write(root/'bad.json',bad)
        with self.assertRaises(ValueError):R.child(br,c,cid,args,root,'CPU')
 def test_wrong_exit_or_incomplete_actual_child_cannot_qualify(self):
    c=self.original_c()
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);cid='a'*64;args=['script.py'];v=dict(child_termination_observed=False,exit_code=0,child_host_pid=123)
        for n,change in enumerate(({},dict(child_termination_observed=True,exit_code=3),dict(child_termination_observed=True,exit_code=0,child_host_pid=0))):
            with self.subTest(change=change),self.assertRaises(ValueError):R.child(write(root/('bad%d.json'%n),dict(v,**change)),c,cid,args,root,'CPU')
 def test_inspect_must_be_one_actual_full_CID_row_with_original_command(self):
    cid='a'*64
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);r=write(root/'inspect.json',dict(exit_code=0,requested_argv=['/usr/bin/docker','inspect',cid],stdout='[{"actual":"test-only"}]'))
        self.assertEqual(R.inspect_row(r,cid)[2],dict(actual='test-only'))
        for n,bad in enumerate((dict(exit_code=2,requested_argv=['/usr/bin/docker','inspect',cid],stdout='[]'),dict(exit_code=0,requested_argv=['/usr/bin/docker','inspect',cid],stdout='[]'),dict(exit_code=0,requested_argv=['/usr/bin/docker','inspect','b'*64],stdout='[{}]'))):
            with self.subTest(n=n),self.assertRaises(ValueError):R.inspect_row(write(root/('bad%d.json'%n),bad),cid)
 def test_actual_source_is_pinned_without_future_result_ref(self):
    self.assertEqual(R.SOURCE['bytes'],824421);self.assertEqual(R.SOURCE['sha256'],'0cb8a78ee572778434b7b64f494fa42de46cdf4561c235effce3440a8b294f01')
    with self.assertRaises(ValueError):R.source_gate(dict(R.SOURCE,sha256='0'*64))
 def test_caller_pass_flags_and_wrong_source_never_write_qualification(self):
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);r=write(root/'caller.json',dict(sameimage_322_parser_and_actual_cold_handoff_pass=True,all_owned_stopped_retained=True));output=root/'G2_V11_CPU_READBACK.json'
        q=subprocess.run([sys.executable,'-I','-B',str(P/'readback_cpu.py'),'--execute','--source-ref',json.dumps(r),'--result-ref',json.dumps(r),'--output',str(output)],capture_output=True,text=True,timeout=10)
        self.assertNotEqual(q.returncode,0);self.assertIn('actual fully pinned',q.stderr);self.assertFalse(output.exists())
 def test_exclusive_output_never_overwrites_and_rejects_wrong_name(self):
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);output=root/'G2_V11_CPU_READBACK.json';r=R.write_exclusive(output,dict(synthetic_test_only=True));self.assertEqual(R.obj(r),dict(synthetic_test_only=True))
        with self.assertRaises(ValueError):R.write_exclusive(output,{})
        with self.assertRaises(ValueError):R.write_exclusive(root/'wrong.json',{})
 def test_default_OFF_help_do_not_read_even_supplied_invalid_Refs(self):
    for args in([],['--help'],['--source-ref','invalid','--result-ref','invalid','--output','/not-created']):
        q=subprocess.run([sys.executable,'-I','-B',str(P/'readback_cpu.py'),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,q.stderr)
        if args!=['--help']:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))

 def stage_fixture(self,root,**changes):
    so=root/'STDOUT.raw';se=root/'STDERR.raw';so.write_bytes(b'complete raw\n');se.write_bytes(b'actual stderr\n')
    value=dict(schema='bole.actual-software-stage-terminal/v11',source=R.SOURCE,label='metadata',actual_argv=['actual-PY','-B','original-metadata.py'],child_pid=13,start_monotonic=100.,end_monotonic=110.,elapsed_seconds=10.,allocated_seconds=120.,returncode=0,timed_out=False,primary=None,stdout=R.ref(so),stderr=R.ref(se),complete_streams_retained=True,cached_PASS_reused=False)
    value.update(changes);return dict(terminal=write(root/'TERMINAL.json',value),stdout=R.ref(so),stderr=R.ref(se))
 def test_stage_reopens_raw_terminal_source_argv_and_original_deadline(self):
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);row=self.stage_fixture(root);t=R.stage(R.SOURCE,row,root,'metadata',['actual-PY','-B','original-metadata.py'],120.,99.,399.)
        self.assertEqual(t['elapsed_seconds'],10.);self.assertEqual(t['allocated_seconds'],120.)
        (root/'STDOUT.raw').write_bytes(b'changed after terminal')
        with self.assertRaises(ValueError):R.stage(R.SOURCE,row,root,'metadata',t['actual_argv'],120.,99.,399.)
 def test_stage_timeout_wrong_source_argv_caching_and_budget_reset_rejected(self):
    for change in(dict(timed_out=True),dict(returncode=1),dict(source=R.V10_SOURCE),dict(cached_PASS_reused=True),dict(actual_argv=['PY','-I','-B']),dict(allocated_seconds=121.),dict(elapsed_seconds=121.,end_monotonic=221.),dict(start_monotonic=98.,end_monotonic=108.)):
        with self.subTest(change=change),tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);row=self.stage_fixture(root,**change)
            with self.assertRaises(ValueError):R.stage(R.SOURCE,row,root,'metadata',['actual-PY','-B','original-metadata.py'],120.,99.,399.)
 def test_host_admission_exact_args_and_deadline_join_actual_MAIN_cleanup_clock(self):
    from unittest.mock import patch
    with tempfile.TemporaryDirectory()as tmp,patch.object(R,'CPU_OUT',Path(tmp)):
        root=Path(tmp)/'cpu-preflight';root.mkdir();args=[str(R.ROOT/'service_entry.py'),'--software','--phase-entry','100.0','--lane-start','200.0','--lane-deadline','500.0']
        value=dict(schema='bole.actual-host-software-allocation/v11',source=R.SOURCE,phase_entry=100.,lane_start=200.,lane_deadline=500.,allocated_seconds=300.,allocation_seconds=dict(parent279=120.,controls=60.,metadata=120.),aggregate_cap_seconds=300.,original_phase_seconds=3600.,original_cleanup_seconds=180.,requested_args=args)
        path=root/'SOFTWARE-ADMISSION.json';write(path,value);self.assertEqual(R.software_args(R.SOURCE,3700.)[2],args)
        for key,bad in(('phase_entry',101.),('lane_deadline',501.),('requested_args',args[:-1]+['800.0'])):
            path.write_text(json.dumps(dict(value,**{key:bad})))
            with self.subTest(key=key),self.assertRaises(ValueError):R.software_args(R.SOURCE,3700.)
 def test_installed_runtime_route_is_explicit_whole_snapshot_never_unknown_prefix(self):
    from unittest.mock import patch
    with tempfile.TemporaryDirectory()as tmp,patch.object(R,'RUNTIME_HOST_KEYS',{'one':'evidence/one.py'}):
        root=Path(tmp);f=root/'evidence/one.py';f.parent.mkdir();f.write_bytes(b'whole original installed source');host=R.ref(f);installed=dict(host,path='/only/in/guest/one.py');m=dict(root=str(root),files={'evidence/one.py':host},runtime_sources={'one':installed})
        self.assertEqual(R.runtime_routes(m)['one'],dict(runtime_ref=installed,host_snapshot_ref=host));self.assertFalse(Path(installed['path']).exists())
        for bad in(dict(m,runtime_sources={'unknown':installed}),dict(m,runtime_sources={'one':dict(installed,sha256='0'*64)}),dict(m,files={'evidence/one.py':dict(host,bytes=host['bytes']+1)})):
            with self.subTest(bad=bad),self.assertRaises(ValueError):R.runtime_routes(bad)
 def test_actual_prepared_SOURCE11_all_runtime_snapshot_names_and_scope_match(self):
    path=P.parent.parent/'g2_review_v11_source/SOURCE_BOUND.json';path=path if path.is_file()else Path(R.SOURCE['path']);b=path.read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(R.SOURCE['bytes'],R.SOURCE['sha256']));m=R.parse(b)
    self.assertEqual(m['service_required_sameimage_software_cases'],322);self.assertEqual(set(m['runtime_sources']),set(R.RUNTIME_HOST_KEYS));self.assertEqual(m['service_software_scope']['controls_source'],R.V10_SOURCE)
    for key,name in R.RUNTIME_HOST_KEYS.items():self.assertEqual((m['runtime_sources'][key]['bytes'],m['runtime_sources'][key]['sha256']),(m['files'][name]['bytes'],m['files'][name]['sha256']))
 def test_actual_completed_source8_metadata_rows_keep_original_policy_not_incomplete_current(self):
    review=P.parent.parent/'g2_review_v10_cpu_failure';ep=review/'cpu-preflight/G2-V9-PARENT-V8-SOFTWARE/EXTRACTION.json';ep=ep if ep.is_file()else Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v10-CPU/cpu-preflight/G2-V9-PARENT-V8-SOFTWARE/EXTRACTION.json');mp=P.parent.parent/'g2_review_v8_cpu/source/SOURCE_BOUND.json';mp=mp if mp.is_file()else Path(R.V8_SOURCE['path']);e=R.parse(ep.read_bytes());m=R.parse(mp.read_bytes());v=e['original_summary']['actual_installed_metadata'];R.metadata(v,R.V8_SOURCE,m)
    bad=copy.deepcopy(v);bad['classes'][0]['source']['sha256']='0'*64
    with self.assertRaises(ValueError):R.metadata(bad,R.V8_SOURCE,m)
    bad=copy.deepcopy(v);bad['actual_HTTP_sampling_params']['ignore_eos']=False
    with self.assertRaises(ValueError):R.metadata(bad,R.V8_SOURCE,m)


 def test_exact_original_derived_CPU_inspect_reexecutes_resource_negative_guards(self):
    from types import SimpleNamespace as NS
    from unittest.mock import patch
    c=self.original_c();review=P.parent.parent/'g1_review_v2';packet=P.parent/'g2_callee_contract_repair_v10';v8=P.parent/'g2_channel_handoff_repair_v8'
    if not review.is_dir():review=Path('/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-tp4-model-once-v1-025')
    if not packet.is_dir():packet=R.ROOT
    if not v8.is_dir():v8=R.ROOT
    def load(path,name):
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    with tempfile.TemporaryDirectory()as tmp,patch.object(R,'CPU_OUT',Path(tmp)):
        root=Path(tmp);leaf=root/'candidate';leaf.mkdir();ext=load((review/'external025.py')if(review/'external025.py').is_file()else R.ROOT/'external025.py','_readback_exact_external')
        sys.path.insert(0,str(packet))
        try:ha=load(v8/'g2_host_adapter.py','_readback_exact_CPU_derive')
        finally:sys.path.remove(str(packet))
        m=dict(g2_callee_contract_v10=dict(original025_sources={'safety_host':R.ref(review/'safety_host.py')}),files={'owned_substrate.py':R.ref(packet/'owned_substrate.py')})
        validator=R.safety_validator(m,NS(external025=ext,g2_host_adapter=ha),c)
        e=dict(cid='a'*64,name='test-only',arm='cpu-preflight',source={'sha256':'b'*64},host_sha256=R.ref(review/'safety_host.py')['sha256'],guest_cpus=[145],mounts={str(leaf):(str(leaf),True),'/adakv-results':(str(leaf),True)})
        argv=validator.create(e);env=[argv[i+1]for i,x in enumerate(argv)if x=='--env'];labels=dict(argv[i+1].split('=',1)for i,x in enumerate(argv)if x=='--label')
        row=dict(Id=e['cid'],Image=c.IMAGE,Name='/'+e['name'],Config=dict(Image=c.IMAGE,Entrypoint=['/bin/bash'],Cmd=['-c','exec /bin/sleep infinity'],WorkingDir=str(c.ROOT),Labels=labels,Env=env),HostConfig=dict(Privileged=False,Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,CpusetCpus='145',IpcMode='private',NetworkMode='none',ShmSize=4*2**30,PidsLimit=2048,DeviceRequests=None,DeviceCgroupRules=None,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Devices=[],ReadonlyRootfs=True,LogConfig=ext.LOG,Tmpfs=None),Mounts=[dict(Type='bind',Destination=dst,Source=src,RW=rw)for dst,(src,rw)in e['mounts'].items()])
        validator.validate(row,e)
        for kind in('memory','devices','readonly','mounts','env'):
            bad=copy.deepcopy(row)
            if kind=='memory':bad['HostConfig']['Memory']+=1
            elif kind=='devices':bad['HostConfig']['Devices']=[dict(PathOnHost='/dev/davinci4',PathInContainer='/dev/davinci0',CgroupPermissions='rwm')]
            elif kind=='readonly':bad['HostConfig']['ReadonlyRootfs']=False
            elif kind=='mounts':bad['Mounts'][0]['RW']=False
            else:bad['Config']['Env'].append(env[0])
            with self.subTest(kind=kind),self.assertRaises(ValueError):validator.validate(bad,e)


if __name__=='__main__':unittest.main()
