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
import g2_contract as G2
import consume_model as CM

SCOPE = G2.SCOPE
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
    import g3_fa_consumer
    C.need(C.ref(g3_fa_consumer.__file__)==m['files']['g3_fa_consumer.py'], 'exact independent long-prefix scratch consumer')
    g3_fa_consumer.consume(t,row,anchor,length)
    q = row["query"].reshape(3, 6, 256)
    k = row["key"].reshape(3, 1, 256)
    v = row["value"].reshape(3, 1, 256)
    C.need(q.dtype == k.dtype == v.dtype == row["output"].dtype == t.bfloat16,
           "unchanged actual FA BF16 ABI")
    table = list(anchor["physical_pages"])
    C.need(len(table) >= (length+2+127)//128 and len(set(table)) == len(table),
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
           and proof['request']==owner['request']and proof['logical_owner_slot']==owner['slot']==0 and
           type(proof['generation'])is int and proof['generation']==owner['generation']in(1,2),
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
           and list(before['physical_pages'])==list(after['physical_pages'])==expanded
           and len(before['physical_pages'])==len(expanded)
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
           and type(remaining) is int and 1 <= remaining < G2.MAX_OUTPUT,
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
    C.need(owner == dict(request=raw["request"]["request"], generation=raw["request"]["generation"],
                         slot=0, length=131 + len(stream) - 1, version=ordinal)
           and 131 <= length <= 131+G2.MAX_OUTPUT-2, "actual monotonic service owner")
    C.need(step["request_output_tokens_before"] == stream
           and step["remaining_output"] == G2.MAX_OUTPUT - len(stream),
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
        request_id=owner["request"], generation=owner["generation"], slot=0, root=0,
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
                   and list(row["actual_physical_pages"]) == table[:(length+2+127)//128],
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

