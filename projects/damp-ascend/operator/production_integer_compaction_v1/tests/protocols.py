"""Frozen fixture/arithmetic protocols with explicit new candidate injection.

Only candidate namespace injection, complete-storage nonalias, and evidence
capture seams differ from the pinned original general-SR gate. No helper from
the production quantizer is used by the independent reference feedback.
"""
import sys
import torch
from gate_contract import PROJECT, STEPS, LIMITS, validate_protocols, require, sha
validate_protocols()
sys.path.insert(0, str(PROJECT/"tests"))
from independent_oracle import (OracleLayout, ValueMajorPacked, errors, pack_value_major,
    restore_state, transform_state, unpack_value_major)
from native_compressed_golden import step as native_step
import restricted_native_golden_gate as restricted
from general_sr_native_gate import (make_layout, turn, audit_cast, tensor_digest, layout_dict,
    half_cell_evidence, ANCHOR_VARIANTS, GENERAL_VARIANTS, PREPARE_INPUT_NAMES)
from candidate_adapter import (REGIONS, exact, storage_disjoint, packed_dict, observe, snapshot)

def cpu_clone(x):
    errors_ = []
    result = snapshot(x, errors_)
    require(not errors_, "CPU copy failure")
    return result

def invoke_reference(gate, ref, inputs, selected, plans, sr, nd):
    tensors = list(inputs)+[nd(selected)]+list(plans)+[sr]
    results, cpu_results, after = observe(gate, "independent_reference", lambda: ref(*tensors), tensors)
    b = selected.shape[0]
    expected = [((b,12,128,128),torch.float32), ((b,12,128),torch.float32),
                ((b,12,128),torch.bfloat16)]
    require(isinstance(results,(tuple,list)) and len(results)==3, "reference output arity")
    from torch_npu import get_npu_format
    for actual, cpu, (shape,dtype) in zip(results,cpu_results,expected):
        require(tuple(actual.shape)==shape and actual.dtype==dtype and get_npu_format(actual)==2,
                "reference output ABI/ND")
        require(bool(torch.isfinite(cpu).all()), "reference nonfinite")
        require(all(storage_disjoint(actual,x) for x in tensors), "reference backing-storage alias")
    require(all(storage_disjoint(results[i],results[j]) for i in range(3) for j in range(i)),
            "reference output/output backing-storage alias")
    record = gate.fixture["independent_reference"]
    require(record["pointers_before"]==record["pointers_after"] and
            all(exact(x,y) for x,y in zip(record["before"],after)), "reference immutable-input guard")
    require(exact(cpu_results[1].bfloat16(),cpu_results[2]), "reference sole final BF16 cast")
    return cpu_results

def invoke_prepare_guard(gate, prepare, inputs, arena):
    require(len(inputs)==6 and len(arena)==3, "prepare6 / packed3 ABI")
    prepared, _, after = observe(gate, "candidate_prepare", lambda: prepare(*inputs), inputs+arena)
    record = gate.fixture["candidate_prepare"]
    guards = {"prepare_returns_none":prepared is None,
              "all_six_prepare_inputs_bitwise":all(exact(x,y) for x,y in zip(record["before"][:6],after[:6])),
              "all_three_packed_regions_bitwise":all(exact(x,y) for x,y in zip(record["before"][6:],after[6:])),
              "all_nine_pointers_stable":record["pointers_before"]==record["pointers_after"]}
    gate.require("eager_prepare_all_inputs_immutable",all(guards.values()),{"guards":guards})

