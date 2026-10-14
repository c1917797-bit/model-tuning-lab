"""Full-denominator bounded-material batches; executor must retain every result."""
def quality_schedule(rows,*,batch_samples=10,repetitions=3):
    if type(batch_samples) is not int or not 1<=batch_samples<=127:
        raise ValueError("bounded batch size required")
    if repetitions!=3 or len(rows)!=127 or [r["index"] for r in rows]!=list(range(127)):
        raise ValueError("full127x3 required")
    if len({r["sample_id"] for r in rows})!=127:raise ValueError("duplicate sample")
    units=[]
    for repetition in range(1,4):
        for start in range(0,127,batch_samples):
            batch=rows[start:start+batch_samples]
            digests=tuple(dict.fromkeys(r["segment"]["tokens_sha256"] for r in batch))
            units.append({"repetition":repetition,"batch":start//batch_samples,
                "sample_indexes":tuple(r["index"] for r in batch),
                "producer_digests":digests,"scored_requests":len(batch)})
    return tuple(units)
