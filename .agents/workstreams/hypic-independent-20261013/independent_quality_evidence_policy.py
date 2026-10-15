"""Draft opt-in quality-hot receipt policy. Never filters client quality results."""
from collections import Counter

DROP_KINDS=frozenset(("mixed_native_gdn_completed","mixed_native_c2_completed","native_decode_batch_completed"))
class QualityEvidencePolicy:
    def __init__(self,profile="full",*,max_shadow_groups=384):
        if profile not in ("full","quality-hot"):raise ValueError("explicit evidence profile required")
        if type(max_shadow_groups) is not int or not 1<=max_shadow_groups<=384:
            raise ValueError("bounded shadow group count required")
        self.profile=profile;self.limit=max_shadow_groups;self.groups={};self.omitted=Counter()
    def descriptor(self):
        return {"event":"quality_evidence_policy_selected","profile":self.profile,
                "omittable_nonhot_events":sorted(DROP_KINDS) if self.profile=="quality-hot" else [],
                "all_private_C1_C2_hot_receipts_retained":True,
                "all_public_generation_eviction_receipts_retained":True,
                "all_shadow_groups_and_their_native_commits_retained":True,
                "client_quality_denominator_untouched":True}
    def select(self,event):
        if self.profile=="full":return dict(event)
        x=dict(event);kind=x.get("event")
        key=(x.get("rank"),x.get("step"),x.get("layer"))
        if kind=="native_decode_batch_shadow_checked":
            if key in self.groups or len(self.groups)>=self.limit:
                raise ValueError("duplicate or excess shadow group")
            ids=x.get("requests")
            if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)):
                raise ValueError("shadow group membership required")
            self.groups[key]={"requests":tuple(ids),"slots":None}
        retain=True
        if kind=="native_decode_batch_completed":
            group=self.groups.get(key);retain=group is not None
            if retain:
                slots=x.get("slots",[])
                if tuple(x.get("requests",()))!=group["requests"] or len(slots)!=len(group["requests"]) or len(slots)!=len(set(slots)):
                    raise ValueError("sampled batch membership/slot drift")
                if group["slots"] is not None:raise ValueError("duplicate sampled batch completion")
                group["slots"]=dict(zip(group["requests"],slots))
        elif kind=="mixed_native_gdn_completed":
            group=self.groups.get(key)
            retain=group is not None and x.get("request_id") in group["requests"]
            if retain and (group["slots"] is None or group["slots"][x["request_id"]]!=x.get("slot")):
                raise ValueError("sampled native commit slot drift")
        elif kind=="mixed_native_c2_completed":retain=False
        if not retain:
            self.omitted[kind]+=1
            if self.omitted[kind]>2147483647:raise ValueError("nonhot receipt counter overflow")
            return None
        x["evidence_profile"]="quality-hot"
        x["omitted_nonhot_counts"]=dict(self.omitted)
        return x
