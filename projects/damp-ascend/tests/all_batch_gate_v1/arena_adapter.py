"""NEW raw-arena allocation and observation seams, never a recurrence oracle."""
import traceback
import torch
import torch_npu
from contract import NAMESPACE, layout, protected_ranges, span, disjoint, require
import candidate_adapter as frozen

DTYPES={"conv":torch.bfloat16,"high":torch.float16,"low":torch.int8,"scales":torch.float32}
REGIONS=frozen.REGIONS
exact=frozen.exact

def tensor_span(tensor):
    require(tensor.is_contiguous(),"span contract requires contiguous view")
    storage=tensor.untyped_storage()
    return span(tensor.data_ptr(),tensor.numel(),tensor.element_size(),
                storage.data_ptr(),storage.nbytes(),tensor.storage_offset())

def storage_disjoint(a,b):
    # TRUE contiguous DATA spans. Different views of the same backing are legal.
    return disjoint(tensor_span(a),tensor_span(b))

def nd_plain(cpu):
    result=torch_npu.npu_format_cast(cpu.to("npu:0").contiguous(),2)
    require(torch_npu.get_npu_format(result)==2 and result.data_ptr()%32==0,
            "explicit input preparation physical ND and32B pointer")
    return result

def identity(tensor):
    begin,end=tensor_span(tensor)
    storage=tensor.untyped_storage()
    return {"data_ptr":begin,"data_end":end,"storage_base":storage.data_ptr(),
            "storage_bytes":storage.nbytes(),"storage_offset":tensor.storage_offset(),
            "shape":list(tensor.shape),"stride":list(tensor.stride()),
            "dtype":str(tensor.dtype),"device":str(tensor.device),
            "physical_format":torch_npu.get_npu_format(tensor)}

class Arena:
    def __init__(self, slots, kind, serial, gate):
        self.spec=layout(slots,kind)
        self.serial=serial
        # Finite/patterned guard bytes, no dependence on allocator's old contents.
        cpu=((torch.arange(self.spec["total_bytes"],dtype=torch.int64)*17+serial*29)%251-125).to(torch.int8)
        self.raw=nd_plain(cpu)
        self.views={}
        gate.fixture["allocating_raw_before"]={"serial":serial,"spec":self.spec,"raw":cpu}
        for name,region in self.spec["regions"].items():
            self.views[name]=self.typed(name,region["offset"])
        bases={x.untyped_storage().data_ptr() for x in self.views.values()}
        require(bases=={self.raw.untyped_storage().data_ptr()},"typed views must retain exactly one raw backing")
        for name,view in self.views.items():
            require(torch_npu.get_npu_format(view)==2 and view.data_ptr()%32==0 and view.is_contiguous(),
                    "typed raw view must itself be physical ND/contiguous/aligned: "+name)
            expected=self.spec["regions"][name]
            require(view.data_ptr()-self.raw.data_ptr()==expected["offset"] and
                    view.numel()*view.element_size()==expected["bytes"],"typed byte interval identity")
        ordered=list(self.views.values())
        require(all(storage_disjoint(a,b) for i,a in enumerate(ordered) for b in ordered[:i]),
                "all FOUR cache intervals must be disjoint")
        self.original=cpu
        self.initial_identities=self.identities()

    def typed(self, name, offset):
        region=self.spec["regions"][name]
        end=offset+region["bytes"]
        require(offset%32==0 and end<=self.spec["total_bytes"],"malformed test view outside backing")
        # Like deployed Mamba allocator: raw byte slice -> dtype -> shape.
        # DO NOT format_cast the typed view (that can silently allocate a sidecar).
        return self.raw[offset:end].view(DTYPES[name]).view(region["shape"])

    def identities(self):
        return {"raw":identity(self.raw),**{n:identity(x) for n,x in self.views.items()}}

    def protected_exact(self, cpu):
        return all(exact(cpu[a:b],self.original[a:b]) for a,b in protected_ranges(self.spec))

