"""No Torch/load/NPU: actual orchestration, source boundaries and checked status only."""
import ast
import dataclasses
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
BASE = Path(__file__).resolve().parents[1]
INTEGRATION = BASE.parent
sys.path.insert(0, str(INTEGRATION))
sys.path.insert(0, str(BASE))
from continuous_metadata_v1.contract import Row, Turn, plan
from damp_continuous_core.core import ContinuousCore, phase, Unsupported
from damp_continuous_core.checked_sink import validate_status_rows
HELPER = INTEGRATION/"continuous_metadata_v1"/"contract.py"
HELPER_SHA = "113f37c597e8b062b217217a48e7f087d885c3456b5efe53305264d9c7b64a1b"

def make_turn(rows):
    starts = [0]
    for r in rows: starts.append(starts[-1]+r.query_tokens)
    return plan(rows, starts, 32)

def row(name, slot, q, done, prompt=8):
    return Row(name, slot, q, done, prompt, slot+100)

class Backend:
    def __init__(self, events, md=True, fail=None):
        self.events, self.md, self.fail = events, md, fail
    def event(self, name, *args):
        self.events.append((name, *args))
        if self.fail == name: raise RuntimeError("fixture failure "+name)
    def metadata(self, prefix):
        self.event("metadata",prefix)
        return object() if self.md else None
    def require_cold(self, layer, turn): self.event("cold",turn.num_decodes,len(turn.prefill_rows))
    def conv(self, layer, md, turn, mixed): self.event("conv",turn.starts[-1],len(turn.rows));return mixed
    def project(self, layer, convolved): self.event("project");return convolved
    def gating(self, layer, a, b, n): self.event("gating",n);return (a,b)
    def decode(self, layer, md, turn, qkv, g):
        self.event("decode",turn.decode_tokens,tuple(r.slot for r in turn.decode_rows))
        return list(range(turn.decode_tokens))
    def prefill(self, layer, md, turn, qkv, g, positions):
        self.event("prefill",len(turn.prefill_rows),turn.prefill_starts,positions)
        return list(range(turn.decode_tokens,turn.starts[-1]))
    def merge(self, decode, prefill): self.event("merge");return (decode or [])+(prefill or [])
    def validate_output(self, out, prefix, turn): self.event("validate",tuple(out))
    def publish(self, target, out, n): self.event("publish",n);target.extend(out)

class Safety:
    def __init__(self, events, turn, fail=None):
        self.events,self.turn,self.fail=events,turn,fail
    def event(self,name,*a):
        self.events.append((name,*a))
        if self.fail==name: raise RuntimeError("prewriter failure")
    def require_layer(self,prefix,md): self.event("require_layer");return self.turn
    def before_writer(self,prefix,turn,md): self.event("before_writer")
    def writer_started(self,prefix): self.event("writer_started")
    def layer_succeeded(self,prefix): self.event("succeeded")
    def retire(self,prefix,reason,retry_allowed=False):
        self.event("retire",retry_allowed,reason)

