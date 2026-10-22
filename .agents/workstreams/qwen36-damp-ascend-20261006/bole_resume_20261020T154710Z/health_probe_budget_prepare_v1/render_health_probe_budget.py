"""Pure narrow health-probe budget delta; no runtime or device execution."""
import hashlib

ORIGINAL_BYTES=6958
ORIGINAL_SHA256='4ddb6f48220423577aaeaf232bb1fb05ecf94d4199bf816d271a81f3b5171b8b'
BEFORE="        value = ctl.h.run(ctl.wrapper(argv), min(4, ctl.remaining(cap=4)))\n"
AFTER=("        health_limit = min(30, end - time.monotonic(), ctl.remaining(cap=30))\n"
       "        C.need(health_limit > 0, 'bounded remaining native startup health budget')\n"
       "        value = ctl.h.run(ctl.wrapper(argv), health_limit)\n")

def need(v,m):
    if not v:raise ValueError(m)

def original(body):
    need(type(body)is bytes and len(body)==ORIGINAL_BYTES and
         hashlib.sha256(body).hexdigest()==ORIGINAL_SHA256,
         'whole actual frozen V6 performance_host input')
    return body

def render(body,*,enable=False):
    original(body);need(type(enable)is bool,'explicit boolean opt-in')
    if not enable:return body
    text=body.decode()
    need(text.count(BEFORE)==1 and AFTER not in text,'one original actual health runner seam')
    result=text.replace(BEFORE,AFTER,1).encode()
    compile(result,'prospective-performance_host.py','exec')
    need(inverse(result)==body,'whole source inverse')
    return result

def inverse(body):
    need(type(body)is bytes,'whole bytes')
    text=body.decode()
    need(text.count(AFTER)==1,'one complete health budget delta')
    restored=text.replace(AFTER,BEFORE,1).encode()
    return original(restored)

if __name__=='__main__':
    import json
    print(json.dumps(dict(enabled=False,source_written=False,NPU=False,commands_executed=False)))
