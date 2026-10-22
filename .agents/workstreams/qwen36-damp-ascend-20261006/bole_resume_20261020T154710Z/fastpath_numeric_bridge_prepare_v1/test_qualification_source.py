"""Focused short8 source closure controls, no fabricated runtime/NPU evidence."""
import copy
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import qualification_short_prepare as Q

class Tests(unittest.TestCase):
    def test_complete_source_compile_inverse_and_math_write_identity(self):
        b=Q.render();self.assertEqual(len(b['files']),419)
        self.assertEqual(Q.inverse(b),b['parent_bundle']['files'])
        for n in ('transaction.py','tp_consensus.py'):
            self.assertEqual(b['files'][n],b['parent_bundle']['files'][n])
        for n in b['files']:
            if n.endswith('.py'):compile(b['files'][n],n,'exec')
        self.assertFalse(b['launch_ready']);self.assertFalse(b['NPU'])
        self.assertEqual(b['manifest']['fastpath_numeric_qualification']['output_tokens'],8)
        self.assertEqual(b['manifest']['performance_profile']['scope']['output_tokens'],8)
        self.assertIn(b'FSP.Probe(',b['files']['service_runner.py'])
        self.assertIn(b'probe.capture(state.bridge,f,record)',b['files']['service_runner.py'])
        self.assertIn(b'qualifier.publication(state.bridge,proposal,publication)',b['files']['service_runner.py'])
        self.assertIn(b'BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE=1',b['files']['host_service.py'])
        self.assertIn(b"['output_tokens']==8",b['files']['fastpath_numeric_sink.py'])
        self.assertEqual(b['manifest']['performance_streaming_client'],b['manifest']['files']['performance_service_client.py'])
        self.assertEqual(b['manifest']['performance_timing_donor'],b['manifest']['files']['benchmark_shared_prefix.py'])
        self.assertIn(b"'output_tokens': 8",b['files']['performance_host.py'])
        self.assertIn(str(Path(b['manifest']['output_root'])).encode(),b['files']['contract090.py'])
        bad=copy.deepcopy(b);bad['files']['transaction.py']+=b'\n#unregistered'
        with self.assertRaisesRegex(ValueError,'inverse ledger'):Q.inverse(bad)

    def test_short_source_all_loaded_before_reuse(self):
        sources,ref=Q.exact_short_sources()
        self.assertEqual(set(sources),{'short_state_digest.py','compare_state_digest.py',
            'performance_client_consumer.py','bole_performance_profile.py','prepare_short_gate.py'})
        self.assertEqual(ref['bytes'],1642902)
        self.assertEqual(ref['sha256'],'74b2f3f82c97e91ff1c0d77e439631a7e7aa62345c46b3ea4428ca80dd16426d')

if __name__=='__main__':unittest.main()
