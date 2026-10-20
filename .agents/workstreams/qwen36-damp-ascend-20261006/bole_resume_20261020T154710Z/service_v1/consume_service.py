"""Independent CPU consumer for the bounded C1 continuous-service experiment.

This reader retains the original component bounds.  It does not infer a native
AR comparison, whole-model numerical qualification, task accuracy, or speedup.
"""
import argparse
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
import sourceio as C
import independent_model as I
import oracle112
import consume_model as CM

SCOPE = dict(schema="bole.c1-service-prefix-experiment/v1", prefix=131,
             max_steps=3, max_output_tokens=4)
DECISION_COLUMNS = ["scheduled_nodes", "target_next0", "target_next1",
                    "target_next2", "terminal", "emitted_count", "emitted0",
                    "emitted1", "remaining_output_tokens"]
LAYERS = [(i, "fa" if i % 4 == 3 else "gdn") for i in range(64)]
GDN_LAYERS = [i for i, kind in LAYERS if kind == "gdn"]
FA_LAYERS = [i for i, kind in LAYERS if kind == "fa"]


def equal(t, a, b, why):
    C.need(I.bits(t, a, b), why)


def by_layer(rows, expected):
    C.need(len(rows) == len(expected)
           and {x["layer"] for x in rows} == set(expected),
           "complete unique actual layer anchors")
    return {x["layer"]: x for x in rows}


def validate_source(sr):
    m = C.obj(sr)
    C.need(m["schema"] == "bole.actual-model-three-node-entry/source-prep-v1"
           and m["root"] == str(P) and m["prepared_only"] is False
           and m["whole_numerical_qualification"] is False
           and m["service_experiment"] == SCOPE,
           "exact source-bound bounded service experiment")
    C.need(C.ref(__file__) == m["files"]["consume_service.py"],
           "exact independent service reader source")
    for reference in m["files"].values():
        C.checked(reference)
    for reference in m["runtime_sources"].values():
        C.checked(reference)
    for module in (C, I, oracle112, CM):
        name = Path(module.__file__).name
        C.need(C.ref(module.__file__) == m["files"][name],
               "exact independent helper source " + name)
    return m


def tp_logits(t, records, policy):
    C.need(len(records) == 4 and policy["lmhead_tp"] is False
           and type(policy["reduce_sample"]) is bool
           and type(policy["vocab_size"]) is int and policy["vocab_size"] > 1,
           "actual TP4 vocabulary policy")
    local = [x["local"] for x in records]
    C.need(all(x.ndim == 2 and x.shape == local[0].shape and x.shape[1] >= 2
               and x.dtype == local[0].dtype
               and x.dtype in (t.bfloat16, t.float32)
               and bool(t.isfinite(x).all()) for x in local),
           "original finite TP logits before promotion/sanitization")
    promoted = []
    for x in local:
        y = x.float()
        if x.dtype == t.bfloat16:
            equal(t, y.to(t.bfloat16), x,
                  "exact BF16 vocabulary promotion roundtrip")
        promoted.append(y)
    assembled = (t.cat(promoted, dim=-1)[:, :policy["vocab_size"]]
                 if policy["reduce_sample"] else promoted[0])
    C.need(assembled.shape == (local[0].shape[0], policy["vocab_size"]),
           "complete actual vocabulary")
    for i, record in enumerate(records):
        if not policy["reduce_sample"]:
            equal(t, promoted[i], assembled,
                  "all4 ordinary full vocabulary replicas")
        equal(t, record["global"], assembled,
              "independent actual rank-major vocabulary assembly")
    return assembled


