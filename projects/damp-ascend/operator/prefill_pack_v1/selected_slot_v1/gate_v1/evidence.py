"""Nullable before/after evidence; no secondary poisoned D2H hides dispatch."""
import json
import traceback
import math
from pathlib import Path

def safe_json(value):
    if isinstance(value,float) and not math.isfinite(value):return {"nonfinite":repr(value)}
    if isinstance(value,dict):return {str(k):safe_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [safe_json(v) for v in value]
    return value

def exact(torch,a,b):
    return (isinstance(a,torch.Tensor) and isinstance(b,torch.Tensor) and a.dtype==b.dtype and
            tuple(a.shape)==tuple(b.shape) and
            torch.equal(a.detach().cpu().contiguous().view(torch.uint8),
                        b.detach().cpu().contiguous().view(torch.uint8)))

def snapshot(torch,value,errors,path="root"):
    if isinstance(value,torch.Tensor):
        try: return value.detach().cpu().contiguous().clone()
        except BaseException as error:
            errors.append({"path":path,"error":repr(error)})
            return None
    if isinstance(value,dict):
        return {k:snapshot(torch,v,errors,path+"."+str(k)) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [snapshot(torch,v,errors,path+"["+str(i)+"]") for i,v in enumerate(value)]
    return value

def pointers(tensors):
    return [(x.data_ptr(),x.untyped_storage().data_ptr(),x.untyped_storage().nbytes(),
             x.storage_offset(),str(x.dtype),tuple(x.shape),tuple(x.stride())) for x in tensors]

def observe(torch,gate,label,dispatch,tensors):
    before_errors=[]
    before=snapshot(torch,tensors,before_errors,label+".before")
    if before_errors: raise RuntimeError("before snapshot failed; no dispatch")
    ptrs=pointers(tensors)
    gate.fixture[label]={"before":before,"pointers_before":ptrs}
    device_out=None
    dispatch_error=None
    try:
        device_out=dispatch()
        torch.npu.synchronize()
    except BaseException as error:
        dispatch_error={"error":repr(error),"traceback":traceback.format_exc()}
    output_errors,input_errors,pointer_errors=[],[],[]
    # Publish the ORIGINAL dispatch failure before ANY after-query can fail.
    # This is a CPU-memory record, not a durable pre-dispatch disk journal.
    record={"before":before,"after":None,"returns":None,"pointers_before":ptrs,
            "pointers_after":None,"dispatch_error":dispatch_error,
            "output_copy_errors":output_errors,"input_copy_errors":input_errors,
            "pointer_query_errors":pointer_errors}
    gate.fixture[label]=record
    gate.last=record
    cpu_out=snapshot(torch,device_out,output_errors,label+".returns")
    after=snapshot(torch,tensors,input_errors,label+".after")
    try:
        ptrs_after=pointers(tensors)
    except BaseException as error:
        ptrs_after=None
        pointer_errors.append({"path":label+".pointers_after","error":repr(error),
                               "traceback":traceback.format_exc()})
    record.update(after=after,returns=cpu_out,pointers_after=ptrs_after)
    return device_out,cpu_out,after,record

class Recorder:
    def __init__(self,torch,out,report):
        self.torch,self.out,self.report=torch,Path(out),report
        self.fixture,self.last={},None
    def save(self):
        (self.out/"report.json").write_text(json.dumps(safe_json(self.report),indent=2,allow_nan=False)+"\n")
    def retain(self,name="first_failure"):
        target=self.out/(name+".pt")
        if target.exists(): return
        errors=[]
        cpu=snapshot(self.torch,self.fixture,errors)
        try:
            self.torch.save({"fixture":cpu,"snapshot_copy_errors":errors},target)
            self.report.setdefault("artifacts",[]).append({"path":str(target),"copy_errors":errors})
        except BaseException as error:
            self.report["failure_save_error"]=repr(error)
        self.save()
    def check(self,label,passed,details=None):
        self.report.setdefault("checks",[]).append({"name":label,"passed":bool(passed),"details":details})
        self.save()
        if not passed:
            self.retain()
            raise AssertionError(label)
    require=check
    def healthy(self,record,label):
        self.check(label,not record["dispatch_error"] and not record["output_copy_errors"] and
                   not record["input_copy_errors"] and not record["pointer_query_errors"], {k:record[k] for k in
                   ("dispatch_error","output_copy_errors","input_copy_errors","pointer_query_errors")})
