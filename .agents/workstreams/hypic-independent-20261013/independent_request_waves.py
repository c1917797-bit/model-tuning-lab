"""Bounded preregistered request waves; overlap is verified by worker ledger."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import time

def validate_waves(waves,count):
    waves=tuple(tuple(w) for w in waves)
    flat=tuple(i for w in waves for i in w)
    if not waves or any(not w or len(w)>16 for w in waves):
        raise ValueError('nonempty bounded request waves required')
    if any(type(i) is not int for i in flat) or sorted(flat)!=list(range(count)):
        raise ValueError('request waves must cover each payload exactly once')
    return waves

def execute_waves(payloads,waves,send,*,check_guard,start_delays=None):
    payloads=tuple(payloads);waves=validate_waves(waves,len(payloads))
    delays={} if start_delays is None else dict(start_delays)
    if any(type(k) is not int or k<0 or k>=len(payloads) or
           type(v) not in (int,float) or not 0<=v<=5 for k,v in delays.items()):
        raise ValueError('bounded explicit request start delays required')
    def invoke(i):
        delay=delays.get(i,0)
        if delay:time.sleep(delay)
        check_guard()
        start=time.monotonic()
        response=send(payloads[i])
        return {'index':i,'payload':payloads[i],'response':response,
                'client_start_monotonic':start,'client_end_monotonic':time.monotonic()}
    for wave in waves:
        check_guard()
        with ThreadPoolExecutor(max_workers=len(wave)) as pool:
            futures=[pool.submit(invoke,i) for i in wave]
            for future in as_completed(futures):
                record=future.result()
                check_guard()
                yield record
