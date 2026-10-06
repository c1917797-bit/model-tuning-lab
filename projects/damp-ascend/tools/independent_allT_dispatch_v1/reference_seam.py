"""Restricted native row-composition ONLY; no candidate math or source rewrite."""
import types

def guard_batch(batch, anchored):
    if type(batch) is not int or not 1 <= batch <= 16:
        raise ValueError("true T1..16, never PAD16")
    if not anchored:
        raise ValueError("actual B16 whole-vs16xB1 native anchors are pending")

def compose_rows(before, batch, call_one, join):
    """Independent own feedback; per-row inputs never come from the candidate."""
    working = before.clone()
    rows = []
    for row in range(batch):
        evidence = call_one(row, working)
        working = evidence["packed"]
        rows.append(evidence)
    return join(working, rows)

def clone_graph_case(graph, protocols, rows, registry, metadata_cases, storage_disjoint):
    """Same frozen code objects, NEW private dependency globals; no old mutation."""
    namespace = dict(vars(graph))
    namespace.update(observe=registry.observe, storage_disjoint=storage_disjoint,
                     metadata_cases=metadata_cases, native_step=rows.step)
    pglobals = dict(vars(protocols))
    pglobals.update(observe=registry.observe, storage_disjoint=storage_disjoint)
    original = protocols.invoke_prepare_guard
    namespace["invoke_prepare_guard"] = types.FunctionType(
        original.__code__, pglobals, original.__name__, original.__defaults__, original.__closure__)
    for name, value in vars(graph).items():
        if isinstance(value, types.FunctionType) and value.__module__ == graph.__name__:
            namespace[name] = types.FunctionType(value.__code__, namespace, value.__name__,
                                                  value.__defaults__, value.__closure__)
    return namespace["graph_case"]

