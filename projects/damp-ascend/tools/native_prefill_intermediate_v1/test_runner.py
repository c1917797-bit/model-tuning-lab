"""Pure stdlib contracts. Fake tensors are NOT a numerical/NPU golden."""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import contract
import runner

class Tensor:
    def __init__(self,rows):self.rows=list(rows);self.shape=(len(self.rows),12,128)
    def __getitem__(self,key):return Tensor(self.rows[key])
    def contiguous(self):return self
    def clone(self):return Tensor(self.rows)
class FakeTorch:
    class npu:
        @staticmethod
        def synchronize():pass
    @staticmethod
    def cat(xs,dim=0):
        assert dim==0
        return Tensor([r for x in xs for r in x.rows])
class Gate:
    def __init__(self):self.fixture={"stage":"test","step":7};self.retained=[]
    def retain(self,name):self.retained.append(copy.deepcopy(self.fixture))
def digest(x):
    return None if x is None else {"fake_rows":list(x.rows)}
def inputs(p):return [Tensor(range(p)) for _ in range(5)]
def invoke(gate,ref,ins,selected,plans,sr,nd):
    tensors=ins+[nd(selected)]+plans+[sr]
    outputs=ref(*tensors)
    record={"before":tensors,"after":tensors,"returns":outputs,"pointers_before":[11]*len(tensors),
            "pointers_after":[11]*len(tensors),"dispatch_error":None,
            "output_copy_errors":[],"input_copy_errors":[]}
    gate.fixture["independent_reference"]=record
    return outputs
def ref(*xs):
    rows=xs[5].rows
    return tuple(Tensor(rows) for _ in range(3))
def make(invoke_=invoke,journal=None):
    records=[];counts={"row_reference_calls":0}
    adapter=runner.RowwiseReference(FakeTorch,invoke_,journal or (lambda row,commit:records.append((row,commit))),
                                   counts,digest=digest,guard=lambda:None)
    return adapter,records,counts

