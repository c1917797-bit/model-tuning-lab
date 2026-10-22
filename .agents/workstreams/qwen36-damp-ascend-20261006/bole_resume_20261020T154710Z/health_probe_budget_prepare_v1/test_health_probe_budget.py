"""Actual startup-loop AST and actual runner negative controls; no Docker/NPU."""
from pathlib import Path
import ast
from datetime import datetime,timezone
import hashlib
import json
import subprocess
import sys
import types
HERE=Path(__file__).resolve().parent
WS=HERE.parent
sys.path.insert(0,str(HERE))
import render_health_probe_budget as R
PERF=WS/'bound-reduction-ON-v6-common_20261022T210000Z/performance_host.py'
RUNNER=WS.parents[3]/'projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py'
PRODUCTION_DELTA=WS/'reduction_probe_prepare_v7_startup_20261022T215000Z/ON/boundary_delta.py'

def need(v,m):
    if not v:raise ValueError(m)

def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def loop_code(body):
    tree=ast.parse(body)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
    matches=[i for i,n in enumerate(fn.body)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='end'for x in n.targets)]
    index=matches[0]
    need(isinstance(fn.body[index+1],ast.While),'actual original adjacent startup loop')
    return compile(ast.Module(body=fn.body[index:index+2],type_ignores=[]),'actual-performance_host-startup-loop','exec')

class Clock:
    def __init__(self):self.now=0.
    def monotonic(self):return self.now
    def time_ns(self):return int(self.now*1e9)
    def sleep(self,n):self.now+=n

def exercise(body,*,phase=1000,observe=0,delay=0,statuses=(0,),server_exit=False,timeout=False):
    clock=Clock();calls=[];writes=[];stats=dict(inflight=0,max_inflight=0,observations=0)
    def remaining(cap):
        value=phase-clock.now
        need(value>0,'actual phase/cleanup remaining exhausted')
        return min(cap,value)
    def poll():return 17 if server_exit else None
    def observed(label):
        stats['observations']+=1;clock.now+=observe
    def run(argv,budget):
        need(0<budget<=30 and budget<=phase-clock.now and clock.now+budget<=min(900,phase),'budget within original phase and900')
        calls.append(budget);stats['inflight']+=1;stats['max_inflight']=max(stats['max_inflight'],stats['inflight'])
        if timeout:
            # No retry after this unknown guest termination: same real exception.
            raise subprocess.TimeoutExpired(argv,budget,output=b'partial\xff',stderr=b'error')
        need(delay<=budget,'fake runner completion fits request')
        clock.now+=delay
        stats['inflight']-=1
        index=min(len(calls)-1,len(statuses)-1)
        return dict(exit_code=statuses[index],stdout='',stderr='',argv=argv)
    ctl=types.SimpleNamespace(server=types.SimpleNamespace(poll=poll),remaining=remaining,
        observe=observed,h=types.SimpleNamespace(run=run),wrapper=lambda x:x,cid='owned-CID',out=Path('/never-written'))
    scope=dict(time=clock,C=types.SimpleNamespace(need=need),ctl=ctl,
        c=types.SimpleNamespace(docker_argv=lambda cid,args:['never-executed-docker','exec',cid,*args],
            write=lambda path,value:writes.append((str(path),value))))
    error=None
    try:exec(loop_code(body),scope)
    except BaseException as e:error=e
    return dict(error=error,calls=calls,writes=writes,clock=clock,stats=stats)

