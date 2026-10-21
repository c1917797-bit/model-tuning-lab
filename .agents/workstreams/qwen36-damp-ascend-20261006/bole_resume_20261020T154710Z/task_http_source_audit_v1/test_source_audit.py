"""Pure software controls only; no actual remote closure or model test."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
import audit_common as A
import source_audit as S


class IOControls(unittest.TestCase):
    def test_ref_and_changed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json';p.write_text('{}')
            r=A.ref(p);self.assertEqual(A.obj(r),{})
            p.write_text('[]')
            with self.assertRaises(ValueError):A.checked(r)

    def test_ref2_and_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json';p.write_text('{}');r=A.ref(p)
            i=A.Inventory();i.add(r,'one');i.add(dict(path=r['path'],sha256=r['sha256']),'two')
            self.assertEqual(i.counts()['unique_files'],1)
            self.assertEqual(i.counts()['duplicate_ref_attachments'],1)
            p.write_text('[]')
            with self.assertRaises(ValueError):i.add(A.ref(p),'conflict')

    def test_before_after_reopen(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json';p.write_text('{}');i=A.Inventory();i.add(A.ref(p),'input')
            self.assertEqual(len(i.recheck()),1)
            p.write_text('[]')
            with self.assertRaises(ValueError):i.recheck()

    def test_ref_no_symlink_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'file';p.write_text('x');q=Path(d)/'link';q.symlink_to(p)
            with self.assertRaises(ValueError):A.ref(q)
            b=Path(d)/'weights.bin';b.write_bytes(b'fake')
            with self.assertRaises(ValueError):A.ref(b)

    def test_strict_json(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}'):
            with self.assertRaises(ValueError):A.parse(raw)

    def test_exclusive_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new';A.new_leaf(p)
            with self.assertRaises(ValueError):A.new_leaf(p)
            A.write(p/'x.json',{})
            with self.assertRaises(ValueError):A.write(p/'x.json',{})

    def test_manifest_entry_whole_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'x.py').write_text('pass\n');r=A.ref(p/'x.py')
            m=A.write(p/'M.json',dict(files={'x.py':{k:r[k]for k in('bytes','sha256')}}))
            self.assertEqual(len(A.verify_manifest(m,p)[1]),2)
            (p/'x.py').write_text('no\n')
            with self.assertRaises(ValueError):A.verify_manifest(m,p)


class SelectionControls(unittest.TestCase):
    def fixture(self,root):
        names=['GSM8K','HumanEval','MMLU'];lengths=iter([89,50,134,126,362,377])
        c=SimpleNamespace(COUNTS={n:2 for n in names},SMOKE={n:[n+'-0',n+'-1']for n in names},
                          TASK_PROTOCOLS={n:'frozen-'+n for n in names},checked=A.checked,digest=lambda v:hashlib.sha256(A.canonical(v)).hexdigest())
        effective={'tasks':{}}
        for n in names:
            rows=[dict(id=n+'-'+str(k),prompt_token_ids=[7]*next(lengths),render_protocol='frozen-'+n,ntrain=5)for k in range(2)]
            p=root/(n+'.json');r=A.write(p,rows);h=hashlib.sha256()
            for row in rows:h.update(bytes.fromhex(c.digest(row)))
            effective['tasks'][n]=dict(rows_ref=r,count=2,max_prompt_tokens=max(len(x['prompt_token_ids'])for x in rows),ordered_row_hash_chain=h.hexdigest())
        return c,effective

    @staticmethod
    def array(p):return iter(json.loads(Path(p).read_bytes()))

    def test_stream_selection_order_counts(self):
        with tempfile.TemporaryDirectory() as d:
            c,e=self.fixture(Path(d));rows,counts=S.select_existing(c,e,self.array)
            self.assertEqual(counts,c.COUNTS)
            self.assertEqual([len(r['prompt_token_ids'])for _,r in rows],[89,50,134,126,362,377])

    def test_wrong_chain_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            c,e=self.fixture(Path(d));e['tasks']['GSM8K']['ordered_row_hash_chain']='0'*64
            with self.assertRaises(ValueError):S.select_existing(c,e,self.array)

    def test_wrong_protocol_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            c,e=self.fixture(Path(d));c.TASK_PROTOCOLS['GSM8K']='other'
            with self.assertRaises(ValueError):S.select_existing(c,e,self.array)

    def test_wrong_shots_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            c,e=self.fixture(Path(d));meta=e['tasks']['MMLU'];p=Path(meta['rows_ref']['path']);rows=json.loads(p.read_bytes());rows[0]['ntrain']=0
            p.write_bytes(A.canonical(rows));meta['rows_ref']=A.ref(p)
            with self.assertRaises(ValueError):S.select_existing(c,e,self.array)

    def test_duplicate_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            c,e=self.fixture(Path(d));meta=e['tasks']['GSM8K'];p=Path(meta['rows_ref']['path']);rows=json.loads(p.read_bytes());rows[1]['id']=rows[0]['id']
            p.write_bytes(A.canonical(rows));meta['rows_ref']=A.ref(p)
            with self.assertRaises(ValueError):S.select_existing(c,e,self.array)

    def test_pure_function_projection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.py';p.write_text("raise RuntimeError('module must never execute')\ndef request_body(row,model):\n C.need(bool(model),'model')\n return {'prompt':row['prompt_token_ids'],'model':model}\n")
            fn,sha=S.frozen_request_body(A.ref(p),SimpleNamespace(need=A.need))
            self.assertEqual(fn({'prompt_token_ids':[1]},'x'),dict(prompt=[1],model='x'))
            self.assertEqual(len(sha),64)

    def test_projection_duplicate_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.py';p.write_text('def request_body(row,model):pass\ndef request_body(row,model):pass\n')
            with self.assertRaises(ValueError):S.frozen_request_body(A.ref(p),None)


class BoundaryControls(unittest.TestCase):
    def test_model_gates_always_pending(self):
        p=S.pending_model_gates()
        self.assertIsNone(p['actual_G2_source_ref']);self.assertIsNone(p['actual_G2_owner_ref'])
        self.assertIsNone(p['actual_G2_independent_ref']);self.assertIsNone(p['actual_G2_consumer_exit_ref'])
        self.assertFalse(p['model_construction_admitted']);self.assertFalse(p['actual_HTTP_executed'])

    def test_default_OFF_and_help(self):
        for flags in ([],['--help']):
            r=subprocess.run([sys.executable,'-I','-B',str(P/'source_audit.py'),*flags],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse(json.loads(subprocess.check_output([sys.executable,'-I','-B',str(P/'source_audit.py')]))['enabled'])

    def test_missing_explicit_refs_rejects(self):
        r=subprocess.run([sys.executable,'-I','-B',str(P/'source_audit.py'),'--prepare'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0)

    def test_import_denied_before_body(self):
        program="import sys;sys.path.insert(0,sys.argv[1]);import audit_common as A;seen=A.install_read_only_import_guard();\ntry:import numpy\nexcept RuntimeError:pass\nelse:raise AssertionError('not denied')\nassert seen==['numpy'] and 'numpy'not in sys.modules"
        r=subprocess.run([sys.executable,'-I','-B','-c',program,str(P)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)

    def test_old_HTTP_manifest_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);m=A.write(p/'M.json',dict(files={'file':{'bytes':0,'sha256':'0'*64}}))
            with self.assertRaises(ValueError):A.verify_manifest(m,p,A.HTTP_SHA)


if __name__=='__main__':unittest.main()
