"""Actual Devices[] prerequisite: fresh reader whole, prompt, safe codec, declared SchedulerConfig."""
import argparse,json,sys
from pathlib import Path
import bridge_contract as B
def run(sha,reader_ref,prompt_ref,output):
    B.need(not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),
      "actual Devices[] necessary CPU gate")
    C,source,m=B.source(sha);C.reader_whole(reader_ref);B.prompt(C,prompt_ref)
    from actual_config import construct
    from model_extension import preflight
    config=construct(source);rpc=preflight(source)
    return C.atomic(output,dict(schema="skvq.model-reader.cpu/v1",status="ACTUAL_READER_PROMPT_PARSER_RPC_CHECKED",
      source_ref=source,reader_whole_ref=reader_ref,prompt_ref=prompt_ref,configuration=config,rpc=rpc,
      Devices_empty=True,full_engine_at_N1_required=True,**B.false_scopes()))
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--reader-whole-ref-json");p.add_argument("--prompt-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**B.false_scopes())));return
    reader=json.loads(Path(a.reader_whole_ref_json).read_bytes());prompt=json.loads(Path(a.prompt_ref_json).read_bytes())
    print(json.dumps(run(a.source_manifest_sha256,reader,prompt,a.output),sort_keys=True))
if __name__=="__main__":main()
