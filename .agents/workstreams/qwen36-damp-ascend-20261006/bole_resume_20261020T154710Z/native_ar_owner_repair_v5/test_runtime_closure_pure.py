"""Actual local source audit and synthetic declaration controls; no admission."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

P=Path(__file__).resolve().parent;W=P.parents[1];PAIR=P.parent/'native_ar_pair'
s=importlib.util.spec_from_file_location('_offline_runtime_common',str(P/'ar_owner_common.py'))
C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
on=json.loads((W/'g1_review_v2/qualification/SOURCE_BOUND.json').read_bytes())
HELPERS=('model_entry.py','worker_entry.py','identity_capture.py','identity_journal.py','identity_oracle.py','sourceio.py')


def sources():
    files={}
    for root in(P,PAIR):
        for p in root.glob('*.py'):
            if not p.name.startswith('test_'):files[root.name+'/'+p.name]=C.ref(p)
    files.update({'helpers/'+name:C.ref(W/'bole_service_reference/qualified'/name)for name in HELPERS})
    return files


class RuntimeControls(unittest.TestCase):
    def test_actual_common_map_and_exact_only_extra(self):
        m=dict(common_runtime_sources=copy.deepcopy(on['runtime_sources']),observer_runtime_sources=C.OBSERVER_RUNTIME,
               runtime_sources=dict(on['runtime_sources'],**C.OBSERVER_RUNTIME))
        common,extra=C.runtime_partition(m,on)
        self.assertEqual(len(common),32)
        self.assertEqual(set(extra),{'device_op'})
        for field in('common_runtime_sources','runtime_sources'):
            bad=copy.deepcopy(m);bad[field]['runner']['bytes']+=1
            with self.assertRaises(ValueError):C.runtime_partition(bad,on)
        bad=copy.deepcopy(m);bad['runtime_sources']['unknown']=dict(C.OBSERVER_RUNTIME['device_op'])
        with self.assertRaises(ValueError):C.runtime_partition(bad,on)
        bad=copy.deepcopy(m);bad['observer_runtime_sources']['device_op']['path']+='.unknown'
        with self.assertRaises(ValueError):C.runtime_partition(bad,on)

    def test_actual_primary_device_source_and_distinct_copy(self):
        p=W/'bole_service_reference/qualified/device_op.py';r=C.ref(p)
        self.assertEqual((r['bytes'],r['sha256']),(78606,'de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47'))
        C.observer_copies({'device_op':r})
        for bad in({},dict(device_op=C.OBSERVER_RUNTIME['device_op']),dict(device_op=dict(r,bytes=78607)),dict(device_op=r,unknown=r)):
            with self.assertRaises(ValueError):C.observer_copies(bad)
        # The actual installed path is absent here; source-only CPU success
        # must never pretend that same-image reopening happened.
        with self.assertRaises(ValueError):C.observer_copies({'device_op':r},installed=True)

    def test_old_real_map_detects_exact_original_failure_before_load(self):
        with self.assertRaisesRegex(ValueError,"missing runtime key.*device_op.*native_ar_observer.py:251"):
            C.runtime_key_audit(sources(),on['runtime_sources'])
        result=C.runtime_key_audit(sources(),dict(on['runtime_sources'],**C.OBSERVER_RUNTIME))
        self.assertEqual(result['missing'],[])
        self.assertEqual(result['unresolved'],[])
        observer=[x for x in result['accesses']if x['file'].endswith('/native_ar_observer.py')]
        dynamic=[x for x in observer if x['kind']=='finite_dynamic']
        self.assertEqual([x['keys']for x in dynamic],[['gpu_input_batch','npu_input_batch','sampling_metadata','sampling_params'],
                                                   ['base_runner','qwen35','qwen_next','runner']])
        self.assertTrue(any(x['line']==371 and x['keys']==['block_table']for x in observer))
        self.assertFalse(result['runtime_exercised'])

    def test_unresolved_dynamic_and_nested_missing_fail_closed(self):
        snippets=["def f(m,k):\n refs=m['runtime_sources']\n return refs[k]\n",
                  "def f(m):\n refs=m['runtime_sources']\n def inner(): return refs['unlisted']\n return inner\n",
                  "def f(m):\n return m['runtime_sources']['unlisted']\n"]
        with tempfile.TemporaryDirectory(dir=P)as directory:
            p=Path(directory)/'fixture.py'
            for source in snippets:
                p.write_text(source)
                with self.assertRaises(ValueError):C.runtime_key_audit({'fixture.py':C.ref(p)},dict(on['runtime_sources'],**C.OBSERVER_RUNTIME))

    def test_new_source_assembly_preserves_frozen_observer_and_math(self):
        s=importlib.util.spec_from_file_location('_offline_v4_builder',str(P/'prepare_native_owner.py'))
        B=importlib.util.module_from_spec(s);s.loader.exec_module(B)
        with tempfile.TemporaryDirectory(dir=P)as directory:
            d=Path(directory);command=C.write(d/'command.json',dict(argv=['vllm','serve','--speculative-config','{"method":"mtp","num_speculative_tokens":8}']))
            donor=dict(on,files={name:C.ref(W/'bole_service_reference/qualified'/name)for name in HELPERS})
            # No g1_pass call: these are explicit unit fixtures, not actual
            # owner inputs, image admission or a qualified G1 source chain.
            fixture=C.write(d/'fixture.json',{'synthetic_unit_only':True})
            sr=B.prepare_ar(C,on=donor,sr=fixture,command=command,shared=fixture,native_packet_root=PAIR,
                            new_root=d/'ar',output_root=d/'out')
            m=C.obj(sr);C.runtime_partition(m,donor)
            self.assertEqual(m['runtime_sources'],dict(on['runtime_sources'],**C.OBSERVER_RUNTIME))
            for name in('native_ar_observer.py','consume_pair.py','pair_contract.py','native_ar_bootstrap.py'):
                self.assertEqual((d/'ar'/name).read_bytes(),(PAIR/name).read_bytes())
            self.assertFalse(m['actual_model_execution'])
            self.assertFalse(m['formal_success'])
            self.assertNotIn('torch',sys.modules)


if __name__=='__main__':unittest.main()
