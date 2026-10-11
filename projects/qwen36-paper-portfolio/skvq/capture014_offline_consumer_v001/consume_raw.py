"""One Devices[] pass over immutable014 QKV/preprojection; no recapture.
Same independent math, unique new receipts and explicitly new consumer identity.
"""
import argparse,ast,hashlib,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import offline_contract as D
TOTAL=3600;CLEANUP=180
def output_root(path):
    p=Path(path)
    D.need(p.is_absolute()and p.name=='work'and p.parent.parent==D.ROOT.parent and
      p.parent.name.startswith('run-skvq-capture014-offline-001-')and p.resolve()==p and p.is_dir(),
      'sole new existing MAIN-owned work leaf, never an old014 output')
    for q in(p,)+tuple(p.parents):D.need(not q.is_symlink(),'no output symlink')
    D.need(not any(p.iterdir()),'new empty consumer output leaf')
    return p
def payload_recheck(old_host,deadline):
    """Execute unchanged original indexed BF16/F32 payload validator body."""
    old=D.obj(D.CAPTURE);row=next(r for r in old['files']if r['path'].endswith('/MAIN_HOST.py'))
    D.checked(row);tree=ast.parse(Path(row['path']).read_bytes(),filename=row['path'])
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='payload']
    D.need(len(nodes)==1,'one exact original payload validator')
    scope=dict(Path=Path,MODEL=Path('/cache/efim/Qwen3.6-27B'),json=json,hashlib=hashlib,
      require=D.need,reference=D.ref)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),row['path'],'exec'),scope)
    class Watch:
        def left(self):D.need(time.monotonic()<deadline and time.time()<D.CUT,'bounded new CPU/cutoff payload recheck')
        def guard(self):D.cpu_only()
    value=scope['payload'](Watch())
    D.need(value==old_host['actual_payload'],'new full indexed weight bytes match original pre-capture full hash')
    return dict(schema='skvq.capture014.after-release-payload-recheck/v1',payload=value,
      original_host_before_ref=__import__('previous_failure').HOST_REF,
      original_function_ref=row,original_function_ast_sha256=hashlib.sha256(ast.dump(nodes[0],include_attributes=False).encode()).hexdigest(),
      every_indexed_shard_whole_bytes_rehashed=True,old_before_after_success_not_claimed=True,
      actual_weight_publisher_identity_pending=True)
def run(source,path):
    start=time.monotonic();deadline=start+TOTAL-CLEANUP;D.cpu_only()
    D.need(time.time()+TOTAL<=D.CUT,'new CPU-only3600 includes180 fits unchanged cutoff')
    out=output_root(path);C,loader,projection,stage=D.original_modules(source)
    import previous_failure as F
    import consume_previous_host as host_reader
    from identity_preflight import inspect_pairs
    def progress(label):
        D.need(time.monotonic()<deadline,'whole raw/payload fixed3420 work budget')
        return D.publish(out/('STAGE-'+label+'.json'),dict(stage=label,source_ref=source,
          producer_source_ref=D.CAPTURE,observed_utc_ns=time.time_ns(),elapsed_seconds=time.monotonic()-start,
          native_ready=False,model_ready=False))
    progress('00-start')
    failure=F.inspect();fr=D.publish(out/'ORIGINAL_FAILURE_CONSUMED.json',failure)
    prior=host_reader.consume(Path(D.RAW_ROOT));pr=D.publish(out/'ORIGINAL_OWNED_PREFLIGHT.json',prior)
    identity=inspect_pairs(source);ir=D.publish(out/'ORDERED_IDENTITY_PREFLIGHT.json',identity)
    root=Path(F.PRODUCER_ROOT);producer_ref=D.ref(root/'PRODUCER_RESULT.json')
    progress('01-baseline-start')
    baseline=loader.consume(root);br=D.publish(out/'BASELINE_CONSUMED.json',baseline)
    progress('02-baseline-complete-projection-start')
    preprojection=projection.consume(root,br['path']);kr=D.publish(out/'PREPROJECTION_CONSUMED.json',preprojection)
    progress('03-projection-complete-payload-start')
    payload=payload_recheck(D.obj(F.HOST_REF),deadline);wr=D.publish(out/'PAYLOAD_AFTER_RELEASE.json',payload)
    progress('04-payload-complete')
    D.need(D.ref(root/'PRODUCER_RESULT.json')==producer_ref,'immutable original producer after full new math')
    combined=stage.combine(baseline,preprojection,D.CAPTURE,br,kr)
    combined.update(derived_identity_consumer_source_ref=source,original_failed_whole_ref=D.FAILED_ORIGINAL,
      original_failed_whole_preserved=True,derived_ordered_identity_ref=ir,
      after_release_full_payload_ref=wr)
    ar=D.publish(out/'CAPTURE_CONSUMED.json',combined)
    old_host_consumed=host_reader.consume(Path(D.RAW_ROOT),ar);hr=D.publish(out/'ORIGINAL_HOST_CONSUMED_DERIVED.json',old_host_consumed)
    D.need(D.source(source['sha256'])==source,'new independent consumer complete source immutable')
    result=dict(schema='skvq.capture014.offline.workload/v1',status='ALL256_ORIGINAL_RAW_WITH_ORDERED_IDENTITY_CONSUMED_PENDING_CPU_WHOLE',
      source_ref=source,producer_source_ref=D.CAPTURE,original_failed_whole_ref=D.FAILED_ORIGINAL,
      original_failure_authority_ref=fr,original_owned_preflight_ref=pr,ordered_identity_preflight_ref=ir,
      full_raw_consumer_ref=ar,derived_old_host_consumer_ref=hr,after_release_payload_ref=wr,
      original_failed_whole_preserved=True,events=16384,qkv_bytes=256*2**30,preprojection_K_raw_bytes=32*2**30,
      elapsed_seconds=time.monotonic()-start,total_seconds=TOTAL,cleanup_reserved_seconds=CLEANUP,
      no_NPU=True,no_Torch=True,host_owned_terminal_consumer_required=True,
      author_calibration_pending=True,native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
    return D.publish(out/'CPU_WORKLOAD_RESULT.json',result)
def main():
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
    p.add_argument('--source-manifest-sha256');p.add_argument('--output');a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,no_NPU=True,model_ready=False)));return
    D.cpu_only();source=D.source(a.source_manifest_sha256)
    print(json.dumps(run(source,a.output),sort_keys=True),flush=True)
if __name__=='__main__':main()
