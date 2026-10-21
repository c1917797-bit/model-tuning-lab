"""Opt-in observers for exact native scheduler/frontend/worker objects.
Original functions execute exactly once. No sampling/cache/counter edits, tensors,
model dispatch, device calls, generated code or API requests originate here.
"""
import inspect
import types
import os
from pathlib import Path
import sys
import time
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C


def process():
    p=Path('/proc/self');text=(p/'stat').read_text();f=text[text.rfind(')')+2:].split()
    return dict(pid=os.getpid(),start_ticks=int(f[19]),uid=os.getuid(),cgroup=(p/'cgroup').read_text(),
                argv=[s.decode()for s in(p/'cmdline').read_bytes().split(b'\0')if s],executable=os.readlink(p/'exe'))


def guard(call,reference,qualname):
    f=getattr(call,'__func__',call);path=C.checked(reference)
    C.need(inspect.isfunction(f)and f.__qualname__==qualname and Path(f.__code__.co_filename)==path
           and Path(inspect.getsourcefile(f))==path,'exact actual original native callable '+qualname)
    # Compile whole pinned source without executing its imports. Compare the
    # actual loaded function code with its precise original code object.
    whole=compile(path.read_bytes(),str(path),'exec');found=[]
    def walk(code):
        if code.co_qualname==qualname:found.append(code)
        for value in code.co_consts:
            if isinstance(value,types.CodeType):walk(value)
    walk(whole)
    C.need(len(found)==1 and f.__code__==found[0],'actual loaded native code equals exact pinned source '+qualname)
    C.need(f.__defaults__==((False,)if qualname=='Scheduler._free_request'else None)
           and not f.__kwdefaults__,'unchanged native callable defaults '+qualname)
    return f


def class_guard(cls,reference,name):
    C.need(isinstance(cls,type) and cls.__name__==name and Path(inspect.getfile(cls))==C.checked(reference),'exact actual native class '+name)


def ids(value):
    out=list(value);C.need(len(out)<=5199 and all(type(v)is int and 0<=v<248320 for v in out),'bounded actual CPU token-ID list');return out


def params(p):
    return dict(ignore_eos=p.ignore_eos,eos_token_id=p.eos_token_id,stop_token_ids=sorted(p.stop_token_ids or()),
        all_stop_token_ids=sorted(p.all_stop_token_ids),stop=list(p.stop or()),min_tokens=p.min_tokens,max_tokens=p.max_tokens,
        temperature=p.temperature,top_p=p.top_p,seed=p.seed,n=p.n,output_kind=str(p.output_kind),
        repetition_detection=None if p.repetition_detection is None else 'ENABLED',
        presence_penalty=p.presence_penalty,frequency_penalty=p.frequency_penalty,repetition_penalty=p.repetition_penalty)


def request_snapshot(r,full=False):
    v=dict(request_id=r.request_id,object_id=id(r),status=r.status.name,stop_reason=r.stop_reason,
        num_output_tokens=r.num_output_tokens,num_tokens=r.num_tokens,request_max_tokens=r.max_tokens,
        pooling=bool(r.pooling_params),resumable=r.resumable,prompt_embeds=r.prompt_embeds is not None,
        parameters=params(r.sampling_params))
    if r.num_output_tokens:v['last_token_id']=r.output_token_ids[-1]
    if full:v.update(prompt_token_ids=ids(r.prompt_token_ids),output_token_ids=ids(r.output_token_ids),all_token_ids=ids(r.all_token_ids))
    return v


