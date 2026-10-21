"""Synthetic audit/source controls; no installed ML package/model/device import."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import cpu_import_guard as A


class TokenizerImportAudit(unittest.TestCase):
    def test_denial_occurs_before_synthetic_forbidden_module_body(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);marker=root/'BODY_EXECUTED';(root/'torch_npu.py').write_text('open('+repr(str(marker))+',"x").write("bad")\n')
            program='''import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport cpu_import_guard as A\nsys.path.insert(0,sys.argv[2])\nt=A.Trace(Path(sys.argv[2]),{'synthetic':True})\ntry:\n    import torch_npu\nexcept A.ForbiddenImport:\n    pass\nelse:\n    raise RuntimeError('synthetic forbidden body was allowed')\nfinally:\n    t.close()\nassert 'torch_npu'not in sys.modules\n'''
            r=subprocess.run([sys.executable,'-I','-B','-c',program,str(P),str(root)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(marker.exists())
            rows=[json.loads(v)for v in(root/'TOKENIZER_IMPORT_TRACE.jsonl').read_text().splitlines()]
            event=next(v for v in rows if v['event']=='forbidden-import-denied')
            self.assertEqual(event['payload']['module'],'torch_npu');self.assertTrue(event['payload']['stack'])
            self.assertIs(rows[-1]['payload']['software_qualification_accepted'],False)

    def test_swallowed_denial_can_never_pass_check(self):
        with tempfile.TemporaryDirectory()as t:
            trace=A.Trace(Path(t),dict(synthetic=True))
            try:
                try:sys.audit('import','torch_npu',None,[],[],[])
                except A.ForbiddenImport:pass
                self.assertNotIn('torch_npu',sys.modules)
                with self.assertRaises(A.ForbiddenImport):trace.check()
            finally:trace.close()

    def test_CPU_torch_import_event_is_not_accelerator_denial(self):
        with tempfile.TemporaryDirectory()as t:
            trace=A.Trace(Path(t),dict(synthetic=True))
            try:sys.audit('import','torch',None,[],[],[]);trace.check();self.assertEqual(trace.forbidden,[])
            finally:trace.close()

    def test_closed_hook_does_not_intercept_later_process_work(self):
        with tempfile.TemporaryDirectory()as t:
            trace=A.Trace(Path(t),dict(synthetic=True));trace.close();before=trace.path.read_bytes()
            sys.audit('import','torch_npu',None,[],[],[])
            self.assertEqual(trace.path.read_bytes(),before)

    def test_actual_source_inventory_frozen_and_old_packet_unchanged(self):
        r=C.ref(P/'TOKENIZER_SOURCE_EXPECTED.json');self.assertEqual(r['sha256'],C.TOKENIZER_EXPECTED_SHA)
        expected=C.obj(r);self.assertEqual(len(expected),7)
        self.assertEqual(expected['import_utils.py']['sha256'],'c05e6063736902b07d0b48e4a326ae7985b75430bacbee48014c954fd4e6cb05')
        original=P.parent/'task_decoder_scorer'
        if original.is_dir():self.assertEqual(C.ref(original/'PROPOSAL_MANIFEST.json')['sha256'],C.LEGACY_PACKET_SHA)

    def test_pre_Python_environment_profile_is_explicit_without_false_fix_claim(self):
        self.assertEqual(N.TOKENIZER_ENV,dict(USE_TORCH='0',USE_TF='0',USE_FLAX='0',USE_TORCH_XLA='0',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
        self.assertNotIn('USE_TORCH_NPU',N.TOKENIZER_ENV)
        tree=ast.parse((P/'owner_namespace.py').read_bytes())
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='cpu_admission']
        self.assertEqual(calls,[])  # The genuine original025 observer invokes unchanged admission.

    def test_probe_defaultOFF_and_help(self):
        for extra in([],['--help']):
            r=subprocess.run([sys.executable,'-I','-B',str(P/'public_probe_gate.py'),*extra],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            if not extra:self.assertIs(json.loads(r.stdout)['software_qualification_accepted'],False)


if __name__=='__main__':unittest.main()
