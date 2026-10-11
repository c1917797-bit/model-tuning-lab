"""Independent author-result int64/labels/ref consumer; no Torch or producer import."""
import argparse,ast,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import need,reference,bound,source,LAYERS
from calibration_inputs import inputs,split_rank
from cluster_oracle import validate
from torch_zip_int64 import decode
def artifact(bundle,whole_ref,packet,pref,commit,rank,layer,axis):
    need(type(rank)is int and 0<=rank<4 and layer in LAYERS and set(axis)=={"K","V"},"actual ordered rank/layer/both axes")
    return dict(schema="skvq-author-calibration/v1",author_commit=commit,layer=layer,tp=4,rank=rank,
      local_kv_heads=1,head_dim=256,key_capture="pre_rope",training_only=True,seed=42,n_init=10,method="KMeans_minmax",
      seed_scope="capture input sampler only; unmodified KMeans random_state=None and actual RNG recorded",
      calibration_executed=True,global_channels=1024,rank_global_channels=list(range(rank*256,(rank+1)*256)),
      source_ref=packet,capture_whole_ref=whole_ref,capture_producer_ref=bundle["capture_producer_ref"],
      model_sha256=bundle["model_identity"]["model_sha256"],model_identity=bundle["model_identity"],host_result_ref=bundle["host_result_ref"],
      model_config_sha256="69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c",
      model_identity_authority_ref=whole_ref,dataset_ref=bundle["capture_producer_ref"],
      producer_sha256=pref["sha256"],dataset_sha256=bundle["capture_producer_ref"]["sha256"],
      named_TP_local_Qwen_adaptation=True,author_global_grouping_equivalent=False,runtime_pre_rope=False,
      smooth_enabled=False,teacher_required_for_default=False,native_ready=False,model_ready=False,**axis)
def consume_writer_artifact(ref,*,bundle,rank,layer):
    from common import writer_calibration
    need(reference(ref["path"])==ref,"actual newly published calibration bytes")
    layouts,receipt=writer_calibration().load(ref["path"],sha256=ref["sha256"],
      model_sha256=bundle["model_identity"]["model_sha256"],layer=layer,rank=rank,tp=4,dim=256)
    value=bound(ref)
    need(value["runtime_pre_rope"]is False and value["smooth_enabled"]is False and
      value["author_global_grouping_equivalent"]is False and value["native_ready"]is False and value["model_ready"]is False,
      "named TP-local/default postRoPE runtime only, not native/model authority")
    for layout in layouts.values():
        need(layout.clip==.95 and layout.smooth==(1.,)*256,"source-bound fixed clip/smooth OFF")
    return dict(calibration_ref=ref,writer_source_ref=reference(writer_calibration().__file__),
      actual_original_writer_loader_executed=True,axes={a:dict(permutation=list(l.permutation),starts=list(l.starts),
      smooth=list(l.smooth),clip=l.clip)for a,l in layouts.items()},native_writer_executed=False)
