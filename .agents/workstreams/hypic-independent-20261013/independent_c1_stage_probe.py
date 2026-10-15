"""Default-off adapters observing actual packed/serialized private C1 stages."""
import hashlib,os,threading
from contextlib import contextmanager
from pathlib import Path
from independent_c1_stage_capture import FirstDivergenceCapture,LAYER
from independent_c1_deferred_capture import DeferredHeadCapture,sampled_head,residual_selection

@contextmanager
def observe_chunk_norm(module,callback):
    """Temporary owned in-memory observer; original arithmetic/output untouched."""
    original=module.l2norm_fwd
    if getattr(original,"_c1_stage_observer",False):raise RuntimeError("normalization observer conflict")
    seen=[]
    owner_thread=threading.get_ident()
    def wrapped(value,*args,**kwargs):
        result=original(value,*args,**kwargs)
        if threading.get_ident()!=owner_thread:return result
        seen.append(result)
        if len(seen)>2:raise ValueError("unexpected official normalization call count")
        if len(seen)==2:callback(*seen)
        return result
    wrapped._c1_stage_observer=True;module.l2norm_fwd=wrapped
    try:
        yield
        if len(seen)!=2:raise ValueError("missing actual official Q/K normalization")
    finally:
        if module.l2norm_fwd is not wrapped:raise RuntimeError("normalization observer ownership changed")
        module.l2norm_fwd=original