class Contracts(unittest.TestCase):
    def test_real_shards(self):
        self.assertEqual(contract.matrix("P2-8"),tuple(range(2,9)))
        self.assertEqual(contract.matrix("P9-15"),tuple(range(9,16)))
        self.assertEqual(set(contract.matrix("P2-8"))|set(contract.matrix("P9-15")),set(range(2,16)))
    def test_counts(self):
        a,b=contract.counts("P2-8"),contract.counts("P9-15")
        self.assertEqual(a["decode_turns"]+b["decode_turns"],8960)
        self.assertEqual(a["row_reference_calls"]+b["row_reference_calls"],76160)
        self.assertEqual(a["native_fraction_decisions"]+b["native_fraction_decisions"],93585408)
    def test_deadline(self):
        contract.deadline(contract.CUTOFF_NS-1)
        with self.assertRaises(RuntimeError):contract.deadline(contract.CUTOFF_NS)
        with self.assertRaises(RuntimeError):contract.deadline(contract.CUTOFF_NS+1)
    def test_no_partial_shard(self):
        for x in ("P2","P1-16","P2-15","PAD16"):
            with self.assertRaises(RuntimeError):contract.matrix(x)
    def test_default_disabled(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:self.assertEqual(runner.main([]),0)
        result=json.loads(output.getvalue())
        self.assertFalse(result["npu_executed"])
        self.assertEqual(result["status"],"disabled")
        self.assertNotIn("torch",sys.modules)
    def test_cli_does_not_accept_fake_batch(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):runner.parser().parse_args(["--batches","16"])
    def test_rowwise_actual_allP_order_and_all_rows(self):
        for p in range(2,16):
            adapter,rows,counts=make();gate=Gate()
            source=Tensor(range(p))
            result=adapter(gate,ref,inputs(p),source,[Tensor([0])]*3,Tensor([1]),lambda x:x)
            self.assertEqual([x.rows for x in result],[list(range(p))]*3)
            self.assertEqual(source.rows,list(range(p)))
            self.assertEqual(counts["row_reference_calls"],p)
            self.assertEqual([x[0]["row"] for x in rows],list(range(p)))
            self.assertEqual([x[0]["step"] for x in rows],[7]*p)
            self.assertEqual(len(gate.fixture["rowwise_reference"]["records"]),p)
            self.assertTrue(rows[-1][1])
            self.assertTrue(all(x[0]["executed"] for x in rows))
    def test_same_reference_partition_anchor_fake_only(self):
        adapter,_,_=make();gate=Gate();source=Tensor(range(16))
        full=invoke(gate,ref,inputs(16),source,[Tensor([0])]*3,Tensor([1]),lambda x:x)
        split=adapter(gate,ref,inputs(16),source,[Tensor([0])]*3,Tensor([1]),lambda x:x)
        self.assertEqual([x.rows for x in full],[x.rows for x in split])
    def test_original_dispatch_survives_old_after_query_and_journal_failure(self):
        primary=RuntimeError("original NPU dispatch")
        def bad_ref(*xs):raise primary
        def old_after_query(gate,ref_,ins,selected,plans,sr,nd):
            gate.fixture["independent_reference"]={"before":ins,"pointers_before":[4]*5}
            try:ref_(*ins)
            except BaseException:raise OSError("secondary pointer query")
        def journal(*unused):raise OSError("secondary evidence IO")
        adapter,_,counts=make(old_after_query,journal);gate=Gate()
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            try:adapter(gate,bad_ref,inputs(2),Tensor(range(2)),[],Tensor([1]),lambda x:x)
            except BaseException as error:self.assertIs(error,primary)
            else:self.fail("must fail")
        self.assertEqual(counts["row_reference_calls"],1)
        self.assertIn("secondary",stderr.getvalue())
        self.assertEqual(gate.retained[0]["rowwise_reference"]["original_native_error"]["error"],repr(primary))
    def test_failure_row_keeps_prior_records(self):
        primary=RuntimeError("row2 original")
        def perrow(*xs):
            if xs[5].rows==[2]:raise primary
            return ref(*xs)
        adapter,rows,counts=make();gate=Gate()
        with self.assertRaises(RuntimeError) as caught:
            adapter(gate,perrow,inputs(4),Tensor(range(4)),[],Tensor([1]),lambda x:x)
        self.assertIs(caught.exception,primary)
        state=gate.retained[0]["rowwise_reference"]
        self.assertEqual([x["row"] for x in state["records"]],[0,1,2])
        self.assertEqual(state["full_selected"].rows,list(range(4)))
        self.assertEqual([x[0]["row"] for x in rows],[0,1,2])
        self.assertEqual(counts["row_reference_calls"],3)
    def test_missing_output_fails_not_pass(self):
        def invalid(*xs):return [Tensor([0])]
        adapter,rows,counts=make();gate=Gate()
        with self.assertRaises(RuntimeError):
            adapter(gate,invalid,inputs(2),Tensor(range(2)),[],Tensor([1]),lambda x:x)
        self.assertIsNotNone(rows[-1][0]["exception"])
        self.assertTrue(rows[-1][0]["executed"])
    def test_software_does_not_import_torch(self):
        self.assertNotIn("torch",sys.modules)
        tree=ast.parse((contract.HERE/"runner.py").read_text())
        self.assertFalse(any(isinstance(x,(ast.Import,ast.ImportFrom)) and
             any(a.name=="torch" for a in getattr(x,"names",[])) for x in tree.body))
    def test_no_frozen_module_global_reassignment(self):
        text=(contract.HERE/"runner.py").read_text()
        self.assertNotIn("setattr(torch.ops",text)
        self.assertNotIn("args.batches",text)
        self.assertNotIn("native_feedback.run(",text)
        self.assertNotIn("parse_args =",text)
        self.assertIn("feedback(torch,npu,nd,decode_ops,ref,rowwise",text)
    def test_durable_before_golden_and_exact160(self):
        text=(contract.HERE/"runner.py").read_text()
        self.assertLess(text.index("checkpoint=durable("),text.index("pack_once(torch,npu,gate"))
        self.assertIn('==160',text)
        self.assertIn('prebuilt_meta=None',text)
        self.assertIn('candidate_prepare_calls"]==2*binding',text)
    def test_actual_builder_pinned(self):
        self.assertEqual(contract.BUILDER_SHA,"42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16")
        self.assertEqual(contract.BUILDER_MANIFEST_SHA,"b05d03335c10dfb3b0e7ed5f8b691ac0e95529d424cac39f85c1d31b1d710b46")
    def test_schema_checks_not_only_meta(self):
        text=(contract.HERE/"runner.py").read_text()
        self.assertIn("decode_reference_schema(decode_real,ref)",text)
        self.assertIn('"actual independent reference10/three nonalias returns"',text)

if __name__=="__main__":unittest.main()