def consume(root,whole_ref,packet,*,write_artifacts=True,module_namespace="live"):
    root=Path(root);pref=reference(root/"PRODUCER_RESULT.json");p=bound(pref);bundle=inputs(whole_ref)
    need(p["schema"]=="skvq.default-tp-local.producer/v1"and p["status"]=="AUTHOR_FUNCTION_ALL4_TP_LOCAL_RETURNED_PENDING_INDEPENDENT_CONSUMER"and
      p["source_ref"]==packet and p["capture_whole_ref"]==whole_ref and len(p["rank_results"])==4 and p["unified_clip"]==.95 and
      p["smooth_enabled"]is False and p["runtime_pre_rope"]is False and p["author_global_grouping_equivalent"]is False and
      p["native_ready"]is False and p["model_ready"]is False,"current all4 author default, not global/model authority")
    from library_probe import verify
    need(type(module_namespace)is str and module_namespace in("live","captured"),"explicit runtime or frozen whole-terminal module namespace")
    library=verify(p["actual_library_probe_ref"],packet,captured=module_namespace=="captured")
    raw_bundle=json.loads((Path(__file__).parent/"author_sources.json").read_bytes());rows={x["name"]:x for x in raw_bundle["files"]}
    need(set(p["author_raw_refs"])==set(rows),"all6 original author source refs")
    for name,r in p["author_raw_refs"].items():
        need(reference(r["path"])==r and r["sha256"]==rows[name]["sha256"]and r["bytes"]==rows[name]["bytes"]and
          Path(r["path"])==root/"author"/name,"source-bound exact author raw including EOF")
    raw_ref=p["author_raw_refs"]["calibration.py"];tree=ast.parse(Path(raw_ref["path"]).read_text())
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="get_reorder_indices"]
    need(len(nodes)==1 and not nodes[0].decorator_list,"one exact original author function");node=nodes[0]
    checked={};artifacts=[];writer_handoffs=[]
    for rank,rref in enumerate(p["rank_results"]):
        need(Path(rref["path"])==root/("rank-"+str(rank))/"PRODUCER_RESULT.json","exact ordered rank results")
        r=bound(rref);stage=root/("rank-"+str(rank));e=bound(r["actual_author_function_execution_ref"])
        need(r["rank"]==rank and r["capture_whole_ref"]==whole_ref and r["n_cluster"]==4 and r["gsize"]==64 and
          r["unified_clip"]==.95 and r["TP_local_not_global_equivalence"]is True and r["native_ready"]is False and
          r["model_ready"]is False and r["author_raw_refs"]==p["author_raw_refs"],"same local256 rank caller")
        need(e["packet_source_manifest_ref"]==packet and e["actual_library_probe_ref"]==p["actual_library_probe_ref"]and e["author_raw_refs"]==p["author_raw_refs"]and
          e["projection_consumed_ref"]==bundle["projection_consumed_ref"]and e["v_consumed_ref"]==bundle["baseline_receipt_ref"]and
          e["actual_arguments"]==dict(n_cluster=4,metric="minmax",num_layers=16,save_path=str(stage/"AUTHOR_GROUPS.pt"))and
          e["actual_cpu_threads"]==dict(intra=1,interop=1)and e["smooth_factor_function_called"]is False and
          e["groupwise_clipping_alpha_search_run"]is False and e["original_function_body_unmodified"]is True and e["observer_changes_fit_or_labels"]is False,"unchanged author's default function arguments")
        want=dict(source_ref=raw_ref,function="get_reorder_indices",first_line=node.lineno,last_line=node.end_lineno,
          ast_sha256=__import__("control_ast").author_digest(Path(raw_ref["path"]).read_bytes()),function_body_unmodified=True,other_author_functions_imported_or_called=False)
        need(e["function"]==want,"independent original AST identity")
        need(e["actual_modules"]=={n:library["actual_modules"][n]for n in("torch","numpy","sklearn","actual_sklearn_KMeans")},
          "actual fitted modules exactly match prior same-image dependency gate")
        if module_namespace=="live":
            for actual in e["actual_modules"].values():need(reference(actual["path"])==actual,"actual same-image CPU module bytes")
        # Captured namespace has already independently checked every full original
        # module Ref against its complete owned snapshot. No guest path is erased.
        pt=e["groups_pt_ref"];need(pt["path"]==str(stage/"AUTHOR_GROUPS.pt")and reference(pt["path"])==pt,"original torch.save bytes")
        saved=decode(pt["path"]);need(len(saved["reorder_indices"])==len(saved["cluster_st_inds"])==16,"full original saved16FA")
        checked[rank]={}
        for i,layer in enumerate(LAYERS):
            need(set(r["layers"][layer])=={"k","v"}and e["layers"]==r["layers"],"both original sides/all fits")
            checked[rank][layer]={};axis={}
            for j,side in enumerate(("k","v")):
                row=r["layers"][layer][side];before=bound(row["fit_raw_pre_ref"]);after=bound(row["fit_result_ref"])
                expected_features=split_rank(bundle["sides"][side],rank)[layer]["feature_rows"]
                need(before["feature_rows"]==expected_features and before["actual_input_shape"]==[256,2]and before["actual_input_device"]=="cpu"and
                  before["original_capture_dtype"]==bundle["dtype"]and before["feature_input_mode"]==p["feature_mode"],"actual original local256 features, no cross-rank or new statistic")
                parameters=before["sklearn_parameters"]
                need(parameters==row["actual_parameters"]and parameters["n_clusters"]==4 and parameters["n_init"]==10 and parameters["random_state"]is None,"unchanged KMeans parameters/RNG")
                need(all(type(pool["num_threads"])is int and pool["num_threads"]==1 for pool in row["actual_threadpools"]),"actual fitted one-thread BLAS/OpenMP budget")
                need(after=={k:v for k,v in row.items()if k not in("fit_result_ref","permutation","cluster_st_inds")},"full observed fit labels/centers before derived layout")
                need(saved["reorder_indices"][i][j]["storage_int64"]==row["permutation"]and
                  saved["cluster_st_inds"][i][j]["storage_int64"]==row["cluster_st_inds"],"independent actual PT fields")
                checked[rank][layer][side]=validate(expected_features,row,4)
                axis[side.upper()]=dict(global_permutation=[rank*256+x for x in row["permutation"]],starts=row["cluster_st_inds"],smooth=[1.]*256,unified_clip=.95)
            value=artifact(bundle,whole_ref,packet,pref,raw_bundle["commit"],rank,layer,axis)
            # Model identity is a named canonical digest of the already full host-hashed
            # indexed payload, not config.json SHA, marketing identity or new PASS.
            destination=root/("CALIBRATION-r"+str(rank)+"-l"+layer.split(".")[2]+".json")
            from common import publish
            if write_artifacts:ar=publish(destination,value)
            else:
                ar=reference(destination);need(bound(ar)==value,"actual existing artifact exact original independent replay; no overwrite")
            artifacts.append(ar)
            writer_handoffs.append(consume_writer_artifact(ar,bundle=bundle,rank=rank,layer=layer))
    need(len(artifacts)==len(writer_handoffs)==64,"all4/all16 actual original writer loader handoffs")
    need(reference(root/"PRODUCER_RESULT.json")==pref,"immutable full producer")
    return dict(schema="skvq.default-tp-local.independent/v1",status="ALL4_TP_LOCAL_DEFAULT_CALIBRATION_CONSUMED",
      source_ref=packet,producer_ref=pref,capture_whole_ref=whole_ref,actual_rank_fits=128,channels_checked=32768,
      original_PT_int64_fields_independently_decoded=True,checked=checked,calibration_refs=artifacts,writer_handoffs=writer_handoffs,
      unified_clip=.95,smooth_enabled=False,runtime_pre_rope=False,teacher_required_for_default=False,
      author_global_grouping_equivalent=False,native_writer_runtime_pending=True,native_ready=False,model_ready=False,performance_ready=False)
def main():
    from common import publish,cpu_only
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true");ap.add_argument("--source-manifest-sha256")
    ap.add_argument("--root");ap.add_argument("--whole-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,native_ready=False,model_ready=False)));return
    packet=source(a.source_manifest_sha256);cpu_only();whole_ref=json.loads(Path(a.whole_ref_json).read_bytes())
    need(Path(a.output)==Path(a.root)/"INDEPENDENT.json","exact new independent sink")
    print(json.dumps(publish(a.output,consume(a.root,whole_ref,packet)),sort_keys=True))
if __name__=="__main__":main()