class Registry:
    def __init__(self, kind, gate):
        self.kind,self.gate=kind,gate
        self.arenas=[]
        self.pending=None
        self.next_region=0
        self.observation_count=0
        self.guard_count=0

    def nd(self,cpu):
        shapes={"high":(12,128,16),"low":(12,128,112),"scales":(12,4,112)}
        found=[n for n in REGIONS if cpu.ndim==4 and tuple(cpu.shape[1:])==shapes[n] and cpu.dtype==DTYPES[n]]
        if not found:return nd_plain(cpu)
        name=found[0]
        require(name==REGIONS[self.next_region],"frozen protocol state allocation must arrive high/low/scales")
        if name=="high":
            self.pending=Arena(cpu.shape[0],self.kind,len(self.arenas)+1,self.gate)
            self.arenas.append(self.pending)
        require(cpu.shape[0]==self.pending.spec["slots"],"same arena slot geometry")
        view=self.pending.views[name]
        view.copy_(cpu);torch.npu.synchronize()
        self.next_region=(self.next_region+1)%3
        if self.next_region==0:self.pending=None
        return view

    def relevant(self,tensors):
        bases={x.untyped_storage().data_ptr() for x in tensors if isinstance(x,torch.Tensor)}
        return [a for a in self.arenas if a.raw.untyped_storage().data_ptr() in bases]

    def observe(self,gate,label,dispatch,tensors):
        """One evidence boundary: original dispatch error + raw-before BEFORE retention."""
        arenas=self.relevant(tensors)
        errors_before=[]
        before=frozen.snapshot(tensors,errors_before,label+".before")
        raw_before=frozen.snapshot([a.raw for a in arenas],errors_before,label+".raw_before")
        identities_before=[a.identities() for a in arenas]
        record={"before":before,"raw_before":raw_before,"arena_serials":[a.serial for a in arenas],
                "arena_identities_before":identities_before,"pointers_before":[t.data_ptr() for t in tensors]}
        gate.fixture[label]=record
        if errors_before:
            record["before_copy_errors"]=errors_before
            gate.retain()
            raise RuntimeError(label+" before snapshot failure; no dispatch")
        returns=None;dispatch_error=None
        try:
            returns=dispatch()
            torch.npu.synchronize()
        except BaseException as error:
            dispatch_error={"error":repr(error),"traceback":traceback.format_exc()}
        output_errors,input_errors,raw_errors=[],[],[]
        cpu_returns=frozen.snapshot(returns,output_errors,label+".returns")
        after=frozen.snapshot(tensors,input_errors,label+".after")
        raw_after=frozen.snapshot([a.raw for a in arenas],raw_errors,label+".raw_after")
        try:identities_after=[a.identities() for a in arenas]
        except BaseException as error:
            identities_after=None;raw_errors.append({"path":label+".identities_after","error":repr(error)})
        record.update(returns=cpu_returns,after=after,raw_after=raw_after,
            pointers_after=[t.data_ptr() for t in tensors],arena_identities_after=identities_after,
            dispatch_error=dispatch_error,output_copy_errors=output_errors,
            input_copy_errors=input_errors,raw_copy_errors=raw_errors)
        # All original and nullable evidence has been assigned BEFORE any assert.
        if dispatch_error or output_errors or input_errors or raw_errors:
            gate.retain()
            raise RuntimeError(label+" dispatch/copy failure; original/raw-before retained")
        guards={
            "raw_and_all_four_view_identities_stable":identities_before==identities_after and
                all(a.initial_identities==d for a,d in zip(arenas,identities_after)),
            "complete_conv_padding_prefix_suffix_bitwise":
                all(a.protected_exact(cpu) for a,cpu in zip(arenas,raw_after)),
            "protected_bytes_unchanged_from_dispatch_before":
                all(all(exact(b[x:y],c[x:y]) for x,y in protected_ranges(a.spec))
                    for a,b,c in zip(arenas,raw_before,raw_after)),
        }
        record["shared_arena_guards"]=guards
        self.observation_count+=1
        if arenas:
            gate.require(label+"_complete_raw_shared_arena_guards",all(guards.values()),
                         {"guards":guards,"arena_serials":[a.serial for a in arenas]})
            self.guard_count+=1
        return returns,cpu_returns,after

    def manifest(self):
        require(self.pending is None and self.next_region==0,"unfinished arena state allocation triplet")
        return {"layout":self.kind,"arenas":[{"serial":a.serial,"spec":a.spec,
                "identities":a.identities(),"raw_guard_bytes":sum(b-a for a,b in protected_ranges(a.spec))}
                for a in self.arenas],"observations":self.observation_count,"guarded_observations":self.guard_count}

