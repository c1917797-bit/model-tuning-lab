"""Read-only common observer of the ORIGINAL native GDN Python code object.

Torch is imported only inside explicit register. No recurrence/gating replacement.
Every D2H is diagnostic and deliberately identical in the three arms.
"""
from __future__ import annotations
import inspect
import marshal
import os
from pathlib import Path
import sys
import threading
from diag_contract import (LAYERS, RANK_LIMIT, RUNTIME, NATIVE_SO, NATIVE_SO_SHA,
                           canonical, file_sha, require, sha, source_contract, write_new)
from profile_logic import Supervisor, TraceFailure
from v2_contract import source_contract as v2_source_contract
from v2_bindings import off_native_bindings

def function_proof(function, path, module):
    require(inspect.isfunction(function), "native ordinary Python function required")
    require(str(Path(function.__code__.co_filename).resolve()) == path and
            str(Path(inspect.getsourcefile(function)).resolve()) == path and
            function.__module__ == module and
            function.__globals__.get("__name__") == module and
            str(Path(function.__globals__.get("__file__", "")).resolve()) == path,
            "native function code/globals/source ownership mismatch")
    require(file_sha(path) == RUNTIME[path], "actual native source bytes drift")
    return {"path": path, "sha256": RUNTIME[path], "module": module,
            "qualname": function.__qualname__, "firstlineno": function.__code__.co_firstlineno,
            "code_sha256": sha(marshal.dumps(function.__code__))}

def mapped_native():
    matches = []
    stat = Path(NATIVE_SO).stat()
    for line in Path("/proc/self/maps").read_text().splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) != 6:
            continue
        if parts[5].endswith(" (deleted)") and parts[5][:-10] == NATIVE_SO:
            raise TraceFailure("native mapped library deleted; current file hash is not mapped-byte proof")
        if parts[5] == NATIVE_SO:
            major, minor = (int(x,16) for x in parts[3].split(":"))
            require(int(parts[4]) == stat.st_ino and os.makedev(major,minor) == stat.st_dev,
                    "mapped native file device/inode mismatch")
            matches.append(line)
    require(matches and file_sha(NATIVE_SO) == NATIVE_SO_SHA, "actual native mapped SO not verified")
    return {"path": NATIVE_SO, "sha256": NATIVE_SO_SHA, "device": stat.st_dev,
            "inode": stat.st_ino, "maps": matches, "deleted": False}

class Writer:
    def __init__(self, root, rank, torch):
        self.root = Path(root)/("trace-rank-"+str(rank))
        self.root.mkdir(parents=True, exist_ok=False)
        self.raw = self.root/"raw"
        self.raw.mkdir()
        self.events = (self.root/"events.jsonl").open("x", encoding="utf-8")
        self.used, self.torch = 0, torch

    def event(self, kind, **record):
        self.events.write(canonical(dict(kind=kind, **record)).decode()+"\n")
        self.events.flush()

    def tensor(self, key, tensor, *, store=True):
        # Copy first, retain original tensor/shape/stride/pointer in the evidence.
        # No dtype conversion on NPU (notably no NPU FP64); raw CPU bytes.
        cpu = tensor.detach().cpu().contiguous()
        data = cpu.view(self.torch.uint8).numpy().tobytes()
        result = {"shape": list(tensor.shape), "stride": list(tensor.stride()),
                  "dtype": str(tensor.dtype), "device": str(tensor.device),
                  "data_ptr": tensor.data_ptr(), "storage_ptr": tensor.untyped_storage().data_ptr(),
                  "storage_offset": tensor.storage_offset(), "storage_bytes": tensor.untyped_storage().nbytes(),
                  "num_bytes": len(data), "sha256": sha(data), "raw": None}
        if store:
            require(self.used+len(data) <= RANK_LIMIT, "rank/arm raw budget exhausted; evidence incomplete")
            path = self.raw/(key+".bin")
            with path.open("xb") as out:
                out.write(data)
            self.used += len(data)
            result["raw"] = {"path": str(path), "sha256": result["sha256"], "size": len(data)}
        # Raw is retained before numerical validation/finite assertion.
        result["finite"] = bool(self.torch.isfinite(cpu).all()) if cpu.is_floating_point() else True
        return result

