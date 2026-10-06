"""Explicit new-namespace adapter and lossless/nullable evidence utilities."""
import json
import dataclasses
import math
from pathlib import Path
import traceback
import torch
from gate_contract import NAMESPACE, require, sha

REGIONS = ("high", "low", "scales")

def safe_json(value):
    if isinstance(value, dict): return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [safe_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value): return {"nonfinite": repr(value)}
    return value

def snapshot(value, copy_errors, where="root"):
    if isinstance(value, torch.Tensor):
        try: return value.detach().cpu().contiguous().clone()
        except BaseException as error:
            copy_errors.append({"path": where, "error": repr(error)})
            return None
    if dataclasses.is_dataclass(value):
        return {x.name: snapshot(getattr(value,x.name), copy_errors, where+"."+x.name)
                for x in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {k: snapshot(v, copy_errors, where+"."+str(k)) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [snapshot(v, copy_errors, where+"["+str(i)+"]") for i, v in enumerate(value)]
    return value

def exact(a, b):
    if not isinstance(a, torch.Tensor) or not isinstance(b, torch.Tensor): return False
    a, b = a.detach().cpu().contiguous(), b.detach().cpu().contiguous()
    return a.shape == b.shape and a.dtype == b.dtype and torch.equal(a.view(torch.uint8), b.view(torch.uint8))

def storage_disjoint(a, b):
    # Complete backing storage, not merely the contiguous view's data span.
    sa, sb = a.untyped_storage(), b.untyped_storage()
    ab, bb = sa.data_ptr(), sb.data_ptr()
    return ab+sa.nbytes() <= bb or bb+sb.nbytes() <= ab

def packed_dict(packed):
    return {n: getattr(packed, n).detach().cpu().clone() for n in REGIONS}

def loaded_libraries():
    paths = set()
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split()
        if fields and fields[-1].startswith("/") and ".so" in fields[-1] and Path(fields[-1]).is_file():
            paths.add(str(Path(fields[-1]).resolve()))
    return {p: sha(p) for p in sorted(paths)}

def observe(gate, label, dispatch, tensors):
    """Always preserve the original exception separately from nullable D2H."""
    before_errors = []
    before = snapshot(tensors, before_errors, label+".before")
    require(not before_errors, "before snapshot failed; do not dispatch")
    pointers = [t.data_ptr() for t in tensors]
    gate.fixture[label] = {"before": before, "pointers_before": pointers}
    returns = None
    dispatch_error = None
    try:
        returns = dispatch()
        torch.npu.synchronize()
    except BaseException as error:
        dispatch_error = {"error": repr(error), "traceback": traceback.format_exc()}
    output_errors, input_errors = [], []
    cpu_returns = snapshot(returns, output_errors, label+".returns")
    after = snapshot(tensors, input_errors, label+".after")
    record = {"before": before, "returns": cpu_returns, "after": after,
              "pointers_before": pointers, "pointers_after": [t.data_ptr() for t in tensors],
              "dispatch_error": dispatch_error, "output_copy_errors": output_errors,
              "input_copy_errors": input_errors}
    gate.fixture[label] = record  # CPU before/expected survives poisoned context.
    if dispatch_error or output_errors or input_errors:
        gate.retain()
        raise RuntimeError(label+" dispatch/copy failure; original error and nullable copies retained")
    return returns, cpu_returns, after

class Candidate:
    def __init__(self):
        self.ops = getattr(torch.ops, NAMESPACE)  # Never replace/assign old torch.ops.
    def prepare(self, *args): return self.ops.prepare(*args)
    def decode(self, *args): return self.ops.decode(*args)
    def schemas(self):
        ds, ps = self.ops.decode.default._schema, self.ops.prepare.default._schema
        decode_names = ["query", "key", "value", "g", "beta", "high_state", "low_state",
                        "low_scale", "pk", "pv", "inv_pv", "sr", "actual_seq_lengths", "state_indices"]
        prepare_names = ["query", "high_state", "pk", "pv", "inv_pv", "sr"]
        require([x.name for x in ds.arguments] == decode_names and
                [x.name for x in ps.arguments] == prepare_names, "new schema argument names/order")
        require([i for i, x in enumerate(ds.arguments) if x.alias_info and x.alias_info.is_write] ==
                [5, 6, 7], "only three typed states may mutate")
        require(len(ds.returns) == 1 and not ds.returns[0].alias_info and
                not ps.returns and not any(x.alias_info for x in ps.arguments),
                "fresh output / immutable void prepare schema")
        return {"namespace": NAMESPACE, "prepare": str(ps), "decode": str(ds)}

    def meta_gate(self):
        positive, negative = [], []
        def make(batch):
            slots = batch+3
            spec = [((batch,4,128),torch.bfloat16), ((batch,4,128),torch.bfloat16),
                    ((batch,12,128),torch.bfloat16), ((batch,12),torch.float32),
                    ((batch,12),torch.bfloat16), ((slots,12,128,16),torch.float16),
                    ((slots,12,128,112),torch.int8), ((slots,12,4,112),torch.float32),
                    ((12,128),torch.int32), ((12,128),torch.int32), ((12,128),torch.int32),
                    ((12,128),torch.float32), ((batch+1,),torch.int32), ((batch,),torch.int32)]
            return [torch.empty(shape,dtype=dtype,device="meta") for shape,dtype in spec]
        def prep(args): return [args[i] for i in (0,5,8,9,10,11)]
        for batch in (1,16):
            args = make(batch)
            require(self.prepare(*prep(args)) is None, "Meta prepare must be void")
            out = self.decode(*args)
            require(out.shape == (batch,12,128) and out.dtype == torch.bfloat16 and
                    out.device.type == "meta" and all(out is not x for x in args),
                    "Meta B1/B16 output contract")
            positive.append({"batch":batch, "prepare":True, "decode":True})
        # Only checks explicitly implemented by register.cpp. Value, format,
        # pointer, CPU plan, slot and graph admission require real NPU gates.
        specifications = [
            ("query_B2",0,(2,4,128),torch.bfloat16),
            ("query_dtype",0,(1,4,128),torch.float16),
            ("key_dtype",1,(1,4,128),torch.float16),
            ("value_shape",2,(1,12,127),torch.bfloat16),
            ("g_dtype",3,(1,12),torch.bfloat16),
            ("beta_dtype",4,(1,12),torch.float32),
            ("hi_shape",5,(4,12,128,15),torch.float16),
            ("hi_dtype",5,(4,12,128,16),torch.float32),
            ("lo_dtype",6,(4,12,128,112),torch.uint8),
            ("scale_shape",7,(4,12,3,112),torch.float32),
            ("lengths_dtype",12,(2,),torch.int64),
            ("indices_shape",13,(2,),torch.int32)]
        for i in (8,9,10,11):
            specifications.append(("plan_dtype_"+str(i),i,(12,128),
                                   torch.int64 if i!=11 else torch.float16))
            specifications.append(("plan_shape_"+str(i),i,(12,127),
                                   torch.int32 if i!=11 else torch.float32))
        for label,index,shape,dtype in specifications:
            args = make(1)
            args[index] = torch.empty(shape,dtype=dtype,device="meta")
            methods = ("decode","prepare") if index in (0,5,8,9,10,11) else ("decode",)
            for method in methods:
                try: getattr(self,method)(*(prep(args) if method=="prepare" else args))
                except RuntimeError:
                    negative.append({"case":label, "method":method}); continue
                raise AssertionError("Meta unexpectedly admitted "+label+"/"+method)
        for index in (0,5,8,9,10,11):
            args = make(1)
            doubled = list(args[index].shape); doubled[-1]*=2
            args[index] = torch.empty(doubled,dtype=args[index].dtype,device="meta")[...,::2]
            for method in ("prepare","decode"):
                try: getattr(self,method)(*(prep(args) if method=="prepare" else args))
                except RuntimeError:
                    negative.append({"case":"noncontiguous_"+str(index), "method":method}); continue
                raise AssertionError("Meta unexpectedly admitted noncontiguous")
        return {"passed":True, "positive_calls":len(positive)*2, "negative_calls":len(negative),
                "positives":positive, "negatives":negative,
                "scope":"schema/shape/dtype/layout only; no physical ND/value/graph/NPU proof"}

class Gate:
    def __init__(self, out, report):
        self.out, self.report = out, report
        self.fixture, self.case = {}, None
    def save(self):
        (self.out/"report.json").write_text(json.dumps(safe_json(self.report),indent=2,allow_nan=False)+"\n")
    def retain(self):
        target = self.out/"first_failure.pt"
        if target.exists(): return
        errors = []
        data = snapshot(self.fixture, errors)
        try:
            torch.save({"fixture":data, "snapshot_copy_errors":errors},target)
            self.report["first_failure"] = {"path":str(target), "sha256":sha(target),
                                            "copy_errors":errors}
        except BaseException as error:
            self.report["failure_save_error"] = repr(error)
    def require(self, name, passed, details=None):
        self.report["checks"].append({"name":name, "passed":bool(passed), "details":details})
        self.save()
        if not passed: raise AssertionError(name)
    def start_case(self, stage, batch, variant):
        names = {"anchor":("SR1_identity_plans","SR1_perHv_permutations","power2_perHv_permutations"),
                 "general":("general_positive_FP32_random","general_positive_FP32_near_half_stress")}
        if stage in names and type(variant) is int: variant = names[stage][variant]
        self.case = {"stage":stage,"batch":batch,"variant":variant,"status":"running","steps":[]}
        self.report["cases"].append(self.case); self.save()
    def step(self, record):
        self.case["steps"].append(record); self.save()
        if not record["passed"]: raise AssertionError("numerical/guard failure; no retry or threshold change")
    def end_case(self):
        self.case["status"] = "passed"; self.save()
