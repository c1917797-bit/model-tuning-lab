"""Synthetic source guard and frozen predecessor checks; no installed ML import."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import decoder as D
import task_contract as C


class NativeSourceGuard(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'synthetic_native.py'
        self.source="class Backend:\n    @classmethod\n    def from_pretrained(cls,path,local_files_only=True):\n        return path\n"
        self.path.write_text(self.source);self.ref=C.ref(self.path)
        self.module=types.ModuleType('synthetic_constructor_fixture')
        exec(compile(self.source,str(self.path),'exec'),self.module.__dict__)

    def tearDown(self):self.tmp.cleanup()

    def test_real_synthetic_classmethod_code_source_accepted(self):
        D.native_constructor_guard(self.module.Backend.from_pretrained,self.ref,'Backend.from_pretrained')

    def test_mutated_loaded_code_rejected_with_unchanged_source(self):
        function=self.module.Backend.from_pretrained.__func__
        function.__code__=function.__code__.replace(co_consts=(None,'changed'))
        with self.assertRaisesRegex(ValueError,'loaded library code'):
            D.native_constructor_guard(function,self.ref,'Backend.from_pretrained')

    def test_source_drift_or_wrong_qualname_rejected(self):
        with self.assertRaises(ValueError):D.native_constructor_guard(self.module.Backend.from_pretrained,self.ref,'Other.from_pretrained')
        self.path.write_text(self.source+'# changed bytes\n')
        with self.assertRaises(ValueError):D.native_constructor_guard(self.module.Backend.from_pretrained,self.ref,'Backend.from_pretrained')


class ProspectiveFreeze(unittest.TestCase):
    def test_constructor_explicit_and_not_qualified(self):
        r=C.ref(P/'DECODER_CONSTRUCTOR.json');self.assertEqual(r['sha256'],C.CONSTRUCTOR_SHA)
        m=C.obj(r)
        self.assertEqual(m['constructor'],'transformers.tokenization_utils_tokenizers.TokenizersBackend.from_pretrained')
        self.assertEqual(m['kwargs'],dict(local_files_only=True,trust_remote_code=False))
        for key in('software_qualified','model_ready','formal_task_accuracy_accepted','input_reencoding_permitted','scorer_rule_changes_permitted'):
            self.assertIs(m[key],False)
        self.assertEqual(C.ref(P/'frozen/decoder_v1.py')['sha256'],m['original_decoder_sha256'])
        self.assertEqual(len(m['native_sources']),7)

    def test_original_decode_controls_and_resource_guard_semantics_preserved(self):
        def functions(path):
            return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        old=functions(P/'frozen/decoder_v1.py');new=functions(P/'decoder.py')
        for name in('decode','controls'):self.assertEqual(old[name],new[name],name)
        prior=C.obj(C.ref(P/'frozen/original_packet_manifest.json'))
        self.assertEqual(C.ref(P/'frozen/original_packet_manifest.json')['sha256'],C.obj(C.ref(P/'DECODER_CONSTRUCTOR.json'))['original_package_manifest_sha256'])
        for name,row in prior['files'].items():
            if name.endswith('.py')and name not in{'decoder.py','prepare_packet.py','task_contract.py'}:
                actual=C.ref(P/name)
                self.assertEqual((actual['bytes'],actual['sha256']),(row['bytes'],row['sha256']),name)
        # This optional local predecessor is an additional function-level resource check.
        oldroot=P.parent/'task_decoder_scorer'
        if oldroot.is_dir():
            a=functions(oldroot/'task_contract.py');b=functions(P/'task_contract.py')
            for name in a:
                if name!='source':self.assertEqual(a[name],b[name],name)



if __name__=='__main__':unittest.main()
