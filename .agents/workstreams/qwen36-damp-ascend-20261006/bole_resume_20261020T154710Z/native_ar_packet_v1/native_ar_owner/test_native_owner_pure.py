"""Offline source/arithmetic controls only; never device/container admission."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

P=Path(__file__).resolve().parent;W=P.parents[1]


def load(path,name):
    s=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


C=load(P/'ar_owner_common.py','_offline_ar_owner_common')
M=load(P/'consume_pair_entry.py','_offline_ar_metadata_entry')


class Controls(unittest.TestCase):
    def test_cold_default_help(self):
        for name in('native_ar_host.py','ar_sameimage_preflight.py','consume_pair_entry.py','prepare_native_owner.py'):
            for args in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,r.stderr)
                if not args:self.assertFalse(json.loads(r.stdout)['enabled'])

    def test_execute_missing_arguments_fails_before_runtime(self):
        for name in('native_ar_host.py','ar_sameimage_preflight.py','consume_pair_entry.py','prepare_native_owner.py'):
            r=subprocess.run([sys.executable,'-I','-B',str(P/name),'--execute'],capture_output=True,text=True,timeout=10)
            self.assertNotEqual(r.returncode,0)
            self.assertNotIn('ModuleNotFoundError',r.stderr)

    def test_all_sources_compile_and_no_worker_signal(self):
        for path in P.glob('*.py'):
            tree=ast.parse(path.read_text());compile(tree,str(path),'exec')
        tree=ast.parse((P/'ar_snapshot_bindings.py').read_text())
        for node in ast.walk(tree):
            self.assertFalse(isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr in('kill','killpg','send_signal'))
        host=(P/'native_ar_host.py').read_text()
        self.assertNotIn('worker_snapshot_owner',host)

    def test_actual_qualified_g1_local_bytes_match_reported_refs(self):
        q=W/'g1_review_v2/qualification'
        expected={'SOURCE_BOUND.json':(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677'),
            'RESULT.json':(131517,'52030a932da1f3cd2392389a2d9246925e40c2d93186b5f67d41fba8cfa1e4fc'),
            'ATTRIBUTION.json':(12221,'8caf55b28f4a3c4108b8b932e9c664e08b3c28ea18f0bf4fc3bdf62de3538d53')}
        for name,pin in expected.items():
            b=(q/name).read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),pin)
        owner=json.loads((q/'RESULT.json').read_bytes());report=json.loads((q/'ATTRIBUTION.json').read_bytes())
        self.assertIsNone(owner['primary']);self.assertEqual(owner['secondary'],[])
        self.assertTrue(report['service_complete']);self.assertTrue(report['component_checks_pass'])
        self.assertEqual(report['completed_request_count'],2)

    def test_actual_model_metadata_paths_and_full_accounting(self):
        r=C.ref(W/'bole_task_assets_reference/ACTUAL_MODEL_MANIFEST.json')
        host=C.model_manifest(r,host=True,rehash=False);guest=C.model_manifest(r,host=False,rehash=False)
        self.assertEqual(len(host['files']),29);self.assertEqual(sum(r['bytes']for r in host['files']),55586107940)
        for a,b in zip(host['files'],guest['files']):
            self.assertEqual(Path(a['path']).relative_to(C.MODEL_ROOT),Path(b['path']).relative_to(C.GUEST_MODEL))
            self.assertEqual((a['bytes'],a['sha256']),(b['bytes'],b['sha256']))
            self.assertNotEqual(a['path'],b['path'])

    def test_actual_runtime_host_copy_mapping_complete(self):
        m=json.loads((W/'g1_review_v2/qualification/SOURCE_BOUND.json').read_bytes())
        for actual in m['runtime_sources'].values():
            copies=[r for r in m['files'].values()if r['path']!=actual['path']and
                    (r['bytes'],r['sha256'])==(actual['bytes'],actual['sha256'])]
            self.assertTrue(copies,actual['path'])
        self.assertTrue(any(r['path'].startswith('/vllm-workspace/')for r in m['runtime_sources'].values()))

    def test_exact_025_safety_source_inverse(self):
        scan=load(W/'g1_review_v2/output_scan131r8.py','_offline_output_scan')
        ext=load(W/'g1_review_v2/external025.py','_offline_external025')
        body=(W/'g1_review_v2/safety_host.py').read_bytes();derived=scan.derive(body)
        self.assertEqual(derived.replace(scan.REPLACEMENT,scan.EXPRESSION),body.decode())
        derived,pairs=ext.derive(body)
        for before,after in reversed(pairs):derived=derived.replace(after,before)
        self.assertEqual(derived,body.decode())

    def test_initial_only_schema_and_source_declared_plugins(self):
        profile_path=W/'g1_review_v2/LAUNCH_PROFILE_INITIAL.json';b=profile_path.read_bytes()
        self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(3344,'519e2f3879acfcb6ee5c4802e47fff2d7f1925dfb1022e1026cd986275b77a78'))
        p=json.loads(b);self.assertEqual(p['schema'],'bole.actual-host-launch-profile-observation/v1')
        self.assertEqual(p['plugins'],['ascend']);self.assertFalse(p['plugin_effect_classification_performed'])
        self.assertEqual(M.declared_plugins(C,C.ref(P.parent/'native_ar_pair/native_ar_server.py')),
                         ['ascend','bole_native_ar_pair'])
        source=(P/'consume_pair_entry.py').read_text()
        self.assertIn('actual_current_os_environ_observed=False',source)
        self.assertIn('matched_common_plugin_effects_gate_pending=True',source)


if __name__=='__main__':unittest.main()
