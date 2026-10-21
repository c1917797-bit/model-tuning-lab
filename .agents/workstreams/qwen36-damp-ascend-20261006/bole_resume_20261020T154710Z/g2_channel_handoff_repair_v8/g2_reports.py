"""Durable bounded oracle receipt; raw successful frames cannot be replayed."""
import hashlib
import json
import math
import g2_contract as G2


def summarize(source,manifest,result,error=None):
    maxima={};booleans={}
    def visit(v,path=''):
        if type(v)is dict:
            for k,w in sorted(v.items()):visit(w,path+'/'+str(k))
        elif type(v)in(list,tuple):
            for w in v:visit(w,path+'/*')
        elif type(v)is bool:booleans[path]=booleans.get(path,True)and v
        elif type(v)is float:
            if not math.isfinite(v):raise ValueError('finite actual oracle result')
            maxima[path]=max(maxima.get(path,0.),abs(v))
    visit(result)
    canonical=json.dumps(result,sort_keys=True,allow_nan=False).encode()
    value=dict(schema='bole.actual-independent-frame-report/v2',source=source,
        raw=manifest['raw'],coverage=manifest['coverage'],kind=manifest['kind'],
        passed=error is None,primary=None if error is None else repr(error),
        full_oracle_result_sha256=hashlib.sha256(canonical).hexdigest(),
        numeric_absolute_maxima=maxima,boolean_conjunctions=booleans,
        bound_sources=dict(GDN='independent_model.old112:2e-5+2e-4*maxabs and relative_l2<=2e-4',
            conv='all elements abs_error<=.001+.01*abs(reference); all3 tails bitwise',
            FA='all elements abs_error<=.001+.01*abs(reference); FP64 and FP32'),
        successful_raw_replay_available=False,timing_is_formal=False)
    if len((json.dumps(value,sort_keys=True)+'\n').encode())>G2.REPORT_CAP:
        raise ValueError('complete audited compact numerical report bound')
    return value
