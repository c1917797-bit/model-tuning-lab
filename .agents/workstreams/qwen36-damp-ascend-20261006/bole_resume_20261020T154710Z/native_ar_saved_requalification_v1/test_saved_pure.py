"""Offline stdlib controls; no positive device/CPU qualification fabricated."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_test_saved_common',ROOT/'saved_common.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()


class SavedTests(unittest.TestCase):
    def test_cold_default_help_no_tensor_imports(self):
        code="""import builtins,runpy,sys
old=builtins.__import__
def guard(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('forbidden cold import')
 return old(name,*a,**k)
builtins.__import__=guard;p=sys.argv[1];sys.argv=[p,*sys.argv[2:]];runpy.run_path(p,run_name='__main__')
"""
        for name in ('prepare_saved_owner.py','saved_cpu_owner.py','saved_preflight.py'):
            for args in ([],['--help']):
                p=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(p.returncode,0,p.stderr)
                if not args:self.assertFalse(json.loads(p.stdout)['enabled'])

    def test_namespace_whole_inverse(self):
        delta=json.loads((ROOT/'NAMESPACE_DELTA.json').read_text());new=(ROOT/'ar_saved_namespace.py').read_text()
        self.assertEqual(new.count(delta['unique_after']),1)
        restored=new.replace(delta['unique_after'],delta['unique_before'])
        original=Path(delta['local_review_copy']).read_text()
        local_ref=C.ref(delta['local_review_copy'])
        self.assertEqual((local_ref['bytes'],local_ref['sha256']),(delta['original']['bytes'],delta['original']['sha256']))
        self.assertEqual(restored,original)
        self.assertFalse(delta['resource_window_protection_functions_changed'])

    def test_actual_saved_primary_and_pair_refs(self):
        local=ROOT.parents[1]/'g1_review_v2/native_ar_v5_saved'
        refs=json.loads((ROOT/'ACTUAL_SAVED_REFS.json').read_text())
        for name,reference in refs.items():
            actual=C.ref(local/name)
            self.assertEqual((actual['bytes'],actual['sha256']),(reference['bytes'],reference['sha256']))
        producer=json.loads((local/'RESULT.json').read_text());pair=json.loads((local/'PAIR-INPUTS.json').read_text())
        self.assertEqual(producer['primary']['error'],"ValueError('ordinary absolute Ref')")
        self.assertEqual(producer['secondary'],[])
        self.assertEqual(producer['source_before'],producer['source_after'])
        self.assertNotIn('independent',producer['summary'])
        self.assertEqual(pair['native_AR'],refs['NATIVE-AR-BUNDLE.json'])
        self.assertEqual(pair['scope']['schema'],'bole.actual-native-ar-bole-token-pair/v1')

    def test_actual_snapshot_installed_closure_classification_only(self):
        local=ROOT.parents[1]/'g1_review_v2/native_ar_v5_saved'
        x=json.loads((local/'OWNER_INPUTS.json').read_text());m=json.loads((local/'AR_SOURCE_BOUND.json').read_text())
        g1=json.loads((ROOT.parents[1]/'g1_review_v2/qualification/CONSUMER_INPUTS.json').read_text())
        mapping=B.installed_map(C,x,m,{},g1,check_copies=False)
        self.assertEqual(len(mapping),35)
        refs=[]
        def walk(v):
            if type(v)is dict:
                if set(v)=={'path','bytes','sha256'}:refs.append(v)
                else:
                    for q in v.values():walk(q)
            elif type(v)is list:
                for q in v:walk(q)
        for name in ('NATIVE-AR-BUNDLE.json','BOLE-BUNDLE.json'):walk(json.loads((local/name).read_text()))
        used={r['path']for r in refs if r['path'].startswith('/vllm-workspace/')}
        self.assertEqual(len(used),7)
        for r in refs:
            if r['path']in used:self.assertEqual(r,mapping[r['path']]['installed'])
        # Declaration classification only: no host copies or installed files opened in this control.

    def test_exact_full_ref_resolution_and_unknown_rejection(self):
        with tempfile.TemporaryDirectory(dir=ROOT)as directory:
            path=Path(directory)/'copy.py';path.write_text('x=1\n');host=C.ref(path)
            installed=dict(host,path=str(Path(directory)/'absent'/'installed.py'))
            mapping={installed['path']:dict(installed=installed,host=host)}
            refs,resolved=B.collect(C,{'snapshot':installed},mapping)
            self.assertEqual(refs,[host]);self.assertEqual(len(resolved),1)
            for bad in (dict(installed,sha256='0'*64),{k:installed[k]for k in('path','sha256')},
                        dict(installed,path=str(Path(directory)/'absent'/'unknown.py'))):
                with self.assertRaises((ValueError,FileNotFoundError)):B.collect(C,bad,mapping)
            with self.assertRaises((ValueError,FileNotFoundError)):B.collect(C,installed,mapping,installed=True)

    def test_no_actual_MAIN_lock_claim_locally(self):
        with self.assertRaises((ValueError,FileNotFoundError)):B.held_main_lock(C)


if __name__=='__main__':unittest.main()