class Journal:
    def __init__(self,source_ref,role,out):
        C.need(os.environ.get('BOLE_TASK_FINISH_OBSERVER_ENABLE')=='1','MAIN explicit native finish observer opt-in')
        self.m=C.source(source_ref);self.source_ref=source_ref;self.role=role;self.process=process();self.count=0;self.bytes=0
        C.need(role in{'scheduler','frontend','worker0','worker1','worker2','worker3'}and out.is_absolute()and out.is_dir(),'exact bounded observer role/new existing owned output')
        self.path=out/(role+'-'+str(self.process['pid'])+'-'+str(self.process['start_ticks'])+'.jsonl')
        self.file=self.path.open('xb');self.closed=False
        self.emit('header',dict(source_ref=source_ref,role=role,process=self.process,native_sources=self.m['native_sources']))

    def emit(self,event,payload):
        C.need(not self.closed and self.count<128,'bounded smoke journal event count')
        raw=C.canonical(dict(schema='bole.actual-native-finish-event/v1',ordinal=self.count,event=event,
            monotonic_ns=time.monotonic_ns(),payload=payload))+b'\n'
        C.need(len(raw)<=2**20 and self.bytes+len(raw)<=16*2**20,'bounded full primitive journal, no silent truncation')
        self.file.write(raw);self.file.flush();os.fsync(self.file.fileno());self.bytes+=len(raw);self.count+=1

    def close(self):
        C.need(not self.closed,'single observer freeze')
        for r in self.m['native_sources'].values():C.checked(r)
        C.need(process()==self.process,'same actual process lifetime/argv/source at observer freeze')
        self.emit('closed',dict(native_source_unchanged=True,process=self.process));self.file.close();self.closed=True
        r=C.ref(self.path);C.write(self.path.with_suffix('.REF.json'),r);return r


class Hooks:
    def __init__(self,journal):self.journal=journal;self.restorations=[]

    def set(self,obj,name,new):
        exists=name in vars(obj);old=vars(obj).get(name);previous=getattr(obj,name)
        setattr(obj,name,new);self.restorations.append((obj,name,exists,old,new));return previous

    def restore(self):
        for obj,name,exists,old,new in reversed(self.restorations):
            C.need(vars(obj).get(name)is new,'observer hook inverse still owns exact installed object')
            if exists:setattr(obj,name,old)
            else:delattr(obj,name)
        self.restorations=[]

    def close(self):
        self.restore()
        return C.ref(self.journal.path)if getattr(self.journal,'closed',False)else self.journal.close()


