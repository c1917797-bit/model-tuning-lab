"""Bounded scalar provenance for first native request preparation."""
class RequestProgressLedger:
    def __init__(self):self.seen=set()
    def observe(self,requests):
        out=[]
        for r in requests:
            first=r.request_id not in self.seen
            if first and len(self.seen)>=128:
                raise ValueError("bounded request progress capacity exceeded")
            self.seen.add(r.request_id)
            if first or r.scheduled_tokens>1:
                out.append({"event":"native_request_progress","request_id":r.request_id,
                    "rank":r.rank,"step":r.step,"first_observed":first,
                    "computed_tokens":r.computed_tokens,"scheduled_tokens":r.scheduled_tokens,
                    "scope":"native runner counters; not by itself a PDC acceptance"})
        return tuple(out)