class C1StageProbe:
    def __init__(self,layout,plans,leased,*,manifest_sha256,root,head_policy="head0"):
        if head_policy not in ("head0","max_state_residual"):
            raise ValueError("explicit bounded diagnostic head policy required")
        self.head_policy=head_policy
        self.deferred=DeferredHeadCapture() if head_policy=="max_state_residual" else None
        self.layout=layout;self.plans={p.request_id:p for p in plans}
        self.root=Path(root);self.sealed=False
        selected=tuple(rid for rid in layout.request_ids if rid in leased)[:1]
        identity=dict(rank=layout.rank,pid=os.getpid(),layer=LAYER,step=layout.step,
            manifest_sha256=manifest_sha256,requests=list(selected),
            generations={rid:leased[rid][1] for rid in selected},
            tokens_sha256={rid:self.plans[rid].tokens_sha256 for rid in selected},
            head_indices=dict(query=0,key=0,value=0),key_width=128,value_width=128)
        self.capture=FirstDivergenceCapture(identity)
        self.jobs={}
        for rid,chain in zip(layout.request_ids,layout.chains):
            if rid not in selected:continue
            jobs=[key for kind,key in chain if kind=="live"]
            if len(jobs)!=2:raise ValueError("two actual live windows required for stage probe")
            self.jobs[rid]=jobs
        self.branches={}
        self.coordinates={rid:dict(slot=layout.state_slots[i],has_initial=layout.has_initial[i],
            body_start=self.plans[rid].body_start,body_end=self.plans[rid].body_end)
            for i,rid in enumerate(layout.request_ids) if rid in leased}

    def add(self,side,rid,stage,window,tensors):
        if window=="body":
            lo,hi=self.plans[rid].body_start,self.plans[rid].body_end
        else:
            job=self.layout.windows[self.jobs[rid][0 if window=="prefix" else 1]]
            lo,hi=job.source_start,job.source_end
        kwargs=dict(side=side,request_id=rid,stage=stage,window=window,
                    source_start=lo,source_end=hi)
        if self.deferred is not None:self.deferred.add(**kwargs,tensors=tensors)
        else:self.capture.add(**kwargs,tensors=sampled_head(stage,tensors,0))

    def packed_recurrent_inputs(self,job,q,k,v,g,beta,initial,branch):
        w=self.layout.windows[job];rid=w.request_id
        if rid not in self.jobs:return
        if job!=self.jobs[rid][0] or branch!="independent_recurrent_le64":
            raise ValueError("actual recurrent prefix job required")
        self.add("packed",rid,"inputs","prefix",dict(q=q[0],k=k[0],v=v[0],
            g=g[0],beta=beta[0],initial=initial[0]))
        self.branches[("packed",rid,"prefix")]=branch

    def packed_inputs(self,shared,v,g,beta,initial,seeds):
        for rid,jobs in self.jobs.items():
            for pos,j in enumerate(jobs):
                if pos==0 and ("packed",rid,"prefix") in self.branches:continue
                w=self.layout.windows[j];span=slice(w.packed_start,w.packed_end)
                # These are the actual head-first BF16 Q/K passed to kernels;
                # V/log-g/beta are original inputs, not WY-produced U.
                self.add("packed",rid,"inputs","prefix" if pos==0 else "suffix",
                    dict(q=shared.q[0,:,span].transpose(0,1),k=shared.k[0,:,span].transpose(0,1),v=v[0,span],
                         g=g[0,span],beta=beta[0,span],
                         initial=(initial if pos==0 else seeds)[j]))
                self.branches[("packed",rid,"prefix" if pos==0 else "suffix")]="official_chunk64"

    def packed_states(self,prefix_terminals,seeds,materials):
        for rid,jobs in self.jobs.items():
            body=materials[self.plans[rid].tokens_sha256]
            self.add("packed",rid,"prefix_terminal","prefix",dict(state=prefix_terminals[jobs[0]]))
            self.add("packed",rid,"cached_composition","body",dict(
                transition=body.affine.transition,zero_state=body.affine.zero_state,
                state=seeds[jobs[1]]))
            self.add("packed",rid,"suffix_seed","suffix",dict(state=seeds[jobs[1]]))

    def serial_inputs(self,rid,lo,hi,q,k,v,g,beta,initial,branch):
        if rid not in self.jobs:return
        base=self.layout.windows[self.jobs[rid][0]].source_start
        w=self.layout.windows[self.jobs[rid][0]]
        window="prefix" if (lo,hi)==(0,w.source_end-w.source_start) else "suffix"
        expected=self.layout.windows[self.jobs[rid][0 if window=="prefix" else 1]]
        if (base+lo,base+hi)!=(expected.source_start,expected.source_end):
            raise ValueError("actual serialized/source window mismatch")
        self.add("serial",rid,"inputs",window,dict(q=q[0],k=k[0],v=v[0],
            g=g[0],beta=beta[0],initial=initial[0]))
        self.branches[("serial",rid,window)]=branch

    def serial_terminal(self,rid,lo,hi,state):
        if rid not in self.jobs:return
        w=self.layout.windows[self.jobs[rid][0]]
        if (lo,hi)==(0,w.source_end-w.source_start):
            self.add("serial",rid,"prefix_terminal","prefix",dict(state=state))

    def serial_state(self,rid,kind,state,material):
        if rid not in self.jobs:return
        if kind=="cached_composition":
            self.add("serial",rid,kind,"body",dict(transition=material.affine.transition,
                zero_state=material.affine.zero_state,state=state))
        elif kind=="suffix_seed":self.add("serial",rid,kind,"suffix",dict(state=state))
        else:raise ValueError("unknown actual serialized state stage")

    def final(self,side,rid,result):
        if rid not in self.jobs:return
        output,state,conv=result;w=self.layout.windows[self.jobs[rid][1]]
        self.add(side,rid,"final","suffix",dict(output=output[-(w.source_end-w.source_start):],
                                              state=state,conv=conv))

    def seal(self,failed_request_id,*,actual_state=None,reference_state=None,reported_max=None):
        if failed_request_id not in self.jobs:
            self.discard()
            return dict(complete=False,reason="failed request outside selected first request")
        selection=None
        if self.deferred is not None:
            try:
                selection=residual_selection(actual_state,reference_state,reported_max)
                head=selection["value_head"]
                self.capture.identity.update(head_policy=self.head_policy,
                    head_indices=dict(query=head//3,key=head//3,value=head),
                    head_selection=selection)
                self.deferred.flush_to(self.capture,head)
            except BaseException:
                self.discard()
                raise
        # All selected requests must have actual paired data; a missing pair
        # remains explicit incomplete evidence for the independent audit.
        receipt=self.capture.seal_failure(self.root,failed_request_id=failed_request_id)
        receipt['capture_manifest_sha256']=receipt.pop('manifest_sha256')
        self.sealed=True
        return dict(receipt,head_policy=self.head_policy,head_selection=selection,branches=[dict(side=k[0],request_id=k[1],window=k[2],branch=v)
            for k,v in self.branches.items()],coordinates=self.coordinates,
            scope="actual selected-head samples; full-group completeness requires independent audit")

    def discard(self):
        if self.deferred is not None and not self.deferred.closed:self.deferred.discard()
        if not self.capture.closed:self.capture.discard()

def make_probe(layer,layout,plans,leased,emit,*,head_policy="head0"):
    # At most 12000 live rows keeps two-sided Q/K/V/output plus state samples
    # below the frozen64MiB bound. Ineligible failed groups are NOT diagnosed.
    if layer.prefix!=LAYER or layout.rank!=0:return None
    hot=tuple(rid for rid in layout.request_ids if rid in leased)
    active={rid for rid,chain in zip(layout.request_ids,layout.chains) if chain}
    excluded=tuple(rid for rid,chain in zip(layout.request_ids,layout.chains) if not chain)
    by_id={p.request_id:p for p in plans}
    reason=None
    if len(hot)!=2 or active!=set(hot):reason="requires_exactly_two_active_hot_chains"
    elif layout.packed_tokens>12000:reason="packed_live_row_bound"
    elif any(len([j for kind,j in chain if kind=="live"])!=2
             for rid,chain in zip(layout.request_ids,layout.chains) if rid in hot):
        reason="requires_two_live_windows_per_hot_request"
    elif any(getattr(by_id[rid],"scheduled_tokens",None)!=1
             or getattr(by_id[rid],"skipped_tokens",None)!=0 for rid in excluded):
        reason="excluded_entry_not_native1"
    if hot and callable(emit):
        emit(dict(event="c1_first_divergence_selection",rank=layout.rank,step=layout.step,
            layer=layer.prefix,total_entries=len(plans),hot_request_ids=list(hot),
            excluded_native_one=list(excluded),active_windows=len(layout.windows),
            packed_tokens=layout.packed_tokens,eligible=reason is None,reason=reason,
            selected_request_id=hot[0] if reason is None else None,
            actual_slot_commit="not_started"))
    if reason is not None:return None
    manifest=getattr(emit,"source_manifest_sha256",None)
    raw=getattr(emit,"stage_capture_root",None)
    if not manifest or not raw:raise ValueError("source-bound diagnostic sink required")
    return C1StageProbe(layout,plans,leased,manifest_sha256=manifest,
        root=Path(raw)/("c1-stage-rank0-step"+str(layout.step)),head_policy=head_policy)