def install_scheduler(scheduler,journal):
    C.need(journal.role=='scheduler','actual scheduler role')
    s=journal.m['native_sources'];class_guard(type(scheduler),s['scheduler'],'Scheduler')
    C.need(scheduler.parallel_config.tensor_parallel_size==4 and scheduler.parallel_config.pipeline_parallel_size==1 and scheduler.parallel_config.data_parallel_size==1
        and scheduler.scheduler_config.max_num_seqs==1 and scheduler.scheduler_config.async_scheduling is False and scheduler.connector is None,'actual single-sequence TP4 sync native scheduler without delayed KV transfer')
    h=Hooks(journal);old_update=scheduler._update_request_with_output;old_free=scheduler._free_request
    old_blocks=scheduler._free_blocks;old_engine=scheduler.update_from_output;manager=scheduler.kv_cache_manager;old_kv=manager.free
    for f,n in((old_update,'_update_request_with_output'),(old_free,'_free_request'),(old_blocks,'_free_blocks'),(old_engine,'update_from_output')):
        guard(f,s['scheduler'],'Scheduler.'+n)
    guard(old_kv,s['kv_cache_manager'],'KVCacheManager.free');class_guard(type(manager),s['kv_cache_manager'],'KVCacheManager')
    module=sys.modules[type(scheduler).__module__];old_stop=module.check_stop;guard(old_stop,s['sched_utils'],'check_stop')
    native_status=old_stop.__globals__['RequestStatus'];class_guard(native_status,s['request'],'RequestStatus')
    active=[];terminal={};strong={};engine_count=[0]
    def check_stop(request,max_model_len):
        if journal.closed:return old_stop(request,max_model_len)
        C.need(len(active)==1 and active[0]is request and max_model_len==scheduler.max_model_len,'actual current native check_stop request link')
        before=request_snapshot(request);returned=old_stop(request,max_model_len)
        if returned:
            after=request_snapshot(request,True);rid=request.request_id;C.need(rid not in terminal,'one actual terminal stop per request')
            terminal[rid]=after;strong[rid]=request
            journal.emit('check_stop',dict(before=before,after=after,max_model_len=max_model_len,returned=returned))
        return returned
    def update(self,request,new_token_ids):
        if journal.closed:return old_update(request,new_token_ids)
        C.need(self is scheduler and not active,'same actual scheduler/nonrecursive native update')
        class_guard(type(request),s['request'],'Request');raw=ids(new_token_ids);before=request.num_output_tokens
        active.append(request)
        try:returned=old_update(request,new_token_ids)
        finally:active.pop()
        if returned[1]:journal.emit('terminal_update',dict(request_id=request.request_id,object_id=id(request),before_output_count=before,
            proposed_token_ids=raw,returned_token_ids=ids(returned[0]),stopped=returned[1],native_list_after=ids(new_token_ids)))
        return returned
    def kv(self,request):
        if journal.closed:return old_kv(request)
        C.need(self is manager and strong.get(request.request_id)is request,'actual original KV.free request link')
        returned=old_kv(request)
        journal.emit('kv_free',dict(request_id=request.request_id,object_id=id(request),manager_object_id=id(manager),
            coordinator_object_id=id(manager.coordinator),original_returned_None=returned is None,allocator_internal_state_observed=False))
        return returned
    def blocks(self,request):
        if journal.closed:return old_blocks(request)
        rid=request.request_id;C.need(self is scheduler and strong.get(rid)is request and self.requests.get(rid)is request,'actual current request before original block free')
        returned=old_blocks(request)
        journal.emit('free_blocks',dict(request_id=rid,object_id=id(request),present_before=True,present_after=rid in self.requests))
        return returned
    def free(self,request,*args,**kwargs):
        if journal.closed:return old_free(request,*args,**kwargs)
        rid=request.request_id;C.need(self is scheduler and strong.get(rid)is request,'actual same terminal request before free')
        returned=old_free(request,*args,**kwargs)
        journal.emit('free_request',dict(request_id=rid,object_id=id(request),finished_req_id_after=rid in self.finished_req_ids,
            request_present_after=rid in self.requests,encoder_manager_object_id=id(self.encoder_cache_manager)))
        strong.pop(rid);return returned
    def engine(self,*args,**kwargs):
        if journal.closed:return old_engine(*args,**kwargs)
        C.need(self is scheduler,'same actual scheduler engine result');returned=old_engine(*args,**kwargs)
        for client,output in returned.items():
            for e in output.outputs:
                if e.finish_reason is not None:
                    C.need(e.request_id in terminal,'engine terminal joins actual native stop')
                    journal.emit('engine_output',dict(request_id=e.request_id,client_index=client,new_token_ids=ids(e.new_token_ids),
                        finish_reason=str(e.finish_reason),stop_reason=e.stop_reason))
                    engine_count[0]+=1
        if engine_count[0]==7:journal.close()
        return returned
    h.set(module,'check_stop',check_stop);h.set(scheduler,'_update_request_with_output',types.MethodType(update,scheduler))
    h.set(manager,'free',types.MethodType(kv,manager));h.set(scheduler,'_free_blocks',types.MethodType(blocks,scheduler))
    h.set(scheduler,'_free_request',types.MethodType(free,scheduler));h.set(scheduler,'update_from_output',types.MethodType(engine,scheduler))
    journal.emit('installed',dict(actual_scheduler_object_id=id(scheduler),actual_manager_object_id=id(manager),
        max_model_len=scheduler.max_model_len,max_num_seqs=scheduler.scheduler_config.max_num_seqs,async_scheduling=scheduler.scheduler_config.async_scheduling,TP=4,PP=1,DP=1))
    return h


