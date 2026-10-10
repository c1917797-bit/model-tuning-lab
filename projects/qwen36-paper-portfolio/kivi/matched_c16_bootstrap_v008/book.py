"""Scalar actual-request lifecycle, not allocation or run authority."""
def need(value, reason):
    if not value:
        raise ValueError(reason)

def frame_valid(frame):
    need(type(frame) is dict and type(frame["epoch"]) is int and frame["epoch"] > 0, "fresh prepare epoch")
    ids, counts, computed, starts, positions = (frame[k] for k in
        ("req_ids", "scheduled_counts", "computed_tokens", "query_start_loc", "positions"))
    need(type(ids) is list and 1 <= len(ids) <= 16 and len(set(ids)) == len(ids)
         and all(type(x) is str and x for x in ids), "actual ordered unique assigned IDs")
    need(len(counts) == len(computed) == len(ids) and len(starts) == len(ids) + 1
         and starts[0] == 0 and type(frame["total_tokens"]) is int, "whole batch partition")
    need(all(type(n) is int and n > 0 for n in counts)
         and all(type(c) is int and c >= 0 for c in computed)
         and all(type(s) is int and s >= 0 for s in starts), "exact integer schedule")
    need(starts[-1] == sum(counts) == frame["total_tokens"] == len(positions), "whole real token span")
    for i, (c, n) in enumerate(zip(computed, counts)):
        need(starts[i+1]-starts[i] == n and positions[starts[i]:starts[i+1]] == list(range(c,c+n)),
             "actual position ordering, no offset or speculative gap")
    need(frame["req_id_to_index"] == {rid:i for i,rid in enumerate(ids)}, "actual native batch permutation")
    return True

class Book:
    def __init__(self, assigned_ids, prompt_lengths, decode_cap=1024):
        need(type(assigned_ids) is list and 0 < len(assigned_ids) <= 64
             and len(set(assigned_ids)) == len(assigned_ids)
             and all(type(r) is str and r for r in assigned_ids), "actual fixed assigned IDs, not HTTP guesses")
        need(type(prompt_lengths) is dict and set(prompt_lengths) == set(assigned_ids)
             and all(type(p) is int and 0 < p <= 32768 for p in prompt_lengths.values())
             and type(decode_cap) is int and decode_cap == 1024, "real prompt lengths and fixed capacity")
        self.allowed=tuple(assigned_ids); self.prompts=dict(prompt_lengths); self.cap=decode_cap
        self.live={}; self.epochs={}; self.ever=set(); self.finished=set()
    def plan(self, frame):
        frame_valid(frame)
        proposals=[]; kinds=[]
        for rid,c,n in zip(frame["req_ids"],frame["computed_tokens"],frame["scheduled_counts"]):
            need(rid in self.allowed and rid not in self.finished, "actual allowed unretired owner")
            p=self.prompts[rid]
            need(c+n <= p+self.cap and ((c < p and c+n <= p) or (c >= p and n == 1)),
                 "one decode append, no prefill/decode crossing or speculative schedule")
            kind="prefill" if c < p else "decode"; kinds.append(kind)
            if rid not in self.live:
                need(c == 0 and rid not in self.ever, "new owner once, no cached-prefix/recompute/fork inference")
                used={x["slot"] for x in self.live.values()} | {x[1] for x in proposals}
                free=[s for s in range(16) if s not in used]
                need(bool(free), "physical compact owner-slot capacity")
                proposals.append((rid,free[0]))
            else:
                x=self.live[rid]
                need(x["length"] == c and x["pending"] is None, "actual sequential frame, no preemption/replay")
        need(set(kinds) <= {"prefill","decode"}, "actual per-request supported schedule kinds")
        for rid,slot in proposals:
            epoch=self.epochs.get(slot,0)+1; self.epochs[slot]=epoch
            self.live[rid]={"slot":slot,"epoch":epoch,"length":0,"pending":None}
            self.ever.add(rid)
        for rid in frame["req_ids"]:
            self.live[rid]["pending"]={"frame_epoch":frame["epoch"],"layers":set()}
        return kinds[0] if len(set(kinds)) == 1 else "mixed"
    def layer_done(self, rid, frame_epoch, layer):
        x=self.live[rid]; p=x["pending"]
        need(p is not None and p["frame_epoch"] == frame_epoch and layer not in p["layers"], "one layer per real frame")
        p["layers"].add(layer)
    def complete(self, frame, layers):
        need(type(layers) is tuple and len(layers) == len(set(layers)) == 16, "real complete FA16")
        for rid,c,n in zip(frame["req_ids"],frame["computed_tokens"],frame["scheduled_counts"]):
            x=self.live[rid]; p=x["pending"]
            need(p is not None and p["frame_epoch"] == frame["epoch"] and p["layers"] == set(layers),
                 "all16 actual attention returns before commit")
            x["length"]=c+n; x["pending"]=None
    def retire(self, finished, requests_after, batch_after, release):
        need(type(finished) is list and len(finished) == len(set(finished))
             and all(type(r) is str and r for r in finished), "actual native finished IDs")
        for rid in finished:
            if rid not in self.allowed:
                continue
            need(rid in self.live and rid not in requests_after and rid not in batch_after,
                 "actual native request and batch retirement, not HTTP done")
            x=self.live[rid]
            need(x["pending"] is None and self.prompts[rid] <= x["length"] <= self.prompts[rid]+self.cap,
                 "committed real length, normal EOS allowed; no pending recycle")
            release(rid,x["slot"],x["epoch"])
            del self.live[rid]; self.finished.add(rid)
    def close(self):
        need(not self.live and self.finished == set(self.allowed), "every assigned owner actually retired")
        return True
