import ast,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import contract
class ShortHorizon(unittest.TestCase):
 def test_source_closure(self):
  ref={"path":str(HERE/"SOURCE_MANIFEST.json"),"sha256":contract.sha(HERE/"SOURCE_MANIFEST.json")}
  m,s=contract.source_admission(ref)
  self.assertEqual(len(s),79);self.assertEqual(m["materialization_interval"],8)
 def test_only_registered_operator_delta(self):
  for name in ["CMakeLists.txt","op_extension/ops.h","op_extension/qwen36_gdn_kvbuffer_short_horizon_v3_torch.cpp","op_extension/register.cpp","op_kernel/qwen36_gdn_kvbuffer_short_horizon_v3_kernel.asc","op_kernel/qwen36_gdn_kvbuffer_short_horizon_v3_tiling.h","op_kernel/qwen36_gdn_kvbuffer_short_horizon_v3.h"]:
   oldname=name.replace("short_horizon_v3","native_order_v2")
   a=(PROJECT/"operator/native_order_v2"/oldname).read_text()
   e=a.replace("native_order_v2","short_horizon_v3").replace("NATIVE_ORDER_V2","SHORT_HORIZON_V3").replace("NativeOrderV2","ShortHorizonV3")
   if name.endswith("/qwen36_gdn_kvbuffer_short_horizon_v3.h"):
    e=e.replace("constexpr uint32_t LOG_CAPACITY = 16;","constexpr uint32_t LOG_CAPACITY = 16;\n// Keep sixteen-lane storage and the four-level tree fold unchanged.\n// This independently named adaptation bounds deferred history at eight steps.\nconstexpr uint32_t FLUSH_INTERVAL = 8;\nstatic_assert(FLUSH_INTERVAL > 1 && FLUSH_INTERVAL <= LOG_CAPACITY,\n              \"deferred materialization horizon must fit the retained ABI\");")
    e=e.replace("lv>=static_cast<int32_t>(LOG_CAPACITY)","lv>=static_cast<int32_t>(FLUSH_INTERVAL)").replace("length+1==LOG_CAPACITY","length+1==FLUSH_INTERVAL")
   self.assertEqual((PROJECT/"operator/short_horizon_v3"/name).read_text(),e)
 def test_storage_tree_abi_unchanged(self):
  s=(PROJECT/"operator/short_horizon_v3/op_kernel/qwen36_gdn_kvbuffer_short_horizon_v3.h").read_text()
  for token in ("LOG_CAPACITY = 16;","FLUSH_INTERVAL = 8;","META_STRIDE = 32;","half = LOG_CAPACITY / 2","Four levels: result is back","DataCopyParams{16,1,3,0}","DataCopyParams{16,8,8,0}"):self.assertIn(token,s)
 def test_oracle_exact_registered_boundary_only(self):
  old=(PROJECT/"tools/split_gate_v2/oracle.py").read_text()
  e=old.replace("qwen36_kvbuffer_native_order_v2","qwen36_kvbuffer_short_horizon_v3").replace("OUT_LIMIT, STATE_LIMIT = .00303, 2e-6","FLUSH_INTERVAL, LOG_CAPACITY = 8, 16\nOUT_LIMIT, STATE_LIMIT = .00303, 2e-6").replace("0<=lengths[0]<16","0<=lengths[0]<FLUSH_INTERVAL").replace("if l==15:","if l==FLUSH_INTERVAL-1:").replace("!=15)","!=FLUSH_INTERVAL-1)").replace("==15 for s in ids","==FLUSH_INTERVAL-1 for s in ids")
  self.assertEqual((HERE/"oracle.py").read_text(),e)
 def test_oracle_thresholds_and_coverage(self):
  t=ast.parse((HERE/"oracle.py").read_text())
  env={}
  for node in t.body:
   if isinstance(node,ast.Assign):
    try:
     val=ast.literal_eval(node.value)
     if len(node.targets)==1 and isinstance(node.targets[0],ast.Tuple):
      for n,v in zip(node.targets[0].elts,val):env[n.id]=v
    except (ValueError,TypeError):pass
  self.assertEqual((env["OUT_LIMIT"],env["STATE_LIMIT"]),(.00303,2e-6))
  s=(HERE/"oracle.py").read_text()
  self.assertIn("range(160)",s);self.assertIn("step in (64,112)",s)
  self.assertIn("lambda_log\"][:,:,:16]",s)
 def test_boundary_repeats_reset(self):
  length=0;merges=[]
  for n in range(1,161):
   if length+1==8:length=0;merges.append(n)
   else:length+=1
   self.assertTrue(0<=length<8)
  self.assertEqual(merges,list(range(8,161,8)))
 def test_protocol_binds_both_capacities(self):
  p=contract.protocol(16,6)
  self.assertEqual((p["materialization_interval"],p["storage_log_capacity"]),(8,16))
  self.assertEqual(p["candidate_namespace"],"qwen36_kvbuffer_short_horizon_v3")
 def test_default_off_cli_and_builder(self):
  for name in ("run.py","meta_probe.py","build_no_device.py"):
   p=subprocess.run([sys.executable,"-B",str(HERE/name)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)
   v=json.loads(p.stdout);self.assertFalse(v["npu_executed"]);self.assertFalse(v["default_enabled"])
 def test_syntax_all_python(self):
  for p in HERE.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
if __name__=="__main__":unittest.main()
