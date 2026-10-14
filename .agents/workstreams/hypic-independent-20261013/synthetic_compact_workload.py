"""Deterministic synthetic token workload; recipes keep large arrays out of Git."""
def public_tokens_from_recipe(recipe):
    start=recipe['start'];length=recipe['length']
    if type(start) is not int or type(length) is not int or start<0 or not 8<length<=32768:
        raise ValueError('invalid public token recipe')
    return list(range(start,start+length))


def expand_payloads(specs,recipe):
    public=public_tokens_from_recipe(recipe);payloads=[]
    for spec in specs:
        if spec['kind']=='public':tokens=public
        elif spec['kind']=='private':
            offset=spec['relocation'];total=spec['input_tokens'];tail=total-offset-len(public)
            if type(offset) is not int or not 1024<=offset<=7168 or tail<=0:
                raise ValueError('invalid private relocation/suffix')
            prefix=list(range(20000,20000+offset));suffix=list(range(30000,30000+tail))
            if set(public).intersection(prefix+suffix):raise ValueError('synthetic segment identity ambiguous')
            tokens=prefix+public+suffix
        else:raise ValueError('unknown synthetic request kind')
        cap=spec['max_tokens']
        if type(cap) is not int or not 1<=cap<=2048:raise ValueError('invalid output token cap')
        payloads.append({'model':'qwen3.5','prompt':tokens,'temperature':0,'seed':0,
                         'max_tokens':cap,'ignore_eos':True})
    return payloads