class NativeRows:
    """Actual native B1 composition, admitted by actual B16 native anchors."""
    def __init__(self, gate, protocols, frozen_native, torch, torch_npu):
        self.gate, self.protocols, self.frozen = gate, protocols, frozen_native
        self.torch, self.torch_npu = torch, torch_npu
        self.anchored = False
        self.calls = 0
        self.anchor_records = []
        self.guard_records = []
        gate.report["native_row_reference"] = {
            "schema": "damp-restricted-native-row-composition/v1",
            "anchors_passed": False, "anchors": self.anchor_records,
            "actual_native_calls": 0, "true_T_reference": "B1 own-state composition",
            "general_sr": False, "calibrated_plan_count": 0,
            "scope": "test-only independent restricted oracle, never production cache"}

    def _native(self, native):
        def checked(*args, **kwargs):
            inputs = list(args) + [kwargs[n] for n in
                ("beta", "actual_seq_lengths", "ssm_state_indices", "g")]
            label = "native_row_call_%d" % self.calls
            self.calls += 1
            self.gate.report["native_row_reference"]["actual_native_calls"] = self.calls
            out, cpu, after = self.protocols.observe(
                self.gate, label, lambda: native(*args, **kwargs), inputs)
            raw = self.gate.fixture[label]
            t = args[0].shape[0]
            guards = {
                "input_pointers_stable": raw["pointers_before"] == raw["pointers_after"],
                "readonly_inputs_exact": all(self.protocols.exact(raw["before"][i], after[i])
                                               for i in range(len(inputs)) if i != 3),
                "output_ABI": tuple(out.shape) == (t,12,128) and out.dtype == self.torch.bfloat16,
                "output_ND": self.torch_npu.get_npu_format(out) == 2,
                "output_finite": bool(self.torch.isfinite(cpu).all()),
                "output_nonalias": all(self.protocols.storage_disjoint(out, x) for x in inputs),
                "state_finite": bool(self.torch.isfinite(after[3]).all())}
            self.guard_records.append(guards)
            self.gate.fixture["native_row_last_guards"] = guards
            if not all(guards.values()):
                raise AssertionError("actual independent native input/output guard")
            return out
        return checked

    def _rows(self, before, layout, q, k, v, g, beta, ids, native, device):
        torch = self.torch
        def one(row, working):
            return self.frozen.step(working, layout, q[row:row+1], k[row:row+1],
                v[row:row+1], g[row:row+1], beta[row:row+1], ids[row:row+1],
                self._native(native), device)
        def join(packed, records):
            result = {"packed": packed}
            for name in ("original_output_bf16", "native_output_reordered_bf16",
                         "restored_fp32_after_native_bf16_cast", "native_updated_selected_fp32",
                         "transformed_value_bf16"):
                result[name] = torch.cat([r[name] for r in records], dim=0)
            for name in ("value_cast_exact", "restored_cast_exact", "native_fp32_untouched_exact"):
                result[name] = all(r[name] is True for r in records)
            result["scope"] = "anchored true-T rowwise restricted native own-feedback only"
            return result
        return compose_rows(before, q.shape[0], one, join)

    def step(self, before, layout, q, k, v, g, beta, ids, native, device):
        guard_batch(q.shape[0], self.anchored)
        self.guard_records = [] # Bounded to this step; durable summaries stay in gate report.
        if q.shape[0] in (1,16):
            return self.frozen.step(before,layout,q,k,v,g,beta,ids,self._native(native),device)
        if ids.unique().numel() != q.shape[0]:
            raise ValueError("true-T slot IDs must be unique before row composition")
        return self._rows(before,layout,q,k,v,g,beta,ids,native,device)

    def anchor(self, native):
        """Six actual B16 changing-feedback whole-vs16xB1 anchors, no resync."""
        torch, p, gate = self.torch, self.protocols, self.gate
        for variant in (0,1):
            layout, initial, generator = p.restricted.layouts(16,variant)
            whole, split = initial.clone(), initial.clone()
            for index in (0,7,159):
                fixture = p.restricted.turn(16,19,index,generator)
                q,k,v,g,beta,ids = fixture
                whole_before, split_before = whole.clone(), split.clone()
                gate.fixture = {"stage":"actual_native_B16_split_anchor","variant":variant,
                    "index":index,"layout":p.layout_dict(layout),
                    "whole_before":p.packed_dict(whole_before),
                    "split_before":p.packed_dict(split_before),
                    "fixture_cpu":[x.clone() for x in fixture]}
                path = gate.out/("native-split-anchor-before-%d-%d.pt"%(variant,index))
                if path.exists(): raise ValueError("never overwrite anchor raw-before")
                torch.save(gate.fixture,path)
                from independent_contract import sha
                before_ref = {"path":str(path),"sha256":sha(path)}
                gate.report.setdefault("native_anchor_raw_before",[]).append(before_ref);gate.save()
                self.guard_records = []
                a = self.frozen.step(whole,layout,q,k,v,g,beta,ids,self._native(native),"npu:0")
                b = self._rows(split,layout,q,k,v,g,beta,ids,native,"npu:0")
                full_a = p.unpack_value_major(whole_before,layout)
                full_b = p.unpack_value_major(split_before,layout)
                full_a.index_copy_(0,ids.long(),a["native_updated_selected_fp32"])
                full_b.index_copy_(0,ids.long(),b["native_updated_selected_fp32"])
                guards = {
                    "complete_FP32_state_bitwise":p.exact(full_a,full_b),
                    "selected_FP32_state_bitwise":p.exact(a["native_updated_selected_fp32"],b["native_updated_selected_fp32"]),
                    "original_BF16_output_bitwise":p.exact(a["original_output_bf16"],b["original_output_bf16"]),
                    "complete_packed_bitwise":all(p.exact(getattr(a["packed"],n),getattr(b["packed"],n))
                                                    for n in p.REGIONS),
                    "native_every_call_guards":len(self.guard_records)==17 and all(
                        all(r.values()) for r in self.guard_records),
                    "native_untouched_bitwise":a["native_fp32_untouched_exact"] is True and b["native_fp32_untouched_exact"] is True}
                gate.fixture.update(whole_after=p.packed_dict(a["packed"]),
                    split_after=p.packed_dict(b["packed"]),native_whole=a,native_split=b,
                    complete_FP32_whole=full_a,complete_FP32_split=full_b,guards=guards)
                record = {"variant":variant,"index":index,"batch":16,"whole_native_calls":1,
                    "split_native_calls":16,"passed":all(guards.values()),"guards":guards,
                    "raw_before":before_ref,
                    "complete_packed_sha256":p.tensor_digest(
                        [getattr(a["packed"],n) for n in p.REGIONS]),
                    "output_sha256":p.tensor_digest([a["original_output_bf16"]])}
                self.anchor_records.append(record)
                gate.require("actual_native_split_anchor_%d_%d"%(variant,index),record["passed"],record)
                whole, split = a["packed"], b["packed"]  # Each OWN feedback; never resynchronize.
        if len(self.anchor_records)!=6 or not all(r["passed"] for r in self.anchor_records):
            raise AssertionError("six actual anchors incomplete")
        self.anchored = True
        gate.report["native_row_reference"]["anchors_passed"] = True
        gate.save()