def fa_math(t, m, row, anchor, length):
    q = row["query"].reshape(3, 6, 256)
    k = row["key"].reshape(3, 1, 256)
    v = row["value"].reshape(3, 1, 256)
    C.need(q.dtype == k.dtype == v.dtype == row["output"].dtype == t.bfloat16,
           "unchanged actual FA BF16 ABI")
    table = list(anchor["physical_pages"])
    C.need(len(table) == 2 and len(set(table)) == 2,
           "owned two physical pages")
    pk = t.stack([anchor["key"][p // 128, p % 128, 0]
                  for p in range(length)])
    pv = t.stack([anchor["value"][p // 128, p % 128, 0]
                  for p in range(length)])
    result = {}
    for name, dtype in (("double", t.float64), ("float", t.float32)):
        values = []
        for node, path in enumerate(((0,), (0, 1), (0, 2))):
            keys = t.cat((pk, t.stack([k[j, 0] for j in path]))).to(dtype)
            vals = t.cat((pv, t.stack([v[j, 0] for j in path]))).to(dtype)
            heads = []
            for h in range(6):
                scores = keys.mv(q[node, h].to(dtype)) * (256 ** -.5)
                prob = (scores - scores.max()).exp()
                prob /= prob.sum()
                heads.append(vals.T.mv(prob))
            values.append(t.stack(heads))
        truth = t.stack(values)
        actual = row["output"]
        C.need(actual.shape == truth.shape, "actual three-row FA output")
        error = (actual.double() - truth.double()).abs()
        result[name] = dict(
            pointwise_pass=bool(t.isfinite(actual).all()
                                and (error <= .001 + .01 * truth.double().abs()).all()),
            peak_abs=float(error.max()))
    boundary = row["trial"]["fp16_boundary"]
    C.need(boundary["source"] == m["files"]["service_fia.py"]
           and boundary["completed"] is True
           and boundary["prefix_length"] == length
           and boundary["input_dtype"] == "torch.float16"
           and boundary["output_dtype"] == "torch.bfloat16",
           "actual source/prefix-bound FP16 FIA receipt")
    for key in ("query", "key", "value"):
        original = row["trial"]["native_before"][key]
        converted = original.to(t.float16)
        C.need(bool(t.isfinite(original).all() and t.isfinite(converted).all()),
               "finite actual service conversion")
        delta = (converted.double() - original.double()).abs()
        C.need(boundary["cast"][key] == dict(
            changed=int((delta != 0).sum()), elements=delta.numel(),
            peak_abs=float(delta.max())), "independent exact conversion ledger")
    return result


def fa_owner(before,after,row,owner):
    proof=before['ownership']
    C.need(proof==after['ownership']and proof['schema']=='bole.service-live-FA-owner/v1'
           and proof['request']==owner['request']and proof['logical_owner_slot']==owner['slot']==0,
           'same actual live FA request, storage, table and geometry before/after native handoff')
    ratio=proof['blocks_per_phys_block']
    C.need(type(ratio)is int and ratio>0 and proof['kernel_block_size']==128
           and proof['physical_block_size']==ratio*128 and type(proof['use_hybrid_blocks'])is bool
           and proof['pcp_world_size']==proof['dcp_world_size']==1,
           'actual native FA physical/kernel page geometry')
    physical=proof['request_physical_blocks']
    C.need(physical and all(type(p)is int and p>=0 for p in physical),
           'actual native request physical block IDs')
    expanded=[p*ratio+j for p in physical for j in range(ratio)]if proof['use_hybrid_blocks']else list(physical)
    pages=(owner['length']+2+127)//128
    C.need(list(proof['CPU_table'])==expanded and len(set(expanded))==len(expanded)
           and list(before['physical_pages'])==list(after['physical_pages'])==expanded[:pages]
           and len(before['physical_pages'])==pages
           and proof['cache_identities']==row['actual_cache_identities'],
           'independent complete native physical-to-kernel expansion and actual selected cache aliases')
    return True


def conv_math(t, row, anchor):
    initial = anchor["full_conv_slot"][0, :3]
    equal(t, row["conv_trial"]["initial"][0], initial,
          "actual current wide-cache leading3 tail")
    C.need(row["conv_bias_is_none"] is True,
           "actual original conv has no omitted bias")
    x = row["raw_projected"]
    w = row["weight"].double()
    values, tails = [], []
    for path in ((0,), (0, 1), (0, 2)):
        history = t.cat((initial, t.stack([x[n] for n in path])), dim=0)
        value = (history[-4:].double() * w.T).sum(0)
        if row["activation"]:
            value = value / (1 + (-value).exp())
        values.append(value)
        tails.append(history[-3:])
    truth = t.stack(values)
    tails = t.stack(tails)
    actual = row["actual_convolved"]
    C.need(actual.dtype == t.bfloat16 and actual.shape == truth.shape,
           "unchanged conv output ABI")
    error = (actual.double() - truth).abs()
    equal(t, row["actual_conv_tail"], tails,
          "all3 actual convolution tails bitwise")
    return dict(output_bound_pass=bool(
        t.isfinite(actual).all() and (error <= .001 + .01 * truth.abs()).all()),
        state_bitwise=True, peak_abs=float(error.max()))


def decide(t, step, target):
    n, remaining = step["scheduled_nodes"], step["remaining_output"]
    tokens = tuple(step["tokens"])
    C.need(type(n) is int and 1 <= n <= 3 and target.shape[0] == n
           and type(remaining) is int and 1 <= remaining <= 3,
           "actual admitted rows and remaining output budget")
    C.need(len(tokens) == 3 and tokens[1] != tokens[2]
           and all(type(x) is int and x >= 0 for x in tokens),
           "genuine root and distinct candidates")
    nxt = tuple(int(x) for x in target.argmax(-1).tolist())
    terminal = 0
    if remaining > 1:
        for child in range(1, n):
            if nxt[0] == tokens[child]:
                terminal = child
                break
    path = (0,) if terminal == 0 else (0, terminal)
    emitted = tuple(tokens[i] for i in path[1:]) + (nxt[terminal],)
    C.need(len(emitted) <= remaining, "no engine-side token trimming")
    return path, emitted, nxt


def tp_owner_agreement(t, record, owner, tokens, terminal, phase, rank):
    digest = hashlib.sha256(owner["request"].encode()).digest()
    hashes = [int.from_bytes(digest[i:i + 8], "big", signed=True)
              for i in range(0, 32, 8)]
    values = [*hashes, owner["generation"], owner["slot"], owner["length"],
              owner["version"], *tokens, terminal, phase, 48, 16]
    C.need(record["rank"] == rank and record["phase"] == phase
           and record["scheduler_committed"] is False
           and record["rows"].dtype == t.int64
           and record["rows"].tolist() == [values] * 4,
           "actual source/request/tree/selected-path TP4 agreement")


def consume_step(t, m, raw, step, ordinal, stream, previous):
    rank = raw["rank"]
    owner = step["owner"]
    length, n, tokens = owner["length"], step["scheduled_nodes"], tuple(step["tokens"])
    C.need(owner == dict(request=raw["request"]["request"], generation=1,
                         slot=0, length=131 + len(stream) - 1, version=ordinal)
           and 131 <= length <= 135, "actual monotonic service owner")
    C.need(step["request_output_tokens_before"] == stream
           and step["remaining_output"] == 4 - len(stream),
           "real output history/budget before bookkeeping")
    C.need(step["native_schedule"] == dict(
        req_ids=[owner["request"]], request_id=owner["request"],
        computed_tokens=length, num_tokens_without_spec=length + 1,
        scheduled_num_tokens=n, scheduled_spec_tokens=list(tokens[1:n]),
        CPU_input_token_ids=list(tokens[:n]), request_output_tokens=stream),
        "actual next native scheduled CPU counter/root/input join")
    path, emitted, nxt = decide(t, step, step["target_logits"])
    terminal = path[-1]
    staged, publication = step["staged"], step["publication"]
    C.need(staged["decision"] == dict(
        request_id=owner["request"], generation=1, slot=0, root=0,
        terminal=terminal, processed_nodes=list(path),
        accepted_draft_nodes=list(path[1:]), emitted_tokens=list(emitted),
        bonus_token=emitted[-1], cancelled=False),
        "independent complete actual greedy Decision")
    C.need(staged["owner"] == owner and staged["processed_nodes"] == list(path)
           and staged["next_length"] == length + len(path)
           and staged["next_version"] == ordinal + 1
           and staged["published"] is False,
           "unpublished source-bound staged plan")
    C.need(publication["owner"] == owner
           and publication["processed_nodes"] == list(path)
           and publication["emitted_tokens"] == list(emitted)
           and publication["next_length"] == length + len(path)
           and publication["next_version"] == ordinal + 1
           and publication["cache_published"] is True
           and publication["scheduled_nodes"] == n
           and tuple(publication["target_next"]) == nxt
           and publication["remaining_output_tokens"] == step["remaining_output"],
           "actual permanent selected cache publication")
    for phase, key in ((1, "before_agreement"), (2, "applied_agreement")):
        tp_owner_agreement(t, publication[key], owner, tokens, terminal, phase, rank)
    agreement = publication["decision_agreement"]
    values = [n, *(list(nxt) + [-1] * (3 - n)), terminal, len(emitted),
              *(list(emitted) + [-1] * (2 - len(emitted))), step["remaining_output"]]
    C.need(agreement["schema"] == "bole.service-TP4-output-decision/v1"
           and agreement["rank"] == rank
           and list(agreement["columns"]) == DECISION_COLUMNS
           and agreement["rows"].dtype == t.int64
           and agreement["rows"].tolist() == [values] * 4,
           "actual all4 admitted rows/bonus/outputbudget decision consensus")
    tree = step["tree_context"]
    C.need(tree["owner"] == owner and tree["tokens"] == list(tokens)
           and tree["positions"] == [length, length + 1, length + 1]
           and [tuple(x) for x in tree["order"]] == LAYERS
           and set(tree["captures"]) == set(range(64)),
           "actual ordered all64 service tree traversal")
    before_g = by_layer(step["before_GDN"], GDN_LAYERS)
    after_g = by_layer(step["after_GDN"], GDN_LAYERS)
    before_f = by_layer(step["before_FA"], FA_LAYERS)
    after_f = by_layer(step["after_FA"], FA_LAYERS)
    if previous is not None:
        prev_g = by_layer(previous["after_GDN"], GDN_LAYERS)
        prev_f = by_layer(previous["after_FA"], FA_LAYERS)
        for i in GDN_LAYERS:
            for key in ("native_state", "full_conv_slot"):
                equal(t, before_g[i][key], prev_g[i][key],
                      "next true GDN preimage equals previous permanent postimage")
            C.need(before_g[i]["slot_binding_identity"] == prev_g[i]["slot_binding_identity"],
                   "same current native GDN allocation across frames")
        for i in FA_LAYERS:
            C.need(before_f[i]["physical_pages"] == prev_f[i]["physical_pages"],
                   "same current FA page allocation")
            for key in ("key", "value"):
                equal(t, before_f[i][key], prev_f[i][key],
                      "next actual whole FA pages equal previous postimage")
            C.need(before_f[i]['ownership']==prev_f[i]['ownership'],
                   'same actual native FA physical/kernel owner across consecutive frames')
    else:
        initial = by_layer(raw["initial_prefill_GDN_observation"], GDN_LAYERS)
        for i in GDN_LAYERS:
            equal(t, before_g[i]["full_conv_slot"][0, :3], initial[i]["raw_last3"],
                  "actual native prefill last3 to first service tail")
            equal(t, before_g[i]["full_conv_slot"][0, 3:], initial[i]["extra_before"],
                  "actual native prefill wide extras unchanged")
            C.need(initial[i]["native_gdn_source"] == m["runtime_sources"]["gdn"],
                   "same genuine prefill GDN source")
    rows = staged["writes"]
    destinations = {(i, k) for i, kind in LAYERS
                    for k in (("state", "conv") if kind == "gdn" else ("key", "value"))}
    C.need(len(rows) == len(publication["actual_applied"]) == 128
           and {(r["layer"], r["kind"]) for r in rows} == destinations,
           "all and only128 real destinations")
    writes = {(r["layer"], r["kind"]): r for r in rows}
    metrics, component = [], True
    for i, kind in LAYERS:
        row = tree["captures"][i]
        metric = dict(layer=i, kind=kind)
        if kind == "gdn":
            before, after = before_g[i], after_g[i]
            identity = before["slot_binding_identity"]
            C.need(identity == after["slot_binding_identity"]
                   and {item["prefix"]: item for item in raw["layer_slot_bindings"]}
                   .get(identity["prefix"]) == identity
                   and identity["request_id"] == owner["request"]
                   and identity["logical_owner_slot"] == 0
                   and identity["group"] == before["group"] == after["group"]
                   and identity["physical_slot"] == before["physical_slot"] == after["physical_slot"],
                   "same actual native GDN owner/group/physical slot")
            base = before["native_state"].transpose(-1, -2).unsqueeze(0)
            equal(t, row["state"], base, "actual canonical GDN preimage")
            q, k, v, beta, gamma = row["normalized_inputs"]
            C.need(q.shape == k.shape == v.shape == (1, 12, 3, 128)
                   and beta.shape == gamma.shape == (1, 12, 3)
                   and all(x.dtype == t.float32 for x in (q, k, v, beta, gamma)),
                   "unchanged actual TP4 normalized GDN ABI")
            truth, states, updates = oracle112.sequential(
                t, q.double(), k.double(), v.double(), beta.double(), gamma.double(),
                base.double(), (-1, 0, 0), return_updates=True)
            metric["FP32_output"] = I.old112(t, row["precast_output"], truth)
            metric["U"] = I.old112(t, row["factors"][1], updates)
            gd = gamma.double()
            product = t.stack((gd[..., 0], gd[..., 0] * gd[..., 1],
                               gd[..., 0] * gd[..., 2]), dim=-1)
            metric["P"] = I.old112(t, row["factors"][0], product)
            state_write = writes[i, "state"]
            actual_state = state_write["after"].transpose(-1, -2).unsqueeze(0)
            metric["selected_state"] = I.old112(t, actual_state, states[terminal])
            metric["conv"] = conv_math(t, row, before)
            equal(t, row["output"], row["precast_output"].permute(0, 2, 1, 3)
                  .squeeze(0).to(t.bfloat16),
                  "actual BF16 output from unchanged FP32 GDN result")
            for key in ("state", "conv"):
                write = writes[i, key]
                C.need(write["slot"] == write["physical_slot"] == before["physical_slot"]
                       and write["group"] == before["group"]
                       and write["logical_owner_slot"] == 0
                       and write["slot_binding_identity"] == identity
                       and "slot_binding" not in write,
                       "serialized real per-layer destination identity")
            equal(t, state_write["before"], before["native_state"],
                  "actual recurrent preimage")
            equal(t, after["native_state"], state_write["after"],
                  "real native recurrent postimage")
            conv_write = writes[i, "conv"]
            equal(t, conv_write["before"], before["full_conv_slot"][0, :3],
                  "actual conv preimage")
            equal(t, conv_write["after"], row["actual_conv_tail"][terminal],
                  "actual accepted conv tail")
            whole = before["full_conv_slot"].clone()
            whole[0, :3] = conv_write["after"]
            equal(t, after["full_conv_slot"], whole,
                  "whole selected wide conv including extras")
            component &= (all(metric[key]["passed"] for key in
                              ("FP32_output", "U", "P", "selected_state"))
                          and metric["conv"]["output_bound_pass"]
                          and metric["conv"]["state_bitwise"])
        else:
            before, after = before_f[i], after_f[i]
            fa_owner(before,after,row,owner)
            table = list(before["physical_pages"])
            C.need(after["physical_pages"] == before["physical_pages"]
                   and list(row["actual_physical_pages"]) == table,
                   "actual same owned FA physical pages")
            metric["attention"] = fa_math(t, m, row, before, length)
            component &= all(x["pointwise_pass"] for x in metric["attention"].values())
            indices = [table[(length + j) // 128] * 128 + (length + j) % 128
                       for j in range(len(path))]
            for key in ("key", "value"):
                write = writes[i, key]
                C.need(write["indices"].tolist() == indices,
                       "only accepted real physical KV positions")
                pre = t.stack([before[key][table.index(index // 128), index % 128]
                               for index in indices])
                equal(t, write["before"], pre, "actual selected KV preimage")
                value = row[key].reshape(3, 1, 256)[list(path)]
                equal(t, write["after"], value, "selected actual post-RoPE KV values")
                whole = before[key].clone()
                for j, index in enumerate(indices):
                    whole[table.index(index // 128), index % 128] = value[j]
                equal(t, after[key], whole,
                      "whole actual selected FA pages including prefix/inactive/padding")
        metrics.append(metric)
    for j, write in enumerate(rows):
        equal(t, publication["actual_applied"][j], write["after"],
              "actual all128 permanent applied values")
    actual = step["native_output"]
    new_stream = stream + list(emitted)
    C.need(actual["req_ids"] == [owner["request"]]
           and actual["sampled_token_ids"] == [list(emitted)]
           and actual["request_output_tokens_after"] == new_stream
           and actual["num_tokens_no_spec_after"] == length + 1 + len(emitted),
           "actual ModelRunnerOutput/bookkeeping emits selected children and unprocessed bonus")
    return dict(ordinal=ordinal, owner=owner, scheduled_nodes=n,
                processed_nodes=list(path), emitted_tokens=list(emitted), rows=metrics,
                component_checks_pass=bool(component),
                selected_state_bound_scope=("selected accepted state; all3 FP32 outputs, "
                                            "P, U, conv and FA checked")), new_stream, path, emitted


def mtp_join(t, m, record, *, ids, positions, hidden, root, sample_index, live_prefix):
    C.need(record["proposer_source"] == m["runtime_sources"]["proposer"]
           and record["mtp_source"] == m["runtime_sources"]["mtp"],
           "genuine original native MTP source chain")
    equal(t, record["target_token_ids"], ids, "actual MTP target token-ID operand")
    equal(t, record["target_positions"], positions, "actual MTP target position operand")
    equal(t, record["target_hidden_states"], hidden, "actual MTP target hidden operand")
    C.need(record["root"].shape == (1,) and int(record["root"][0]) == root,
           "actual next native MTP root/bonus")
    C.need(record["token_indices_to_sample"].tolist() == [sample_index],
           "actual accepted last-row sampling index")
    first = record["first_pass_inputs"]
    C.need(first["token_indices_to_sample"].tolist() == [sample_index],
           "actual firstpass selected sample index")
    C.need(first["input_ids"].shape == ids.shape
           and first["input_ids"][:len(live_prefix)].tolist() == list(live_prefix),
           "actual firstpass live prefix is accepted child then bonus")
    C.need(positions.dtype == t.int64 and first["positions"].dtype == t.int32,
           "actual native target int64 and drafter int32 position ABIs")
    narrowed_positions = positions.to(t.int32)
    equal(t, narrowed_positions.to(t.int64), positions,
          "exact native position int64/int32 roundtrip")
    equal(t, first["positions"], narrowed_positions,
          "actual firstpass copied native positions at installed int32 ABI")
    equal(t, first["hidden_states"], hidden,
          "actual firstpass copied compacted target hidden")
    metadata = first["metadata"]
    C.need(metadata["query_start_loc"].tolist()
           == metadata["query_start_loc_cpu"].tolist() == [0, ids.numel()],
           "actual full admitted n-row MTP metadata; no accepted-only truncation")
    C.need(len(record["calls"]) == 1 and record["first_logits"].shape[0] == 1,
           "exactly one genuine original MTP iteration")
    logits, children = record["first_logits"], record["children"]
    C.need(children.shape == (1, 2) and children.dtype == t.int64
           and int(children[0, 0]) != int(children[0, 1]),
           "two distinct actual full-vocab MTP candidates")
    values = logits.gather(1, children).sort(descending=True).values
    C.need(t.equal(values, t.topk(logits, 2, dim=-1).values),
           "independent actual global top2 values without invented tie policy")
    C.need(record["returned_drafts"] == children.tolist(),
           "actual two-wide CPU draft publication to native scheduler")
    result = record["native_result"]
    C.need(result.shape == (1, 1)
           and float(logits[0, int(result[0, 0])]) == float(logits[0].max()),
           "original one-step native greedy draft genuinely executed")
    return tuple(int(x) for x in children[0].tolist())


def consume_rank(t, m, raw):
    C.need(raw["schema"] == "bole.actual-c1-continuous-service/v1"
           and raw["request"] == dict(request=raw["request"]["request"],
                                      generation=1, slot=0, length=131, version=0),
           "explicit first request service experiment")
    rid = raw["request"]["request"]
    C.need(raw["source_after"] == m["files"]
           and raw["runtime_sources_after"] == m["runtime_sources"]
           and raw["primary"] is None,
           "actual source/runtime readsets rechecked unchanged at producer freeze")
    slots = raw["layer_slot_bindings"]
    C.need(len(slots) == 48 and len({item["prefix"] for item in slots}) == 48
           and all(item["request_id"] == rid and item["logical_owner_slot"] == 0
                   and item["length"] == 131 for item in slots),
           "complete original registered GDN physical slot identities")
    ids = raw["actual_native_prefill_ids"]
    pos = raw["actual_native_prefill_positions"]
    hidden = raw["actual_native_prefill_hidden"]
    observation = raw["actual_native_prefill_input"]
    C.need(ids.dtype == t.int32 and ids.shape == (131,)
           and hidden.shape == (131, 5120) and hidden.dtype == t.bfloat16
           and bool(t.isfinite(hidden).all()), "actual native text prefill operands")
    equal(t, observation["actual_token_ids"], ids, "observed actual native prefill IDs")
    C.need(ids.tolist() == observation["actual_CPU_token_ids"]
           == observation["request_prompt_token_ids"]
           and observation["no_mm_features"] is True
           and observation["no_soft_prompt"] is True,
           "strong request and CPU buffer input join")
    C.need(observation["sources"] == {key: m["runtime_sources"][key]
           for key in ("runner", "base_runner", "qwen35", "qwen_next")},
           "actual native-input runtime sources")
    C.need(observation["actual_input_mode"] in
           ("native-token-ids", "native-text-embeddings"), "actual native text route")
    if observation["actual_input_mode"] == "native-text-embeddings":
        equal(t, observation["actual_native_embeddings"],
              observation["independent_token_embeddings"],
              "native text embedding/token lookup join")
        C.need(observation["actual_native_embeddings"].shape == (131, 5120)
               and observation["actual_native_embeddings"].dtype == t.bfloat16,
               "exact native embedding ABI")
    axes = pos.ndim
    C.need(pos.dtype == t.int64 and (axes == 1 or pos.shape == (3, 131))
           and pos.tolist() == (list(range(131)) if axes == 1 else [list(range(131))] * 3),
           "original native prefill RoPE coordinates")
    equal(t, raw["initial_target_head_hidden"], hidden[-1:],
          "actual prefill target LMhead operand")
    equal(t, raw["initial_target_head_local_logits"], raw["initial_root_local_logits"],
          "actual prefill sampler input equals unsanitized real LMhead return")
    root = int(raw["initial_root_logits"][0].argmax())
    stream = [root]
    initial = raw["initial_native_output"]
    C.need(initial["req_ids"] == [rid] and initial["sampled_token_ids"] == [[root]]
           and initial["request_output_tokens_after"] == stream
           and initial["num_tokens_no_spec_after"] == 132,
           "actual original native prefill sample/bookkeeping")
    children = mtp_join(t, m, raw["initial_draft"], ids=ids, positions=pos,
                        hidden=hidden, root=root, sample_index=130,
                        live_prefix=ids[1:].tolist() + [root])
    steps = raw["steps"]
    C.need(1 <= len(steps) <= 3, "bounded genuine continuous service target steps")
    reports, previous = [], None
    for ordinal, step in enumerate(steps):
        C.need(tuple(step["tokens"]) == (stream[-1], *children),
               "actual next tree is root plus preceding genuine MTP children")
        n, length = step["scheduled_nodes"], step["owner"]["length"]
        linear, depth = list(range(length, length + n)), [length, length + 1, length + 1]
        C.need(step["original_positions"].dtype == t.int64
               and step["original_positions"].tolist() == (linear if axes == 1 else [linear] * 3),
               "actual native linear coordinates before substitution")
        C.need(step["tree_positions"].dtype == t.int64
               and step["tree_positions"].tolist() == (depth if axes == 1 else [depth] * 3),
               "actual tree-depth coordinates")
        C.need(step["tree_hidden"].shape == (3, 5120)
               and step["tree_hidden"].dtype == t.bfloat16
               and bool(t.isfinite(step["tree_hidden"]).all()),
               "actual finite all64 normalized target hidden")
        equal(t, step["target_head_hidden"], step["tree_hidden"][:n],
              "actual LMhead consumed exact admitted target hidden rows")
        equal(t, step["target_head_local_logits"], step["target_local_logits"],
              "actual native sample input is exact original head output")
        report, stream, path, emitted = consume_step(
            t, m, raw, step, ordinal, stream, previous)
        reports.append(report)
        order = [0, 2, 1] if path[-1] == 2 else [0, 1, 2]
        index = t.tensor(order[:n], dtype=t.long)
        native_ids = t.tensor(step["tokens"], dtype=ids.dtype).index_select(0, index)
        native_pos = step["tree_positions"].index_select(-1, index)
        native_hidden = step["tree_hidden"].index_select(0, index)
        children = mtp_join(t, m, step["next_mtp"], ids=native_ids,
                            positions=native_pos, hidden=native_hidden,
                            root=emitted[-1], sample_index=len(path) - 1,
                            live_prefix=emitted)
        rejected = step["next_mtp"]["num_rejected_tokens"]
        if n == 1:
            C.need(rejected is None or rejected.tolist() == [0],
                   "no rejected drafts in native root-only schedule")
        else:
            C.need(rejected is not None and rejected.tolist() == [n - len(path)],
                   "actual original padded-drafter rejection accounting")
        previous = step
    C.need(len(stream) == 4
           and sum(len(x["processed_nodes"]) for x in reports) == 3,
           "exact four actual output tokens; final bonus is unprocessed")
    retirement = raw["retirement"]
    acknowledgements = retirement["next_counter_acknowledgements"]
    C.need(retirement["schema"] == "bole.service-owner-native-retirement/v1"
           and retirement["request"] == rid and retirement["generation"] == 1
           and retirement["steps"] == len(steps)
           and len(acknowledgements) == len(steps) - 1
           and retirement["final_ack_by_retirement_pending"] is True,
           "real removed owner with independent final HTTP/worker-retirement join")
    for i, acknowledgement in enumerate(acknowledgements):
        prev, following = steps[i], steps[i + 1]
        C.need(acknowledgement["schema"] == "bole.service-native-scheduler-ack/v1"
               and acknowledgement["request"] == rid
               and acknowledgement["previous_version"] == i
               and acknowledgement["version"] == i + 1
               and acknowledgement["computed_tokens"]
               == prev["publication"]["next_length"] == following["owner"]["length"]
               and acknowledgement["next_root"]
               == prev["publication"]["emitted_tokens"][-1] == following["tokens"][0]
               and acknowledgement["scheduler_committed"] is True,
               "actual next native CPU counter/root acknowledgement")
    last = steps[-1]["publication"]
    C.need(retirement["last_publication"] == dict(
        owner=last["owner"], next_length=last["next_length"],
        next_version=last["next_version"], emitted_tokens=last["emitted_tokens"]),
        "final actual publication linked to removed owner")
    return dict(rank=raw["rank"], request=rid, output_token_ids=stream,
                steps=reports, component_checks_pass=all(
                    x["component_checks_pass"] for x in reports),
                actual_next_counter_acknowledgements=len(acknowledgements),
                actual_final_retirement_observed=True,
                native_AR_greedy_comparison_performed=False,
                whole_numerical_qualified=False, model_ready=False,
                performance_ready=False, task_ready=False)


def http_join(t, sr, bundle, raws, reports):
    http = C.obj(bundle["http"])
    C.need(http["source"] == sr and [x["label"] for x in http["rows"]]
           == ["tree", "retirement-barrier"], "actual bounded service and retirement HTTP requests")
    first_ids = raws[0]["actual_native_prefill_ids"].tolist()
    for row, count in zip(http["rows"], (4, 1)):
        request, response = row["request"], C.obj(row["response"])
        C.need(request["prompt"] == first_ids and request["max_tokens"] == count
               and request["temperature"] == 0 and request["top_p"] == 1
               and request["n"] == 1 and request["stream"] is False
               and request["ignore_eos"] is True and request["return_token_ids"] is True,
               "exact source-proven deterministic HTTP token-ID protocol")
        C.need(row["http_status"] == 200 and "error" not in response
               and response["id"] == "cmpl-" + row["header"]
               and response["usage"]["prompt_tokens"] == 131
               and response["usage"]["completion_tokens"] == count
               and len(response["choices"]) == 1,
               "actual completed request/header/token counts")
        ids = response["choices"][0]["token_ids"]
        C.need(type(ids) is list and len(ids) == count
               and all(type(x) is int and x >= 0 for x in ids),
               "actual CompletionResponse returned token IDs")
        if row["label"] == "tree":
            C.need(all(report["output_token_ids"] == ids for report in reports),
                   "actual HTTP output IDs join all4 real worker selected paths")
    return True


def rank_vocabulary_joins(t, m, raws):
    policies = [raw["native_logits_policy"] for raw in raws]
    C.need(all(policy == policies[0] for policy in policies)
           and policies[0]["proposer_source"] == m["runtime_sources"]["proposer"],
           "all4 exact original native vocabulary policy and source")
    policy = policies[0]
    tp_logits(t, [{"local": raw["initial_root_local_logits"],
                   "global": raw["initial_root_logits"]} for raw in raws], policy)
    tp_logits(t, [{"local": raw["initial_draft"]["first_local_logits"],
                   "global": raw["initial_draft"]["first_logits"]} for raw in raws], policy)
    C.need(all(len(raw["steps"]) == len(raws[0]["steps"]) for raw in raws),
           "all4 same actual continuous target step count")
    for ordinal in range(len(raws[0]["steps"])):
        steps = [raw["steps"][ordinal] for raw in raws]
        C.need(all(step["owner"] == steps[0]["owner"]
                   and step["tokens"] == steps[0]["tokens"]
                   and step["scheduled_nodes"] == steps[0]["scheduled_nodes"]
                   and step["remaining_output"] == steps[0]["remaining_output"]
                   for step in steps), "all4 actual current owner/tree/admission/budget")
        tp_logits(t, [{"local": step["target_local_logits"],
                       "global": step["target_logits"]} for step in steps], policy)
        tp_logits(t, [{"local": step["next_mtp"]["first_local_logits"],
                       "global": step["next_mtp"]["first_logits"]} for step in steps], policy)


def run(t, sr, bundle_ref, out):
    m = validate_source(sr)
    C.need(out.is_absolute() and out.is_dir()
           and not any(x.is_symlink() for x in (out, *out.parents)),
           "precreated ordinary absolute consumer output directory")
    bundle = C.obj(bundle_ref)
    C.need(bundle["source"] == sr, "exact source-bound owned host input ledger")
    assigned, bindings = CM.identity_join(sr, bundle)
    C.need(len(bundle["ranks"]) == 4, "all4 exact actual rank capture references")
    raws, capture_refs, calibrations = [], [], []
    import model_calibration131r12 as MC
    MC.own_module(C, m, MC)
    old_abi = C.obj(m["actual118c"]["capture"])["actual_device_abi_ref"]
    for rank, pair in enumerate(bundle["ranks"]):
        root = Path(m["model_receipt_root"])
        C.need(pair["receipt"]["path"] == str(root / ("BOLE-TREE-RANK-%d.json" % rank))
               and pair["raw"]["path"] == str(root / ("BOLE-TREE-RANK-%d.pt" % rank)),
               "exact genuine worker capture filenames in declared owned leaf")
        receipt = C.obj(pair["receipt"])
        C.need(receipt["source"] == sr and receipt["rank"] == rank
               and receipt["primary"] is None and receipt["raw"] == pair["raw"],
               "actual source/rank/raw/firstfault receipt")
        rest = receipt["stat"][receipt["stat"].rfind(")") + 2:].split()
        C.need(dict(pid=receipt["pid"], start_ticks=int(rest[19]),
                    cgroup=receipt["cgroup"]) == bindings[rank],
               "actual worker capture and independent owned PID/start/cgroup join")
        exported = t.load(C.checked(pair["raw"]), map_location="cpu", weights_only=False)
        C.need(exported["schema"] == "bole.model-diagnostic-primitives/v1"
               and 0 <= exported["logical_tensor_bytes"] <= exported["cap_bytes"] == 2 ** 30,
               "actual bounded primitive-only capture export")
        raw = exported["payload"]
        C.need(raw["source"] == sr and raw["rank"] == rank
               and raw["request"]["request"] == assigned,
               "actual assigned engine ID and source/rank identity")
        C.need(raw["same_model_conv_calibration"] == receipt["model_calibration_ref"],
               "host mounted same actual rank convolution calibration")
        calibration = MC.consume(t, C, raw["same_model_conv_calibration"],
                                 old_abi, sr, rank)
        C.need(pair["raw"]["bytes"] + calibration["raw_bytes"]
               + raw["same_model_conv_calibration"]["bytes"] <= 2 ** 30 + 2 ** 20,
               "original combined worker raw1GiB plus bounded headers and calibration")
        raws.append(raw)
        capture_refs.append(dict(receipt=pair["receipt"], raw=pair["raw"]))
        calibrations.append(calibration)
    rank_vocabulary_joins(t, m, raws)
    reports, references = [], []
    for rank, raw in enumerate(raws):
        report = consume_rank(t, m, raw)
        reports.append(report)
        references.append(C.write(out / ("RANK-%d.json" % rank), dict(
            source=sr, **capture_refs[rank], report=report)))
    C.need(all(report["output_token_ids"] == reports[0]["output_token_ids"]
               for report in reports), "all4 exact actual emitted token identity")
    http_join(t, sr, bundle, raws, reports)
    components = all(report["component_checks_pass"] for report in reports)
    result = dict(
        schema="bole.actual-c1-continuous-service-independent/v1", source=sr,
        inputs=bundle_ref, ranks=references,
        independently_recomputed_same_model_conv_calibrations=calibrations,
        scope="C1/first131-token-prefix/four-output-tokens/max3-target-tree-steps",
        actual_all4_retirement=True, actual_HTTP_output_token_ID_join=True,
        independent_actual_MTP_TP4_vocabulary_join=True,
        independent_actual_target_TP4_vocabulary_join=True,
        actual_scheduler_flow_observed=True,
        scheduler_committed=bool(components), component_checks_pass=bool(components),
        scheduler_committed_independently=bool(components),
        service_complete=bool(components),
        service_experiment_pass=bool(components),
        selected_state_scope="accepted selected states; all3 output/P/U/conv/FA rows checked",
        native_AR_greedy_comparison_performed=False,
        greedy_identity_pass=None,
        whole_numerical_qualified=False, whole_numerical_threshold=None,
        model_ready=False, task_ready=False, performance_ready=False,
        formal_success=False)
    C.write(out / "ATTRIBUTION.json", result)
    C.need(components, "original component mathematical bounds failed; raw captures and metrics retained")
    return result


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--validate-source", action="store_true")
    parser.add_argument("--source-ref")
    parser.add_argument("--inputs-ref")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.execute and not args.validate_source:
        print('{"enabled":false,"NPU":false}')
        return 0
    C.need(args.source_ref is not None, "explicit exact source reference")
    source_ref = json.loads(args.source_ref)
    validate_source(source_ref)
    if args.validate_source and not args.execute:
        print('{"source_validated":true,"NPU":false}')
        return 0
    C.need(args.inputs_ref is not None and args.output is not None,
           "explicit bound input ledger and consumer output")
    C.need(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == ""
           and os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD") == "0",
           "actual owned Devices[] independent CPU consumer")
    C.need(not list(Path("/dev").glob("davinci[0-9]*")),
           "no device nodes in independent CPU consumer")
    import torch
    try:
        run(torch, source_ref, json.loads(args.inputs_ref), args.output)
    except BaseException as error:
        C.write(args.output / "FAILURE.json", dict(
            primary=repr(error), traceback=traceback.format_exc()))
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
