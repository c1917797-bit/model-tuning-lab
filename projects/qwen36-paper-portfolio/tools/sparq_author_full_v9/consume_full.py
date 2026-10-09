"""Independent entire-originalauthor-ANN-v2 numeric permission reader; OFF by default.
This consumer grants only the source-bound prerequisite, NEVER TP4/model/perf/task PASS.
"""
import argparse,json
from pathlib import Path
import source_contract as c
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--numeric-authority");p.add_argument("--numeric-authority-sha256")
 p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",ready=False,model_ready=False)));return
 c.require(a.source_manifest_sha256 and a.numeric_authority and a.numeric_authority_sha256 and a.output and
  a.output.is_absolute() and Path("/cache/cch") in a.output.parents and not a.output.exists(),"all actual explicitRefs/new output")
 source,files=c.source(str(c.ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
 authority=c.actual_component(a.numeric_authority,a.numeric_authority_sha256)
 result=dict(schema="sparq.full-source-numeric-prerequisite/v1-author-ann",source=source,source_files=files,
  **{"exact_originalauthor-ANN-v2_whole_consumer_replayed":True},numeric_authority=dict(path=a.numeric_authority,sha256=a.numeric_authority_sha256),
  original_terminal=authority["original_terminal"],original_operation_id=authority["original_operation_id"],
  precision_contract=authority["precision_contract"],original009_numeric_status="failed-not-promoted",
  native_substrate_sources=41,cases=128,steps=20480,TP4_executed=False,
  actual64_layer_numeric_gate=False,paired1024=False,final2048=False,model_ready=False,ready=False)
 c.write(a.output,result);print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