def anchor_case(gate, native, ref, nd, torch_npu, batch, variant, steps):
    layout, original_transformed, generator = make_layout(batch, variant, "anchor")
    native_state = nd(original_transformed)
    reference_state = original_transformed.clone()  # Test-only uncompressed anchor.
    state_ptr = native_state.data_ptr()
    plans = [nd(x.int()) for x in (layout.pk, layout.pv, layout.pv.argsort(1))]
    sr, lens = nd(layout.c), nd(torch.tensor([0]+[1]*batch, dtype=torch.int32))
    static, static_cpu = plans+[sr, lens], [x.cpu().clone() for x in plans+[sr, lens]]
    static_ptrs = [x.data_ptr() for x in static]
    gate.start_case("anchor", batch, variant)
    gate.case["initial_fixture_sha256"] = tensor_digest(
        [original_transformed, layout.c, layout.pk, layout.pv])
    gate.save()
    for index in range(steps):
        q, k, v, g, beta, ids = turn(batch, batch+3, index, generator, True)
        cast_ok, reordered_v = audit_cast(v, layout)
        native_before, reference_before = native_state.cpu().clone(), reference_state.clone()
        gate.fixture = {"stage": "native_reference_anchor", "batch": batch, "variant": variant,
                        "step": index+1, "layout": layout_dict(layout), "q": q, "k": k,
                        "v": v, "g": g, "beta": beta, "indices": ids,
                        "native_before": native_before, "reference_before": reference_before}
        gate.require("anchor_scaledV_BF16_exact", cast_ok)
        inputs = [nd(x) for x in (q, k, v, g, beta)]
        input_before = [x.cpu().clone() for x in inputs]
        input_ptrs = [x.data_ptr() for x in inputs]
        # Native NK=12 is a test-only expansion enabling arbitrary per-Hv Pk.
        # Model/production ABI stays HQ=4; every value head takes source h//3.
        expanded_q = q.repeat_interleave(3, 1).gather(
            2, layout.pk.long().unsqueeze(0).expand(batch, -1, -1))
        expanded_k = k.repeat_interleave(3, 1).gather(
            2, layout.pk.long().unsqueeze(0).expand(batch, -1, -1))
        nq, nk, nv, nids = [nd(x.contiguous()) for x in
                            (expanded_q, expanded_k, reordered_v.bfloat16(), ids)]
        native_inputs = [nq, nk, nv, inputs[3], inputs[4], lens, nids]
        native_inputs_before = [x.cpu().clone() for x in native_inputs]
        native_input_ptrs = [x.data_ptr() for x in native_inputs]
        native_out, native_cpu, native_observed = observe(
            gate, "native_anchor", lambda: native(nq, nk, nv, native_state,
                beta=inputs[4], scale=128**-0.5, actual_seq_lengths=lens,
                ssm_state_indices=nids, num_accepted_tokens=None, g=inputs[3], gk=None),
            native_inputs+[native_state])
        native_after = native_observed[-1]
        gate.fixture.update(native_after=native_after, native_output_reordered=native_cpu,
                            native_inputs_after=native_observed[:-1])
        updated, output_fp32, output_bf16 = invoke_reference(
            gate, ref, inputs, reference_state.index_select(0, ids.long()).contiguous(), plans, sr, nd)
        reference_state.index_copy_(0, ids.long(), updated)
        native_after = native_state.cpu().clone()
        # FP32-before-cast native readout is unavailable. Only power2 permits
        # this exact BF16-rounding commutation anchor, checked explicitly.
        inv = layout.pv.argsort(1).long().unsqueeze(0).expand(batch, -1, -1)
        restored_native = native_out.cpu().float().gather(2, inv) * layout.c.unsqueeze(0)
        restored_exact = exact(restored_native.bfloat16().float(), restored_native)
        untouched = [s for s in range(batch+3) if s not in ids.tolist()]
        state_metric = errors(native_after, reference_state)
        output_metric = errors(restored_native.bfloat16(), output_bf16)
        guards = {
            "native_untouched_bitwise": exact(native_after[untouched], native_before[untouched]),
            "reference_untouched_bitwise": exact(reference_state[untouched], reference_before[untouched]),
            "native_storage_stable": native_state.data_ptr() == state_ptr,
            "static_inputs_bitwise": all(exact(x, y) for x, y in zip(static, static_cpu)),
            "static_input_pointers_stable": static_ptrs == [x.data_ptr() for x in static],
            "reference_turn_inputs_bitwise": all(exact(x, y) for x, y in zip(inputs, input_before)),
            "reference_turn_input_pointers_stable": input_ptrs == [x.data_ptr() for x in inputs],
            "native_turn_inputs_bitwise": all(exact(x, y) for x, y in zip(native_inputs, native_inputs_before)),
            "native_turn_input_pointers_stable": native_input_ptrs == [x.data_ptr() for x in native_inputs],
            "native_restored_cast_exact": restored_exact,
            "native_output_ABI": native_out.shape == (batch, 12, 128) and native_out.dtype == torch.bfloat16,
            "native_output_ND": torch_npu.get_npu_format(native_out) == 2,
            "native_output_nonalias": all(storage_disjoint(native_out, x) for x in native_inputs+[native_state]),
            "complete_state_bitwise": exact(native_after, reference_state),
            "original_output_bitwise": exact(restored_native.bfloat16(), output_bf16),
        }
        gate.fixture.update(native_after=native_after, reference_after=reference_state,
                            native_output_reordered=native_out, native_output_restored=restored_native,
                            reference_updated_fp32=updated, reference_original_output_fp32=output_fp32,
                            reference_original_output_bf16=output_bf16)
        gate.step({"step": index+1, "indices": ids.tolist(),
                   "passed": all(guards.values()) and state_metric["finite"] and output_metric["finite"],
                   "turn_fixture_sha256": tensor_digest([q, k, v, g, beta, ids]),
                   "complete_transformed_state": state_metric, "original_output": output_metric,
                   "guards": guards})
    gate.end_case()

