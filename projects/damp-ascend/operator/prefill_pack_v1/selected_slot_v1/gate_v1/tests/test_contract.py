"""Pure stdlib source/oracle/evidence contract tests. NO Torch import."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import random
import sys
import unittest
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from selected_contract import (GUARD,status_rows,selection,arena_layout,validate_proof,
                               validate_build,COMPILED,SELECTED_MANIFEST_SHA,SELECTED_SO_SHA,IMAGE,OPP_SHA)
from fraction_locator import divide
FLOAT_ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location("independent_float_div",FLOAT_ROOT/"independent_float_div.py")
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)

class Contract(unittest.TestCase):
    def test_status_all_heads_and_complete_guards(self):
        values=[GUARD]*8+[1,0,4,0,16384,16384,0,0]*12+[GUARD]*8
        self.assertEqual(len(status_rows(values,1)),12)
        for i in (0,8,9,10,11,12,13,14,15,len(values)-1):
            bad=values.copy();bad[i]+=1
            with self.assertRaises(RuntimeError):status_rows(bad,1)
    def test_metadata_zero_writer(self):
        values=[GUARD]*8+[0,1,0,0,0,16384,0,0]*192+[GUARD]*8
        status_rows(values,16,1)
        values[10]=1
        with self.assertRaises(RuntimeError):status_rows(values,16,1)
    def test_numeric_partial_retirement(self):
        values=[GUARD]*8+[1,0,4,0,16384,16384,0,0]*12+[GUARD]*8
        values[8:16]=[0,2,2,0,10000,16384,0,0]
        status_rows(values,1,2)
    def test_real_unique_selected_slots(self):
        for p in range(1,17):
            for turn in range(20):
                ids=selection(p,p+3,turn)
                self.assertEqual(len(ids),p);self.assertEqual(len(set(ids)),p)
                self.assertTrue(all(0<=i<p+3 for i in ids))
        self.assertEqual(selection(1,4,0),[0]);self.assertEqual(selection(1,4,1),[3])
    def test_arena_shared_exact_geometry(self):
        for slots in (4,19):
            for kind in ("adjacent","guard_gaps"):
                rows=arena_layout(slots,kind)["regions"]
                self.assertEqual([r["width"] for r in rows],[2,2,1,4])
                for row in rows:self.assertEqual(row["start"]%32,0);self.assertEqual(row["stop"]%32,0)
                self.assertTrue(all(a["stop"]<=b["start"] for a,b in zip(rows,rows[1:])))
    def test_device_proof(self):
        for card in (4,5,6,7):
            p={"physical_npu_ids":[card],"logical_to_physical":{"0":card},"privileged":False,
               "exclusive_resource_check_passed":True,"observed_at_unix_ns":100}
            self.assertTrue(validate_proof(p,card,100))
            for key,value in (("physical_npu_ids",[0]),("privileged",True),
                              ("observed_at_unix_ns",101),("exclusive_resource_check_passed",False)):
                bad=dict(p);bad[key]=value
                with self.assertRaises(RuntimeError):validate_proof(bad,card,100)
    def test_exact_locator_all_boundaries(self):
        scale_bits=[1,2,0x007fffff,0x00800000,0x00800001,0x3f800000,0x3f8ccccd,0x7f7fffff]
        xbits=[0,1,2,0x007fffff,0x00800000,0x00800001,0x3f7fffff,0x3f800000,
               0x3f800001,0x477fefff,0x477ff000,0x7f7fffff]
        for x in xbits:
            for s in scale_bits:
                for sign in (0,0x80000000):
                    self.assertEqual(divide(x|sign,s),oracle.oracle(x|sign,s))
    def test_exact_locator_random(self):
        rng=random.Random(260627513)
        for _ in range(3000):
            x=rng.randrange(0x7f800000)|(rng.randrange(2)<<31)
            s=rng.randrange(1,0x7f800000)
            self.assertEqual(divide(x,s),oracle.oracle(x,s))
    def test_invalid_float_inputs(self):
        for x,s in ((0x7fc00000,0x3f800000),(1,0),(1,0x80000000),(1,0xff800000)):
            self.assertEqual(divide(x,s),(False,False,0))
    def test_default_off_before_torch(self):
        source=(HERE/"run.py").read_text()
        tree=ast.parse(source)
        module_imports=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any("torch" in ast.unparse(n) for n in module_imports))
        self.assertIn('if not args.execute:',source)
        self.assertLess(source.index('binding=admission(args)'),source.index('    import torch\n'))
        self.assertIn('exist_ok=False',source)
        self.assertNotIn('torch.ops =',source)
    def test_evidence_poisoned_copy_preserved(self):
        source=(HERE/"evidence.py").read_text()
        self.assertIn('"dispatch_error":dispatch_error',source)
        self.assertIn('"output_copy_errors":output_errors',source)
        self.assertIn('"input_copy_errors":input_errors',source)
        self.assertLess(source.index('gate.fixture[label]=record'),source.index('return device_out'))
        self.assertIn('snapshot(self.torch,self.fixture,errors)',source)
    def test_native_apis_not_fake_globals(self):
        source=(HERE/"native_feedback.py").read_text()
        self.assertIn('initialize_model_parallel(',source)
        self.assertIn('override_forward_context(context)',source)
        self.assertIn('backend="gloo"',source)
        self.assertNotIn('_PCP=',source);self.assertNotIn('get_pcp_group=lambda',source)
        self.assertIn('prebuilt_meta=None',source)
        self.assertIn('range(160)',source)
    def test_real_repo_and_integration_paths(self):
        import run
        self.assertEqual(run.REPO,HERE.parents[5])
        self.assertTrue((run.PROJECT/"tests/independent_oracle.py").is_file())
        source=(HERE/"native_feedback.py").read_text()
        self.assertIn('sys.path.insert(0,str(PROJECT/"integration"))',source)
        self.assertNotIn('parents[5]/"projects/damp',source)
    def test_actual_allbatch_build_contract(self):
        from selected_contract import require_decode_admission,ALL_BATCH_COMPILED,ALL_BATCH_SO_SHA
        receipt={
          "cann_identity": {
            "opp_version_info_sha256": "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6",
            "root": "/usr/local/Ascend/cann-9.1.0",
            "version_info": "Version=9.1.0\nversion_dir=cann\nrequired_package_runtime_version=\">=8.5\"\nrequired_package_ge-executor_version=\">=8.5\"\nrequired_package_metadef_version=\">=8.5\"\nrequired_package_asc-devkit_version=\">=8.5\"\nrequired_package_bisheng-compiler_version=\">=8.5\"\ntimestamp=20260730_231653901\n"
          },
          "cann_version_info_sha256": "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6",
          "commands": [
            {
              "command": [
                "/usr/local/python3.12.13/bin/python3",
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "/opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/all_batch_wrapper_v3/tests",
                "-p",
                "test_all_batch_contract.py",
                "-v"
              ],
              "exit_code": 0,
              "log_path": "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/phase-0.log",
              "log_sha256": "2a74fd54195a7afa142f0a9ec00272991a1c6c71d7f09ff4f54a055b600e054e"
            },
            {
              "command": [
                "cmake",
                "-S",
                "/opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/all_batch_wrapper_v3",
                "-B",
                "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3",
                "-DDAMP_BUILD_ALL_BATCH_WRAPPER_V3=ON"
              ],
              "exit_code": 0,
              "log_path": "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/phase-1.log",
              "log_sha256": "e0731e4b1762e182925a8cce537c2a4e0eb33b5531f58b8cc973a03dfa4b0be6"
            },
            {
              "command": [
                "cmake",
                "--build",
                "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake",
                "-j2"
              ],
              "exit_code": 0,
              "log_path": "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/phase-2.log",
              "log_sha256": "828df840259d5181e00fefc2590390c55a0350804fe4a59b71dc09992849619a"
            }
          ],
          "completed_utc": "2026-10-06T15:10:36.704080+00:00",
          "exported_kernel": {
            "audit_path": "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/elf-dynamic-symbols.json",
            "audit_sha256": "b35eafb241269093c91942842a65f1219dfbc75b6a8727996b99cb16cece634e",
            "defined": True,
            "name": "qwen36_gdn_damp_all_batch_v3_decode_kernel",
            "type": "T"
          },
          "image_id": "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
          "kernel_symbols": [
            "00000000000ad290 T qwen36_gdn_damp_all_batch_v3_decode_kernel"
          ],
          "library_sha256": "a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade",
          "namespace": "qwen36_damp_all_batch_v3",
          "npu_arch": "dav-2201",
          "npu_executed": False,
          "schema": "damp_all_batch_wrapper_build_v3",
          "serving_ready": False,
          "source_manifest_sha256": "a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958",
          "sources": {
            "projects/damp-ascend/operator/all_batch_wrapper_v3/CMakeLists.txt": "febb3e7e7dd955c98c8ca1e054afedeb77cdd6512040cf4d3551a950deb24561",
            "projects/damp-ascend/operator/all_batch_wrapper_v3/op_extension/ops.h": "8f103382816ac8e4206ebd24f996f41186f5d92f6ace9918362936191c7e8b84",
            "projects/damp-ascend/operator/all_batch_wrapper_v3/op_extension/qwen36_gdn_damp_all_batch_v3_decode_torch.cpp": "b8c0304b9efb13c03537894549c9e3028bd7a4e866305b2b86122875f5b45812",
            "projects/damp-ascend/operator/all_batch_wrapper_v3/op_extension/register.cpp": "cdfac8e115b450262d372aa76b464fb1c4948d88b8f906cef4e9c7fe2950ac08",
            "projects/damp-ascend/operator/all_batch_wrapper_v3/op_kernel/qwen36_gdn_damp_all_batch_v3_decode.h": "16505660b4c4714bfb3c7ab5cbc3b5330eec88337f693ecdd4c48a79ab2db60e",
            "projects/damp-ascend/operator/all_batch_wrapper_v3/op_kernel/qwen36_gdn_damp_all_batch_v3_decode_kernel.asc": "5bfc1847a8a117b9ca0b8fcdf947a41a876009bf593174dcebdfc91f77e1b66b",
            "projects/damp-ascend/operator/production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h": "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc",
            "projects/damp-ascend/operator/quantizer/exact_quantizer_bits.h": "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
            "projects/damp-ascend/operator/quantizer/fast_integer_certificate/integer_certificate_ascendc.h": "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb"
          },
          "started_utc": "2026-10-06T15:07:24.963212+00:00",
          "status": "compiled_no_device"
        }
        manifest={"namespace":"qwen36_damp_all_batch_v3","compiled_sources":ALL_BATCH_COMPILED}
        self.assertTrue(require_decode_admission(receipt,manifest,ALL_BATCH_SO_SHA))
        for field,value in (("schema","old_schema"),("npu_executed",True),
                ("serving_ready",True),("library_sha256","0"*64),("namespace","old")):
            bad=copy.deepcopy(receipt);bad[field]=value
            with self.assertRaises(RuntimeError):require_decode_admission(bad,manifest,ALL_BATCH_SO_SHA)
        bad=copy.deepcopy(receipt);bad["exported_kernel"]["type"]="U"
        with self.assertRaises(RuntimeError):require_decode_admission(bad,manifest,ALL_BATCH_SO_SHA)
    def test_actual_selected_build_contract(self):
        receipt={
          "cann_identity": {
            "opp_version_info": "Version=9.1.0\nversion_dir=cann\nrequired_package_runtime_version=\">=8.5\"\nrequired_package_ge-executor_version=\">=8.5\"\nrequired_package_metadef_version=\">=8.5\"\nrequired_package_asc-devkit_version=\">=8.5\"\nrequired_package_bisheng-compiler_version=\">=8.5\"\ntimestamp=20260730_231653901\n",
            "opp_version_info_path": "/usr/local/Ascend/cann-9.1.0/opp/version.info",
            "opp_version_info_sha256": "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6"
          },
          "cann_version_info_sha256": "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6",
          "commands": [
            {
              "command": [
                "/usr/local/python3.12.13/bin/python3",
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "/opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/tests",
                "-p",
                "test_selected_contract.py",
                "-v"
              ],
              "exit_code": 0,
              "log_path": "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/phase-0.log",
              "log_sha256": "b0913abd3acf1874b4fcf3faa64cd20017ce2053cc062ebc0d19c4227a810ceb"
            },
            {
              "command": [
                "cmake",
                "-S",
                "/opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1",
                "-B",
                "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3",
                "-DDAMP_BUILD_SELECTED_PREFILL_V1=ON"
              ],
              "exit_code": 0,
              "log_path": "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/phase-1.log",
              "log_sha256": "c26a8b3f4a67b2e9a5681de898885146cfba23d2df0b6cb4a223b469d8a11850"
            },
            {
              "command": [
                "cmake",
                "--build",
                "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build",
                "-j2"
              ],
              "exit_code": 0,
              "log_path": "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/phase-2.log",
              "log_sha256": "9fa045a5b091cf1aed6c2daa1fb704b9e556e892386192fa8f9012880cd0a8cc"
            }
          ],
          "exported_kernel": {
            "audit_path": "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/elf-dynamic-symbols.json",
            "audit_sha256": "72162b443e99005946c6621cc202db1a29e9f12a3675bb807aace5039aa73bf0",
            "defined": True,
            "name": "qwen36_damp_selected_prefill_pack_kernel",
            "type": "T"
          },
          "image_id": "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
          "kernel_symbols": [
            "00000000000ad7d0 T qwen36_damp_selected_prefill_pack_kernel"
          ],
          "library_sha256": "28684cb4f502ead28fd9974a54f420d0ec027de19ccc6728ba3942209fc910d7",
          "namespace": "qwen36_damp_selected_prefill_v1",
          "npu_arch": "dav-2201",
          "npu_executed": False,
          "schema": "damp-selected-prefill-build/v1",
          "serving_ready": False,
          "source_manifest_sha256": "5670a88c77fde9fd81abadcb7c88d2b3f6bb684928e24f445a3a1d3a67f0a8bf",
          "sources": {
            "projects/damp-ascend/operator/prefill_pack_v1/exact_float_div_bits.h": "bca2ab982ac57ebed71efa4145281b5ee37faa5ec46cc0beccddf9d83eb2ae04",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/CMakeLists.txt": "269966c5f70b5b1d57ff8c0f7e53b9c98bef6b96765829f9cb5d30617ac877ac",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/ops.h": "8554be1ec4c86b81f472787ae98c6e2a51ec4fad2e422bcdadef3af9dbdf481d",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/register.cpp": "bd94f4c761769bb40636f3b12ed5c6cabc2aae1316d344143bab19fb8c3c5571",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/selected_prefill_torch.cpp": "dd03d2c2b56397566507952fc962b3336ac054ebd85b803eb6cd892c0b0e2236",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_kernel/prefill_plan.h": "449c36746067c784f0f7612e526ea836556247aa0b660a68d2c0b04b75a11aa1",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_kernel/selected_prefill.h": "e2355651657152c8b3bc530f4cab805d4bae6cbcfec329f11e018150196e5c30",
            "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_kernel/selected_prefill_kernel.asc": "87a67006ad535a9101304f329ad496a1dcc291f259e1b87bab4191f3ca5f01d4",
            "projects/damp-ascend/operator/production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h": "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc",
            "projects/damp-ascend/operator/quantizer/exact_quantizer_bits.h": "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
            "projects/damp-ascend/operator/quantizer/fast_integer_certificate/integer_certificate_ascendc.h": "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb"
          },
          "started_utc": "2026-10-06T16:19:55.937542+00:00",
          "status": "compiled_no_device"
        }
        validate_build(receipt)
        for field,value in (("npu_executed",True),("schema","unknown"),("npu_arch","dav-3510")):
            bad=copy.deepcopy(receipt);bad[field]=value
            with self.assertRaises(RuntimeError):validate_build(bad)
    def test_feedback_fixture_before_clone_survives_inplace_update(self):
        # Execute the actual fixture assignment from feedback's loop, not a
        # hand-written replacement. The old getattr(golden,n) fails this test.
        from types import SimpleNamespace
        tree=ast.parse((HERE/"native_feedback.py").read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="feedback")
        loop=next(n for n in fn.body if isinstance(n,ast.For))
        nodes=[]
        for n in loop.body:
            if not isinstance(n,ast.Assign):continue
            if any(isinstance(t,ast.Name) and t.id=="golden_before" for t in n.targets):
                nodes.append(n)
            if any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and
                   t.value.id=="gate" and t.attr=="fixture" for t in n.targets):
                nodes.append(n)
        self.assertEqual(len(nodes),2)
        class Plane:
            def __init__(self,values):self.values=list(values)
        class Packed:
            def __init__(self):
                self.high=Plane([1]);self.low=Plane([2]);self.scales=Plane([3])
            def clone(self):
                p=Packed()
                for name in ("high","low","scales"):
                    getattr(p,name).values=getattr(self,name).values.copy()
                return p
        golden=Packed();gate=SimpleNamespace(fixture={})
        env={"golden":golden,"gate":gate,"REGIONS":("high","low","scales"),
             "label":"actual","index":0,"q":None,"k":None,"v":None,"g":None,
             "beta":None,"ids":None,"before":b"before"}
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
                     "actual_feedback_fixture_fragment","exec"),env)
        for name in ("high","low","scales"):
            getattr(golden,name).values[0]=999
        self.assertEqual([gate.fixture["golden_before"][n].values for n in ("high","low","scales")],
                         [[1],[2],[3]])
    def test_ast_all_sources(self):
        for path in HERE.glob("*.py"):ast.parse(path.read_text(),filename=str(path))
class PoisonedEvidence(unittest.TestCase):
    def test_copy_errors_cannot_hide_original_dispatch(self):
        from types import SimpleNamespace
        from evidence import observe
        class Tensor:
            def __init__(self):self.poison=False
            def detach(self):return self
            def cpu(self):
                if self.poison:raise RuntimeError("secondary D2H poisoned")
                return self
            def contiguous(self):return self
            def clone(self):return self
            def data_ptr(self):return 64
            def untyped_storage(self):return SimpleNamespace(data_ptr=lambda:64,nbytes=lambda:32)
            def storage_offset(self):return 0
            def stride(self):return (1,)
            shape=(8,)
            dtype="INT32"
        value=Tensor();gate=SimpleNamespace(fixture={},last=None)
        fake=SimpleNamespace(Tensor=Tensor,npu=SimpleNamespace(synchronize=lambda:None))
        def dispatch():
            value.poison=True
            raise RuntimeError("ORIGINAL_DISPATCH")
        out,cpu,after,record=observe(fake,gate,"fail",dispatch,[value])
        self.assertIn("ORIGINAL_DISPATCH",record["dispatch_error"]["error"])
        self.assertIsNone(after[0]);self.assertEqual(len(record["input_copy_errors"]),1)
        self.assertIn("before",gate.fixture["fail"])
        self.assertIs(gate.fixture["fail"]["before"][0],value)
    def test_pointer_after_error_preserves_original_dispatch_and_record(self):
        from types import SimpleNamespace
        from evidence import observe
        class Tensor:
            poison=False
            def detach(self):return self
            def cpu(self):return self
            def contiguous(self):return self
            def clone(self):return self
            def data_ptr(self):
                if self.poison:raise RuntimeError("AFTER_POINTER_POISONED")
                return 64
            def untyped_storage(self):return SimpleNamespace(data_ptr=lambda:64,nbytes=lambda:32)
            def storage_offset(self):return 0
            def stride(self):return (1,)
            shape=(8,);dtype="INT32"
        value=Tensor();gate=SimpleNamespace(fixture={},last=None)
        fake=SimpleNamespace(Tensor=Tensor,npu=SimpleNamespace(synchronize=lambda:None))
        def dispatch():
            value.poison=True
            raise RuntimeError("ORIGINAL_DISPATCH")
        out,cpu,after,record=observe(fake,gate,"pointer_fail",dispatch,[value])
        self.assertIn("ORIGINAL_DISPATCH",record["dispatch_error"]["error"])
        self.assertIsNone(record["pointers_after"])
        self.assertEqual(len(record["pointer_query_errors"]),1)
        self.assertIn("AFTER_POINTER_POISONED",record["pointer_query_errors"][0]["error"])
        self.assertIs(gate.fixture["pointer_fail"],record)
        self.assertIs(gate.last,record)
        self.assertEqual(record["output_copy_errors"],[])
        self.assertEqual(record["input_copy_errors"],[])
    def test_safe_json_nonfinite_kept(self):
        from evidence import safe_json
        self.assertEqual(safe_json({"x":float("inf")}),{"x":{"nonfinite":"inf"}})

if __name__=="__main__":unittest.main()