def register():
    require(sys.version_info[:2] == (3,12) and callable(getattr(threading,"getprofile",None)),
            "source-bound target must bePython3.12 with public threading.getprofile")
    import torch
    import torch.distributed as dist
    import torch_npu  # noqa:F401
    import vllm_ascend.ops  # noqa:F401
    import vllm_ascend.ops.gdn as gdn
    import vllm_ascend.worker.model_runner_v1 as runners
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention as Target
    from vllm.distributed import get_tensor_model_parallel_rank, get_tensor_model_parallel_world_size
    from damp_capture import patch as capture
    from damp_capture.bindings import verify_native_alias, live_bindings
    from damp_capture.contract import load_manifest
    from damp_capture.session import layer_index
    from damp_capture.text_positions import TEXT_METADATA_SOURCES, text_request, ordered_text_positions, text_axis
    packet = {"frozen_v1": source_contract(), "new_v2": v2_source_contract()}
    require(os.environ.get("DAMP_ADMISSION_ARM") in ("off-a", "off-b", "on"), "unknown diagnostic arm")
    arm = os.environ["DAMP_ADMISSION_ARM"]
    require(os.environ.get("DAMP_CAPTURE_ENABLE") == ("1" if arm == "on" else "0"),
            "arm/collector mode mismatch")
    require(os.environ.get("DAMP_ADMISSION_TRACE_ENABLE") == "1", "diagnostic default OFF")
    m = load_manifest(os.environ["DAMP_CAPTURE_MANIFEST"])
    require(m["mode"] == "smoke" and len(m["rows"]) == 1 and len(m["rows"][0]["input_ids"]) == 1024
            and m["generation"]["max_tokens"] == 33, "only C1/1024/33 diagnostic admitted")
    for path, digest in dict(RUNTIME, **TEXT_METADATA_SOURCES).items():
        require(file_sha(path) == digest, "actual image source mismatch: "+path)
    donor, Runner = gdn.AscendGatedDeltaNetAttention, runners.NPUModelRunner
    copier = sys.modules.get("vllm_ascend.patch.worker.patch_qwen3_5")
    require(copier is not None and copier._GDN_PATCH_TARGET is Target, "native receiver copier absent")
    native_core = verify_native_alias(donor, Target)
    native_forward = Runner._model_forward
    core_source = function_proof(native_core,
        "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py", "vllm_ascend.ops.gdn")
    runner_source = function_proof(native_forward,
        "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py",
        "vllm_ascend.worker.model_runner_v1")
    # Exactly once; OFF returns without changes, ON retains original frozen logic.
    capture.register()
    installed_forward, installed_core = Runner._model_forward, donor._forward_core
    require((installed_forward is native_forward and installed_core is native_core) if arm != "on"
            else (Runner._damp_original_forward is native_forward and
                  donor._damp_original_core is Target._damp_original_core is native_core and
                  donor._forward_core is Target._forward_core), "collector installation ownership changed")
    original_signature = inspect.signature(native_forward)
    class Observer:
        def __init__(self):
            self.writer = None
            self.turn = -1
            self.bound = False
            self.seen = []
            self.previous = {}
            self.pointers = {}
            self.current = None
            self.request = None

        def begin(self, runner, args, kwargs):
            require(runner.model_config.enforce_eager and not runner.speculative_config and
                    runner.pcp_size == runner.dcp_size == 1, "strict eager/no-spec/CP1")
            require(dist.is_initialized() and dist.get_world_size() == get_tensor_model_parallel_world_size() == 4,
                    "strict actual TP4")
            rank = get_tensor_model_parallel_rank()
            require(rank in range(4) and torch.npu.current_device() == rank, "rank/device mismatch")
            if self.writer is None:
                self.writer = Writer(os.environ["DAMP_CAPTURE_OUTPUT"], rank, torch)
                self.writer.event("started", rank=rank, physical=rank+4, arm=arm,
                    packet=packet, core_source=core_source, runner_source=runner_source,
                    native_library=mapped_native(),
                    recurrent_schema=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema),
                    scope="short-common-profile-not-full-calibration", performance_measurement=False)
            batch = runner.input_batch
            ids = tuple(batch.req_ids[:batch.num_reqs])
            require(len(ids) == 1 and len(runner.requests) == 1, "actual admission not exactly C1")
            require(self.request is None or ids == self.request, "request UUID changed in one arm")
            self.request = ids
            cached = runner.requests[ids[0]]
            require(list(cached.prompt_token_ids) == m["rows"][0]["input_ids"], "actual prompt IDs differ")
            text_request(len(cached.prompt_token_ids), cached.mm_features, cached.prompt_embeds,
                         cached.prompt_is_token_ids, runner.uses_mrope, cached.mrope_position_delta,
                         cached.mrope_positions.tolist() if runner.uses_mrope and self.turn < 0 else None)
            self.turn += 1
            require(self.turn < 33, "unexpected extra native model turn")
            starts = runner.gdn_query_start_loc.cpu[:2].tolist()
            computed = batch.num_computed_tokens_cpu_tensor[:1].tolist()
            n = 1024 if self.turn == 0 else 1
            require(starts == [0,n] and computed == [0 if self.turn == 0 else 1023+self.turn],
                    "native admission shape/time differs from fixed protocol")
            bound = original_signature.bind(runner,*args,**kwargs)
            positions = bound.arguments.get("positions")
            require(positions is not None, "positions unavailable")
            positions_cpu = (positions[:, :n] if runner.uses_mrope else positions[:n]).detach().cpu().tolist()
            axis = text_axis(positions_cpu, ordered_text_positions(starts,computed,n), runner.uses_mrope)
            context = gdn.get_forward_context()
            bindings = (live_bindings(context.no_compile_layers, donor, Target, installed_core)
                        if arm == "on" else
                        off_native_bindings(context.no_compile_layers, donor, Target, native_core))
            if not self.bound:
                self.writer.event("bindings", layers=bindings)
                self.bound = True
            input_ids = bound.arguments.get("input_ids")
            extra = bound.arguments.get("model_kwargs", {})
            require(all(value is None or type(value) in (str,int,float,bool) for value in extra.values()),
                    "unobserved non-scalar native model kwargs")
            require(bound.arguments.get("intermediate_tensors") is None, "pipeline intermediates unsupported")
            parameters = {"num_tokens_padded": bound.arguments["num_tokens_padded"],
                          "positions_shape": list(positions.shape), "positions": positions_cpu,
                          "text_axis": list(axis), "input_ids": None,
                          "intermediate_tensors_none": bound.arguments.get("intermediate_tensors") is None,
                          "inputs_embeds_none": bound.arguments.get("inputs_embeds") is None,
                          "model_kwargs": extra, "inputs_embeds": None}
            if input_ids is not None:
                parameters["input_ids"] = self.writer.tensor("t%03d-runner-input"%self.turn,input_ids[:n],store=True)
            embeds = bound.arguments.get("inputs_embeds")
            if embeds is not None:
                parameters["inputs_embeds"] = self.writer.tensor("t%03d-runner-embeds"%self.turn,embeds[:n])
            self.current = parameters
            self.seen = []
            self.writer.event("turn_begin", turn=self.turn, runtime_ids=list(ids), cpu_starts=starts,
                              computed=computed, parameters=parameters)

        def geometry(self,tensor):
            return {"shape": list(tensor.shape), "stride": list(tensor.stride()), "dtype": str(tensor.dtype),
                    "storage_bytes": tensor.untyped_storage().nbytes()}

        def before(self,frame):
            values = frame.f_locals
            attention = values["self"]
            require(type(attention) is Target, "native code invoked for unexpected GDN class")
            layer, prefix = layer_index(attention.prefix), attention.prefix
            require(layer in LAYERS and layer not in self.seen, "duplicate/unexpected GDN layer")
            md = gdn.get_forward_context().attn_metadata[prefix]
            nd,np,n = int(md.num_decodes),int(md.num_prefills),int(md.num_actual_tokens)
            require(md.spec_sequence_masks is None and int(md.num_decode_tokens) == nd and
                    ((nd,np,n)==(0,1,1024) if self.turn == 0 else (nd,np,n)==(1,0,1)),
                    "mixed/spec/dummy native admission differs")
            slots = (md.prefill_state_indices if np else md.non_spec_state_indices_tensor[:nd]).detach().cpu().tolist()
            require(len(slots)==1 and type(slots[0]) is int and slots[0]>=0, "one valid actual state slot required")
            slot=slots[0]
            ssm,conv = attention.kv_cache[1],attention.kv_cache[0]
            require(ssm.dtype == torch.float32 and tuple(ssm.shape[1:]) == (12,128,128)
                    and slot < ssm.shape[0] and slot < conv.shape[0], "native typed-state geometry/slot mismatch")
            p=(ssm.data_ptr(),ssm.untyped_storage().data_ptr(),conv.data_ptr(),conv.untyped_storage().data_ptr(),slot)
            require(layer not in self.pointers or self.pointers[layer] == p, "native cache pointer/slot changed")
            self.pointers[layer]=p
            initial = md.prefill_has_initial_state.detach().cpu().tolist() if np else []
            starts = md.prefill_query_start_loc.detach().cpu().tolist() if np else [0]
            actual_lengths = md.non_spec_decode_metadata.actual_seq_lengths.detach().cpu().tolist() if nd else []
            require((initial == [False] and starts == [0,1024]) if np else actual_lengths == [0,1],
                    "native initial/decode ABI differs")
            metadata = {"nd":nd,"np":np,"n":n,"prefill_initial":initial,"prefill_starts":starts,
                        "decode_actual_seq_lengths":actual_lengths}
            base="t%03d-l%02d"%(self.turn,layer)
            snapshots={}
            # Each raw entry is retained before finite assertions; no native tensor writes.
            for name in ("mixed_qkv","b","a"):
                value=values[name]
                snapshots[name]=self.writer.tensor(base+"-"+name,value[:n],store=True)
            snapshots["ssm_before"]=self.writer.tensor(base+"-ssm-before",ssm[slot],store=self.turn==0)
            prev=self.previous.get(layer)
            consistent = prev is None or snapshots["ssm_before"]["sha256"] == prev["ssm_after"]["sha256"]
            if prev is not None:
                snapshots["ssm_before"]["previous_after"] = prev["ssm_after"]["raw"]
                if not consistent:
                    snapshots["ssm_before"]=self.writer.tensor(base+"-ssm-before-diverged",ssm[slot],store=True)
            snapshots["conv_before"]=self.writer.tensor(base+"-conv-before",conv[slot],store=self.turn==0)
            if prev is not None:
                if snapshots["conv_before"]["sha256"] == prev["conv_after"]["sha256"]:
                    snapshots["conv_before"]["previous_after"] = prev["conv_after"]["raw"]
                else:
                    snapshots["conv_before"] = self.writer.tensor(base+"-conv-before-changed",conv[slot])
            record={"turn":self.turn,"layer":layer,"prefix":prefix,"slot":slot,"metadata":metadata,
                    "parameters":{"mixed_qkv":self.geometry(values["mixed_qkv"]),
                                  "b":self.geometry(values["b"]),"a":self.geometry(values["a"]),
                                  "core_attn_out":self.geometry(values["core_attn_out"])},
                    "ssm_geometry":self.geometry(ssm),"conv_geometry":self.geometry(conv),
                    "pointers":list(p),"inputs":snapshots,"ssm_previous_after_consistent":consistent,
                    "conv_previous_after_consistency_asserted":False}
            self.writer.event("core_before", **record)
            self.seen.append(layer)
            require(consistent,"true recurrent-state before differs from previous-after; retained raw")
            require(all(v["finite"] for v in snapshots.values()),"nonfinite native input/state")
            return record

        def after(self,frame,record):
            v=frame.f_locals; attention=v["self"]; layer=record["layer"]; slot=record["slot"]
            base="t%03d-l%02d"%(self.turn,layer)
            after={"ssm_after":self.writer.tensor(base+"-ssm-after",attention.kv_cache[1][slot]),
                   "conv_after":self.writer.tensor(base+"-conv-after",attention.kv_cache[0][slot]),
                   "core_output":self.writer.tensor(base+"-output",v["core_attn_out"][:record["metadata"]["n"]])}
            # Native g/beta locals are an observed seam, not a recomputed oracle.
            for name in ("g","beta"):
                require(name in v, "native success locals absent (or exceptional unwind)")
                after[name]=self.writer.tensor(base+"-"+name,v[name])
            self.writer.event("core_after",turn=self.turn,layer=layer,prefix=record["prefix"],
                slot=slot,after=after,pointers=[attention.kv_cache[1].data_ptr(),
                    attention.kv_cache[1].untyped_storage().data_ptr(),attention.kv_cache[0].data_ptr(),
                    attention.kv_cache[0].untyped_storage().data_ptr(),slot])
            self.previous[layer]=after
            require(all(x["finite"] for x in after.values()),"nonfinite native output/state")

        def finish(self):
            require(len(self.seen)==48 and set(self.seen)==set(LAYERS), "all48 native coverage missing")
            self.writer.event("turn_commit",turn=self.turn,layers=list(self.seen),native_return_preserved=True,
                              raw_bytes=self.writer.used)
            if self.turn==32:
                self.writer.event("complete",turns=33,layers=list(LAYERS),raw_bytes=self.writer.used)
            return self.turn == 32

        def native_failure(self,error,secondary):
            if self.writer:
                self.writer.event("native_failure",turn=self.turn,error=type(error).__name__,
                                  detail=str(error),secondary=list(secondary),original_exception_preserved=True)

        def secondary_failure(self,event,error):
            if self.writer:
                self.writer.event("observer_failure",turn=self.turn,event=event,
                                  error=type(error).__name__,detail=str(error))
    observer=Observer()
    supervisor=Supervisor(native_core.__code__,observer)
    supervisor.install()
    def supervised_forward(runner,*args,**kwargs):
        batch=getattr(runner,"input_batch",None)
        if batch is None or not int(getattr(batch,"num_reqs",0)):
            return installed_forward(runner,*args,**kwargs)
        observer.begin(runner,args,kwargs)
        return supervisor.invoke(installed_forward,runner,*args,**kwargs)
    require(not hasattr(Runner,"_damp_admission_supervisor"),"diagnostic installed twice")
    Runner._damp_admission_supervisor=supervisor
    Runner._model_forward=supervised_forward
