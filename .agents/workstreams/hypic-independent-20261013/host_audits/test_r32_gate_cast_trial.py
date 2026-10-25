"""Exercise the real R32 HOST owner/argv/workload boundary without NPU allocation."""
from pathlib import Path
import copy,itertools,json,subprocess,tempfile,unittest
from unittest import mock
from host_audits import r32_gate_cast_trial as owner

W=Path(__file__).resolve().parent.parent
def contract(arm="A1"):
    return json.loads((W/("GATE_CAST_R32_"+arm+"_20261025_CONTRACT.json")).read_text())
EMPTY={"processes":[],"foreign":[],"owners":[],"utc":"HOST_ONLY","raw":"HOST mocked no process table"}

class HostBoundary(unittest.TestCase):
    def test_all_actual_contract_checks_no_device(self):
        for arm in("A1","B1","A2"):
            with self.subTest(arm=arm):
                r=owner.check_contract(contract(arm))
                self.assertFalse(r["device_run"]);self.assertEqual(r["source_bindings"],426)
    def test_one_boolean_difference_and_same_sources(self):
        a,b=contract(),contract("B1")
        self.assertEqual(a["cache_diagnostic"]["source_sha256"],b["cache_diagnostic"]["source_sha256"])
        ma=json.loads((W/a["successor_manifest"]).read_text())
        mb=json.loads((W/b["successor_manifest"]).read_text())
        ca=json.loads((W/ma["config"]).read_text());cb=json.loads((W/mb["config"]).read_text())
        self.assertEqual({k for k in ca if ca[k]!=cb[k]},{"c1_gate_cast_hoist"})
    def test_existing_root_is_rejected_without_deletion(self):
        with tempfile.TemporaryDirectory(dir="/cache/cch")as directory:
            c=contract();c["raw_root"]=directory
            with self.assertRaises(ValueError):owner.check_contract(c)
            self.assertTrue(owner.check_contract(c,require_new_root=False)["configuration_valid"])
    def test_invalid_axis_rejected(self):
        for k,v in(("r32_arm","X"),("enable_prefix_caching",True),("max_output_tokens",1024),("formal_performance",True)):
            c=contract();c[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):owner.check_contract(c)
    def test_actual_base_launch_rewrite_stops_before_docker(self):
        for arm in("A1","B1"):
            with self.subTest(arm=arm),tempfile.TemporaryDirectory(dir="/cache/cch")as directory:
                c=contract(arm);c["raw_root"]=str(Path(directory)/"new-root")
                allocated=[];launches=[]
                real_write=owner.base.write
                def write(root,name,data):
                    if name=="launch.json":launches.append(copy.deepcopy(data))
                    return real_write(root,name,data)
                def command(args,timeout=30):
                    if args[:3]==["docker","image","inspect"]:
                        return json.dumps([{"Config":{"Env":[]}}])
                    if args[:2]==["docker","run"]:
                        allocated.append(args);raise RuntimeError("HOST_STOP_BEFORE_DOCKER_ALLOCATION")
                    if args[:3]==["git","rev-parse","HEAD"]:return"HOST_ONLY"
                    if args[:2]==["ss","-H"]:return""
                    raise AssertionError(args)
                original_slot=owner.workload_slot.run_formal_workload
                with mock.patch.object(owner.base,"write",new=write),mock.patch.object(owner.base,"command",new=command),mock.patch.object(owner.base,"snapshot",return_value=EMPTY),mock.patch.object(owner.base,"port_free",return_value=None):
                    with self.assertRaises(SystemExit):owner.run_contract(c)
                self.assertIs(owner.workload_slot.run_formal_workload,original_slot)
                self.assertEqual(len(allocated),1);self.assertEqual(len(launches),1)
                argv=allocated[0]
                self.assertNotIn("--profiler-config",argv)
                self.assertIn("INDEPENDENT_GRAPH_HYPIC=1",argv)
                self.assertIn("VLLM_LOGGING_LEVEL=INFO",argv)
                self.assertIn("TRITON_CACHE_DIR=/scratch/compiled-cache",argv)
                self.assertEqual(json.loads(argv[argv.index("--compilation-config")+1])["mode"],3)
                self.assertEqual(launches[0]["host_controller_sha256"],c["host_controller_sha256"])
                self.assertFalse(launches[0]["r32_trial"]["profiler_enabled"])
    def test_actual_workload_warms_same_shape_without_profiler_http(self):
        c=contract();n=itertools.count();sent=[];events=[]
        def send(p):
            sent.append(p)
            return{"id":"host-"+str(next(n)),"usage":{"prompt_tokens":len(p["prompt"]),"completion_tokens":p["max_tokens"]},"choices":[{"text":"HOST_ONLY"}]}
        unit=owner.run_unit(c["formal_token_artifact"],send_warmup=send,send_measured=lambda p:(_ for _ in()).throw(AssertionError("diagnostic must use declared full-body HTTP")),guard=lambda:None,record=events.append,require_material_ready=lambda:None)
        self.assertTrue(unit["valid"]);self.assertFalse(unit["profiler_enabled"])
        self.assertEqual(len(unit["results"]),16);self.assertEqual(len(unit["private_warmup_results"]),16)
        self.assertGreater(unit["diagnostic_makespan_seconds"],0)
        names=[e["event"]for e in events]
        self.assertEqual(names.count("r32-private-warmup"),16)
        self.assertEqual(names.count("r32-response"),16)
        self.assertLess(max(i for i,x in enumerate(names)if x=="r32-private-warmup"),names.index("r32-begin"))
        self.assertTrue(all(p["max_tokens"]==64 for p in sent[-32:]))

if __name__=="__main__":unittest.main()
