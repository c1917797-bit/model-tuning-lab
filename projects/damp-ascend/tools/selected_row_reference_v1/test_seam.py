"""SYNTHETIC stdlib behavior tests: no Torch, native load or NPU evidence."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import seam as m

class Tensor:
    """Small symbolic row container; NOT floating-point numerical validation."""
    def __init__(self, values, shape=None, dtype="float32", device="cpu"):
        self.values = copy.deepcopy(list(values))
        self.shape = tuple(shape or (len(self.values),))
        self.dtype = dtype
        self.device = types.SimpleNamespace(type=device)
    def clone(self):
        return Tensor(self.values, self.shape, self.dtype, self.device.type)
    def long(self):
        result = self.clone(); result.dtype = "int64"; return result
    def tolist(self):
        return copy.deepcopy(self.values)
    def index_select(self, dim, index):
        assert dim == 0
        return Tensor([self.values[i] for i in index.values],
                      (len(index.values),) + self.shape[1:], self.dtype)
    def index_copy_(self, dim, index, source):
        assert dim == 0 and len(index.values) == len(source.values)
        for i, value in zip(index.values, source.values):
            self.values[i] = copy.deepcopy(value)
        return self
    def __getitem__(self, index):
        if isinstance(index, slice):
            selected = self.values[index]
        elif isinstance(index, list):
            selected = [self.values[i] for i in index]
        else:
            selected = [self.values[index]]
        return Tensor(selected, (len(selected),) + self.shape[1:], self.dtype)

class Packed:
    def __init__(self, high, low, scales):
        self.high, self.low, self.scales = high, low, scales
    def clone(self):
        return Packed(*(getattr(self, n).clone() for n in m.REGIONS))

def packed(slots):
    return Packed(Tensor(range(slots), (slots,12,128,16), "float16"),
                  Tensor(range(100,100+slots), (slots,12,128,112), "int8"),
                  Tensor(range(200,200+slots), (slots,12,4,112), "float32"))

def exact(left, right):
    return (left.shape == right.shape and left.dtype == right.dtype
            and left.values == right.values)

def inputs(ids):
    b = len(ids)
    return (Tensor(range(b), (b,4,128), "bfloat16"),
            Tensor(range(b), (b,4,128), "bfloat16"),
            Tensor(range(b), (b,12,128), "bfloat16"),
            Tensor(range(b), (b,12), "float32"),
            Tensor(range(b), (b,12), "bfloat16"),
            Tensor(ids, (b,), "int32"))

class Torch:
    int32, int64, long, bfloat16 = "int32", "int64", "int64", "bfloat16"
    @staticmethod
    def tensor(values, dtype):
        return Tensor(values, dtype=dtype)
    @staticmethod
    def cat(rows, dim):
        assert dim == 0
        return Tensor([v for row in rows for v in row.values],
                      (sum(row.shape[0] for row in rows),)+rows[0].shape[1:],
                      rows[0].dtype)
    @staticmethod
    def save(value, path):
        # Tests retain only an explicit symbolic snapshot, never fake .pt.
        Path(path).write_bytes(repr(value).encode())

class Gate:
    def __init__(self, out):
        self.out, self.fixture, self.report = Path(out), {}, {}
        self.required, self.retained, self.saved = [], 0, 0
        self.retain_error, self.save_error = None, None
    def retain(self):
        self.retained += 1
        if self.retain_error: raise self.retain_error
    def require(self, name, passed, details):
        self.required.append((name, passed, copy.deepcopy(details)))
        if not passed: raise AssertionError(name)
    def save(self):
        self.saved += 1
        if self.save_error: raise self.save_error

class Restricted:
    @staticmethod
    def layouts(batch, variant):
        return types.SimpleNamespace(variant=variant), packed(batch+3), object()
    @staticmethod
    def turn(batch, slots, index, generator):
        return inputs([(i+index)%slots for i in range(batch)])

class Protocols:
    exact = staticmethod(exact)
    restricted = Restricted
    REGIONS = m.REGIONS
    @staticmethod
    def packed_dict(p):
        return {n:getattr(p,n).clone() for n in m.REGIONS}
    @staticmethod
    def layout_dict(layout):
        return dict(vars(layout))

class FakeFrozen:
    ValueMajorPacked = Packed
    def __init__(self):
        self.calls, self.validated, self.error = [], [], None
        self.corrupt_source = False
        self.corrupt_local_result = False
        self.bad_flags = False
        self.delta_for_full = 10
    def unpack_value_major(self, p, layout):
        self.validated.append(p.high.shape[0])
        if any(v < 0 for v in p.scales.values) or -128 in p.low.values:
            raise ValueError("invalid UNSELECTED CPU packed state")
        return Tensor(p.high.values, (p.high.shape[0],12,128,128))
    def step(self, before, layout, q,k,v,g,beta,ids,native,device):
        self.unpack_value_major(before, layout)
        self.calls.append({"S":before.high.shape[0],"ids":ids.tolist(),
                           "before":Protocols.packed_dict(before),"Q":q.clone()})
        if self.error is not None: raise self.error
        # A symbolic same-state arithmetic stand-in, not a native result.
        after = before.clone()
        delta = 10 if before.high.shape[0] == 1 else self.delta_for_full
        for name in m.REGIONS:
            for i in ids.values: getattr(after,name).values[i] += delta
        selected = Tensor([after.high.values[i] for i in ids.values],
                          (q.shape[0],12,128,128))
        out = Tensor([after.high.values[i] for i in ids.values],
                     (q.shape[0],12,128), "bfloat16")
        if self.corrupt_source: before.high.values[0] += 1
        if self.corrupt_local_result: after.low.dtype = "float16"
        result = {"packed":after, "native_updated_selected_fp32":selected}
        for name in m.FIELDS:
            result.setdefault(name, out.clone())
        for name in ("value_cast_exact","restored_cast_exact","native_fp32_untouched_exact"):
            result[name] = not self.bad_flags
        native(q,k,v,before,beta=beta,actual_seq_lengths=ids,ssm_state_indices=ids,g=g)
        return result

class SeamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.gate = Gate(self.temp.name)
        self.frozen = FakeFrozen()
        self.ref = types.SimpleNamespace(protocols=Protocols,torch=Torch,frozen=self.frozen,
            gate=self.gate,guard_records=[],local_equivalence_passed=False,equivalence_batches=(),
            selected_row_identity={"SYNTHETIC":True},assert_sources=lambda:None)
        def checked(native):
            def inner(*args,**kwargs):
                self.ref.guard_records.append({"SYNTHETIC_call_guard":True})
                return native(*args,**kwargs)
            return inner
        self.ref._native = checked
        self.native = lambda *a,**kw: None
        self.layout = types.SimpleNamespace(variant=0)
    def call(self, before=None, ids=(3,0)):
        return m.selected_compose(self.ref, before or packed(5), self.layout,
                                 *inputs(ids), self.native, "SYNTHETIC_not_NPU")
    def test_01_matrix_is_192_and_registered_shards_48(self):
        self.assertEqual(len(m.equivalence_plan(range(1,17))),192)
        for group in ((1,2,3,4),(5,6,7,8),(9,10,11,12),(13,14,15,16)):
            plan = m.equivalence_plan(group)
            self.assertEqual(len(plan),48)
            self.assertTrue(all(r["local_slots"] == 1 and r["local_index"] == 0 for r in plan))
            self.assertTrue(all(r["original_slot"] in (0,r["slots"]-1) for r in plan))
    def test_02_invalid_batch_matrix_rejected(self):
        for batches in ((),(0,),(17,),(1,1),(True,),(1.0,)):
            with self.subTest(batches=batches), self.assertRaises(m.Pending):
                m.equivalence_plan(batches)
    def test_03_original_mapping_and_all_other_slots_exact(self):
        before = packed(5); snapshot = before.clone()
        result = self.call(before)
        self.assertEqual(self.frozen.calls[0]["S"],1)
        self.assertEqual([x["ids"] for x in self.frozen.calls],[[0],[0]])
        self.assertEqual([x["before"]["high"].values for x in self.frozen.calls],[[3],[0]])
        self.assertEqual(result["packed"].high.values,[10,1,2,13,4])
        self.assertTrue(all(exact(getattr(before,n),getattr(snapshot,n)) for n in m.REGIONS))
        detail = result["selected_row_reference"]
        self.assertTrue(detail["original_CPU_all_other_slots_bitwise"])
        self.assertIn("empty set",detail["native_untouched_observation"])
        self.assertEqual([r["original_slot"] for r in detail["rows"]],[3,0])
    def test_04_duplicate_oob_dtype_and_device_before_dispatch(self):
        for ids in ((1,1),(0,5),(-1,0)):
            with self.subTest(ids=ids), self.assertRaises(ValueError): self.call(ids=ids)
        args = list(inputs((0,1)))
        for tensor in (Tensor([0,1],dtype="float32"),Tensor([0,1],dtype="int32",device="npu")):
            args[5] = tensor
            with self.assertRaises(ValueError):
                m.selected_compose(self.ref,packed(5),self.layout,*args,self.native,"unused")
        self.assertEqual(self.frozen.calls,[])
    def test_05_invalid_unselected_state_still_rejected(self):
        before=packed(5);before.scales.values[4]=-1
        with self.assertRaisesRegex(ValueError,"UNSELECTED"): self.call(before,ids=(0,))
        self.assertEqual(self.frozen.calls,[])
        before=packed(5);before.low.values[4]=-128
        with self.assertRaisesRegex(ValueError,"UNSELECTED"): self.call(before,ids=(0,))
        self.assertEqual(self.frozen.calls,[])
    def test_06_readonly_local_input_guard_not_removed(self):
        self.frozen.corrupt_source=True
        with self.assertRaisesRegex(AssertionError,"readonly"): self.call()
        self.assertEqual(self.gate.retained,1)
    def test_07_local_result_shape_dtype_and_cast_guard_not_removed(self):
        self.frozen.corrupt_local_result=True
        with self.assertRaisesRegex(AssertionError,"ABI"): self.call()
        self.frozen.corrupt_local_result=False;self.frozen.bad_flags=True
        with self.assertRaisesRegex(AssertionError,"cast guard"): self.call()
    def test_08_original_exception_not_replaced_by_retention(self):
        primary=RuntimeError("original dispatched failure")
        self.frozen.error=primary;self.gate.retain_error=OSError("secondary save")
        with self.assertRaises(RuntimeError) as caught: self.call()
        self.assertIs(caught.exception,primary)
        record=self.gate.fixture["selected_row_last"]
        self.assertIn("original dispatched failure",record["primary_error"]["error"])
        self.assertIn("secondary save",record["retention_error"])
        self.assertIn("original_row_before",record)
        self.assertNotIn("local_after",record)
    def test_09_equivalence_symbolic_positive_and_admission_after_save(self):
        report=m.run_equivalence(self.ref,self.native,(2,),"SYNTHETIC_not_NPU")
        self.assertEqual(report["pair_count"],12)
        self.assertTrue(all(r["guards"]["complete_FP32_state_bitwise"] for r in report["cases"]))
        self.assertEqual(len(self.gate.required),12)
        self.assertTrue(self.ref.local_equivalence_passed)
        self.assertEqual(self.ref.equivalence_batches,(2,))
        self.assertFalse(report["serving_ready"])
        self.assertFalse(report["general_sr_supported"])
        self.assertFalse(report["performance_measurement_admitted"])
        # This in-memory simulated report is never saved as actual receipt.
    def test_10_equivalence_mismatch_rejected_without_admission(self):
        self.frozen.delta_for_full=11
        with self.assertRaisesRegex(AssertionError,"selected_row_equivalence"):
            m.run_equivalence(self.ref,self.native,(2,),"SYNTHETIC_not_NPU")
        self.assertFalse(self.ref.local_equivalence_passed)
        self.assertEqual(self.ref.equivalence_batches,())
        self.assertTrue(self.gate.retained)
    def test_11_report_save_failure_does_not_arm_reference(self):
        primary=OSError("checkpoint failed"); self.gate.save_error=primary
        with self.assertRaisesRegex(OSError,"checkpoint failed"):
            m.run_equivalence(self.ref,self.native,(2,),"SYNTHETIC_not_NPU")
        self.assertFalse(self.ref.local_equivalence_passed)
        self.assertEqual(self.ref.equivalence_batches,())
        self.assertIsNot(self.gate.fixture.get("selected_row_last"),self.gate.fixture)
        self.assertIn("checkpoint failed",self.gate.fixture["primary_error"]["error"])
    def test_12_no_raw_before_overwrite_or_silent_retry(self):
        m.run_equivalence(self.ref,self.native,(1,),"SYNTHETIC_not_NPU")
        with self.assertRaisesRegex(ValueError,"never overwrite"):
            m.run_equivalence(self.ref,self.native,(1,),"SYNTHETIC_not_NPU")
        self.assertFalse(self.ref.local_equivalence_passed)
    def test_13_source_manifest_actual_bytes_and_drift(self):
        root=Path(self.temp.name); here=root/"new";here.mkdir()
        source=root/"source.py";source.write_text("# real bytes\n")
        manifest={"schema":"damp-selected-row-reference-source/v1","default_enabled":False,
            "npu_executed":False,"sources":{"source.py":m.sha(source)},"dependencies":{}}
        path=here/"SOURCE_MANIFEST.json";path.write_text(json.dumps(manifest))
        with patch.object(m,"HERE",here):
            actual=m.source_bindings(root,m.sha(path))
            self.assertEqual(actual["sources"],manifest["sources"])
            source.write_text("# different\n")
            with self.assertRaisesRegex(m.Pending,"drift"):m.source_bindings(root,m.sha(path))
    def test_14_source_manifest_escape_and_identity_rejected(self):
        root=Path(self.temp.name);here=root/"new";here.mkdir()
        path=here/"SOURCE_MANIFEST.json"
        path.write_text(json.dumps({"schema":"damp-selected-row-reference-source/v1",
            "default_enabled":False,"npu_executed":False,"sources":{"../escape":"0"*64},"dependencies":{}}))
        with patch.object(m,"HERE",here):
            with self.assertRaises(m.Pending):m.source_bindings(root,m.sha(path))
            with self.assertRaisesRegex(m.Pending,"identity"):m.source_bindings(root,"f"*64)
    def test_15_factory_default_off_no_native_import(self):
        with self.assertRaisesRegex(m.Pending,"default OFF"):
            m.build_reference(None,None,None,None,None,"/unused","unused")
    def test_16_factory_inherits_real_frozen_owner_but_remains_pending(self):
        root=HERE
        while root.name != "model-tuning-lab" and root.parent != root:root=root.parent
        if not (root/m.BASE_PATH).exists():self.fail("actual frozen base source unavailable")
        protocols=types.SimpleNamespace(__file__=str(root/
            "projects/damp-ascend/operator/production_integer_compaction_v1/tests/protocols.py"))
        with patch.object(m,"source_bindings",return_value={"SYNTHETIC":True}),\
             patch.object(m.inspect,"getsourcefile",return_value=str(root/m.FROZEN_PATH)):
            rows=m.build_reference(self.gate,protocols,self.frozen,Torch,None,root,"unused",enabled=True)
        self.assertEqual(rows.__class__.__bases__[0].__name__,"NativeRows")
        self.assertEqual(rows.__class__.__bases__[0]._rows.__module__,"_damp_selected_row_frozen_base")
        with self.assertRaisesRegex(m.Pending,"this true T"):rows.step(None,None,inputs((0,1))[0])
        rows.local_equivalence_passed=True;rows.equivalence_batches=(1,)
        with self.assertRaisesRegex(m.Pending,"this true T"):rows.step(None,None,inputs((0,1))[0])
        # Original anchor admission must ALSO stay active.
        rows.equivalence_batches=(2,)
        with self.assertRaisesRegex(ValueError,"anchors"):
            rows.step(packed(5),self.layout,*inputs((0,1)),self.native,"SYNTHETIC_not_NPU")
    def test_17_execute_cli_refuses_without_acquiring_framework(self):
        with self.assertRaisesRegex(m.Pending,"consumer/proof bridge"):
            m.main(["--repo-root","/unused","--source-manifest-sha256","unused",
                    "--batches","2","--execute"])
    def test_19_source_recheck_failure_cannot_arm_reference(self):
        calls=[]
        def drift():
            calls.append(1)
            if len(calls) == 2: raise m.Pending("source drift after actual pairs")
        self.ref.assert_sources=drift
        with self.assertRaisesRegex(m.Pending,"source drift"):
            m.run_equivalence(self.ref,self.native,(2,),"SYNTHETIC_not_NPU")
        self.assertEqual(len(calls),2)
        self.assertFalse(self.ref.local_equivalence_passed)
        self.assertEqual(self.ref.equivalence_batches,())
        self.assertNotIn("selected_row_equivalence",self.gate.report)
    def test_18_invalid_full_shape_before_dispatch(self):
        original=self.frozen.unpack_value_major
        self.frozen.unpack_value_major=lambda *a:Tensor([0],(1,1,1,1))
        with self.assertRaisesRegex(ValueError,"full CPU state ABI"):self.call()
        self.assertEqual(self.frozen.calls,[])
        self.frozen.unpack_value_major=original

if __name__ == "__main__":
    unittest.main()
