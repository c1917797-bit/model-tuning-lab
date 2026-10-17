"""Explicit diagnostic first-decode wiring, not a public production installer.

Original native prefill -> actual first decode -> preserved evidence -> stop.
The caller must bind this module in a NEW source and owned32GiB experiment.
No entry may manufacture actual byte ABI/resource/worker proofs from booleans.
"""
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path

import live_adapter as V

ENABLE='DL_FIRST_REAL_DECODE_DIAGNOSTIC_ENABLE'

class DiagnosticStop(RuntimeError):
    pass

def need(v,s):
    if not v:raise V.Refusal(s)

def domain_from_actual_loaded(F,loaded,model_source,cid,rank,namespace_pid,stat,cgroup):
    """No namespace PID is ever substituted for the actual host proof PID."""
    need(type(loaded) is dict and loaded['schema']=='deltalog.actual-all4-loaded/v004'
         and loaded['source']==model_source and len(loaded['rows'])==4,'actual current all4 loaded source')
    rows=loaded['rows'];need({r['rank'] for r in rows}=={0,1,2,3}
        and len({r['actual_host_process']['pid'] for r in rows})==4
        and len({r['namespace_pid'] for r in rows})==4,'distinct actual workers/ranks')
    need(type(rank) is int and rank in range(4) and type(namespace_pid) is int and namespace_pid>0,'actual process/TP rank')
    need(len(cid)==64 and all(c in '0123456789abcdef' for c in cid),'exact actual own CID')
    row=next(r for r in rows if r['rank']==rank);p=row['actual_host_process']
    ticks=int(stat[stat.rfind(')')+2:].split()[19])
    need(row['logical']==rank and row['physical']==rank+4 and row['namespace_pid']==namespace_pid
         and p['physical']==rank+4 and p['namespace_pids'][0]==p['pid']
         and p['namespace_pids'][-1]==namespace_pid and p['start_ticks']==ticks
         and cid in p['cgroup'] and cid in cgroup and p['actual_executable']=='/usr/local/python3.12.13/bin/python3.12',
         'current /proc stat/cgroup, actual host PID/start/NSpid and rank/card join')
    domain=F.Domain(cid,p['pid'],ticks,p['physical'],rank)
    need(domain.valid(),'actual strong pool domain')
    return domain,row

class LazyBinding:
    """Allocate strong binding exactly at first real execute, after weights/KV."""
    def __init__(self,F,reader,legacy,domain_factory,allocation_ref,binding_ref):
        need(type(reader) is V.NativeReader,'actual source-bound reader')
        self.F,self.reader,self.legacy=F,reader,legacy
        self.domain_factory=domain_factory;self.allocation_ref=allocation_ref;self.binding_ref=binding_ref
        self.value=None;self.gateway=None
    def bind(self,r):
        need(self.value is None and self.gateway is not None,'one lazy actual complete pool binding')
        value=V.StaticBinding(self.F,self.reader,self.domain_factory(r),self.allocation_ref,self.binding_ref)
        value.gateway=self.gateway;value.register(r,self.legacy,self.reader.torch);self.value=value
        return value
    def static_overlap_pending(self,*a):
        need(self.value is not None,'all64 strong views before any provisional registration')
        return self.value.static_overlap_pending(*a)

def phase(frame,reader):
    r=frame.runner;ids=tuple(r.input_batch.req_ids);s=frame.scheduler
    need(len(ids)==1 and r.input_batch.req_id_to_index=={ids[0]:0}
         and set(s.num_scheduled_tokens)==set(ids),'one actual C1 request, not dummy')
    q=s.num_scheduled_tokens[ids[0]];computed=reader.small(r.input_batch.num_computed_tokens_cpu_tensor[:1],'cpu')
    need(type(q) is int and computed and type(computed[0]) is int,'actual CPU query/computed integers')
    if (computed[0],q)==(0,2048):return 'native-prefill'
    need((computed[0],q)==(2048,1),'only native2K prefill then actual first decode; no chunking/substitution')
    return 'first-decode'

