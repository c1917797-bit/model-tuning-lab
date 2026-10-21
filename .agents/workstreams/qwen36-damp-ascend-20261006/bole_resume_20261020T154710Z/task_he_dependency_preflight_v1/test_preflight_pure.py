"""No container, device, real namespace/network probe, evaluator or dependency import."""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import he_policy as H
import preflight_host as Host
import preflight_evidence as E
import preflight_contract as T


def payload():
    expected=C.obj(C.ref(P/'DEPENDENCY_EXPECTED.json'))
    def lib(name):
        r=expected['files'][name];return dict(path=r['installed_path'],bytes=r['copied_ref']['bytes'],sha256=r['copied_ref']['sha256'])
    return dict(schema='bole.actual-HE-official-sandbox-result/v2',mode='preflight',root_source_sha256='r'*64,
        capsule_sha256='c'*64,input_sha256='i'*64,authority_sha256='a'*64,official_evaluation_sha256=E.EVAL_SHA,
        official_execution_sha256=E.EXEC_SHA,generated_code_executed=False,task_score_produced=False,
        task_accuracy_accepted=False,model_ready=False,NPU=False,network_admission={},runtime_identity=dict(
        python_executable='/usr/local/python3.12.13/bin/python3',python_version='3.12.13 (synthetic fixture)',
        numpy_version='1.26.4',tqdm_version='4.synthetic',numpy_source=lib('numpy_init.py'),tqdm_source=lib('tqdm_init.py')))


class Pure(unittest.TestCase):
    def parse(self,v):
        stage=dict(original_task_source_ref=dict(sha256='r'*64),capsule_ref=dict(sha256='c'*64),inputs_ref=dict(sha256='i'*64))
        obj=C.obj
        with patch.object(C,'obj',side_effect=lambda r:dict(authority_sha256='a'*64)if r==stage['capsule_ref']else obj(r)):
            return E.parse(E.MARKER+json.dumps(v),stage)
    def test_preflight_parse_only_no_score(self):
        v=self.parse(payload());self.assertFalse(v['generated_code_executed']);self.assertEqual(v['mode'],'preflight')
    def test_wrong_or_duplicate_result(self):
        v=payload();v['mode']='controls'
        with self.assertRaises(ValueError):self.parse(v)
        stage=dict(capsule_ref={},inputs_ref={},original_task_source_ref={})
        with self.assertRaises(ValueError):E.parse(E.MARKER+'{}\n'+E.MARKER+'{}',stage)
    def test_task_rows_or_scores_forbidden(self):
        for name,val in(('rows',[]),('component_score',1),('generated_code_executed',True),('task_score_produced',True)):
            v=payload();v[name]=val
            with self.assertRaises(ValueError,msg=name):self.parse(v)
    def test_wrong_python_or_library_source_rejected(self):
        for key,val in(('python_executable','/usr/bin/python3'),('python_version','3.10.12 synthetic'),('numpy_version','stub'),('tqdm_version','UNKNOWN')):
            v=payload();v['runtime_identity'][key]=val
            with self.assertRaises(ValueError,msg=key):self.parse(v)
        v=payload();v['runtime_identity']['numpy_source']['sha256']='0'*64
        with self.assertRaises(ValueError):self.parse(v)
    def test_only_path_delta_in_policy(self):
        expected='PATH=/usr/local/python3.12.13/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        self.assertEqual(H.ENV[0],expected)
        for mode in('preflight','controls','tasks'):
            argv=H.argv('bole-he-synthetic','sha256:'+'1'*64,'/public/source','/public/suite','/public/inputs','c'*64,mode)
            self.assertEqual(argv[argv.index('python3'):],['python3','-I','-B','/source/he_worker.py','--'+mode,'--capsule-sha256','c'*64])
            self.assertIn('--network',argv);self.assertIn('none',argv);self.assertIn('65534:65534',argv)
            self.assertEqual(sum(v=='--mount'for v in argv),3)
        old=P.parent/'task_decoder_scorer_v3'
        if old.exists():
            self.assertEqual((P/'he_policy.py').read_text().replace('/usr/local/python3.12.13/bin:',''),(old/'he_policy.py').read_text())
    def test_original_worker_guard_and_official_call_unchanged(self):
        old=P.parent/'task_decoder_scorer_v3'
        if old.exists():
            for name in T.PUBLIC:self.assertEqual((P/name).read_bytes(),(old/name).read_bytes(),name)
        tree=ast.parse((P/'he_worker.py').read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
        branch=next(n for n in f.body if isinstance(n,ast.If)and ast.unparse(n.test)=="mode == 'preflight'")
        self.assertIsInstance(branch.body[-1],ast.Return)
        self.assertNotIn('evaluate_functional_correctness',ast.unparse(branch))
        call=next(n for n in ast.walk(f)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='evaluate_functional_correctness')
        self.assertEqual({k.arg:ast.literal_eval(k.value)for k in call.keywords if k.arg in('k','n_workers','timeout')},{'k':[1],'n_workers':1,'timeout':3.0})
    def test_original_resource_namespace_admission_helpers_unchanged(self):
        old=P.parent/'task_cpu_owner_qualification_v12'
        if old.exists():
            for name in('he_owned.py','owner_namespace.py','main_quiescence.py','lock_evidence.py','network_evidence.py','he_admission.py'):
                self.assertEqual((P/name).read_bytes(),(old/name).read_bytes(),name)
    def test_mode_selected_only_once_and_owner_default_off(self):
        tree=ast.parse((P/'preflight_host.py').read_bytes());source=ast.unparse(tree)
        self.assertIn("self.command[self.command.index('--controls')] = '--preflight'",source)
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        self.assertEqual(ast.unparse(main.body[0]),'entry_start = time.monotonic()')
    def test_binding_strict_new_path_whole_expected_binary(self):
        s=(P/'binding.py').read_text();self.assertIn("for directory in('/usr/local/python3.12.13/bin',",s)
        self.assertIn('5d137e6378d886d6ee0390e126011e9e8af81290032e3fefa13a81f72651fda0',s)
        self.assertIn("'/source/he_worker.py','--preflight'",s);self.assertIn("'actual HE loaded executable matches whole namespace PATH binary'",s)
    def test_no_model_eval_or_dependency_import_in_owner_reader(self):
        for name in('preflight_host.py','preflight_evidence.py','prepare_preflight.py','binding.py'):
            tree=ast.parse((P/name).read_bytes());imports=[]
            for n in ast.walk(tree):
                if isinstance(n,ast.Import):imports.extend(v.name for v in n.names)
                if isinstance(n,ast.ImportFrom):imports.append(n.module)
            self.assertFalse({'numpy','tqdm','torch','torch_npu','vllm','transformers'}&set(imports),name)
            self.assertNotIn('evaluate_functional_correctness',ast.unparse(tree))
    def test_default_off_and_help(self):
        for name in('prepare_preflight.py','preflight_host.py','preflight_evidence.py'):
            for args in((),('--help',)):
                r=subprocess.run([sys.executable,'-I','-B',str(P/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,(name,r.stderr))
                if not args:self.assertFalse(json.loads(r.stdout)['enabled'])


if __name__=='__main__':unittest.main()