class Candidate(frozen.Candidate):
    def __init__(self):
        self.ops=getattr(torch.ops,NAMESPACE)  # Explicit namespace only.
    def schemas(self):
        result=super().schemas()
        result["namespace"]=NAMESPACE
        require(NAMESPACE+"::" in result["decode"] and NAMESPACE+"::" in result["prepare"],
                "schema must be actual T1..16 v3 registry")
        return result

    def meta_gate(self):
        positive, negative = [], []
        def make(batch):
            slots = batch+3
            spec = [((batch,4,128),torch.bfloat16), ((batch,4,128),torch.bfloat16),
                    ((batch,12,128),torch.bfloat16), ((batch,12),torch.float32),
                    ((batch,12),torch.bfloat16), ((slots,12,128,16),torch.float16),
                    ((slots,12,128,112),torch.int8), ((slots,12,4,112),torch.float32),
                    ((12,128),torch.int32), ((12,128),torch.int32), ((12,128),torch.int32),
                    ((12,128),torch.float32), ((batch+1,),torch.int32), ((batch,),torch.int32)]
            return [torch.empty(shape,dtype=dtype,device="meta") for shape,dtype in spec]
        def prep(args): return [args[i] for i in (0,5,8,9,10,11)]
        for batch in range(1,17):
            args = make(batch)
            require(self.prepare(*prep(args)) is None, "Meta prepare must be void")
            out = self.decode(*args)
            require(out.shape == (batch,12,128) and out.dtype == torch.bfloat16 and
                    out.device.type == "meta" and all(out is not x for x in args),
                    "Meta real T1..16 output contract")
            positive.append({"batch":batch, "prepare":True, "decode":True})
        # Only checks explicitly implemented by register.cpp. Value, format,
        # pointer, CPU plan, slot and graph admission require real NPU gates.
        specifications = [
            ("query_T0",0,(0,4,128),torch.bfloat16),
            ("query_T17",0,(17,4,128),torch.bfloat16),
            ("query_dtype",0,(1,4,128),torch.float16),
            ("key_dtype",1,(1,4,128),torch.float16),
            ("value_shape",2,(1,12,127),torch.bfloat16),
            ("g_dtype",3,(1,12),torch.bfloat16),
            ("beta_dtype",4,(1,12),torch.float32),
            ("hi_shape",5,(4,12,128,15),torch.float16),
            ("hi_dtype",5,(4,12,128,16),torch.float32),
            ("lo_dtype",6,(4,12,128,112),torch.uint8),
            ("scale_shape",7,(4,12,3,112),torch.float32),
            ("lengths_dtype",12,(2,),torch.int64),
            ("indices_shape",13,(2,),torch.int32)]
        for i in (8,9,10,11):
            specifications.append(("plan_dtype_"+str(i),i,(12,128),
                                   torch.int64 if i!=11 else torch.float16))
            specifications.append(("plan_shape_"+str(i),i,(12,127),
                                   torch.int32 if i!=11 else torch.float32))
        for label,index,shape,dtype in specifications:
            args = make(1)
            args[index] = torch.empty(shape,dtype=dtype,device="meta")
            methods = ("decode","prepare") if index in (0,5,8,9,10,11) else ("decode",)
            for method in methods:
                try: getattr(self,method)(*(prep(args) if method=="prepare" else args))
                except RuntimeError:
                    negative.append({"case":label, "method":method}); continue
                raise AssertionError("Meta unexpectedly admitted "+label+"/"+method)
        for index in (0,5,8,9,10,11):
            args = make(1)
            doubled = list(args[index].shape); doubled[-1]*=2
            args[index] = torch.empty(doubled,dtype=args[index].dtype,device="meta")[...,::2]
            for method in ("prepare","decode"):
                try: getattr(self,method)(*(prep(args) if method=="prepare" else args))
                except RuntimeError:
                    negative.append({"case":"noncontiguous_"+str(index), "method":method}); continue
                raise AssertionError("Meta unexpectedly admitted noncontiguous")
        return {"passed":True, "positive_calls":len(positive)*2, "negative_calls":len(negative),
                "positives":positive, "negatives":negative,
                "scope":"schema/shape/dtype/layout only; no physical ND/value/graph/NPU proof"}

