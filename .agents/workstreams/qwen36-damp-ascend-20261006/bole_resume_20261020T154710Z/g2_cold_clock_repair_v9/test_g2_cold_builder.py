"""Exact whole inverse, safe portability, original source279, and alias controls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import prepare_g2_cold_v9 as B
import sourceio as C
import g2_cold_parent_output as O


def old():
    review=P.parent/'g2_channel_handoff_repair_v8'
    if review.is_dir():return{n:(P.parent/'g2_parent_software_repair_v4/service_entry.py'if n=='service_entry.py'else review/n)for n in B.CHANGED}
    m=C.obj(C.ref(P/'SOURCE_BOUND.json'));parent=C.obj(m['g2_cold_clock_v9']['parent_source']);return{n:C.checked(parent['files'][n])for n in B.CHANGED}


class BuilderControls(unittest.TestCase):
 def test_exact_declared_whole_inverses_recover_frozen_v8(self):
    for n,path in old().items():self.assertEqual(B.inverse(n,(P/n).read_text()),path.read_text(),n)
 def test_undeclared_host_create_or_capture_delta_cannot_invert_to_parent(self):
    for n,path in old().items():
        bad=(P/n).read_text()+'\n# undeclared-delta\n'
        self.assertNotEqual(B.inverse(n,bad),path.read_text())
 def test_original_production_four_copy_and_atomic_functions_ast_unchanged(self):
    import ast
    before=ast.parse(old()['g2_handoff.py'].read_text());after=ast.parse((P/'g2_handoff.py').read_text())
    def funcs(tree):return{n.name:ast.dump(n,include_attributes=False)for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    a,b=funcs(before),funcs(after)
    for name in a:
        if name not in('stage_saved_probe','verify_saved_probe'):self.assertEqual(a[name],b[name],name)
 def test_one_parent_rw_alias_rejects_shadowing_any_actual_input(self):
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);parent=C.write(root/'parent.json',dict(output_root=str(root/'old-model')));sr=C.write(root/'source.json',dict(g2_cold_clock_v9=dict(parent_source=parent)));leaf=root/'new/cpu-preflight';source=root/'new-source'
        expected=root/'old-model/cpu-preflight';got=O.parent_alias(C,sr,leaf,[],source)
        self.assertEqual(got,{str(expected):(str(leaf),True)})
        for path in(expected,expected/'existing-input.json'):
            with self.subTest(path=path),self.assertRaises(ValueError):O.parent_alias(C,sr,leaf,[dict(path=str(path))],source)
        self.assertNotIn(str(root/'old-model-CPU/cpu-preflight'),got)
 def test_ordinary_portable_refs_accept_bytes_only_and_reject_wrong_bytes_or_symlink(self):
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);p=root/'file';p.write_bytes(b'actual');r=B.ref(p)
        self.assertEqual(B.checked(r),p)
        for key,value in(('bytes',r['bytes']+1),('sha256','0'*64),('path',str(root/'missing'))):
            with self.subTest(key=key),self.assertRaises((ValueError,FileNotFoundError)):B.checked(dict(r,**{key:value}))
        alias=root/'alias';alias.symlink_to(p)
        with self.assertRaises(ValueError):B.ref(alias)
 def test_prepare_audit_software_and_host_default_OFF_help(self):
    for name in('prepare_g2_cold_v9.py','audit_source_v9.py','service_entry.py','host_service.py'):
        for args in([],['--help']):
            q=subprocess.run([sys.executable,'-I','-B',str(P/name),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,name+q.stderr)
            if not args:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))


class ActualEvidenceControls(unittest.TestCase):
 def review(self):
    review=P.parent.parent/'g2_review_v8_cpu'
    return review if review.is_dir()else None
 def test_retained_actual_parent279_parser_failure_is_not_cold_or_model_pass(self):
    review=self.review()
    if review is None:
        m,refs,cause=B.evidence(B.SOURCE,B.FAILED_OWNER,B.AUDIT)
    else:
        refs=json.loads((review/'ACTUAL_REFS.json').read_text());by_path={r['path']:(r,review/rel)for rel,r in refs.items()}
        rawref=B.ref;rawcheck=B.checked
        def route_check(r):
            if r['path']not in by_path:return rawcheck(r)
            expected,path=by_path[r['path']];self.assertEqual(r,expected);data=path.read_bytes();self.assertEqual((len(data),hashlib.sha256(data).hexdigest()),(r['bytes'],r['sha256']));return path
        def route_ref(path):
            if str(path)not in by_path:return rawref(path)
            r,local=by_path[str(path)];route_check(r);return r
        with patch.object(B,'checked',route_check),patch.object(B,'ref',route_ref):m,refs,cause=B.evidence(B.SOURCE,B.FAILED_OWNER,B.AUDIT)
    self.assertEqual(m['service_required_sameimage_software_cases'],279);self.assertTrue(cause['actual279_software_only']);self.assertFalse(cause['actual_saved_handoff_pass']);self.assertFalse(cause['actual_model_pass']);self.assertTrue(cause['old_elapsed_is_late_and_not_rewritten'])
 def test_exact_parent_extract_preserves_noise_and_rejects_missing_duplicate_failed_wrong_source(self):
    review=self.review()
    if review is None:
        parent=B.obj(B.SOURCE);owner=B.obj(B.FAILED_OWNER);child=B.obj(B.legacy(owner['summary']['actual_software_child']));raw=B.checked(B.legacy(child['stdout_ref'])).read_bytes();helper=C.checked(parent['files']['parent_software_output.py'])
    else:
        parent=json.loads((review/'source/SOURCE_BOUND.json').read_bytes());raw=(review/'cpu-preflight/SOFTWARE.stdout').read_bytes();helper=P.parent/'g2_parent_software_repair_v4/parent_software_output.py'
        self.assertEqual((helper.stat().st_size,hashlib.sha256(helper.read_bytes()).hexdigest()),(parent['files']['parent_software_output.py']['bytes'],parent['files']['parent_software_output.py']['sha256']))
    oldcheck=C.checked
    def checked(r):return helper if r==parent['files']['parent_software_output.py']else oldcheck(r)
    with patch.object(C,'checked',checked):
        actual=O.extract(b'non-JSON prefix\n'+raw+b'non-JSON tail\n',B.SOURCE,parent);self.assertEqual(actual['tests'],279)
        for bad in(b'noise only\n',raw+raw,O.canonical(dict(actual,all_tests_passed=False))+b'\n',O.canonical(dict(actual,source=dict(B.SOURCE,sha256='0'*64)))+b'\n'):
            with self.subTest(bad=bad[:30]),self.assertRaises(ValueError):O.extract(bad,B.SOURCE,parent)


if __name__=='__main__':unittest.main()