class CoreTests(unittest.TestCase):
    def run_turn(self, turn, fail=None):
        events=[];target=[]
        core=ContinuousCore(Backend(events,fail=fail),Safety(events,turn),enabled=True)
        core(SimpleNamespace(prefix="model.layers.0.linear_attn"), "qkv", "b", "a", target)
        return events,target
    def test_helper_source_bound(self):
        self.assertEqual(hashlib.sha256(HELPER.read_bytes()).hexdigest(), HELPER_SHA)
    def test_default_off(self):
        with self.assertRaises(Unsupported):ContinuousCore(None,None)
    def test_profile_no_writers(self):
        ev=[];target=[]
        ContinuousCore(Backend(ev,md=False),Safety(ev,None),True)(
            SimpleNamespace(prefix="p"),None,None,None,target)
        self.assertEqual([x[0] for x in ev],["metadata"]);self.assertEqual(target,[])
    def test_fresh_prefill(self):
        turn=make_turn([row("new",1,8,0)])
        ev,out=self.run_turn(turn)
        self.assertEqual(out,list(range(8)))
        self.assertIn(("prefill",1,(0,8),()),ev)
        self.assertNotIn("decode",[x[0] for x in ev])
    def test_continuation_prefill(self):
        turn=make_turn([row("cont",1,3,2)])
        ev,_=self.run_turn(turn)
        self.assertIn(("prefill",1,(0,3),(0,)),ev)
    def test_mixed_native_order_and_one_conv(self):
        turn=make_turn([row("decode",0,1,8),row("cont",1,3,2),row("fresh",2,8,0)])
        ev,out=self.run_turn(turn)
        self.assertEqual(out,list(range(12)))
        self.assertEqual([x[0] for x in ev].count("conv"),1)
        self.assertEqual([x[0] for x in ev].count("gating"),1)
        self.assertIn(("conv",12,3),ev)
        self.assertIn(("decode",1,(0,)),ev)
        self.assertIn(("prefill",2,(0,3,11),(0,)),ev)
    def test_q1_continuation_reclassified_decode(self):
        turn=make_turn([row("short",1,1,2)])
        ev,out=self.run_turn(turn)
        self.assertIn(("decode",1,(1,)),ev)
        self.assertNotIn("prefill",[x[0] for x in ev]);self.assertEqual(out,[0])
    def test_real_c16_count_not_padding(self):
        turn=make_turn([row(str(i),i,1,8) for i in range(16)])
        ev,out=self.run_turn(turn);self.assertEqual(out,list(range(16)))
        self.assertIn(("cold",16,0),ev)
        turn=make_turn([row("one",0,1,8)])
        ev,_=self.run_turn(turn);self.assertIn(("cold",1,0),ev)
    def test_before_writer_precedes_every_runtime_write(self):
        turn=make_turn([row("new",1,8,0)])
        ev,_=self.run_turn(turn);names=[x[0] for x in ev]
        self.assertLess(names.index("before_writer"),names.index("writer_started"))
        self.assertLess(names.index("cold"),names.index("conv"))
        self.assertLess(names.index("writer_started"),names.index("conv"))
    def test_precheck_failure_no_writer(self):
        turn=make_turn([row("new",1,8,0)]);ev=[]
        core=ContinuousCore(Backend(ev),Safety(ev,turn,fail="before_writer"),True)
        with self.assertRaises(RuntimeError):core(SimpleNamespace(prefix="p"),None,None,None,[])
        self.assertNotIn("conv",[x[0] for x in ev])
        self.assertNotIn("writer_started",[x[0] for x in ev])
    def test_numerical_failure_retire_no_fallback_retry_publish(self):
        turn=make_turn([row("decode",0,1,8),row("fresh",1,8,0)]);ev=[];target=[]
        core=ContinuousCore(Backend(ev,fail="prefill"),Safety(ev,turn),True)
        with self.assertRaises(RuntimeError):core(SimpleNamespace(prefix="p"),None,None,None,target)
        names=[x[0] for x in ev]
        self.assertEqual(names.count("conv"),1);self.assertEqual(names.count("decode"),1)
        self.assertEqual(names.count("prefill"),1);self.assertIn("retire",names)
        self.assertFalse(next(x for x in ev if x[0]=="retire")[1])
        self.assertNotIn("publish",names);self.assertNotIn("succeeded",names);self.assertEqual(target,[])
    def test_bad_actual_boundaries_reject(self):
        turn=make_turn([row("decode",0,1,8),row("fresh",1,8,0)])
        for bad in (dataclasses.replace(turn,decode_tokens=16),
                    dataclasses.replace(turn,starts=(0,2,9)),
                    dataclasses.replace(turn,prefill_slots=(0,)),
                    dataclasses.replace(turn,has_initial=(True,))):
            with self.assertRaises(Unsupported):phase("p",bad)
    def test_static_module_no_torch_or_device_import(self):
        for path in (BASE/"damp_continuous_core").glob("*.py"):
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    mods=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ""]
                    self.assertFalse(any(x.split(".")[0] in ("torch","torch_npu","vllm","vllm_ascend") for x in mods))
    def test_unpack_source_axes_and_hot_copy_boundary(self):
        src=(BASE/"damp_continuous_core"/"torch_backend.py").read_text()
        tree=ast.parse(src);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="TorchBackend")
        methods={n.name:ast.get_source_segment(src,n) for n in cls.body if isinstance(n,ast.FunctionDef)}
        for name,body in methods.items():
            if name!="prepare_layer":
                self.assertNotIn(".cpu()",body);self.assertNotIn(".tolist()",body)
        un=methods["unpack_selected"]
        self.assertIn("selected_sc[:,head].repeat_interleave(32,dim=1)",un)
        self.assertIn("r.plan.inv_pv[head].long()",un)
        self.assertIn("r.inv_pk[head].long()",un)
        self.assertIn("original*r.plan.sr[head][None,:,None]",un)
        self.assertIn("original.transpose(-1,-2)",un)
        self.assertIn("if not positions:return initial",un)
        self.assertIn("(p,12,128,128)",un)
        self.assertNotIn("(hi.shape[0],12",un)
        self.assertIn("formal_perf is False",src)
        self.assertIn("world_size == 1",src)
        self.assertIn("self.sink.pack_status(status",src)
    def test_status_complete_then_failure(self):
        good=[0x13579bdf]*8+([1,0,4,16384,0,16384,0,0]*12)+[0x13579bdf]*8
        self.assertEqual(len(validate_status_rows(good,1)),12)
        for ix,value in ((0,0),(8,0),(9,2),(10,3),(11,16383),(-1,0)):
            bad=good.copy();bad[ix]=value
            with self.assertRaises(Unsupported):validate_status_rows(bad,1)
        with self.assertRaises(Unsupported):validate_status_rows(good[8:-8],1)
    def test_no_installer_or_implicit_load(self):
        src=(BASE/"damp_continuous_core"/"binding.py").read_text()
        self.assertNotIn("load_library",src);self.assertNotIn("torch.ops =",src)
        self.assertIn("receiver._forward_core is original",src)
        self.assertIn("authority.require_complete_before_install()",src)
        self.assertIn("default OFF",src)
        self.assertIn("48 instances BEFORE",src)

if __name__=="__main__":unittest.main()
