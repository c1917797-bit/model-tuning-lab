"""Actual original025 module + real creator before any resource/Docker action."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_callee_proof as Q
import g2_cold_parent_output as O
import owned_create as CREATOR


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def actual_original(name):
    refs=Q.declarations(P/'owned_substrate.py');r=refs[name]
    review=P.parent.parent/'g1_review_v2'
    if review.is_dir():
        p=review/(name+'.py');data=p.read_bytes();C.need((len(data),hashlib.sha256(data).hexdigest())==(r['bytes'],r['sha256']),'actual whole copied025 source');return p
    return C.checked(r)


class NoResourceBoundary(RuntimeError):pass


class CalleeControls(unittest.TestCase):
 def actual_c(self):return module(actual_original('model_contract'),'_g2_v10_actual025_model_contract')
 def fixture(self,c,parent_under_source=False):
    td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);source=root/'new-source';source.mkdir();leaf=root/'new-output/cpu-preflight';leaf.mkdir(parents=True)
    oldout=source if parent_under_source else root/'old-model-output'
    parent=C.write(root/'parent.json',dict(output_root=str(oldout)));sr=C.write(root/'source.json',dict(g2_cold_clock_v9=dict(parent_source=parent)))
    calls=[]
    def call(label,argv,**kw):calls.append((label,argv,kw));raise NoResourceBoundary('actual real creator reached first Docker boundary, deliberately not invoked')
    ctl=NS(out=leaf,name='g2-v10-source-only-no-container',call=call,expected=None)
    S=NS(__file__=str(actual_original('safety_host')),DOCKER='/usr/bin/docker')
    return root,source,leaf,sr,ctl,S,calls,oldout/'cpu-preflight'
 def test_real_original025_has_require_not_need_and_old_v9_failure_is_reproduced(self):
    c=self.actual_c();self.assertTrue(callable(c.require));self.assertFalse(hasattr(c,'need'))
    root,source,leaf,sr,ctl,S,calls,alias=self.fixture(c)
    # Reconstruct only the exact prior function text from the reviewed new inverse.
    import prepare_g2_callee_v10 as B
    old=B.inverse((P/'g2_cold_parent_output.py').read_text());tree=ast.parse(old);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='parent_alias');scope=dict(Path=Path,C=C)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-v9-original-parent_alias','exec'),scope)
    with self.assertRaisesRegex(AttributeError,'need'):scope['parent_alias'](c,sr,leaf,[],source)
    self.assertEqual(calls,[])
 def test_real_original025_alias_and_real_creator_reach_next_boundary_without_Docker(self):
    c=self.actual_c();root,source,leaf,sr,ctl,S,calls,alias=self.fixture(c)
    self.assertEqual(O.parent_alias(c,sr,leaf,[],source),{str(alias):(str(leaf),True)})
    with self.assertRaises(NoResourceBoundary):CREATOR.create(c,S,ctl,sr,[],'cpu-preflight',source)
    self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],'unique-name');self.assertEqual(calls[0][1][:3],['/usr/bin/docker','ps','-a'])
    self.assertEqual(ctl.expected['source'],sr);self.assertEqual(ctl.expected['guest_cpus'],[145]);self.assertEqual(ctl.expected['mounts'][str(alias)],(str(leaf),True));self.assertTrue(all(Path(src)==leaf for src,rw in ctl.expected['mounts'].values()if rw))
 def test_real_original025_illegal_alias_and_actual_readset_shadow_fail_before_Docker(self):
    c=self.actual_c()
    for kind in('source-alias','exact-input','descendant-input'):
        root,source,leaf,sr,ctl,S,calls,alias=self.fixture(c,parent_under_source=kind=='source-alias');readset=[]
        if kind!='source-alias':
            alias.mkdir(parents=True);p=alias/'input.json'if kind=='descendant-input'else alias
            if kind=='descendant-input':readset=[C.write(p,dict(actual=True))]
            else:readset=[dict(path=str(p),bytes=0,sha256='0'*64)]
        with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'cannot hide immutable evidence'):CREATOR.create(c,S,ctl,sr,readset,'cpu-preflight',source)
        self.assertEqual(calls,[]);self.assertIsNone(ctl.expected)
 def test_real_original025_wrong_source_SHA_fails_before_alias_or_Docker(self):
    c=self.actual_c();root,source,leaf,sr,ctl,S,calls,alias=self.fixture(c)
    with self.assertRaises(ValueError):CREATOR.create(c,S,ctl,dict(sr,sha256='0'*64),[],'cpu-preflight',source)
    self.assertEqual(calls,[]);self.assertFalse(hasattr(c,'need'))
 def test_exact_original18_fallback_resolves_bound_snapshot_without_local_review(self):
    import shutil
    actual=actual_original('safety_host')
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp)/'isolated/source';root.mkdir(parents=True);snapshot=root/'safety_host.py';shutil.copyfile(actual,snapshot)
        C.write(root/'SOURCE_BOUND.json',dict(files={'safety_host.py':C.ref(snapshot)}))
        self.assertFalse((root.parent.parent/'g1_review_v2').exists())
        tree=ast.parse((P/'test_g2_cold_clock.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='original');scope=dict(P=root,C=C,Path=Path)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(P/'test_g2_cold_clock.py')+'#unchanged-original-fallback','exec'),scope)
        self.assertEqual(scope['original']('safety_host.py'),snapshot);self.assertEqual(snapshot.read_bytes(),actual.read_bytes())
    if(P/'SOURCE_BOUND.json').exists():
        m=C.obj(C.ref(P/'SOURCE_BOUND.json'));proof=Q.verify_snapshot(m);self.assertTrue(proof['byteequal']);self.assertFalse(proof['snapshot_imported_as_controller'])
 def test_all_original18_test_files_and_runtime_cold_seams_are_whole_byteequal(self):
    import prepare_g2_callee_v10 as B
    review=P.parent/'g2_cold_clock_repair_v9'
    if review.is_dir():before={n:review/n for n in B.PRESERVED}
    else:
        m=C.obj(C.ref(P/'SOURCE_BOUND.json'));parent=C.obj(m['g2_callee_contract_v10']['parent_source']);before={n:C.checked(parent['files'][n])for n in B.PRESERVED}
    for n,p in before.items():self.assertEqual((P/n).read_bytes(),p.read_bytes(),n)
    self.assertEqual(B.inverse((P/'g2_cold_parent_output.py').read_text()),(review/'g2_cold_parent_output.py').read_text()if review.is_dir()else C.checked(parent['files']['g2_cold_parent_output.py']).read_text())
 def test_new_preparer_and_audit_are_default_OFF_and_help(self):
    import subprocess
    for n in('prepare_g2_callee_v10.py','audit_source_v10.py'):
        for args in([],['--help']):
            q=subprocess.run([sys.executable,'-I','-B',str(P/n),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,q.stderr)
            if not args:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))
        program="import importlib.util,json,pathlib; p=pathlib.Path("+repr(str(P))+ "); s=importlib.util.spec_from_file_location('isolated_prepare',p/'prepare_g2_callee_v10.py'); b=importlib.util.module_from_spec(s); s.loader.exec_module(b); q=b.proof_module(p,b.ref(p/'sourceio.py')); print(json.dumps(q.declarations(p/'owned_substrate.py')))"
        q=subprocess.run([sys.executable,'-I','-B','-c',program],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(set(json.loads(q.stdout)),{'model_contract','safety_host','host_once'})


if __name__=='__main__':unittest.main()
