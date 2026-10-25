"""HOST CPU cost/semantic model for unused prefix outputs; no runtime installation."""
import ast,hashlib,inspect,json,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))

def build_cpu_counterfactual():
    import torch
    import independent_recurrent_boundary as reference
    import independent_c1_short_prefix as caller
    source=inspect.getsource(reference.recurrent_boundary)
    caller_tree=ast.parse(inspect.getsource(caller.align_short_prefix_terminals))
    calls=[n for n in ast.walk(caller_tree)if isinstance(n,ast.Assign)
           and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)
           and n.value.func.id=="recurrent_boundary"]
    if len(calls)!=1 or ast.unparse(calls[0].targets[0])!="(_, state)":
        raise ValueError("exact prefix-only discarded output caller required")
    if any(isinstance(n,ast.Name)and isinstance(n.ctx,ast.Load)and n.id=="_"
           for n in ast.walk(caller_tree)):
        raise ValueError("discarded output is actually consumed")
    tree=ast.parse(source);removed=[];rewritten=[]
    class OutputOnly(ast.NodeTransformer):
        def visit_Expr(self,node):
            value=node.value
            if (isinstance(value,ast.Call)and isinstance(value.func,ast.Attribute)
                    and isinstance(value.func.value,ast.Name)
                    and value.func.value.id=="outputs"and value.func.attr=="append"):
                removed.append(ast.unparse(node));return None
            return self.generic_visit(node)
        def visit_Assign(self,node):
            if len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id=="result":
                if not isinstance(node.value,ast.Tuple)or len(node.value.elts)!=2:
                    raise ValueError("exact output/state result ABI required")
                first=ast.unparse(node.value.elts[0]);last=ast.unparse(node.value.elts[1])
                if first!="torch.stack(outputs)[None].to(v.dtype)"or last!="state[None]":
                    raise ValueError("unexpected state/result construction")
                rewritten.append(first);node.value.elts[0]=ast.Constant(value=None)
            return self.generic_visit(node)
    tree=OutputOnly().visit(tree);ast.fix_missing_locations(tree)
    if len(removed)!=1 or len(rewritten)!=1:
        raise ValueError("one unused-output arithmetic site and output assembly only")
    namespace={"torch":torch}
    compile_source=ast.unparse(tree)
    exec(compile(tree,"<HOST-prefix-output-counterfactual>","exec"),namespace)
    generated=namespace["recurrent_boundary"]
    def cpu_only(*args,**kwargs):
        if any(isinstance(t,torch.Tensor)and t.device.type!="cpu"for t in args):
            raise ValueError("HOST model cannot execute on devices")
        return generated(*args,**kwargs)
    return reference.recurrent_boundary,cpu_only,{
        "reference_source_sha256":hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
        "caller_source_sha256":hashlib.sha256(Path(caller.__file__).read_bytes()).hexdigest(),
        "counterfactual_ast_sha256":hashlib.sha256(compile_source.encode()).hexdigest(),
        "removed_sites":removed,"rewritten_assembly":rewritten,
        "state_arithmetic_or_order_changed":False,
        "query_normalization_and_input_observer_retained":True,
        "runtime_installed":False,"device_run":False}

def run_cpu_model():
    import torch
    from torch.utils._python_dispatch import TorchDispatchMode
    torch.set_num_threads(1)
    old,new,identity=build_cpu_counterfactual()
    class CountMatmul(TorchDispatchMode):
        def __init__(self):self.calls=0
        def __torch_dispatch__(self,func,types,args=(),kwargs=None):
            if func in(torch.ops.aten.bmm.default,torch.ops.aten.mm.default):
                self.calls+=1
            return func(*args,**(kwargs or{}))
    rows=[]
    for dtype in(torch.float64,torch.float32,torch.bfloat16):
        for length in(1,8,39,64):
            torch.manual_seed(length)
            q=torch.randn(1,length,4,128,dtype=dtype)
            k=torch.randn_like(q);v=torch.randn(1,length,12,128,dtype=dtype)
            g=-torch.rand(1,length,12,dtype=torch.float32)
            beta=torch.rand(1,length,12,dtype=dtype)
            initial=torch.randn(1,12,128,128,dtype=torch.float32)*0.01
            args=(q,k,v,g,beta,initial)
            snapshots=[x.clone()for x in args]
            original_mode=CountMatmul();new_mode=CountMatmul()
            old_observed=[];new_observed=[]
            with original_mode:full,state=old(*args,input_observer=lambda **x:old_observed.append(x))
            with new_mode:unused,after=new(*args,input_observer=lambda **x:new_observed.append(x))
            assert unused is None and torch.equal(state,after)
            assert original_mode.calls==2*length and new_mode.calls==length
            assert all(torch.equal(x,y)for x,y in zip(args,snapshots))
            assert len(old_observed)==len(new_observed)==1
            for key in old_observed[0]:
                x=old_observed[0][key];y=new_observed[0][key]
                assert torch.equal(x,y)if isinstance(x,torch.Tensor)else x==y
            rows.append({"dtype":str(dtype),"length":length,"HK":4,"HV":12,"DK":128,"DV":128,
                "terminal_state_bitwise_equal":True,"inputs_unchanged":True,
                "input_observer_equal":True,"original_cpu_matmul_calls":original_mode.calls,
                "counterfactual_cpu_matmul_calls":new_mode.calls})
    return {"schema":"hypic-prefix-terminal-host-model/v1","identity":identity,
        "cases":rows,"cpu_cases_passed":len(rows),
        "math":"H_t depends on k,v,g,beta,H_prev; the prefix caller consumes H_terminal only. Per-token q@H and stacked outputs are discarded there.",
        "scope":"HOST exact semantic and operation-count counterfactual only. Not NPU latency, integrated source activation, formal speed, whole-model quality or paper acceptance.",
        "speed_cause_confirmed":False,"npu_run":False,"runtime_installed":False}

if __name__=="__main__":
    import argparse,os
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    result=run_cpu_model();data=(json.dumps(result,sort_keys=True)+"\n").encode()
    with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"output":a.output,"sha256":hashlib.sha256(data).hexdigest(),
        "cpu_cases_passed":result["cpu_cases_passed"],"npu_run":False,"runtime_installed":False}))
