"""Pure exact owning-argv and whole inverse regressions. No devices or processes."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_g2_v7_reviewed_preparer',P/'prepare_g2_consumer_v7.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)


def helper():
    tree=ast.parse((P/'g2_stream_owner.py').read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='consumer_commandline'];assert len(nodes)==1
    scope=dict(Path=Path,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/'g2_stream_owner.py'),'exec'),scope);return scope['consumer_commandline']


def original():
    if(P/'SOURCE_BOUND.json').exists():
        m=B.obj(B.ref(P/'SOURCE_BOUND.json'));parent=B.obj(m['g2_exact_consumer_v7']['failed_source']);return B.checked(parent['files']['g2_stream_owner.py']).read_text()
    return (P.parent/'g2_long_output/g2_stream_owner.py').read_text()


class ConsumerArgv(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source=self.root/'SOURCE_BOUND.json';self.source.write_text('{"fixture":"exact ordinary source"}\n');self.sr=B.ref(self.source);self.C=SimpleNamespace(need=B.need,ref=B.ref,checked=B.checked);self.c=SimpleNamespace(PY='/usr/local/python3.12.13/bin/python3');self.guard=helper();self.argv=[self.c.PY,'-B',str(self.root/'g2_consumer.py'),'--execute','--bootstrap','--source-ref',json.dumps(self.sr)]
    def call(self,argv,source=None,root=None):return self.guard(self.C,self.c,argv,source_ref=self.sr if source is None else source,root=str(self.root)if root is None else root)
    def test_exact_original_B_argv_is_accepted(self):self.assertEqual(self.call(self.argv),self.argv)
    def test_stale_isolated_mode_and_missing_B_are_rejected(self):
        for argv in([self.argv[0],'-I',*self.argv[1:]],[self.argv[0],*self.argv[2:]],self.argv[1:]):
            with self.subTest(argv=argv),self.assertRaises(ValueError):self.call(argv)
    def test_executable_script_and_root_must_match_exact_owned_source(self):
        for index,value in((0,'python3'),(0,'/usr/bin/python3'),(2,str(self.root/'foreign.py'))):
            argv=list(self.argv);argv[index]=value
            with self.subTest(index=index,value=value),self.assertRaises(ValueError):self.call(argv)
        with self.assertRaises(ValueError):self.call(self.argv,root=str(self.root/'other'))
    def test_extra_duplicate_or_reordered_flags_cannot_supply_partial_positive_evidence(self):
        for argv in(self.argv+['--channel-ref','foreign'],self.argv+['--execute'],self.argv[:3]+['--bootstrap','--execute',*self.argv[5:]],self.argv[:-2]+['--source-ref',self.argv[-1],'--source-ref',self.argv[-1]]):
            with self.subTest(argv=argv),self.assertRaises(ValueError):self.call(argv)
    def test_source_hash_path_and_literal_canonical_json_are_all_required(self):
        for wrong in(dict(self.sr,sha256='0'*64),dict(self.sr,path=str(self.root/'wrong/SOURCE_BOUND.json'))):
            argv=list(self.argv);argv[-1]=json.dumps(wrong)
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):self.call(argv)
        argv=list(self.argv);argv[-1]=json.dumps(dict(reversed(list(self.sr.items()))));self.assertEqual(json.loads(argv[-1]),self.sr)
        with self.assertRaises(ValueError):self.call(argv)
        self.source.write_text('changed')
        with self.assertRaises(ValueError):self.call(self.argv)
    def test_whole_owner_file_inverse_preserves_all_source_resource_namespace_guards(self):
        before=original();after=B.patch(before);self.assertEqual(after,(P/'g2_stream_owner.py').read_text());self.assertEqual(B.inverse(after),before)
        for text in("cpu['HostConfig']['Devices']in(None,[])","model_view['effective_capacity']==3","view['effective_cpus']==[145]",'actual_mounts==cpu_ctl.expected',"boot['source_before']==m['files']",'identity_owner.frontend',"lifetime['host']['argv']==argv"):
            self.assertIn(text,before);self.assertIn(text,after)
    def test_undeclared_source_or_guard_edits_are_rejected_by_inverse(self):
        before=original()
        with self.assertRaises(ValueError):B.patch(before.replace("model_view['effective_capacity']==3","model_view['effective_capacity']==2"))
        with self.assertRaises(ValueError):B.inverse((P/'g2_stream_owner.py').read_text().replace('consumer_commandline(C,c,argv,source_ref=source_ref,root=m[\'root\'])','pass'))
    def test_preparer_is_cold_defaultOFF_and_help_does_not_launch(self):
        for args in([],['--help']):
            q=subprocess.run([sys.executable,'-I','-B',str(P/'prepare_g2_consumer_v7.py'),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,q.stderr)
            if not args:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))


if __name__=='__main__':unittest.main()