def general_case(gate, candidate, ref, nd, torch_npu, batch, variant, steps):
    layout, transformed, generator = make_layout(batch, variant, "general")
    golden = pack_value_major(transformed, layout)
    arena = [nd(x) for x in (golden.high, golden.low, golden.scales)]
    plans = [nd(x.int()) for x in (layout.pk, layout.pv, layout.pv.argsort(1))]
    sr, lens = nd(layout.c), nd(torch.tensor([0]+[1]*batch, dtype=torch.int32))
    static, static_before = plans+[sr, lens], [x.cpu().clone() for x in plans+[sr, lens]]
    static_ptrs = [x.data_ptr() for x in static]
    pointers = [x.data_ptr() for x in arena]
    q0 = nd(torch.zeros(batch, 4, 128, dtype=torch.bfloat16))
    gate.start_case("general", batch, variant)
    gate.case["initial_fixture_sha256"] = tensor_digest(
        [golden.high, golden.low, golden.scales, layout.c, layout.pk, layout.pv])
    gate.save()
    gate.fixture = {"stage": "eager_prepare", "batch": batch, "variant": variant,
                    "layout": layout_dict(layout)}
    invoke_prepare_guard(gate, candidate.prepare,
                         [q0, arena[0], *plans, sr], arena)
    # No persistent FP32 candidate sidecar; drop initialization now.
    del transformed
    for index in range(steps):
        q, k, v, g, beta, ids = turn(batch, batch+3, index, generator, False)
        before = ValueMajorPacked(*[x.cpu().clone() for x in arena])
        golden_before = golden.clone()
        gate.fixture = {"stage": "general_sr_compressed_feedback", "batch": batch,
                        "variant": variant, "step": index+1, "layout": layout_dict(layout),
                        "q": q, "k": k, "v": v, "g": g, "beta": beta, "indices": ids,
                        "candidate_before": packed_dict(before), "reference_before": packed_dict(golden_before)}
        inputs, nids = [nd(x) for x in (q, k, v, g, beta)], nd(ids)
        input_before = [x.cpu().clone() for x in inputs]
        input_ptrs = [x.data_ptr() for x in inputs] + [nids.data_ptr()]
        # Reference starts ONLY from its own independently quantized feedback.
        selected = unpack_value_major(golden, layout).index_select(0, ids.long()).contiguous()
        updated, output_fp32, expected_output = invoke_reference(gate, ref, inputs, selected, plans, sr, nd)
        selected_packed = pack_value_major(updated, layout)
        boundary = half_cell_evidence(updated, selected_packed, layout)
        for name in REGIONS:
            getattr(golden, name).index_copy_(0, ids.long(), getattr(selected_packed, name))
        # CPU reference evidence is retained BEFORE candidate dispatch.
        gate.fixture.update(reference_after=packed_dict(golden), reference_updated_fp32=updated,
                            reference_original_output_fp32=output_fp32,
                            reference_original_output_bf16=expected_output, reference_pre_RINT=boundary)
        output, output_cpu, observed = observe(gate, "candidate_decode",
            lambda: candidate.decode(*inputs, *arena, *plans, sr, lens, nids),
            inputs+arena+plans+[sr, lens, nids])
        actual = ValueMajorPacked(*observed[5:8])
        gate.fixture.update(candidate_after=packed_dict(actual), candidate_output=output_cpu,
                            candidate_inputs_after=observed[:5]+[observed[-1]],
                            static_inputs_after=observed[8:13])
        untouched = [s for s in range(batch+3) if s not in ids.tolist()]
        actual_dense = restore_state(unpack_value_major(actual, layout), layout)
        expected_dense = restore_state(unpack_value_major(golden, layout), layout)
        selected_state_metric = errors(actual_dense.index_select(0, ids.long()),
                                       expected_dense.index_select(0, ids.long()))
        complete_state_metric = errors(actual_dense, expected_dense)
        output_metric = errors(output, expected_output)
        guards = {
            "candidate_untouched_bitwise": all(exact(getattr(actual, n)[untouched],
                                    getattr(before, n)[untouched]) for n in REGIONS),
            "reference_untouched_bitwise": all(exact(getattr(golden, n)[untouched],
                                    getattr(golden_before, n)[untouched]) for n in REGIONS),
            "storage_pointers_stable": pointers == [x.data_ptr() for x in arena],
            "static_inputs_bitwise": all(exact(x, y) for x, y in zip(static, static_before)),
            "static_input_pointers_stable": static_ptrs == [x.data_ptr() for x in static],
            "turn_inputs_bitwise": all(exact(x, y) for x, y in zip(inputs, input_before)),
            "turn_input_pointers_stable": input_ptrs == [x.data_ptr() for x in inputs]+[nids.data_ptr()],
            "indices_bitwise": exact(nids, ids),
            "output_ABI": output.shape == (batch, 12, 128) and output.dtype == torch.bfloat16,
            "output_ND": torch_npu.get_npu_format(output) == 2,
            "output_nonalias": all(storage_disjoint(output, x) for x in arena+inputs+static+[nids]),
            "reference_SR_general": bool((layout.c > 0).all()) and bool(torch.isfinite(layout.c).all()),
        }
        passed = (all(guards.values()) and selected_state_metric["finite"] and
                  complete_state_metric["finite"] and output_metric["finite"] and
                  selected_state_metric["max_head_relative_l2"] <= LIMITS["state"] and
                  complete_state_metric["max_head_relative_l2"] <= LIMITS["state"] and
                  output_metric["max_head_relative_l2"] <= LIMITS["output"])
        gate.fixture.update(candidate_after=packed_dict(actual), reference_after=packed_dict(golden),
                            reference_updated_fp32=updated, reference_original_output_fp32=output_fp32,
                            reference_original_output_bf16=expected_output, candidate_output=output,
                            reference_pre_RINT=boundary)
        gate.step({"step": index+1, "indices": ids.tolist(), "passed": passed,
                   "turn_fixture_sha256": tensor_digest([q, k, v, g, beta, ids]),
                   "selected_original_state": selected_state_metric,
                   "complete_original_state": complete_state_metric, "output": output_metric,
                   "guards": guards,
                   "reference_half_cell": {k: x for k, x in boundary.items() if k != "quotient_fp32"},
                   "packed_bitwise_diagnostic": {n: exact(getattr(actual, n), getattr(golden, n))
                                                for n in REGIONS}})
        # selected/update/restore tensors are temporary test diagnostics, never feedback.
        del selected, updated, actual_dense, expected_dense
    gate.end_case()

