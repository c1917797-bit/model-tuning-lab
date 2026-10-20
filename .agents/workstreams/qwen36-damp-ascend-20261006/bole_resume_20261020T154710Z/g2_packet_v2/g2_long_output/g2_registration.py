"""Exact G1 native-registration joins, with explicit G2 fixed output policy."""
import hashlib,json
from pathlib import Path
import sourceio as C
import g2_contract as G2
from g2_numeric import by_layer,GDN_LAYERS,FA_LAYERS

def canonical(value):
    if type(value) in (list, tuple):
        return [canonical(x) for x in value]
    if type(value) is dict:
        return {k: canonical(v) for k, v in value.items()}
    return value

def positive_object(value):
    return type(value) is int and value > 0

def capture_join(sr, m, item, binding, calibrated, MC, old_abi):
    """Join each callback's actual integer/native identities to the numerical frame."""
    rank, owner = item["rank"], item["request"]
    generation, rid = owner["generation"], owner["request"]
    root = Path(m["model_receipt_root"])
    refs = item["request_capture_refs"]
    C.need(set(refs) == {"cache_observation", "fa_prefill", "registration_audit"},
           "three independent original callback references per request")
    names = dict(cache_observation="BOLE-PREFILL-CACHE", fa_prefill="BOLE-FA-PREFILL-MAPPING",
                 registration_audit="BOLE-NATIVE-LIBRARY-IDENTITY")
    docs = {}
    for key, prefix in names.items():
        ref = refs[key]
        C.need(ref["path"] == str(root / ("%s-REQUEST-%02d-RANK-%d.json" %
                                        (prefix, generation, rank))),
               "exact current request callback pathname")
        doc = C.obj(ref)
        C.need(doc["source"] == sr and doc["rank"] == rank
               and doc["request_epoch"] == generation,
               "actual callback rank/source/request epoch")
        docs[key] = doc
    cache, fa, registration = (docs[k] for k in
                              ("cache_observation", "fa_prefill", "registration_audit"))
    C.need(cache["schema"] == "bole.post-native-prefill-cache-observation/v131r4"
           and cache["pid"] == binding["pid"] and cache["observer"] == m["files"]["cache_observation.py"]
           and cache["native_prefill_returned"] is True
           and cache["observation_ordinal"] == generation
           and cache["actual_slot_ids_not_copied"] is True
           and cache["guard_bypassed"] is False and cache["numerical_qualified"] is False
           and cache["request"]["request_id"] == rid and cache["request"]["CPU_row"] == 0
           and cache["runtime_sources"] == {k: m["runtime_sources"][k] for k in
                                           ("runner", "base_runner", "gdn", "block_table")},
           "actual post-native-prefill request callback without metadata bypass")
    object_id = cache["request"]["object_id"]
    C.need(positive_object(object_id) and fa["request_id"] == rid
           and fa["request_object_id"] == object_id
           and fa["schema"] == "bole.actual-FA-prefill-mapping-operands/v131r10"
           and fa["generic_context_type"] == "dict" and fa["generic_context_keys"] == []
           and fa["integer_metadata_D2H"] is True
           and fa["cache_contents_captured"] is False and fa["numerical_qualified"] is False
           and fa["runtime_sources"] == {k: m["runtime_sources"][k] for k in
                ("runner", "block_table", "attention", "ascend_attention",
                 "forward_context", "ascend_forward_context")},
           "same actual strong request and unmodified native prefill metadata path")
    slots = {x["prefix"]: x for x in item["layer_slot_bindings"]}
    observed = {x["prefix"]: x for x in cache["all48"]}
    selected = by_layer(fa["GDN_selected_operands"], GDN_LAYERS)
    C.need(len(observed) == len(cache["all48"]) == len(slots) == 48
           and set(observed) == set(slots), "all48 callback/native GDN binding joins")
    groups = {x["gid"]: x for x in cache["groups"]}
    C.need(len(groups) == len(cache["groups"]), "unique actual native groups")
    for prefix, identity in slots.items():
        obs = observed[prefix]
        layer = obs["index"]
        sel = selected[layer]
        C.need(identity["request_object_id"] == object_id
               and identity["generation"] == generation and identity["request_id"] == rid
               and obs["groups"] == [identity["group"]]
               and obs["object_id"] == identity["layer_object_id"]
               and obs["static_same"] is True and obs["dispatcher_same"] is True
               and identity["table_object_id"] == groups[identity["group"]]["table_object_id"]
               and identity["physical_slot"] in groups[identity["group"]]["CPU_row"]
               and cache["request"]["block_ids"][identity["group"]]
               == groups[identity["group"]]["CPU_row"]
               and sel["prefix"] == prefix and sel["selected"]["values"] == [identity["physical_slot"]]
               and sel["selected"]["identity"][1] == obs["prefill_state_indices"]["data_ptr"],
               "independent real per-layer physical state slot and strong request metadata")
        for key, actual in (("conv_identity", obs["conv"]), ("state_identity", obs["state"])):
            expected = [actual["storage_ptr"], actual["data_ptr"], actual["storage_offset"],
                        actual["shape"], actual["stride"], actual["dtype"], actual["device"]]
            C.need(canonical(sel[key]) == expected,
                   "same original native state/conv storage in both independent observers")
    before = by_layer(item["steps"][0]["before_FA"], FA_LAYERS)
    for row in by_layer(fa["rows"], FA_LAYERS).values():
        proof = before[row["layer"]]["ownership"]
        ratio, physical = row["blocks_per_phys_block"], row["request_physical_blocks"]
        C.need(type(ratio) is int and ratio > 0 and row["kernel_block_size"] == 128
               and row["physical_block_size"] == ratio * 128 and type(row["use_hybrid_blocks"]) is bool
               and physical and all(type(p) is int and p >= 0 for p in physical),
               "actual native physical1536/kernel128 prefill geometry")
        expanded = [p * ratio + j for p in physical for j in range(ratio)] if row["use_hybrid_blocks"] else list(physical)
        expected_slots = [expanded[p // 128] * 128 + p % 128 for p in range(131)]
        C.need(row["allocated"] == len(expanded) and len(set(expanded)) == len(expanded)
               and row["CPU_table"]["values"] == row["GPU_table"]["values"]
               == row["metadata_table"]["values"] == expanded
               and row["native_slot_mapping"]["values"]
               == row["metadata_slot_mapping"]["values"] == expected_slots
               and row["GPU_table"]["identity"] == row["metadata_table"]["identity"]
               and row["native_slot_mapping"]["identity"] == row["metadata_slot_mapping"]["identity"]
               and row["generic_slot_mapping"] is None
               and row["num_actual_tokens"] == 131
               and row["seq_lens_list"] == row["actual_seq_lengths_q"] == [131]
               and proof["request_object_id"] == object_id and proof["generation"] == generation
               and proof["request"] == rid and proof["prefix"] == row["prefix"]
               and proof["group"] == row["group"]
               and proof["layer_object_id"] == row["layer_object_id"]
               and proof["table_object_id"] == groups[row["group"]]["table_object_id"]
               and proof["CPU_table"] == expanded
               and list(proof["request_physical_blocks"]) == physical
               and cache["request"]["block_ids"][row["group"]] == physical
               and row["context_object_id"] == cache["context_object_id"],
               "all native prefill writes, tables, aliases and current live FA owner independently joined")
        for key in ("physical_block_size", "kernel_block_size", "blocks_per_phys_block", "use_hybrid_blocks"):
            C.need(proof[key] == row[key], "same prefill and target FA page geometry")
    C.need(registration["schema"] == "bole.actual-native-library-identity-before-gate/v131r11"
           and registration["pid"] == binding["pid"] and registration["calibrated_abi_ref"] == old_abi
           and registration["calibrated_registration"] == C.obj(old_abi)["registration"]
           and registration["gate_relaxed"] is False and registration["model_ready"] is False,
           "original loaded-versus-old calibration mismatch is retained without relaxation")
    import registration_audit131r11 as RA
    MC.own_module(C, m, RA)
    C.need(registration["comparison"] == RA.compare(registration["actual_registration"],
                                                   registration["calibrated_registration"])
           and MC.identity(registration["actual_registration"])
           == MC.identity(calibrated["registration"]),
           "independent exact complete loaded-library comparison and new original12 lineage")
    for library in (MC.identity(registration["actual_registration"])["extension"],
                    *MC.identity(registration["actual_registration"])["opapi"]):
        C.checked(library)
        C.need(any(line.split() and line.split()[-1] == library["path"]
                   for line in registration["actual_process_maps"].splitlines()),
               "each independently checked actual library appears in that request's process maps")
    expected = dict(n=1, temperature=0, top_p=1, min_p=0, repetition_penalty=1,
        frequency_penalty=0, presence_penalty=0, max_tokens=G2.MAX_OUTPUT, min_tokens=0, ignore_eos=True)
    policies = item["policy_receipts"]
    C.need(len(policies) == 3 and [p["generated_before"] for p in policies] == [0, 0, 1]
           and all(all(p[k] == v for k, v in expected.items()) and p["top_k"] in (0, -1)
                   and p["all_greedy"] is True and p["no_penalties"] is True
                   and p["no_thinking_budget"] is True for p in policies),
           "actual source-guarded neutral native greedy policies before prefill and target samples")
    arenas = dict(
        GDN=[dict(prefix=prefix, layer_object_id=observed[prefix]["object_id"],
                  group=identity["group"], group_object_id=identity["group_object_id"],
                  table_object_id=identity["table_object_id"],
                  conv=observed[prefix]["conv"], state=observed[prefix]["state"])
             for prefix, identity in sorted(slots.items())],
        FA=[{key: before[i]["ownership"][key] for key in
             ("prefix", "group", "table_object_id", "layer_object_id", "cache_identities")}
            for i in FA_LAYERS])
    arena_digest = hashlib.sha256(json.dumps(canonical(arenas), sort_keys=True,
        allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    return dict(generation=generation, request=rid, request_object_id=object_id,
                native_arena_identity_sha256=arena_digest,
                GDN_slots=[dict(prefix=p,group=i['group'],physical_slot=i['physical_slot'])for p,i in sorted(slots.items())],
                FA_pages=[dict(layer=i,physical_pages=list(before[i]['physical_pages']))for i in FA_LAYERS],
                references=refs, actual_callback_identity_join=True)