def main():
    old=PERF.read_bytes();cases=[]
    candidates=[n for n in ast.walk(ast.parse(PRODUCTION_DELTA.read_bytes()))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='once'
        and len(n.args)==3 and isinstance(n.args[1],ast.Constant) and n.args[1].value==R.BEFORE]
    need(len(candidates)==1 and ast.literal_eval(candidates[0].args[2])==R.AFTER,
         'actual V7 boundary_delta exact canonical health seam')
    new=R.render(old,enable=True)
    cases.append('actual_V7_delta_AST_exactly_matches_tested_fragment')
    need(R.render(old)==old and R.inverse(new)==old,'whole exact defaultOFF/inverse')
    need(new.count(b'timeout=2')==old.count(b'timeout=2') and b'min(900, ctl.remaining(cap=900))'in new,'inner2/startup900 retained')
    tree=ast.parse(new);need(not any(isinstance(n,ast.ExceptHandler)for n in ast.walk(tree)),'no catch or retry-on-unknown-timeout introduced')
    cases.append('actual_whole_source_defaultOFF_inverse_no_catch_urllib2_startup900')
    a=exercise(new,delay=5,statuses=(1,0))
    need(a['error']is None and a['calls']==[30,30]and len(a['writes'])==2 and a['stats']['max_inflight']==1,'completed nonzero only may loop;5s overhead no longer false4s fail')
    cases.append('completed_nonzero_then_health_success_serial_30s_budget')
    a=exercise(new,phase=8,observe=2,delay=1)
    need(a['error']is None and a['calls']==[6],'phase bound smaller than30')
    cases.append('phase_remaining_clamps_30_without_extension')
    a=exercise(new,phase=1000,observe=899,delay=1,statuses=(1,))
    need(isinstance(a['error'],ValueError)and a['calls']==[1]and a['clock'].now>=900,'startup900 expires before another probe')
    cases.append('original_startup900_exhaustion_fails_without_second_probe')
    a=exercise(new,server_exit=True)
    need(isinstance(a['error'],ValueError)and not a['calls'],'server exit fails before probe')
    cases.append('real_loop_server_exit_negative_control')
    a=exercise(new,phase=8,observe=9)
    need(isinstance(a['error'],ValueError)and not a['calls'],'observation exhausted total budget; no negative-timeout launch')
    cases.append('observe_exhausts_phase_no_probe_or_budget_reset')
    a=exercise(new,timeout=True)
    need(isinstance(a['error'],subprocess.TimeoutExpired)and len(a['calls'])==1 and not a['writes'],'unknown timeout propagates no overlap or false124 receipt')
    cases.append('TimeoutExpired_propagates_no_retry_unknown_guest')
    # Execute only actual original function AST, using a harmless bounded local
    # Python child. No original CLI/main/import bootstrap is invoked.
    raw=RUNNER.read_bytes()
    need(len(raw)==16517 and hashlib.sha256(raw).hexdigest()=='86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc','whole actual runner pin')
    fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)and n.name=='run')
    env=dict(subprocess=subprocess,datetime=datetime,timezone=timezone)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-host_run.run','exec'),env)
    try:
        env['run']([sys.executable,'-I','-B','-c',"import sys,time;print('partial',flush=True);print('err',file=sys.stderr,flush=True);time.sleep(.5)"],.2)
    except subprocess.TimeoutExpired as e:
        need(e.timeout==.2 and isinstance(e.output,(bytes,type(None))) and isinstance(e.stderr,(bytes,type(None))),'real runner text=True timeout partial may be bytes')
        actual=dict(error_type=type(e).__name__,timeout=e.timeout,
            stdout_hex=None if e.output is None else e.output.hex(),
            stderr_hex=None if e.stderr is None else e.stderr.hex(),unknown_guest_retry_permitted=False)
    else:raise AssertionError('real original runner swallowed timeout')
    cases.append('actual_original_runner_local_TimeoutExpired_bytes_propagation')
    print(json.dumps(dict(schema='bole.bounded-startup-health-budget-controls/v1',status='PASS',
        cases=cases,case_count=len(cases),source=ref(PERF),runner=ref(RUNNER),production_delta=ref(PRODUCTION_DELTA),
        prospective=dict(bytes=len(new),sha256=hashlib.sha256(new).hexdigest()),
        actual_runner_timeout=actual,NPU=False,Docker=False,frozen_source_changed=False,
        phase3600_unchanged=True,cleanup180_unchanged=True,startup900_unchanged=True),sort_keys=True))

if __name__=='__main__':main()
