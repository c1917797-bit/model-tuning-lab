"""Pure source/control tests; no tensor/native import or admission exercised."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent
def module(name,file):
    s=importlib.util.spec_from_file_location(name,P/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
Q=module('_probe_pure_contract','gdn_probe_contract.py');R=module('_probe_pure_runtime','gdn_probe_runtime.py')
B=module('_probe_pure_builder','prepare_gdn_probe.py')

class C:
    need=staticmethod(B.need);ref=staticmethod(B.ref);checked=staticmethod(B.checked);obj=staticmethod(B.obj);write=staticmethod(B.write)

def report():
    return dict(schema='bole.g1-cold-aggregate-software/v1',source={'unit-source':1},tests=231,all_tests_passed=True,
        complete_readset_audited=True,NPU=False,actual_scheduler_executed=False,actual_cold_cli=[dict(exit_code=0)for _ in range(10)])


class Tests(unittest.TestCase):
    def test_trailing_runtime_log_preserved_unique_schema_not_last_line(self):
        v=report();text='prelude log\n'+json.dumps(v)+'\n[INFO] process group destroyed\n'
        self.assertEqual(Q.json_report(C,text,v['source'],231),v)

    def test_duplicate_stale_missing_wrong_count_failure_reports_reject(self):
        v=report()
        for text in ('runtime shutdown only',json.dumps(v)+'\n'+json.dumps(v),json.dumps(dict(v,source={'stale':1})),
                     json.dumps(dict(v,tests=214)),json.dumps(dict(v,all_tests_passed=False)),
                     json.dumps(dict(v,actual_cold_cli=[dict(exit_code=0)]))):
            with self.assertRaises(ValueError):Q.json_report(C,text,v['source'],231)

    def test_synthetic_CPU_handoff_join_and_wrong_terminal_reject(self):
        # CPU metadata unit fixtures only. The source token is deliberately
        # not a Ref3, so this cannot admit the real source/replay/model gate.
        with tempfile.TemporaryDirectory(dir='/adakv-results')as directory:
            root=Path(directory);v=report();cid='1'*64
            (root/'SOFTWARE.stdout').write_text(json.dumps(v)+'\n[INFO] shutdown complete\n')
            (root/'SOFTWARE.stderr').write_text('unit metadata, no tensor runtime\n')
            inspect=C.write(root/'inspect.json',dict(stdout=json.dumps([dict(Id=cid,Image=Q.IMAGE,
                              State=dict(Running=False),HostConfig=dict(Devices=[]))])))
            release=C.write(root/'release.json',dict(container=cid,stopped=True,retained=True,errors=[],after_inspect=inspect))
            child=dict(exit_code=0,child_termination_observed=True,stdout_ref=C.ref(root/'SOFTWARE.stdout'),
                       stderr_ref=C.ref(root/'SOFTWARE.stderr'),requested_argv=['/usr/bin/docker','exec',cid,'unit-python','/unit/service_entry.py','--software'])
            childref=C.write(root/'child.json',child);m=dict(service_required_sameimage_software_cases=231,
                                                         files={'service_entry.py':dict(path='/unit/service_entry.py')})
            r=Q.materialize_software(C,root,childref,release,v['source'],m)
            self.assertEqual(Q.software(C,r,v['source'],m),v)
            gate=C.obj(r);self.assertFalse(gate['actual_NPU_admission_granted'])
            badchild=C.write(root/'badchild.json',dict(child,exit_code=3))
            bad=C.write(root/'badgate.json',dict(gate,child=badchild))
            with self.assertRaises(ValueError):Q.software(C,bad,v['source'],m)

    def test_explicit_default_off_and_cold_builder(self):
        with patch.dict(os.environ,{},clear=True):self.assertFalse(R.install(object(),object(),C,{})['enabled'])
        for args in([],['--help']):
            r=subprocess.run([sys.executable,'-I','-B',str(P/'prepare_gdn_probe.py'),*args],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr)
            if not args:self.assertFalse(json.loads(r.stdout)['enabled'])
        r=subprocess.run([sys.executable,'-I','-B',str(P/'prepare_gdn_probe.py'),'--execute'],capture_output=True,text=True,timeout=10)
        self.assertNotEqual(r.returncode,0)

    def test_exact_ref_skip_only_and_drift_fails(self):
        installed=dict(path='/vllm-workspace/unit-absent.py',bytes=4,sha256='1'*64)
        self.assertEqual(R.collect(C,[installed],installed_refs=[installed]),[])
        with self.assertRaises((ValueError,FileNotFoundError)):R.collect(C,[dict(installed,bytes=5)],installed_refs=[installed])
        with tempfile.TemporaryDirectory(dir='/adakv-results')as directory:
            p=Path(directory)/'fixture';p.write_text('unit\n');r=C.ref(p)
            self.assertEqual(R.collect(C,[r,r]),[r])
            with self.assertRaises(ValueError):R.collect(C,[r,dict(r,sha256='2'*64)])

    def test_actual_overlay_source_boundaries_and_unchanged_math(self):
        # Host donor bytes are provided only during MAIN assembly. Locally the
        # exact installed-source manifest and matching copied primary files
        # are available; no host paths or fake model owner are constructed.
        if (P.parents[1]/'g1_review_v2/qualification/SOURCE_BOUND.json').is_file():
            W=P.parents[1];on=json.loads((W/'g1_review_v2/qualification/SOURCE_BOUND.json').read_bytes())
            paths={n:W/'bole_service_proposals/g1_multi_request'/n for n in('service_bridge.py','server090.py')}
            paths.update({'contract090.py':W/'g1_review_v2/contract090.py','host_service.py':W/'bole_service_proposals/g1_repair_v2/host_service.py',
                          'command_contract.py':W/'bole_service_proposals/g1_repair_v2/command_contract.py'})
            donor=copy.deepcopy(on)
            for n,p in paths.items():
                r=C.ref(p);self.assertEqual((r['bytes'],r['sha256']),(on['files'][n]['bytes'],on['files'][n]['sha256']));donor['files'][n]=r
        else:
            # In the assembled actual packet, source-derived new hook operands
            # must have exact whole-file G1 inverses to real donor sources.
            m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());donor=C.obj(C.obj(m['gdn_service_extension']['source'])['prior_G1']['source'])
        changed=B.overlays(donor,Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-UNIT'))
        before=ast.parse(C.checked(donor['files']['service_bridge.py']).read_bytes());after=ast.parse(changed['service_bridge.py'])
        f=lambda tree,name:ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name),include_attributes=False)
        self.assertEqual(f(before,'_fa'),f(after,'_fa'))
        self.assertIn('GP.handoff_readset',changed['host_service.py'])
        self.assertIn("'--gdn-software-gate-ref'",changed['host_service.py'])
        self.assertIn("'--owned-probe-consumer'",changed['host_service.py'])
        for n,text in changed.items():compile(ast.parse(text),n,'exec')
        with self.assertRaises(ValueError):B.overlays(dict(donor,output_root='/unexpected-output'),Path('/new'))

    def test_owned_bridge_restore_restores_seam_then_exact_original(self):
        calls=[]
        class Bridge:
            def restore(self):calls.append('native-bridge');return 'native-return'
        class Control:
            def restore(self):calls.append('seam')
        control=Control();seam=NS(Controller=Control,install=lambda *a,**k:control)
        fake=NS(software=lambda *a:None,load=lambda *a:seam)
        bridge=Bridge();m=dict(root='/UNIT',files={'gdn_probe_runtime.py':{'unit':1},'gdn_service_seam.py':{'unit-seam':1}},gdn_service_extension={'source':{'extension':1}});bridge.own_source=m
        class Guard:
            need=staticmethod(C.need)
            ref=staticmethod(lambda p:{'unit':1})
            obj=staticmethod(lambda r:m)
        with patch.object(R,'helper',return_value=fake),patch.dict(os.environ,{'BOLE_GDN_SERVICE_FUSION_ENABLE':'1','BOLE_GDN_SERVICE_SOFTWARE_REF':'{}'}):
            R.install(bridge,object(),Guard,m)
        self.assertIn('restore',bridge.__dict__)
        self.assertEqual(bridge.restore(),'native-return');self.assertEqual(calls,['seam','native-bridge']);self.assertNotIn('restore',bridge.__dict__)

    def test_failed_abort_preserves_original_exception(self):
        primary=ValueError('original control fault')
        def fail(ctx):raise RuntimeError('private abort control fault')
        R.abort(NS(_bole_gdn_extension=NS(abort=fail)),object(),primary)
        self.assertEqual(str(primary),'original control fault');self.assertIn('private abort',primary.__notes__[0])

    def test_runtime_modules_never_import_tensors_at_module_load(self):
        script="import importlib.util,sys; from pathlib import Path; p=Path(sys.argv[1]); " + \
            "s=importlib.util.spec_from_file_location('cold',p); v=importlib.util.module_from_spec(s); s.loader.exec_module(v); " + \
            "assert not any(k.split('.')[0] in ('torch','torch_npu','triton','vllm','vllm_ascend') for k in sys.modules)"
        for name in('gdn_probe_contract.py','gdn_probe_runtime.py','gdn_service_gate.py','gdn_service_seam.py'):
            r=subprocess.run([sys.executable,'-I','-B','-c',script,str(P/name)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr)
        for name in B.ADDED:compile(ast.parse((P/name).read_bytes()),str(P/name),'exec')


if __name__=='__main__':unittest.main()
