"""Focused actual-AST software regressions; never model/NPU success."""
from __future__ import annotations
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import v2_bindings as binding
import v2_peak as peak
import v2_release as release
from v2_contract import BINDINGS_SHA,ROOT,require,v1

class Binding(unittest.TestCase):
    def setUp(self):
        p=ROOT/"projects/damp-ascend/collector/damp_capture/bindings.py"
        raw=p.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),BINDINGS_SHA)
        tree=ast.parse(raw.decode(),filename=str(p));nodes={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        self.layers=tuple(i for i in range(64) if i%4!=3)
        self.ns={"require":require,"inspect":inspect,"Path":Path,"LAYERS":self.layers,
            "file_digest":lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),
            "layer_index":lambda p:int(p.split(".")[2]),
            "function_identity":lambda f:{"fixture":True,"qualname":getattr(f,"__func__",f).__qualname__}}
        for name in ("live_bindings","verify_native_alias"):
            exec(compile(ast.Module(body=[nodes[name]],type_ignores=[]),str(p),"exec"),self.ns)
            self.assertEqual(self.ns[name].__code__.co_filename,str(p))
        def native_core(self,*args,**kwargs):return None
        def native_forward(self,*args,**kwargs):return None
        self.core=native_core
        self.donor=type("FixtureDonor",(object,),{"__module__":__name__,"forward":native_forward,"_forward_core":native_core})
        self.target=type("FixtureTarget",(object,),{"__module__":__name__,"forward":native_forward,"_forward_core":native_core})
        self.table={}
        for layer in self.layers:
            p="model.layers."+str(layer)+".linear_attn";o=self.target();o.prefix=p;self.table[p]=o
        self.old_helpers=binding.helpers
        fake=SimpleNamespace(verify_native_alias=self.ns["verify_native_alias"],
                             function_identity=self.ns["function_identity"])
        binding.helpers=lambda:(fake,self.layers,self.ns["layer_index"])

    def tearDown(self): binding.helpers=self.old_helpers

    def run_off(self,table=None):return binding.off_native_bindings(self.table if table is None else table,self.donor,self.target,self.core)

    def test_actual_old_body_reproduces_off_attribute_failure(self):
        with self.assertRaisesRegex(AttributeError,"_damp_original_core"):
            self.ns["live_bindings"](self.table,self.donor,self.target,self.core)

    def test_new_off_48_does_not_add_attributes(self):
        before={id(x):dict(vars(x)) for x in self.table.values()}
        self.assertEqual(len(self.run_off()),48)
        self.assertFalse(hasattr(self.target,"_damp_original_core"))
        self.assertTrue(all(vars(x)==before[id(x)] for x in self.table.values()))

    def test_missing_subclass_prefix_core_reject(self):
        wrong=dict(self.table);wrong.pop(next(iter(wrong)))
        with self.assertRaises(ValueError):self.run_off(wrong)
        p=next(iter(self.table))
        for cls,prefix in ((type("BadSubclass",(self.target,),{}),p),(self.target,p+".bad")):
            wrong=dict(self.table);o=cls();o.prefix=prefix;wrong[p]=o
            with self.assertRaises(ValueError):self.run_off(wrong)
        def other(self,*args,**kwargs):return None
        self.target._forward_core=other
        with self.assertRaises(ValueError):self.run_off()

    def test_original_on_helper_unchanged(self):
        def wrapper(self,*args,**kwargs):return None
        self.donor._damp_original_core=self.target._damp_original_core=self.core
        self.donor._forward_core=self.target._forward_core=wrapper
        self.assertEqual(len(self.ns["live_bindings"](self.table,self.donor,self.target,wrapper)),48)

class Release(unittest.TestCase):
    def fixture(self,card=4):
        p=release.ROOT/("physical"+str(card)+"/device-proof.json")
        return json.loads(p.read_text())["container_inspect"]

    def test_actual_proof_identity_then_mutations_reject(self):
        obj=self.fixture();self.assertEqual(release.identity(obj,4)["id"],release.IDS[4])
        for mutate in (
            lambda v:v.update(Id="0"*64),
            lambda v:v.update(Name="/wrong"),
            lambda v:v.update(Image="sha256:"+"0"*64),
            lambda v:v["HostConfig"]["Devices"][0].update(PathOnHost="/dev/davinci0")):
            bad=copy.deepcopy(obj);mutate(bad)
            with self.assertRaises(ValueError):release.identity(bad,4)

    def terminal(self):
        record={"id":release.OP,"state":"completed","cancelled":False,"timedOut":False,"exitCode":1,"cwd":str(v1().ROOT)}
        return {"schema":"agentweb.operation/v1","operationId":release.OP,"terminal":True,"phase":"completed","status":"completed",
            "operation":{"routeDecision":"peer_direct","targetPeerId":release.PEER,"fallbackUsed":False,"result":{"record":record}}}

    def test_nonzero_terminal_only_releases_scheduling(self):
        obj=release.terminal(self.terminal())
        self.assertTrue(obj["scheduling_terminal_only"]);self.assertFalse(obj["numerical_pass_claimed"])
        for key,value in (("operationId","exec-00000000000006a0"),("terminal",False)):
            bad=self.terminal();bad[key]=value
            with self.assertRaises(ValueError):release.terminal(bad)

class Peak(unittest.TestCase):
    def test_exact_owned_memory_v1_and_broad_reject(self):
        ident=release.IDS[4];member="/system.slice/docker-"+ident+".scope"
        cg="9:memory:"+member+"\n"
        mount="41 32 0:37 / /sys/fs/cgroup/memory rw - cgroup cgroup rw,memory\n"
        self.assertEqual(peak.memory_path(cg,mount,ident),Path("/sys/fs/cgroup/memory")/member[1:])
        for bad in ("9:memory:/\n","9:memory:/system.slice/docker-"+"0"*64+".scope\n",
                    "9:memory:/../../docker-"+ident+".scope\n"):
            with self.assertRaises(ValueError):peak.memory_path(bad,mount,ident)

    def test_real_counter_not_display_and_limit_fail(self):
        vals={"memory.usage_in_bytes":"64","memory.max_usage_in_bytes":"128",
              "memory.limit_in_bytes":"256","memory.failcnt":"0","memory.stat":"rss 32\ncache 32\n"}
        data=peak.counters(lambda p:vals[p.name],Path("/fixture"),256)
        self.assertEqual(data["kernel_peak_bytes"],128);self.assertEqual(data["memory_stat"]["rss"],32)
        with self.assertRaises(ValueError):peak.counters(lambda p:vals[p.name],Path("/fixture"),512)

if __name__=="__main__":unittest.main()
