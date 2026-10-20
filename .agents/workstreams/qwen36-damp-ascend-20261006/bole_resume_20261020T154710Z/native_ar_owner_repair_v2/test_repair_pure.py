"""Offline source/decorator controls; no runtime imports or NPU qualification."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

P=Path(__file__).resolve().parent;W=P.parents[1];V1=P.parent/'native_ar_owner'


def load(p,name):
    s=importlib.util.spec_from_file_location(name,str(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


C=load(P/'ar_owner_common.py','_repair_ar_common')
F=load(P/'ar_sameimage_preflight.py','_repair_ar_preflight')


class Controls(unittest.TestCase):
    def test_cold_entrypoints(self):
        for name in('native_ar_host.py','ar_sameimage_preflight.py','consume_pair_entry.py','prepare_native_owner.py'):
            for args in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,r.stderr)
                if not args:self.assertFalse(json.loads(r.stdout)['enabled'])

    def test_only_preflight_source_changes(self):
        for name in('ar_owner_common.py','ar_host_namespace.py','ar_snapshot_bindings.py','native_ar_host.py','consume_pair_entry.py','prepare_native_owner.py'):
            self.assertEqual((P/name).read_bytes(),(V1/name).read_bytes())

    def test_no_native_or_tensor_import_execution_path(self):
        tree=ast.parse((P/'ar_sameimage_preflight.py').read_bytes())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertTrue(all(n.name.split('.')[0]not in('torch','torch_npu','triton','vllm','vllm_ascend')for n in node.names))
            if isinstance(node,ast.ImportFrom):self.assertNotIn((node.module or '').split('.')[0],('torch','torch_npu','triton','vllm','vllm_ascend'))
            if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute):
                self.assertNotIn(node.func.attr,('import_module','getclosurevars'))
        text=(P/'ar_sameimage_preflight.py').read_text()
        self.assertIn('actual_runtime_closure_guard_exercised=False',text)
        self.assertIn('actual_instance_guards_exercised=False',text)

    def test_decorator_declaration_and_mutations(self):
        with tempfile.TemporaryDirectory(dir=P)as directory:
            p=Path(directory)/'runner.py'
            good='class NativeRunner:\n @torch.inference_mode()\n def sample_tokens(self): pass\n'
            p.write_text(good)
            row=F.runner_source_declaration(C,C.ref(p));self.assertEqual(row['class_name'],'NativeRunner')
            self.assertFalse(row['actual_runtime_wrapper_or_closure_examined'])
            for changed in(good.replace('@torch.inference_mode()','@torch.no_grad()'),
                           good.replace('@torch.inference_mode()','@torch.inference_mode(False)'),
                           good+good.replace('NativeRunner','OtherRunner')):
                p.write_text(changed)
                with self.assertRaises(ValueError):F.runner_source_declaration(C,C.ref(p))

    def test_actual_primary_runner_declaration_without_import(self):
        # Existing text transport copy has exactly one extra final LF. Accept
        # reconstructed bytes ONLY after matching actual G1 runtime bytes/hash.
        m=json.loads((W/'g1_review_v2/qualification/SOURCE_BOUND.json').read_bytes())
        reference=m['runtime_sources']['runner'];raw=(W/'bole_service_reference/installed/runner.py').read_bytes()
        if len(raw)==reference['bytes']+1 and raw.endswith(b'\n'):raw=raw[:-1]
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(reference['bytes'],reference['sha256']))
        with tempfile.TemporaryDirectory(dir=P)as directory:
            p=Path(directory)/'actual_runner.py';p.write_bytes(raw)
            declaration=F.runner_source_declaration(C,C.ref(p))
            self.assertEqual(declaration['class_name'],'NPUModelRunner')
            self.assertEqual(declaration['decorators'],['torch.inference_mode()'])

    def test_all_compile_and_original_observer_guards_remain(self):
        for p in P.glob('*.py'):compile(ast.parse(p.read_text()),str(p),'exec')
        path=P.parent/'native_ar_pair/native_ar_observer.py';raw=path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'3ccb13c1bd2da589e49ad46ce01f6544d346537136ebd13dafbabe0d8e6c26ac')
        text=raw.decode();self.assertIn('inspect.getclosurevars(wrapped).nonlocals',text)
        self.assertIn("type(context) is t.inference_mode and context.mode is True",text)
        self.assertIn("old_samples = native_method(runner,'sample_tokens',refs['torch_contextlib'])",text)


if __name__=='__main__':unittest.main()
