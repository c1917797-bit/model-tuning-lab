"""Independent CPU raw consumption entry. No Torch/candidate algorithm import."""
import argparse,importlib.util,json,sys
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def entry(sha,client_ref,output):
 here=Path(__file__).resolve().parent
 spec=importlib.util.spec_from_file_location("_kivi_firstdecode_raw_source",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(sha);roles=m["runtime_roles"]
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
  installer_sha256=roles["installer"]["sha256"],capture_sha256=roles["capture"]["sha256"],
  kernel_sha256=roles["kernel"]["sha256"],writer_reader_ref=roles["writer_reader"])
 memory.consume_memory(memory.memory(expected_limit=8*1024**3),expected_limit=8*1024**3)
 result.update(source=source,client_ref=client_ref,independent_oracle_source=roles["fast_oracle"],
  independent_reader_source=roles["fast_consume"],writer_reader_source=roles["writer_reader"],
  actual_memory_before=before,no_candidate_math_import=True)
 return l.publish(output,result)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--client-ref-json",type=Path);p.add_argument("--output",type=Path)
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return 0
 need(a.client_ref_json is not None and a.output is not None,"explicit actual source/input/output")
 entry(a.source_manifest_sha256,json.loads(a.client_ref_json.read_bytes()),a.output);return 0
if __name__=="__main__":raise SystemExit(main())
