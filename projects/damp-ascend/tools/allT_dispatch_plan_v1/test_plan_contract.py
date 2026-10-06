#!/usr/bin/env python3
"""No-device/stdlb contract tests. In-memory admission simulations are not device proof."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("damp_allT_dispatch_plan",BASE/"plan.py")
plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)

class DispatchContract(unittest.TestCase):
    def entries(self):
        return [plan.shard("software_contract",p,plan.ROOT/"allT-dispatch-software_contract")
                for p in (4,5,6,7)]

    def simulation(self):
        """Only mutable in-memory Python dicts; never save these as actual records."""
        now=1800000000000000000
        entries=self.entries();records={}
        admission={"schema":"damp_allT_MAIN_live_admission_v1","observed_at_unix_ns":now,
            "capture_operation_id":plan.CAPTURE_OPERATION,"capture_terminal":True,
            "owned_TP4_lease_released":True,"physical_npu_ids":[4,5,6,7],
            "exclusive_resource_check_passed":True,"protected_NPU0_3_unchanged":True,
            "ordinary_mem_available_bytes":plan.AGGREGATE_MIN_BYTES,
            "per_card_cgroup_limit_bytes":plan.PER_CARD_BYTES,
            "free_disk_bytes":plan.DISK_MIN_BYTES,"cards":{},
            "docker_cpu_capacity":{"observed_at_unix_ns":now,
                "info_path":str(plan.ROOT/"allT-dispatch-software_contract/engine-info.json"),
                "info_sha256":"c"*64,"per_numeric_shard_cpu_quota":1,"numeric_shards_cpu_quota":4,
                "optional_selector_cpu_quota":2,"joint_cpu_quota":6,"formal_performance_exclusive":True}}
        records[admission["docker_cpu_capacity"]["info_path"]]={"NCPU":7,"Name":"in-memory-test-only"}
        for e in entries:
            p=e["physical_card"]
            proof={"physical_npu_ids":[p],"logical_to_physical":{"0":p},"privileged":False,
                   "exclusive_resource_check_passed":True,"observed_at_unix_ns":now}
            canary={"schema":"damp_allT_canary_v1","status":"actual_canary_pass",
                "npu_executed":True,"expected_physical_card":p,"logical_device":0,
                "runtime_soc":"Ascend910B4","result":[1.,4.,9.],"completed_at_unix_ns":now,
                "create_argv_sha256":e["create_argv_sha256"],"canary_program_sha256":plan.CANARY_SHA}
            admission["cards"][str(p)]={"container_name":e["container_name"],"container_id":"1"*64,
                "container_image_id":plan.IMAGE,"create_argv_sha256":e["create_argv_sha256"],
                "fresh_created_from_this_plan":True,"inspect_single_card_scope_passed":True,
                "device_proof":e["expected_device_proof_path"],"device_proof_sha256":"a"*64,
                "canary":e["expected_canary_path"],"canary_sha256":"b"*64}
            records[e["expected_device_proof_path"]]=proof
            records[e["expected_canary_path"]]=canary
        return now,entries,admission,records

    def validate_simulation(self,now,entries,admission,records):
        with patch.object(plan,"read_bound",side_effect=lambda path,digest:copy.deepcopy(records[str(path)])), \
             patch.object(Path,"exists",return_value=False):
            return plan.validate_live_admission(admission,entries,plan.gate_contract(),now)

    def test_actual_source_admission_no_device(self):
        s=plan.source_admission()
        self.assertEqual((s["compiled_sources"],s["runtime_sources"]),(9,20))
        self.assertEqual(s["library_sha256"],plan.LIBRARY_SHA)
        self.assertNotIn("torch",sys.modules)
        self.assertNotIn("torch_npu",sys.modules)

    def test_existing_native_identity_and_missing(self):
        native,missing=plan.native_identity()
        self.assertFalse(missing)
        self.assertEqual(native["sha256"],plan.NATIVE_SHA)
        no_identity,missing=plan.native_identity(plan.ROOT/"allT-native-definitely-absent.json")
        self.assertIsNone(no_identity)
        self.assertEqual(missing[0]["stage"],"native_identity")

    def test_real_T_partition_and_no_fabricated_proof(self):
        entries=self.entries()
        self.assertEqual([e["batches"] for e in entries],[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])
        for e in entries:
            self.assertIsNone(e["gate_argv"])
            self.assertIsNone(e["docker_gate_exec_argv"])
            self.assertEqual(e["pending_mandatory_arguments"],["--device-proof","--device-proof-sha256"])
            argv=e["gate_argv_source_bound_incomplete"]
            for flag,value in (("--library",str(plan.LIBRARY)),("--library-sha256",plan.LIBRARY_SHA),
                ("--build-receipt-sha256",plan.RECEIPT_SHA),("--runtime-manifest-sha256",plan.RUNTIME_SHA),
                ("--native-source-manifest",str(plan.NATIVE)),("--native-source-manifest-sha256",plan.NATIVE_SHA)):
                self.assertEqual(argv[argv.index(flag)+1],value)
            self.assertNotIn("--device-proof",argv)
            self.assertTrue(all("<" not in x and "PLACEHOLDER" not in x for x in argv))
            self.assertEqual(plan.argv_sha(e["docker_create_argv"]),e["create_argv_sha256"])

    def test_container_device_and_security_scope(self):
        for e in self.entries():
            argv=e["docker_create_argv"]
            devices=[argv[i+1] for i,x in enumerate(argv) if x=="--device"]
            self.assertEqual(devices,["/dev/davinci"+str(e["physical_card"])+":/dev/davinci0",
                                     "/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"])
            for flag,value in (("--memory","8g"),("--memory-swap","8g"),("--network","none"),
                               ("--cap-drop","ALL"),("--security-opt","no-new-privileges"),("--cpus","1")):
                self.assertEqual(argv[argv.index(flag)+1],value)
            self.assertNotIn("--privileged",argv)
            self.assertNotIn("--rm",argv)
            self.assertEqual(argv[argv.index("--entrypoint")+1],"/bin/bash")
            self.assertIn(plan.IMAGE,argv)

    def test_mount_scope_and_control_paths(self):
        for e in self.entries():
            argv=e["docker_create_argv"]
            mounts=[argv[i+1] for i,x in enumerate(argv) if x=="--mount"]
            ro=[m for m in mounts if m.endswith(",readonly")]
            rw=[m for m in mounts if not m.endswith(",readonly")]
            self.assertEqual(len(ro),5)
            self.assertEqual(rw,["type=bind,source="+e["host_output_mount"]+",target="+e["host_output_mount"]])
            for path in (plan.REPO,plan.BUILD,plan.NATIVE_REFERENCE,plan.NATIVE,Path("/usr/local/Ascend/driver")):
                self.assertIn("type=bind,source="+str(path)+",target="+str(path)+",readonly",ro)

    def test_reject_unsafe_id_card_output(self):
        for run in ("../escape","v1;id","BAD","a"*33,""):
            with self.assertRaises(ValueError):plan.shard(run,4,plan.ROOT/("allT-dispatch-"+run))
        for p in (0,1,2,3,8,True,"4"):
            with self.assertRaises(ValueError):plan.shard("software_contract",p,plan.ROOT/"allT-dispatch-software_contract")
        for root in (Path("/"),plan.REPO,plan.ROOT,plan.ROOT/"different"):
            with self.assertRaises(ValueError):plan.shard("software_contract",4,root)

    def test_simulated_complete_argv_is_not_execution(self):
        now,entries,admission,records=self.simulation()
        result=self.validate_simulation(now,entries,admission,records)
        self.assertEqual(result["total_cgroup_bytes"],32*plan.GIB)
        self.assertEqual(result["reserve_bytes"],8*plan.GIB)
        self.assertEqual(result["joint_cpu_quota"],6)
        self.assertEqual(result["docker_ncpu"],7)
        for e in entries:
            self.assertEqual(e["gate_argv"][-4:],["--device-proof",e["expected_device_proof_path"],
                                                 "--device-proof-sha256","a"*64])
            self.assertEqual(e["docker_gate_exec_argv"][:3],["docker","exec",e["container_name"]])
            self.assertFalse(e["pending_mandatory_arguments"])

    def test_simulated_invalid_resource_and_capture_rejected(self):
        for key,value in (("capture_terminal",False),("owned_TP4_lease_released",False),
            ("capture_operation_id","wrong"),("protected_NPU0_3_unchanged",False),
            ("exclusive_resource_check_passed",False),("ordinary_mem_available_bytes",plan.AGGREGATE_MIN_BYTES-1),
            ("free_disk_bytes",plan.DISK_MIN_BYTES-1),("physical_npu_ids",[0,1,2,3]),
            ("observed_at_unix_ns",1800000000000000000-301*10**9)):
            now,entries,admission,records=self.simulation();admission[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.validate_simulation(now,entries,admission,records)

    def test_simulated_canary_container_and_mapping_rejected(self):
        for target,key,value in (("container","container_image_id","wrong"),
            ("container","create_argv_sha256","0"*64),("container","inspect_single_card_scope_passed",False),
            ("canary","status","failed"),("canary","npu_executed",False),
            ("canary","canary_program_sha256","0"*64),("canary","expected_physical_card",0),
            ("canary","completed_at_unix_ns",1800000000000000000-301*10**9),
            ("proof","logical_to_physical",{"0":0}),("proof","privileged",True)):
            now,entries,admission,records=self.simulation()
            obj=(admission["cards"]["4"] if target=="container" else
                 records[entries[0]["expected_canary_path" if target=="canary" else "expected_device_proof_path"]])
            obj[key]=value
            with self.subTest(target=target,key=key),self.assertRaises(ValueError):
                self.validate_simulation(now,entries,admission,records)

    def test_simulated_missing_stale_or_insufficient_Docker_NCPU_rejected(self):
        now,entries,admission,records=self.simulation()
        admission.pop("docker_cpu_capacity")
        with self.assertRaises(ValueError):self.validate_simulation(now,entries,admission,records)
        for ncpu in (0,4,5,6.0,True):
            now,entries,admission,records=self.simulation()
            records[admission["docker_cpu_capacity"]["info_path"]]["NCPU"]=ncpu
            with self.subTest(NCPU=ncpu),self.assertRaises(ValueError):
                self.validate_simulation(now,entries,admission,records)
        for field,value in (("observed_at_unix_ns",1800000000000000000-301*10**9),
            ("per_numeric_shard_cpu_quota",2),("numeric_shards_cpu_quota",8),
            ("optional_selector_cpu_quota",8),("joint_cpu_quota",10),
            ("formal_performance_exclusive",False)):
            now,entries,admission,records=self.simulation()
            admission["docker_cpu_capacity"][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                self.validate_simulation(now,entries,admission,records)

    def test_source_bound_cli_pending_only(self):
        with patch.object(Path,"exists",return_value=False):
            result=plan.make_plan("software_contract",plan.ROOT/"allT-dispatch-software_contract")
        self.assertEqual(result["status"],"waiting_MAIN_live_admission")
        self.assertIs(result["executed"],False)
        self.assertIs(result["npu_executed"],False)
        self.assertEqual(len(result["shards"]),4)
        self.assertIsNone(result["shards"][0]["gate_argv"])
        self.assertEqual(result["aggregate_ram_min_bytes"],40*plan.GIB)
        self.assertEqual(result["cpu_policy"]["joint_cpu_quota"],6)
        self.assertIs(result["cpu_policy"]["needs_MAIN_fresh_actual_Docker_NCPU"],True)

    def test_generator_no_execution_or_writes(self):
        tree=ast.parse((BASE/"plan.py").read_text())
        imports={a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertFalse(imports & {"torch","torch_npu","subprocess","ctypes","os"})
        for n in ast.walk(tree):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
                self.assertNotIn(n.func.attr,{"system","Popen","run","check_call","check_output",
                    "write","write_text","write_bytes","mkdir","unlink","remove","rmdir","exec"})
        ast.parse(plan.CANARY_CODE)  # Future emitted program syntax only; never import/execute it.

if __name__=="__main__":
    unittest.main(verbosity=2)
