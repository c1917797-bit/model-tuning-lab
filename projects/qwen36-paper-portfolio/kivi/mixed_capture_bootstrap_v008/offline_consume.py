"""Independent long CPU consumption AFTER actual stopped TP4; no controller.
CLI consumes a source-bound recipe. Existing MAIN host owns CPU8/timeout/cleanup.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
CUTOFF=1791788425
CORE_SHA="a5d27c8945e21c88f5ba82e5b6f1f8c05c7252b68b7ea237b67d7aef7cae31e1"
RELEASE_SHA="bacb98cb15e6cc8b4542e9153d2124a3cb73045735c44485970074b969485f37"
ROLE_SHA={"capture_receipt":"7048bfa09c5a8dcc156da3edf8fd9ace954cc10ebee7ff9ffa15ed74b128918d","stage_consumer":"d3f6a9089287521fdb01a4114f814391cfbfc4f25500a103dad0599502aa7da4","original_writer":"26d680f232f8cd5a0afde9b21ccb64f4955428052352c93901a80f4bfc2150da","stage_lifecycle":"def3ba9590673f1559c5bfbbc19191716197742c61d24e0f8b1b8c57c8c322a0","matrix_consumer":"734fcd8e512c124a605716cdb13760e7dfdf08eb17af3af0dc93b5128ef1e68a","bindings":"a72c8ea47f6f04f661a9b8e6c159e02eb7f743aa3fe94a27c212e7a6cd7e8761","assignment_oracle":"f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333","fast_oracle":"f57c2703e19b59c3cd6c6b0df52a21fdfc1c0a43ab6fe86d236b6e750e24d39c","fast_consume":"4dda2abbabc3a474d4ee09f462bb1ea9acbd4847cd3c49fe4f360efe4eef3bfa","geometry_helper":"3e4a100be9225c3ec464e1d256761a780648fad3dfd4b1dc79db8f883fd092f1","codec":"45ccb0c2fff417e518cb591aaf5ba201645551a1aeafc9d8bdc3c97ce6a8fd49","release_replay":"bacb98cb15e6cc8b4542e9153d2124a3cb73045735c44485970074b969485f37","release_core":"a5d27c8945e21c88f5ba82e5b6f1f8c05c7252b68b7ea237b67d7aef7cae31e1"}
ROLES=("capture_receipt","stage_consumer","original_writer","stage_lifecycle",
       "matrix_consumer","bindings","assignment_oracle","fast_oracle","fast_consume",
       "geometry_helper","codec","release_replay","release_core")
def need(v,m):
    if not v:raise ValueError(m)
def deadline(epoch):
    need(type(epoch) in (int,float) and time.time()<epoch<=CUTOFF,
         "original bounded CPU stage deadline; never extend absolute1791788425")
def run(recipe,*,core,release,ctx,modules,publish):
    need("torch" not in sys.modules and "torch_npu" not in sys.modules,"separate no-Torch CPU process")
    need(recipe["schema"]=="kivi.mixed-offline-numeric-recipe/v2"
         and recipe["producer_ref"]==ctx.producer and len(recipe["capture_receipt_refs"])==16
         and len(recipe["rank_final_refs"])==4 and recipe["portfolio_cutoff_epoch"]==CUTOFF,
         "whole source-bound capture and CPU phase recipe")
    source=recipe["source_refs"]
    need(set(source)==set(ROLES) and all(source[k]["sha256"]==ROLE_SHA[k] for k in ROLES),
         "whole exact independent source set")
    release.pin(release,source["release_replay"])
    need(all(ref in ctx.m["files"]+ctx.m["dependencies"] for ref in source.values()),
         "every independent source in actual qualified host manifest")
    for name,module in modules.items():
        need(name in source,"declared source role only");release.pin(module,source[name])
    need(set(modules)==set(ROLES)-{"geometry_helper","codec","release_core","release_replay"},
         "all exact loaded independent module roles")
    deadline(recipe["cpu_deadline_epoch"])
    released=release.before_numeric(ctx,core=core,core_ref=source["release_core"],
        npu_cleanup_ref=recipe["npu_cleanup_ref"],npu_owned_ref=recipe["npu_owned_ref"],
        host_pid=recipe["actual_host_pid"],cpu_inspect_ref=recipe["cpu_started_inspect_ref"],
        cpu_owned_ref=recipe["cpu_owned_ref"])
    # This call is before any output/writer invocation. No fallback if live/failed.
    plan=recipe["capture_plan_ref"];refs=[];timings=[]
    for stage,capture_ref in enumerate(recipe["capture_receipt_refs"]):
        deadline(recipe["cpu_deadline_epoch"])
        captured=modules["capture_receipt"].validate(capture_ref,stage=stage,plan_ref=plan,
            identities=recipe["rank_identities"],document=core.obj)
        start=time.monotonic()
        result=modules["stage_consumer"].consume(captured["rank_stage_refs"],
            output_module=modules["fast_consume"],oracle_module=modules["fast_oracle"],
            writer_module=modules["original_writer"],source_refs=source,
            installer_sha256=recipe["installer_sha256"],capture_sha256=recipe["capture_sha256"],
            observer_sha256=recipe["observer_sha256"])
        deadline(recipe["cpu_deadline_epoch"])
        refs.append(publish("STAGE-%02d-INDEPENDENT"%stage,result))
        timings.append(time.monotonic()-start)
    joined=modules["matrix_consumer"].consume(refs,recipe["rank_final_refs"],plan,
        capture_receipt_refs=recipe["capture_receipt_refs"],capture_reader=modules["capture_receipt"],
        stage_reader=modules["stage_consumer"],life=modules["stage_lifecycle"],
        bindings=modules["bindings"],oracle=modules["assignment_oracle"],source_refs=source,
        installer_sha256=recipe["installer_sha256"])
    deadline(recipe["cpu_deadline_epoch"])
    return dict(schema="kivi.mixed-offline-numeric-components/v2",
        status="ALL16_STAGES_NUMERIC_AND_SCALAR_CONSUMED_AFTER_RELEASE",
        producer_ref=ctx.producer,release_replay=released,stage_result_refs=refs,
        stage_CPU_seconds=timings,matrix=joined,whole_original_CPU_terminal_required=True,
        cpu_cleanup_and_memory_evidence_still_required=True,raw_deleted=False,
        model_ready=False,performance_ready=False,run_authority=False,cleanup_authority=False)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recipe",required=True);p.add_argument("--recipe-sha256",required=True)
    p.add_argument("--release-core",required=True);p.add_argument("--release-core-bytes",type=int,required=True)
    p.add_argument("--output-dir",required=True)
    a=p.parse_args()
    core_path=Path(a.release_core)
    need(core_path.is_absolute() and not core_path.is_symlink() and core_path.stat().st_size==a.release_core_bytes
         and hashlib.sha256(core_path.read_bytes()).hexdigest()==CORE_SHA,"exact reviewed release source before import")
    import importlib.util
    spec=importlib.util.spec_from_file_location("_kivi_mixed_original_release_core",core_path)
    core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
    recipe=core.obj(dict(path=a.recipe,sha256=a.recipe_sha256))
    src=recipe["source_refs"];need(src["release_core"]==core.ref(core_path),"recipe and CLI exact release source")
    need(set(src)==set(ROLES) and all(src[k]["sha256"]==ROLE_SHA[k] for k in ROLES),
         "all source identities before any independent module import")
    release=core.source_module(src["release_replay"],"_kivi_mixed_release_replay")
    need(src["release_replay"]["sha256"]==RELEASE_SHA,"exact release adapter")
    ctx=release.make_context(recipe["producer_ref"],core=core,core_ref=src["release_core"])
    need(all(ref in ctx.m["files"]+ctx.m["dependencies"] for ref in src.values()),
         "all independent sources in actual host closure before imports")
    out=Path(a.output_dir)
    need(out.is_absolute() and out.resolve()==out and not out.is_symlink() and out.is_dir()
         and Path("/cache/cch") in out.parents,"existing exact owned CPU output leaf")
    modules={}
    order=("fast_oracle","fast_consume","capture_receipt","stage_consumer","original_writer",
           "stage_lifecycle","matrix_consumer","bindings","assignment_oracle")
    for name in order:
        namespace=name if name=="fast_oracle" else "_kivi_mixed_offline_"+name
        modules[name]=core.source_module(src[name],namespace)
    def publish(label,value):
        return ctx.c.write(out/(label+".json"),value)
    result=run(recipe,core=core,release=release,ctx=ctx,modules=modules,publish=publish)
    print(json.dumps({"result":publish("RESULT",result),"status":result["status"]}),flush=True)
if __name__=="__main__":main()