def install_frontend(request_state_class,journal):
    C.need(journal.role=='frontend','actual frontend role');s=journal.m['native_sources'];h=Hooks(journal)
    class_guard(request_state_class,s['output_processor'],'RequestState');old=request_state_class._new_completion_output
    guard(old,s['output_processor'],'RequestState._new_completion_output');finished_count=[0]
    def completion(self,token_ids,finish_reason,stop_reason):
        if journal.closed:return old(self,token_ids,finish_reason,stop_reason)
        returned=old(self,token_ids,finish_reason,stop_reason)
        if finish_reason is not None:
            C.need(type(self)is request_state_class and self.parent_req is None and self.request_index==0,'actual single native request state')
            journal.emit('frontend_output',dict(request_id=self.request_id,external_req_id=self.external_req_id,object_id=id(self),
                prompt_token_ids=ids(self.prompt_token_ids),output_kind=str(self.output_kind),max_tokens_param=self.max_tokens_param,
                output_token_ids=ids(returned.token_ids),text=returned.text,finish_reason=returned.finish_reason,stop_reason=returned.stop_reason,
                input_finish_reason=str(finish_reason),input_stop_reason=stop_reason))
            finished_count[0]+=1
            if finished_count[0]==7:journal.close()
        return returned
    h.set(request_state_class,'_new_completion_output',completion);journal.emit('installed',dict(actual_request_state_class_object_id=id(request_state_class)))
    return h


def install_worker(worker,journal):
    s=journal.m['native_sources'];class_guard(type(worker),s['worker'],'NPUWorker')
    C.need(worker.model_runner is not None and worker.rank==worker.parallel_config.rank
        and worker.parallel_config.tensor_parallel_size==4 and worker.parallel_config.pipeline_parallel_size==1
        and worker.parallel_config.data_parallel_size==1 and journal.role=='worker'+str(worker.rank),'actual TP4/PP1/DP1 worker rank owner')
    runner=worker.model_runner;class_guard(type(runner),s['runner'],'NPUModelRunner')
    class_guard(type(runner.input_batch),s['npu_input_batch'],'NPUInputBatch')
    guard(super(type(runner),runner)._update_states,s['base_runner'],'GPUModelRunner._update_states')
    guard(runner.input_batch.remove_request,s['gpu_input_batch'],'InputBatch.remove_request')
    old=runner._update_states;guard(old,s['runner'],'NPUModelRunner._update_states');h=Hooks(journal);retired_count=[0]
    def update(self,scheduler_output):
        if journal.closed:return old(scheduler_output)
        C.need(worker.model_runner is self is runner,'same native runner owner throughout retirement')
        finished=tuple(sorted(scheduler_output.finished_req_ids));snap=[];held=[]
        for rid in finished:
            request=self.requests.get(rid);held.append(request)
            snap.append(dict(request_id=rid,object_id=None if request is None else id(request),present_before=request is not None,
                batch_index_before=self.input_batch.req_id_to_index.get(rid),prompt_token_ids=None if request is None else ids(request.prompt_token_ids)))
        returned=old(scheduler_output)
        for row,request in zip(snap,held):
            rid=row['request_id'];journal.emit('worker_retired',dict(**row,rank=worker.rank,worker_object_id=id(worker),runner_object_id=id(runner),
                scheduler_finished_req_ids=list(finished),present_after=rid in self.requests,batch_present_after=rid in self.input_batch.req_id_to_index))
            retired_count[0]+=1
        if retired_count[0]>=6:journal.close()
        return returned
    h.set(runner,'_update_states',types.MethodType(update,runner));journal.emit('installed',dict(rank=worker.rank,local_rank=worker.local_rank,
        worker_object_id=id(worker),runner_object_id=id(runner),TP=4,PP=1,DP=1))
    return h


if __name__=='__main__':
    import argparse
    argparse.ArgumentParser(description='Default OFF; installation is explicit on actual supported native objects.',allow_abbrev=False).parse_args()
    print('{"enabled":false,"observer_installed":false,"NPU_dispatch":false}')
