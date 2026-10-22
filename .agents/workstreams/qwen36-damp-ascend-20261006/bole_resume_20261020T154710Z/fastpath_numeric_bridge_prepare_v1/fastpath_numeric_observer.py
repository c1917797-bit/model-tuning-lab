"""Qualification-only readonly taps around actual FAST math/publication. Default OFF."""
import dataclasses
import inspect
import os

FLAG='BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE'
SCHEMA='bole.actual-fastpath-frame-numeric-capture/v1'


def need(v,s):
    if not v:raise ValueError(s)


def clone(t,x):
    if isinstance(x,t.Tensor):return x.detach().clone()
    if x is None or type(x)in(str,int,float,bool):return x
    if type(x)in(tuple,list):return [clone(t,v)for v in x]
    if type(x)is dict:return {k:clone(t,v)for k,v in x.items()if k not in('arena','slot_binding')}
    if dataclasses.is_dataclass(x):return {f.name:clone(t,getattr(x,f.name))for f in dataclasses.fields(x)}
    raise TypeError('opaque qualification capture: '+type(x).__name__)


class Observer:
    def __init__(self,t,C,source,m,rank,*,snapshot,sink):
        need(os.environ.get(FLAG)=='1','qualification producer default OFF')
        p=m['fastpath_numeric_qualification']
        need(p==dict(schema='bole.fastpath-numeric-qualification-profile/v1',enabled=True,
              input_tokens=131,output_tokens=p['output_tokens'],generations=2,
              logical_frame_cap=384*2**20,independent_reference=True,formal_performance=False) and
              type(p['output_tokens'])is int and p['output_tokens']in(8,160,1024),
              'explicit source-bound smoke/long qualification domain, not performance')
        need(C.ref(__file__)==m['files']['fastpath_numeric_observer.py'] and
             C.ref(inspect.getsourcefile(snapshot))==m['files']['service_runner.py'] and
             C.ref(inspect.getsourcefile(sink))==m['files']['fastpath_numeric_sink.py'],
             'actual source-bound observer, original snapshot and reviewed bounded sink')
        need(type(rank)is int and 0<=rank<4,'actual TP4 rank')
        need(os.environ.get('HCCL_DETERMINISTIC')=='true','same actual production deterministic HCCL policy')
        self.t=t;self.C=C;self.source=source;self.m=m;self.rank=rank
        self.snapshot=snapshot;self.sink=sink;self.current=None;self.ordinal={1:0,2:0}
        self.receipts=[];self.used=0

    def _capture(self,value):
        def size(x):
            if isinstance(x,self.t.Tensor):return x.numel()*x.element_size()
            if x is None or type(x)in(str,int,float,bool):return 0
            if type(x)in(tuple,list):return sum(size(v)for v in x)
            if type(x)is dict:return sum(size(v)for k,v in x.items()if k not in('arena','slot_binding'))
            if dataclasses.is_dataclass(x):return sum(size(getattr(x,f.name))for f in dataclasses.fields(x))
            raise TypeError('unbounded opaque qualification object')
        count=size(value);need(self.used+count<=384*2**20,'qualification clone budget before allocation')
        self.used+=count;return clone(self.t,value)

    def _snapshot(self,bridge,owner):
        count=0
        for b in bridge.bindings:
            if b['kind']=='gdn':
                slot=bridge._physical_slot(b,owner)
                tensors=(b['state'][slot],b['conv_arena'][slot:slot+1])
            else:
                tensors=(b['key'][:len(b['table'])],b['value'][:len(b['table'])])
            count+=sum(x.numel()*x.element_size()for x in tensors)
        need(self.used+count<=384*2**20,'actual snapshot budget before native clone')
        self.used+=count;return self.snapshot(self.t,bridge,owner)

    def before_layer(self,bridge,b):
        ctx=__import__('model_entry').BUS.get();need(ctx is not None,'real active target context')
        if self.current is None:
            need(b['index']==0 and ctx.owner.generation in(1,2),'start at actual first target layer')
            self.used=0;before=self._snapshot(bridge,ctx.owner)
            self.current=dict(owner=clone(self.t,ctx.owner),before_GDN=before[0],before_FA=before[1],
                captures={},order=[])
        need(self.current['owner']==clone(self.t,ctx.owner) and
             b['index']==len(self.current['order']),'same true frame owner/all64 ordered layers')
        self.current['order'].append(b['index'])

    def conv(self,b,trial,weight,bias,activation,convolved,tail):
        need(self.current is not None and b['kind']=='gdn'and bias is None,'actual qualified conv inputs/no omitted bias')
        self.current['captures'][b['index']]=self._capture(dict(kind='gdn',conv_trial=trial,
            raw_projected=trial.inputs,weight=weight,conv_bias_is_none=True,
            activation=activation,actual_convolved=convolved,actual_conv_tail=tail))

    def gdn(self,b,q,k,v,beta,gamma,state,value,factors,output):
        row=self.current['captures'][b['index']]
        need(row['kind']=='gdn','actual native convolution precedes actual GDN')
        need(all(isinstance(x,self.t.Tensor)and x.device.type=='npu'for x in(q,k,v,beta,gamma,state,value,output)),
             'actual captured NPU operands and outputs, never CPU fixtures')
        row.update(self._capture(dict(state=state,keys=k,normalized_inputs=(q,k,v,beta,gamma),
                                   precast_output=value,factors=factors,output=output)))

    def fa(self,b,query,key,value,output,physical_pages,cache_identities):
        need(self.current is not None and b['kind']=='fa','actual FA layer event')
        need(all(isinstance(x,self.t.Tensor)and x.device.type=='npu'for x in(query,key,value,output)),
             'actual native NPU FA operands and return')
        self.current['captures'][b['index']]=self._capture(dict(kind='fa',query=query,key=key,value=value,
            output=output,actual_physical_pages=physical_pages,actual_cache_identities=cache_identities))

    def publication(self,bridge,proposal,result):
        f=self.current
        need(f is not None and f['order']==list(range(64)) and set(f['captures'])==set(range(64)) and
             f['owner']==clone(self.t,proposal['owner']) and result['cache_published']is True and
             result['diagnostic_readback_performed']is False and result['actual_applied']==[],
             'actual FAST completed all64; original readback/clones remain elided')
        after=self._snapshot(bridge,proposal['owner']);applied=[]
        for row in proposal['writes']:
            arena=row['arena']
            actual=arena[row['slot']]if row['kind']in('conv','state')else arena[row['indices']//128,row['indices']%128]
            need(actual.device.type=='npu','actual permanent NPU destination')
            applied.append(self._capture(actual))
        generation=f['owner']['generation'];ordinal=self.ordinal[generation]
        f.update(schema=SCHEMA,source=self.source,rank=self.rank,generation=generation,ordinal=ordinal,
            after_GDN=after[0],after_FA=after[1],staged=self._capture(proposal),
            publication=self._capture(result),observed_applied=applied,
            actual_FAST_readback_elided=True,qualification_observer=True,
            formal_performance=False,numerical_qualified=False)
        f['runtime_execution']=dict(environment={k:os.environ.get(k)for k in
            ('HCCL_DETERMINISTIC','HCCL_ALGO','ASCEND_LAUNCH_BLOCKING')},
            torch_deterministic_enabled=self.t.are_deterministic_algorithms_enabled(),
            torch_deterministic_warn_only=self.t.is_deterministic_algorithms_warn_only_enabled())
        # A bounded original stream adapter must synchronously export/consume
        # this one frame and return its exact actual independent-consumer ACK.
        # No accumulating frame list or background/unowned worker is allowed.
        proof=self.sink(f)
        need(type(proof)is dict and proof.get('schema')=='bole.actual-fastpath-numeric-frame-ack/v1'and
             proof.get('source')==self.source and proof.get('rank')==self.rank and
             proof.get('generation')==generation and proof.get('ordinal')==ordinal and
             proof.get('frame_checks_passed')is True and proof.get('formal_performance')is False,
             'actual independent numeric consumer acknowledged this complete frame')
        self.C.checked(proof['report']);report=self.C.obj(proof['report'])
        need(all(report[k]==proof[k]for k in('schema','source','rank','generation','ordinal','frame_checks_passed')),
             'actual reopened independent numeric report matches ACK')
        self.receipts.append(proof['report']);self.current=None;self.ordinal[generation]+=1
        return proof

    def close(self):
        need(self.current is None,'no unconsumed actual qualification frame')
        return self.receipts


def install(t,C,source,m,rank,*,snapshot,sink):
    flag=os.environ.get(FLAG)
    if flag in(None,'','0'):
        need(m.get('fastpath_numeric_qualification')is None,'declared qualification requires explicit opt-in')
        return None
    need(flag=='1','explicit qualification opt-in')
    return Observer(t,C,source,m,rank,snapshot=snapshot,sink=sink)
