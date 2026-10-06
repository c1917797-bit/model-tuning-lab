"""CPU dispatch planning fixtures. No Docker, Torch, devices or selector execution."""
import ast
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).parent))
import plan as p

class PlanTests(unittest.TestCase):
    def test_plan_cannot_launch_from_missing_parent(self):
        parent=SimpleNamespace(PLANS=p.RESULTS/"calibration-plans-v1")
        result=p.packet(parent,[])
        self.assertIsNone(result["selector_create_argv"])
        self.assertFalse(result["launchable"])
        self.assertFalse(result["reference_finalized"])
        self.assertFalse(result["npu_executed"])
    def test_finalized_parent_still_not_resource_admission(self):
        parent=SimpleNamespace(PLANS=p.RESULTS/"calibration-plans-v1",finalized=Mock())
        result=p.packet(parent,[],"a"*64,"b"*64)
        parent.finalized.assert_called_once_with("a"*64,"b"*64)
        self.assertTrue(result["reference_finalized"])
        self.assertFalse(result["launchable"])
        args=result["selector_create_argv"]
        self.assertIn("DAMP_POST_REFERENCE_CPU_EXECUTE=1",args)
        self.assertIn("--execute",args)
        self.assertNotEqual(result["container_name"],result["canary_name"])
    def test_canary_and_selector_distinct(self):
        args=p.create_argv([])
        self.assertEqual(args[args.index("--name")+1],p.CANARY_NAME)
        self.assertNotIn("--execute",args)
    def test_no_device_or_privilege(self):
        args=p.create_argv([])
        self.assertNotIn("--device",args)
        self.assertNotIn("--privileged",args)
        self.assertNotIn("--ipc=host",args)
        self.assertNotIn("--net=host",args)
        self.assertEqual(args[args.index("--network")+1],"none")
    def test_exact_cpu_resource_bound(self):
        args=p.create_argv([])
        self.assertEqual(args[args.index("--memory")+1],"4g")
        self.assertEqual(args[args.index("--memory-swap")+1],"4g")
        self.assertEqual(args[args.index("--cpus")+1],"2")
        self.assertIn("ASCEND_RT_VISIBLE_DEVICES=",args)
        self.assertIn("CUDA_VISIBLE_DEVICES=",args)
        self.assertIn("TORCH_DEVICE_BACKEND_AUTOLOAD=0",args)
    def test_protected_children_ro(self):
        children=[p.RESULTS/"full-reference-resume-v1-on",p.RESULTS/"calibration-inputs"]
        args=p.create_argv(children)
        mounts=[args[i+1] for i,a in enumerate(args) if a=="--mount"]
        self.assertTrue(all(any("src="+str(x)+"," in m and m.endswith(",readonly") for m in mounts)
            for x in children))
    def test_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);output=root/"plans";output.mkdir()
            with self.assertRaises(ValueError):p.protection_roots(root,output)
    def test_fresh_protected_children(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"existing").mkdir()
            (root/"evidence.json").write_text("{}")
            self.assertEqual([x.name for x in p.protection_roots(root,root/"plans")],
                ["evidence.json","existing"])
    def test_parent_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(ValueError):p.protection_roots(root,root/"nested/plans")
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"existing").mkdir()
            (root/"alias").symlink_to(root/"existing",target_is_directory=True)
            with self.assertRaises(ValueError):p.protection_roots(root,root/"plans")
    def test_bounded_mount_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for i in range(257):(root/str(i)).mkdir()
            with self.assertRaises(ValueError):p.protection_roots(root,root/"plans")
    def test_no_top_level_hardware_or_subprocess(self):
        tree=ast.parse((Path(__file__).parent/"plan.py").read_text())
        modules=[alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names]
        self.assertNotIn("torch",modules);self.assertNotIn("subprocess",modules)
        self.assertNotIn("torch_npu",sys.modules)
    def test_actual_parent_pins_stdlib(self):
        parent=p.parent_contract()
        self.assertEqual(parent.IMAGE,p.IMAGE)
        self.assertNotIn("torch",sys.modules)
    def test_cpu_gate_never_task_claim(self):
        parent=SimpleNamespace(PLANS=p.RESULTS/"calibration-plans-v1")
        packet=p.packet(parent,[])
        self.assertIn("task accuracy",packet["not_proven"])
        self.assertEqual(packet["host_mem_required_bytes"],12*p.GIB)
        self.assertEqual(packet["ordinary_host_reserve_bytes"],8*p.GIB)
        self.assertEqual(packet["with_four_allT_shards_host_mem_required_bytes"],44*p.GIB)

if __name__=="__main__":unittest.main()
