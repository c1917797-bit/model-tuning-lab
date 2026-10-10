"""Pure independent selected-mixed terminal replay; no device or controller.
No PASS flag supplied by a caller is enough. Replays the exact source-qualified
existing capture/after-release-CPU consumer and original operation records.
"""
import importlib.util,json,sys
from pathlib import Path
import screen_contract as c
# Set by final source assembly, never inherited as a numerical PASS.
MIXED_CONSUMER_SHA="3535642efbf50039f35cf65c5a61b36350e141b9c0ab0f9c7261a25aab3be243"
def check(value,source):
 c.need(value["schema"]=="kivi.actual-mixed-whole-terminal-consumed/v1"
  and value["status"]=="SELECTED_MIXED_NUMERIC_AND_ALL64_LIFECYCLE_WHOLE_CONSUMED"
  and value["source"]==source and value["MAIN_original_operations_verified"]is True
  and value["actual_NPU_released_before_CPU"]is True and value["CPU_stopped_retained"]is True
  and value["full_selected_FA64_checked"]is True and value["numeric_frames"]==320
  and value["whole_output_rows"]==576 and value["full_output_elements_per_row"]==1536
  and value["all64_owner_native_lifecycle_checked"]is True
  and all(value[k]is False for k in("raw_deleted","model_ready","performance_ready","run_authority",
    "cleanup_authority","full_model_correctness_verified","graph_checked","GDN_numerically_checked")),
  "actual selected mixed coverage, not full-frame/performance/task permission")
 return value
def replay(arguments,paired_manifest):
 from consumer_namespace import isolated_call
 return isolated_call(lambda:_replay(arguments,paired_manifest),"mixed")
def _replay(arguments,paired_manifest):
 source=arguments["mixed_source"];request=c.read(arguments["mixed_input"])
 mf=c.read(source);roles=mf["runtime_roles"];ours=paired_manifest["runtime_roles"]
 c.need(type(MIXED_CONSUMER_SHA)is str and len(MIXED_CONSUMER_SHA)==64,
  "mixed007 whole consumer identity is not frozen; no device admission")
 consumer=roles["whole_cpu_consumer"]
 c.need(consumer["sha256"]==MIXED_CONSUMER_SHA and request["source"]==source,
  "exact reviewed mixed terminal consumer and original input")
 for name in("kernel","metadata","producer","provenance","formal","lifecycle","callback",
             "book","mixed","installer","explicit_provider","explicit_geometry"):
  c.need(roles[name]["sha256"]==ours[name]["sha256"],
   "same candidate mathematical/allocator/lifecycle source used in mixed proof: "+name)
 for row in mf["files"]+mf["dependencies"]:c.need(c.ref(row["path"])==row,"whole mixed source closure")
 c.need(consumer in mf["files"],"mixed consumer is an own immutable source")
 name="_kivi_c16_exact_mixed_whole";c.need(name not in sys.modules,"no ambient mixed consumer")
 spec=importlib.util.spec_from_file_location(name,consumer["path"]);mod=importlib.util.module_from_spec(spec)
 sys.modules[name]=mod;spec.loader.exec_module(mod)
 return check(mod.consume(mod.context(source),request),source)