def overlap_negatives(gate,candidate,registry,batch):
    """Host rejects actual partial/exact byte overlap before queue; all raw no-write."""
    import protocols
    layout_,initial,generator=protocols.restricted.layouts(batch,0)
    states=[registry.nd(getattr(initial,n)) for n in REGIONS]
    arena=registry.arenas[-1]
    q,k,v,g,beta,ids=protocols.restricted.turn(batch,batch+3,0,generator)
    inputs=[nd_plain(x) for x in (q,k,v,g,beta)]
    plans=[nd_plain(x.int()) for x in (layout_.pk,layout_.pv,layout_.pv.argsort(1))]
    sr=nd_plain(layout_.c)
    lens=nd_plain(torch.tensor([0]+[1]*batch,dtype=torch.int32))
    indices=nd_plain(ids)
    args=inputs+states+plans+[sr,lens,indices]
    protocols.invoke_prepare_guard(gate,candidate.prepare,[args[0],args[5],*args[8:12]],states)
    # These shapes/dtypes/ND/alignment/storage bounds remain valid; only DATA overlap differs.
    cases=[]
    high=arena.spec["regions"]["high"];low=arena.spec["regions"]["low"]
    cases.append(("high_low_partial32",6,arena.typed("low",high["offset"]+high["bytes"]-32)))
    cases.append(("high_scale_partial32",7,arena.typed("scales",high["offset"]+high["bytes"]-32)))
    cases.append(("low_scale_partial32",7,arena.typed("scales",low["offset"]+low["bytes"]-32)))
    cases.append(("high_low_shared_start",6,arena.typed("low",high["offset"])))
    # All eleven read-only input kinds independently overlap the mutable high interval.
    for index in list(range(5))+list(range(8,14)):
        tensor=args[index]
        begin=high["offset"]
        size=tensor.numel()*tensor.element_size()
        bad=arena.raw[begin:begin+size].view(tensor.dtype).view(tensor.shape)
        cases.append(("readonly_"+str(index)+"_overlaps_high",index,bad))
    records=[]
    for label,index,bad in cases:
        gate.fixture={"stage":"actual_overlap_rejection","batch":batch,"label":label,
                      "malformed_input_index":index,"malformed_input_identity":identity(bad)}
        replacement=list(args);replacement[index]=bad
        before_errors=[]
        raw_before=frozen.snapshot(arena.raw,before_errors,label+".raw_before")
        input_before=frozen.snapshot(replacement,before_errors,label+".before")
        gate.fixture.update(raw_before=raw_before,before=input_before)
        require(not before_errors,"negative before snapshot failed, no dispatch")
        ptrs=[x.data_ptr() for x in replacement];before_ids=arena.identities()
        rejection=None;trace=None
        try:
            candidate.decode(*replacement)
            torch.npu.synchronize()
        except RuntimeError as error:
            rejection=str(error);trace=traceback.format_exc()
        copy_errors=[]
        raw_after=frozen.snapshot(arena.raw,copy_errors,label+".raw_after")
        after=frozen.snapshot(replacement,copy_errors,label+".after")
        try:after_ids=arena.identities()
        except BaseException as error:
            after_ids=None;copy_errors.append({"path":label+".identities_after","error":repr(error)})
        gate.fixture.update(raw_after=raw_after,after=after,rejection=rejection,
            rejection_traceback=trace,copy_errors=copy_errors,
            pointers_before=ptrs,pointers_after=[x.data_ptr() for x in replacement],
            identities_before=before_ids,identities_after=after_ids)
        if copy_errors:
            gate.retain()
            raise RuntimeError("negative nullable copy failure, original rejection retained")
        guards={
            "synchronous_actual_data_overlap_rejection":
                rejection is not None and "DATA byte intervals overlap" in rejection,
            "entire_raw_arena_bitwise_no_write":exact(raw_before,raw_after),
            "every_input_bitwise_no_write":all(exact(a,b) for a,b in zip(input_before,after)),
            "all_four_views_raw_and_argument_pointers_stable":
                before_ids==after_ids and ptrs==[x.data_ptr() for x in replacement],
            "conv_padding_guards_unchanged":arena.protected_exact(raw_after),
        }
        gate.require("actual_overlap_"+label,all(guards.values()),guards)
        records.append({"label":label,"guards":guards,"rejection":rejection})
    return records
