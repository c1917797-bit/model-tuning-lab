#!/usr/bin/env python3
"""Pure-stdlib regression only. No Torch/NPU/Docker execution."""
import ast,contextlib,io,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def mem_module(name,path):
    m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
    exec(compile(path.read_text(),str(path),"exec"),m.__dict__);return m
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=mem_module("_diag_replay_software",HERE/"replay.py")
        cls.h=mem_module("_diag_host_software",HERE/"host.py")
    def test_default_off_replay(self):
        with patch.object(self.r,"sha",side_effect=AssertionError("OFF file read")),contextlib.redirect_stdout(io.StringIO()) as out:
            self.r.main([])
        self.assertFalse(json.loads(out.getvalue())["npu_executed"])
    def test_default_off_host(self):
        with patch.object(self.h,"frozen",side_effect=AssertionError("OFF imports")),contextlib.redirect_stdout(io.StringIO()) as out:
            self.h.main([])
        self.assertFalse(json.loads(out.getvalue())["npu_executed"])
    def fixture(self):
        names={"base","k_log","u_log","lambda_log","decay","length"}
        return dict(schema="kvbp.raw-step/v1",batch=16,mode="graph",trial=0,step=37,active=12,reset_slot=None,
                    before=dict.fromkeys(names),after=dict.fromkeys(names),guards_before=dict.fromkeys(names),guards=dict.fromkeys(names))
    def test_exact_fixture(self):self.r.metadata(self.fixture())
    def test_fixture_negatives(self):
        for key,value in (("batch",1),("mode","eager"),("trial",1),("step",36),("active",16),("reset_slot",0)):
            f=self.fixture();f[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.r.metadata(f)
    def test_full_guard_required(self):
        f=self.fixture();f["guards"].pop("u_log")
        with self.assertRaises(ValueError):self.r.metadata(f)
    def test_ram_floor_and_fullmodel_unchanged(self):
        v=self.h.floor(16*1024**3,3,13*1024**3)
        self.assertEqual(v["full_model_floor_unchanged"],72*1024**3)
        for values in ((16*1024**3-1,3,13*1024**3),(16*1024**3,2,13*1024**3),(16*1024**3,3,13*1024**3-1)):
            with self.assertRaises(ValueError):self.h.floor(*values)
    def test_exact_single_device(self):
        d=self.h.devices();self.assertEqual(d["/dev/davinci6"],"/dev/davinci0");self.assertEqual(len(d),4)
    def test_inspect_complete_actual_mapping(self):
        d=self.h.devices();m={"/r":("/r",False),"/kvbuffer-results":("/out",True)}
        x={"Id":"a"*64,"Name":"/"+self.h.NAME,"Image":self.h.IMAGE,
           "Config":{"Labels":{"model-tuning-lab.owner":self.h.OWNER,"model-tuning-lab.run":self.h.NAME,
                              "model-tuning-lab.producer-sha256":"c"*64}},
           "HostConfig":{"Privileged":False,"Memory":self.h.MEM,"MemorySwap":self.h.MEM,"NanoCpus":10**9,
             "NetworkMode":"none","PidsLimit":512,"CapDrop":["ALL"],"SecurityOpt":["no-new-privileges"],
             "Devices":[dict(PathOnHost=a,PathInContainer=b,CgroupPermissions="rwm") for a,b in d.items()]},
           "Mounts":[dict(Source=a,Destination=b,RW=c,Type="bind") for b,(a,c) in m.items()]}
        with patch.object(self.h,"mounts",return_value=m):
            self.h.validate_inspect(x,"a"*64,"c"*64)
            x["HostConfig"]["Devices"].append(dict(PathOnHost="/dev/davinci5",PathInContainer="/dev/davinci1",CgroupPermissions="rwm"))
            with self.assertRaises(ValueError):self.h.validate_inspect(x,"a"*64,"c"*64)
            x["HostConfig"]["Devices"].pop();x["Mounts"].append(dict(Source="/tmp",Destination="/tmp",RW=True,Type="bind"))
            with self.assertRaises(ValueError):self.h.validate_inspect(x,"a"*64,"c"*64)
    def test_metrics_actual_scope_ast(self):
        tree=ast.parse((HERE/"replay.py").read_text());f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="metrics")
        calls=[x for x in ast.walk(f) if isinstance(x,ast.Call)]
        self.assertTrue(any(isinstance(x.func,ast.Attribute) and x.func.attr=="finite_receipt" for x in calls))
        self.assertIn("slots=19",ast.unparse(f).replace(" ",""))
        self.assertIn("active=12",ast.unparse(f).replace(" ",""))
        self.assertIn("expected[:active]",ast.unparse(f))
        self.assertIn("y[active:]",ast.unparse(f))
    def test_save_before_metrics_and_assert(self):
        src=ast.parse((HERE/"replay.py").read_text());f=next(x for x in src.body if isinstance(x,ast.FunctionDef) and x.name=="main")
        call_lines={}
        for x in ast.walk(f):
            if isinstance(x,ast.Call):
                name=ast.unparse(x.func);call_lines.setdefault(name,[]).append(x.lineno)
        self.assertLess(min(call_lines["old.step"]),min(call_lines["metrics"]))
        self.assertLess(min(call_lines["cpu_difference"]),min(call_lines["enable_custom_op"]))
        self.assertLess(min(call_lines["torch.save"]),min(call_lines["enable_custom_op"]))
        self.assertEqual(len([x for x in ast.walk(src) if isinstance(x,ast.Call) and ast.unparse(x.func)=="old.step"]),1)
    def test_cpu_double_not_npu_double(self):
        source=(HERE/"replay.py").read_text()
        self.assertNotIn(".double()",source)
        self.assertNotIn("OUT_LIMIT =",source)
        self.assertIn("original_numeric_pass",source)
    def test_history_not_trace(self):
        tree=ast.parse((HERE/"replay.py").read_text());f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="history_branch")
        source=ast.unparse(f)
        self.assertIn("'precise_candidate_trace': False",source)
        self.assertIn("'attribution_closed': False",source)
        self.assertLess(source.index("torch.save"),source.index("h.output_error"))
    def test_pid_raw_before_validation_ast(self):
        tree=ast.parse((HERE/"host.py").read_text());f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="observe_child")
        writes=[x.lineno for x in ast.walk(f) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=="write"]
        vals=[x.lineno for x in ast.walk(f) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=="validate_pid"]
        self.assertLess(min(writes),min(vals))
        pred=next(x for x in ast.walk(f) if isinstance(x,ast.If) and ast.unparse(x.test)=="p.poll() is not None")
        self.assertLess(pred.lineno,min(vals))
        self.assertTrue(any(isinstance(x,ast.Break) for x in pred.body))
    def test_child_terminal_skips_stale_pid_behavior(self):
        h=self.h;events=[]
        class P:
            returncode=0
            count=0
            def poll(self):
                self.count+=1;return None if self.count==1 else 0
        p=P();dummy=types.SimpleNamespace(legacy=lambda:types.SimpleNamespace(process_rows=lambda t:[(6,0,999)]))
        ref={"path":"/raw","sha256":"0"*64}
        class File:
            def __enter__(self):return self
            def __exit__(self,*a):return False
        with patch.object(Path,"open",return_value=File()),patch.object(h,"frozen",return_value=dummy),\
             patch.object(h.subprocess,"Popen",return_value=p),patch.object(h,"capture",return_value=({"stdout":"raw"},ref)),\
             patch.object(h,"proc_raw",return_value={"pid":999,"files":{}}),\
             patch.object(h,"write",side_effect=lambda *a:(events.append(a[1]) or ref)),\
             patch.object(h,"sha",return_value="0"*64),\
             patch.object(h,"validate_pid",side_effect=AssertionError("stale PID predicate")):
            with self.assertRaisesRegex(ValueError,"no actual workload PID proof"):
                h.observe_child("a"*64,"diagnostic",["/usr/bin/docker","exec","a"*64,"/usr/local/python3.12.13/bin/python3","-B","replay"],"replay",h.time.monotonic()+1000,"c"*64,[])
        self.assertTrue(any(v.get("ownership_validated") is False for v in events))
        self.assertTrue(any(v.get("child_termination_observed") is True and v["exit_code"]==0 for v in events))
    def test_primary_survives_cleanup_behavior(self):
        h=self.h;ref={"path":"/raw","sha256":"0"*64};primary=ValueError("PRIMARY exact ownership")
        class P:
            returncode=None
            def poll(self):return None
            def wait(self,**a):raise RuntimeError("SECONDARY wait")
        p=P()
        class File:
            def __enter__(self):return self
            def __exit__(self,*a):return False
        with patch.object(Path,"open",return_value=File()),patch.object(h.subprocess,"Popen",return_value=p),\
             patch.object(h,"capture",side_effect=primary),patch.object(h,"inspect",side_effect=RuntimeError("SECONDARY inspect")),\
             patch.object(h,"write",return_value=ref),patch.object(h,"sha",return_value="0"*64):
            with self.assertRaises(ValueError) as got:
                h.observe_child("a"*64,"diagnostic",["/usr/bin/docker","exec","a"*64,"/usr/local/python3.12.13/bin/python3"],"replay",h.time.monotonic()+1000,"c"*64,[])
        self.assertIs(got.exception,primary)
    def test_default_no_import_torch(self):
        for name in ("replay.py","host.py"):
            tree=ast.parse((HERE/name).read_text())
            self.assertFalse(any(isinstance(x,ast.Import) and any(a.name in ("torch","torch_npu") for a in x.names)
                                 for x in tree.body))
    def test_budget_time_no_scope_upgrade(self):
        self.assertEqual((self.h.CAP,self.h.CLEANUP),(600,90))
        self.assertEqual(self.r.RAW_BYTES,99004309)
        self.assertEqual(self.r.RAW_SHA,"ff6c632f7655e396d1f9752591688496791538c6b787a2af24fb2f43f9353f14")
        self.assertNotIn("new_single_step_numerical_pass",(HERE/"replay.py").read_text())
if __name__=="__main__":unittest.main()