def restricted_case(gate, candidate, native, nd, torch_npu, batch, variant, steps):
    # Exact original fixture generators and native-derived compressed feedback.
    layout, golden, generator = restricted.layouts(batch, variant)
    arena = [nd(getattr(golden,n)) for n in REGIONS]
    plans = [nd(x.int()) for x in (layout.pk,layout.pv,layout.pv.argsort(1))]
    sr = nd(layout.c)
    lengths = nd(torch.tensor([0]+[1]*batch,dtype=torch.int32))
    static = plans+[sr,lengths]
    static_before = [x.cpu().clone() for x in static]
    static_ptrs = [x.data_ptr() for x in static]
    pointers = [x.data_ptr() for x in arena]
    q0 = nd(torch.zeros(batch,4,128,dtype=torch.bfloat16))
    gate.start_case("restricted",batch,("SR1_perHv_permutations","power2_perHv_permutations")[variant])
    gate.fixture = {"stage":"restricted_prepare","batch":batch,"variant":variant,
                    "layout":layout_dict(layout)}
    invoke_prepare_guard(gate,candidate.prepare,[q0,arena[0],*plans,sr],arena)
    for index in range(steps):
        q,k,v,g,beta,ids = restricted.turn(batch,batch+3,index,generator)
        before = ValueMajorPacked(*[x.cpu().clone() for x in arena])
        golden_before = golden.clone()
        gate.fixture = {"stage":"restricted_native_compressed_feedback","batch":batch,
                        "variant":variant,"step":index+1,"layout":layout_dict(layout),
                        "q":q,"k":k,"v":v,"g":g,"beta":beta,"indices":ids,
                        "candidate_before":packed_dict(before),"reference_before":packed_dict(golden_before)}
        # This helper is source-pinned and calls actual native NK12 with four
        # positional + seven keyword-only arguments. It never reads candidate.
        evidence, cpu_evidence, _ = observe(gate,"restricted_native_reference",
            lambda: native_step(golden,layout,q,k,v,g,beta,ids,native,"npu:0"),[])
        golden = evidence["packed"]
        gate.fixture.update(native_evidence={k:v for k,v in cpu_evidence.items() if k!="packed"},
                            reference_after=packed_dict(golden))
        inputs = [nd(x) for x in (q,k,v,g,beta)]
        nids = nd(ids)
        output, output_cpu, after = observe(gate,"candidate_decode",
            lambda: candidate.decode(*inputs,*arena,*plans,sr,lengths,nids),
            inputs+arena+static+[nids])
        actual = ValueMajorPacked(*after[5:8])
        gate.fixture.update(candidate_after=packed_dict(actual),candidate_output=output_cpu)
        untouched = [s for s in range(batch+3) if s not in ids.tolist()]
        actual_dense = restore_state(unpack_value_major(actual,layout),layout)
        expected_dense = restore_state(unpack_value_major(golden,layout),layout)
        metrics = {"selected_state":errors(actual_dense.index_select(0,ids.long()),
                                           expected_dense.index_select(0,ids.long())),
                   "complete_state":errors(actual_dense,expected_dense),
                   "output":errors(output_cpu,evidence["original_output_bf16"])}
        record = gate.fixture["candidate_decode"]
        guards = {
            "candidate_untouched_bitwise":all(exact(getattr(actual,n)[untouched],
                                                    getattr(before,n)[untouched]) for n in REGIONS),
            "reference_untouched_bitwise":all(exact(getattr(golden,n)[untouched],
                                                    getattr(golden_before,n)[untouched]) for n in REGIONS),
            "all_input_pointers_stable":record["pointers_before"]==record["pointers_after"],
            "immutable_inputs_bitwise":all(exact(record["before"][i],after[i])
                                          for i in list(range(5))+list(range(8,14))),
            "state_pointers_stable":pointers==[x.data_ptr() for x in arena],
            "static_inputs_bitwise":all(exact(x,y) for x,y in zip(static,static_before)),
            "static_pointers_stable":static_ptrs==[x.data_ptr() for x in static],
            "output_ABI":tuple(output.shape)==(batch,12,128) and output.dtype==torch.bfloat16,
            "output_ND":torch_npu.get_npu_format(output)==2,
            "output_nonalias":all(storage_disjoint(output,x) for x in inputs+arena+static+[nids]),
            "native_scaledV_BF16_exact":evidence["value_cast_exact"],
            "native_restore_BF16_exact":evidence["restored_cast_exact"],
        }
        passed = all(guards.values()) and all(x["finite"] for x in metrics.values()) and (
            metrics["selected_state"]["max_head_relative_l2"]<=LIMITS["state"] and
            metrics["complete_state"]["max_head_relative_l2"]<=LIMITS["state"] and
            metrics["output"]["max_head_relative_l2"]<=LIMITS["output"])
        gate.step({"step":index+1,"indices":ids.tolist(),"passed":passed,"metrics":metrics,
                   "guards":guards,"turn_fixture_sha256":tensor_digest([q,k,v,g,beta,ids]),
                   "packed_bitwise_diagnostic":{n:exact(getattr(actual,n),getattr(golden,n)) for n in REGIONS}})
    gate.end_case()