def wrappers(R,lazy,bridge,get_context,collector):
    """Source-direct native hooks prepared before original M/W install.

    collector is an actual source-owned Collector, not a JSON permission. It
    owns persistent raw/counters and an admitted byte Store, built after runtime
    evidence checks by the separate explicit diagnostic installer.
    """
    from firstdecode_capture import Collector
    need(type(collector) is Collector and collector.lazy is lazy,'same actual source-owned collector')
    execute,prepare,forward=R.execute_model,R._prepare_inputs,R._model_forward
    need(R is lazy.reader.runner_class and all(inspect.getsourcefile(f)==inspect.getsourcefile(R)
        for f in(prepare,forward)),'original direct native prepare/forward methods before hooks')
    from native_entries import execute_entry
    execute_entry(lazy.reader.torch,R,execute,lazy.reader.native_torch_sources)
    V.digest_file(inspect.getsourcefile(R),V.RUNNER_SHA)
    count=[0];state=['await-prefill'];runner=[None]
    @functools.wraps(execute)
    def execute_wrapped(r,scheduler_output,*a,**kw):
        need(V.CURRENT.get() is None and state[0]!='complete','no reentrant/second diagnostic experiment')
        if runner[0] is None:runner[0]=r
        need(runner[0] is r,'one actual runner object')
        count[0]+=1;frame=V.ExecutionFrame(V._SEAL,r,scheduler_output,count[0]);token=V.CURRENT.set(frame)
        try:
            if lazy.value is None:lazy.bind(r)
            return execute(r,scheduler_output,*a,**kw)
        finally:V.CURRENT.reset(token)
    @functools.wraps(prepare)
    def prepare_wrapped(r,*a,**kw):
        f=V.CURRENT.get();need(type(f) is V.ExecutionFrame and f.runner is r and not f.prepared,'actual source native prepare in same execute')
        out=prepare(r,*a,**kw);f.prepared=True;return out
    @functools.wraps(forward)
    def forward_wrapped(r,*a,**kw):
        f=V.CURRENT.get();manager=bridge.manager(r)
        if f is None:
            need(not manager.live and not any(x is not None for x in r.input_batch.req_ids),'native startup dummy only before live requests')
            return forward(r,*a,**kw)
        need(f.runner is r and lazy.value is not None,'same actual complete binding')
        epoch=V.live_epoch(lazy.value,manager,get_context(),lazy.binding_ref)
        kind=phase(f,lazy.reader)
        need((state[0],kind) in(('await-prefill','native-prefill'),('await-decode','first-decode')),'exact two-phase real request')
        if kind=='native-prefill':
            collector.begin(epoch,kind)
            out=forward(r,*a,**kw)
            # Original native chunk/clear/physicalwriteback are checked inside
            # Collector+Lifecycle. No allpool snapshot or candidate arithmetic
            # claim is made on this native history-establishment step.
            collector.end_prefill(epoch,bridge.M)
            state[0]='await-decode';return out
        collector.begin(epoch,kind)
        collector.snapshot_before(epoch)  # one complete actual before, before decoder
        forward(r,*a,**kw)
        summary=epoch.finish(manager,bridge.M)  # original 48 receipt + bytewise inactive
        collector.end_decode(epoch,summary)
        state[0]='complete'
        raise DiagnosticStop('DL_FIRST_DECODE_COMPLETE_OBSERVATION_NOT_MODEL_QUALIFICATION')
    lazy.gateway=forward_wrapped
    return dict(execute=execute_wrapped,prepare=prepare_wrapped,forward=forward_wrapped)

def install_actual(R,F,LC,reader,domain_factory,allocation_ref,binding_ref,collector_factory):
    """Explicit diagnostic entry, requires source-validated evidence upstream.

    It is deliberately not reachable from public install/default plugin. The
    source-bound gate MUST first authenticate actual tiny success, short16/CPU
    component evidence, new owner budget/mount and fixed clock. Native live
    object checks here remain mandatory, not replaced by those JSON receipts.
    """
    need(os.environ.get(ENABLE)=='1','explicit new diagnostic optin')
    V.digest_file(R.__file__,'785a9ae27c98178daa9e9a56071560cec3a2e717a41a968872311093db603316')
    need(not R._STATE and not R._SEEN and R._OP is None,'one cold original runtime before actual register')
    # Official source-proven order, matching actual successful R17 parser.
    from vllm_ascend.utils import enable_custom_op
    import vllm_ascend.ops.gdn as G
    from vllm.v1.worker import mamba_utils
    from vllm_ascend.worker import model_runner_v1 as runner
    from vllm_ascend.ops.triton.fla import chunk
    N=runner.NPUModelRunner
    callbacks=LC.prepared_callbacks(R.M,R.W,R.H,R.L,G,runner,chunk,
        lambda t:t.npu.current_stream().synchronize())
    lazy=LazyBinding(F,reader,R.L,domain_factory,allocation_ref,binding_ref)
    collector=collector_factory(lazy,callbacks['bridge'])
    built=wrappers(N,lazy,callbacks['bridge'],G.get_forward_context,collector)
    changed=V.prepared_mirror_functions(R.M,LC)
    # Mirror compiles in original M globals/contextvars. All other functions
    # retain original bodies/source pins. No generic unwrap or sys.modules reset.
    R.M._SELECTED=lazy;R.M.lifecycle=callbacks['lifecycle']
    R.M.install=changed['install'];R.M.register_layers=changed['register_layers']
    N._update_states=callbacks['update'];N.execute_model=built['execute']
    N._prepare_inputs=built['prepare'];N._model_forward=built['forward']
    G.clear_ssm_states=callbacks['clear'];G.chunk_gated_delta_rule=collector.chunk(callbacks['chunk'])
    R.H.execute_mixed_core=collector.core(callbacks['execute'])
    R._route=collector.route(R._route)
    R.register()  # Original short16 admission, real13arg production DSO+schema
    collector.activate(R)
    need(R._OP is collector.dispatch,'actual production dispatch capture installed')
    return dict(installed=True,diagnostic_first_decode_only=True,public_production_install=False,
        model_qualified=False,lifecycle_reuse_qualified=False,long160_qualified=False,performance_qualified=False,task_qualified=False)

def install(*a,**kw):
    if os.environ.get(ENABLE)!='1':return dict(installed=False,default_OFF=True)
    raise V.Refusal('public installation blocked; only new source-bound owned diagnostic entry may call install_actual')
