"""Stdlib metadata fixtures for actual T, not T16 padding or a fake slot."""
from contract import require

def metadata_cases(batch, slots):
    require(type(batch) is int and 1<=batch<=16 and slots==batch+3,"real T1..16 and T+3 slots")
    lens=[0]+[1]*batch
    ids=list(range(batch))
    rows=[]
    def add(name, ls=None, ix=None):
        rows.append((name,list(lens if ls is None else ls),list(ids if ix is None else ix)))
    for value in (1,-1):
        altered=list(lens);altered[0]=value
        add("prefix_"+str(value),ls=altered)
    for value in (0,2,-1):
        altered=list(lens);altered[-1]=value
        add("last_length_"+str(value),ls=altered)
    for value in (-1,slots,2147483647,-2147483648):
        altered=list(ids);altered[-1]=value
        add("last_index_"+str(value),ix=altered)
    if batch>1:
        altered=list(ids);altered[-1]=altered[0]
        add("duplicate_slots",ix=altered)
        altered=list(lens);altered[-1]=batch
        add("cumulative_lengths_not_one_token",ls=altered)
    # Metadata copies round to8. Exercise BOTH active sides of7/8 where present.
    # Tail already has three cases above; no inactive/padding token is invented.
    for token in (0,7,8):
        if token>=batch or token==batch-1:continue
        for value in (0,2,-1):
            altered=list(lens);altered[token+1]=value
            add("active_token_"+str(token)+"_length_"+str(value),ls=altered)
    return rows

def metadata_valid(lengths,indices,slots):
    # Independent host mathematical predicate, NOT a replacement for NPU validation.
    return (bool(lengths) and lengths[0]==0 and all(x==1 for x in lengths[1:]) and
            len(lengths)==len(indices)+1 and all(0<=x<slots for x in indices) and
            len(set(indices))==len(indices))

def copy_bounds(batch):
    require(type(batch) is int and 1<=batch<=16,"real T")
    return {"indices_copied_int32":((batch+7)//8)*8,
            "lengths_copied_int32":((batch+8)//8)*8,
            "lengths_offset_int32":16,"last_local_int32_exclusive":16+((batch+8)//8)*8,
            "device_metadata_capacity_int32":40,"tokens":batch,"tasks":12*batch}
