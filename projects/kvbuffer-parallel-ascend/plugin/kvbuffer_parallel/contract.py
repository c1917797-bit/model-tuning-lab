"""CPU-only admission and binding contracts. Not numerical NPU evidence."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

CAPACITY, KH, VH, D, META = 16, 4, 12, 128, 32
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
SOURCES = {
 "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py":
 "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
 "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py":
 "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
 "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py":
 "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py":
 "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
}
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MODEL_CONFIG = "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_identity():
    actual = {path: sha(path) for path in SOURCES}
    require(actual == SOURCES, "source identities changed; fresh audit required")
    return actual

def admit_text_request(prompt_token_ids, prompt_embeds, mm_features, prompt_is_token_ids):
    """Pinned CachedRequestState: None mask means an all-token-ID prompt."""
    require(type(prompt_token_ids) is list and bool(prompt_token_ids) and
            all(type(v) is int and v >= 0 for v in prompt_token_ids),
            "native nonempty token-ID prompt required")
    require(prompt_embeds is None, "prompt embeddings unsupported")
    require(mm_features is None or (type(mm_features) is list and not mm_features),
            "multimodal features unsupported")
    if prompt_is_token_ids is not None:
        require(type(prompt_is_token_ids) is list and
                len(prompt_is_token_ids) == len(prompt_token_ids) and
                all(type(v) is bool for v in prompt_is_token_ids) and
                all(prompt_is_token_ids),
                "mixed/invalid prompt token-ID mask unsupported")

def admit_lengths(seq, indices, tokens, slots, expected_active=None):
    require(type(tokens) is int and 1 <= tokens <= 16, "T must be1..16")
    require(type(slots) is int and slots > 0, "invalid arena")
    require(len(seq) == tokens+1 and len(indices) == tokens, "length ABI/cardinality")
    require(all(type(v) is int for v in seq+indices), "integer CPU metadata required")
    require(seq[0] == 0, "initial offset must be0, not a cumulative sequence array")
    values = seq[1:]
    require(all(v in (0,1) for v in values), "one-token non-spec decode only")
    active = sum(values)
    require(values == [1]*active+[0]*(tokens-active), "real tokens must precede dummy")
    require(expected_active is None or active == expected_active, "active-token mismatch")
    live = indices[:active]
    require(len(set(live)) == len(live), "duplicate mutable state writers")
    require(all(0 <= v < slots for v in live), "live slot out of arena")
    # Native dummy slot is commonly0, not PAD_SLOT_ID. It is never a live slot.
    require(all(v == 0 for v in indices[active:]), "unproven dummy slot ABI")
    return tuple(live)

def aux_bytes(slots, layers=48):
    require(type(slots) is int and slots>0 and layers==48, "full48 allocation required")
    per_slot = KH*CAPACITY*D*2 + VH*CAPACITY*D*4 + VH*META*(4+4+4)
    return per_slot*slots*layers

def admission_specs(specs):
    require(specs and specs[0]["dtype"]=="bf16", "query spec missing")
    dev=specs[0]["device"]
    for s in specs:
        require(s["device"]==dev and str(dev).startswith("npu:"), "same NPU required")
        require(s["contiguous"] and s["format"]==2, "physical ND required")
    for i,a in enumerate(specs):
        if not a.get("mutable"): continue
        for j,b in enumerate(specs):
            if i==j: continue
            require(a["ptr"]+a["bytes"] <= b["ptr"] or
                    b["ptr"]+b["bytes"] <= a["ptr"], "mutable range aliases another tensor")

def verify_alias(donor, target):
    require(target._forward_core is donor._forward_core, "receiver is not native donor alias")
    require(target.forward is donor.forward, "outer forward is not pinned Ascend alias")

def bind(donor,target,wrapper):
    verify_alias(donor,target)
    original=donor._forward_core
    require(not hasattr(target,"_kvbp_original_core"), "double/incompatible patch")
    donor._kvbp_original_core=target._kvbp_original_core=original
    donor._forward_core=target._forward_core=wrapper
    return original

def live_bindings(mapping,donor,target,wrapper):
    rows=[]
    for obj in mapping.values():
        if not isinstance(obj,target): continue
        require(type(obj) is target, "unreviewed GDN subclass")
        match=re.search(r"(?:^|\.)layers\.(\d+)\.",str(obj.prefix))
        require(match is not None, "unrecognized GDN prefix")
        layer=int(match.group(1))
        require(obj._forward_core.__func__ is wrapper and
                obj.forward.__func__ is donor.forward, "actual instance binding differs")
        rows.append({"layer":layer,"prefix":obj.prefix,"class":type(obj).__module__+"."+type(obj).__qualname__,
                     "core_owner":wrapper.__module__+"."+wrapper.__qualname__,
                     "forward_owner":donor.forward.__module__+"."+donor.forward.__qualname__})
    require(len(rows)==48 and {r["layer"] for r in rows}==set(LAYERS),
            "all48 real GDN receiver instances required")
    require(len({r["prefix"] for r in rows})==48, "duplicate actual GDN prefix")
    return sorted(rows,key=lambda r:r["layer"])
