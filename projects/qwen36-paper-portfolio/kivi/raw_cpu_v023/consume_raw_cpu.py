"""Independent CPU raw consumption entry. No Torch/candidate algorithm import."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def entry(sha,client_ref,output,entry_sha256):
 actual=Path(__file__).resolve();need(hashlib.sha256(actual.read_bytes()).hexdigest()==entry_sha256,"exact explicitly source-bound CPU-only corrected caller")
 here=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-018")
 spec=importlib.util.spec_from_file_location("_kivi_firstdecode_raw_source",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(sha);roles=m["runtime_roles"]
 original=l.own(m,"consume_raw.py");need(original["bytes"]==3252 and original["sha256"]=="05ed6ed6a179dd1d4e4d78331a5c051be68608fd589ab718f3d9fe57e5ea6231","exact retained018 raw caller")
 l.checked(original)
 need(roles["provenance"]["bytes"]==3643 and roles["provenance"]["sha256"]=="a93894bbbd0d73b72c9bc43664a121106525fa5a27bca0d361aff9a2ba00def7"
  and roles["capture"]["bytes"]==7966 and roles["capture"]["sha256"]=="398cd59b469af2ffa81df15a2c5786f048b41836a22ed7348803900495d7c88a","distinct original-prefill provenance and native layout collector")
 l.checked(roles["provenance"]);l.checked(roles["capture"])
 memory=l.memory_module(m);before=memory.memory(expected_limit=8*1024**3)
 memory.consume_memory(before,expected_limit=8*1024**3)
 # Only scalar receipt/geometry/oracle modules. Do not call donor.load_modules(),
 # PackedBatch, candidate dequantization/score/output, or replay any model feedback.
 for alias in("allocator","kivi_layout_consumer"):
  l.module(alias,roles[alias])
 l.module("provider_zeroer",roles["spans"])
 l.module("provider_independent",l.own(m,"provider_independent.py"))
 geometry=l.module("explicit_geometry",l.own(m,"explicit_geometry.py"))
 oracle=l.module("fast_oracle",roles["fast_oracle"])
 out=l.module("_kivi_firstdecode_fast_raw",roles["fast_consume"])
 need(out.oracle is oracle,"exact independent oracle, not preexisting scalar/candidate namespace")
 modules={name:l.module("_kivi_firstdecode_independent_"+name,roles[name])
          for name in("journal","book","bindings","assignment_oracle","fields","spans","writer_reader")}
 consume=l.module("_kivi_firstdecode_aggregate",l.own(m,"consume_first_decode.py"))
 client=l.obj(client_ref)
 need(client["schema"]=="kivi.actual-firstdecode-client/v1"and
      client["status"]=="HTTP_AND_NATIVE_FINAL_OBSERVED"and client["source_ref"]==source,
      "complete actual same-source HTTP+all4 final, not fixture/source/old unit result")
 result=consume.consume(client["rank_bundle_refs"],journal=modules["journal"],book=modules["book"],
  bindings=modules["bindings"],assignment_oracle=modules["assignment_oracle"],
  output_reader=out,writer_reader=modules["writer_reader"],codec_ref=roles["codec"],
  fields=geometry,spans=modules["spans"],
  installer_sha256=roles["installer"]["sha256"],capture_sha256=roles["provenance"]["sha256"],
  kernel_sha256=roles["kernel"]["sha256"],writer_reader_ref=roles["writer_reader"])
 memory.consume_memory(memory.memory(expected_limit=8*1024**3),expected_limit=8*1024**3)
 result.update(source=source,client_ref=client_ref,independent_oracle_source=roles["fast_oracle"],
  independent_reader_source=roles["fast_consume"],writer_reader_source=roles["writer_reader"],
  actual_memory_before=before,no_candidate_math_import=True,
  adapted_raw_entry_source=l.ref(actual),original_raw_entry_source=original,
  original_prefill_capture_source=roles["provenance"],native_layout_capture_source=roles["capture"])
 return l.publish(output,result)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--entry-sha256");p.add_argument("--source-manifest-sha256");p.add_argument("--client-ref-json",type=Path);p.add_argument("--output",type=Path)
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return 0
 need(a.entry_sha256 is not None and a.client_ref_json is not None and a.output is not None,"explicit actual source/input/output")
 entry(a.source_manifest_sha256,json.loads(a.client_ref_json.read_bytes()),a.output,a.entry_sha256);return 0
if __name__=="__main__":raise SystemExit(main())
