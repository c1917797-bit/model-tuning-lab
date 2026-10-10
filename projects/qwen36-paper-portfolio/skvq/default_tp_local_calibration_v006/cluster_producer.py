"""Unmodified author get_reorder_indices execution on legal Qwen TRAIN statistics."""
import ast,hashlib,inspect,os,traceback
from pathlib import Path
from typing import Literal
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import need,reference,publish,feature_dtype
def extract(raw_ref,torch,kmeans):
    need(reference(raw_ref["path"])==raw_ref,"actual fixed calibration.py bytes")
    raw=Path(raw_ref["path"]).read_text();tree=ast.parse(raw)
    matches=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="get_reorder_indices"]
    need(len(matches)==1,"one original get_reorder_indices")
    node=matches[0]
    need(not node.decorator_list,"no hidden author decorator execution")
    scope={"torch":torch,"KMeans":kmeans,"os":os,"Literal":Literal}
    # No rewriting the function body/algorithm/importing model/CUDA calibration code.
    exec(compile(ast.Module(body=[node],type_ignores=[]),raw_ref["path"],"exec"),scope)
    info={"source_ref":raw_ref,"function":"get_reorder_indices",
          "first_line":node.lineno,"last_line":node.end_lineno,
          "ast_sha256":hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),
          "function_body_unmodified":True,"other_author_functions_imported_or_called":False}
    return scope["get_reorder_indices"],info
def run(bundle,out,gsize,packet_ref,feature_mode,library_ref):
    need(gsize in (32,64,128) and 256%gsize==0,"official mean group sizes for256 channels")
    ncluster=256//gsize
    from library_probe import verify,match_loaded
    dependency=verify(library_ref,packet_ref);match_loaded(dependency)
    import torch,numpy as np,sklearn
    from sklearn.cluster import KMeans
    from threadpoolctl import threadpool_info
    need(torch.get_num_threads()==torch.get_num_interop_threads()==1,"caller actual CPU thread budget")
    need(all(os.environ.get(k)=="1"for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")),"explicit one-thread CPU libraries")
    feature_name=feature_dtype(bundle["dtype"],feature_mode)
    dtype=torch.float16 if feature_name=="torch.float16" else torch.float32
    data={metric:{side:[] for side in ("k","v")} for metric in ("min","max","absmax")}
    from common import LAYERS
    for layer in LAYERS:
        for metric in data:
            for side in ("k","v"):
                vals=bundle["sides"][side][layer][metric]
                t=torch.tensor(vals,dtype=dtype,device="cpu")
                need(t.to(torch.float64).tolist()==vals,"exact original A16 extrema, no new precision/statistics")
                data[metric][side].append(t)
    # This observer invokes the real unmodified sklearn class with EXACT author args;
    # it does not seed, repair empty groups, change initialization or replay a fixture.
    fits=[]
    class ObserveKMeans:
        def __init__(self,*a,**kw):
            need(a==(ncluster,) and kw=={"n_init":10},"actual unchanged author KMeans arguments")
            self.inner=KMeans(*a,**kw)
        def fit(self,x):
            number=len(fits);layer=LAYERS[number//2];side=("k","v")[number%2]
            stage=out/("fit-%02d"%number);stage.mkdir()
            rows=x.to(torch.float64).tolist()
            need(rows==bundle["sides"][side][layer]["feature_rows"],"actual author minmax stack.T argument")
            state=np.random.get_state()
            pre=publish(stage/"RAW_PRE.json",{"logical_layer":layer,"side":side,"feature_rows":rows,
                "actual_input_dtype":str(x.dtype),"original_capture_dtype":bundle["dtype"],
                "feature_input_mode":feature_mode,"actual_input_shape":list(x.shape),"actual_input_device":str(x.device),
                "sklearn_parameters":self.inner.get_params(deep=False),
                "numpy_rng":{"algorithm":state[0],"keys":state[1].tolist(),"position":int(state[2]),
                             "has_gauss":int(state[3]),"cached_gaussian":float(state[4])},
                "author_does_not_set_random_state":True,"not_teacher_or_clipping_alpha":True})
            try:
                fitted=self.inner.fit(x)
                need(fitted is self.inner,"original sklearn fit result identity")
                pools=threadpool_info()
                need(all(type(p.get("num_threads"))is int and p["num_threads"]==1 for p in pools),"actual fitting OpenMP/BLAS thread count")
                row={"logical_layer":layer,"side":side,"fit_raw_pre_ref":pre,
                     "labels":[int(v) for v in self.inner.labels_],
                     "centers":self.inner.cluster_centers_.tolist(),
                     "inertia":float(self.inner.inertia_),"iterations":int(self.inner.n_iter_),
                     "actual_parameters":self.inner.get_params(deep=False),"actual_threadpools":pools}
                row["fit_result_ref"]=publish(stage/"FIT_RESULT.json",row)
                fits.append(row);return self
            except BaseException as e:
                publish(stage/"FAILED.json",{"primary":{"type":type(e).__name__,"message":str(e),
                    "traceback":traceback.format_exc()},"raw_pre_ref":pre});raise
        @property
        def labels_(self):return self.inner.labels_
    function,function_info=extract(bundle["author_raw_refs"]["calibration.py"],torch,ObserveKMeans)
    group_path=out/"AUTHOR_GROUPS.pt"
    need(not group_path.exists(),"original author's exclusive new save target")
    function(data,ncluster,str(group_path),metric="minmax",num_layers=16)
    need(len(fits)==32,"bothK/V all16actual FA original function calls")
    groups_ref=reference(group_path)
    saved=torch.load(group_path,map_location="cpu",weights_only=True)
    need(set(saved)=={"reorder_indices","cluster_st_inds"} and
         len(saved["reorder_indices"])==len(saved["cluster_st_inds"])==16,
         "whole original author serialized return")
    layers={}
    for i,layer in enumerate(LAYERS):
        layers[layer]={}
        for j,side in enumerate(("k","v")):
            row=fits[2*i+j].copy()
            row["permutation"]=saved["reorder_indices"][i][j].tolist()
            row["cluster_st_inds"]=saved["cluster_st_inds"][i][j].tolist()
            layers[layer][side]=row
    module_refs={}
    for name,obj in (("torch",torch),("numpy",np),("sklearn",sklearn),("actual_sklearn_KMeans",KMeans)):
        path=Path(inspect.getfile(obj));module_refs[name]=reference(path)
    execution={"schema":"SKVQ_ACTUAL_AUTHOR_FUNCTION_EXECUTION_V1","function":function_info,
        "packet_source_manifest_ref":packet_ref,"author_raw_refs":bundle["author_raw_refs"],"actual_library_probe_ref":library_ref,
        "projection_consumed_ref":bundle["projection_consumed_ref"],"v_consumed_ref":bundle["v_consumed_ref"],
        "dtype":bundle["dtype"],"feature_dtype":feature_name,"feature_input_mode":feature_mode,
        "original_A16_extrema_equal_effective_feature_values":True,"actual_arguments":{"n_cluster":ncluster,"metric":"minmax","num_layers":16,
            "save_path":str(group_path)},"actual_modules":module_refs,
        "versions":{"torch":torch.__version__,"numpy":np.__version__,"sklearn":sklearn.__version__},
        "actual_cpu_threads":{"intra":torch.get_num_threads(),"interop":torch.get_num_interop_threads()},
        "actual_no_npu_tensor":True,"groups_pt_ref":groups_ref,"layers":layers,
        "original_function_body_unmodified":True,"observer_changes_fit_or_labels":False,
        "smooth_factor_function_called":False,"groupwise_clipping_alpha_search_run":False,
        "native_ready":False,"model_ready":False}
    eref=publish(out/"AUTHOR_EXECUTION.json",execution)
    result={"schema":"SKVQ_AUTHOR_CLUSTERING_PRODUCER_V1",
        "status":"ACTUAL_AUTHOR_CLUSTERING_RETURNED_PENDING_INDEPENDENT_CONSUMER",
        "actual_author_function_execution_ref":eref,"author_raw_refs":bundle["author_raw_refs"],
        "projection_consumed_ref":bundle["projection_consumed_ref"],"v_consumed_ref":bundle["v_consumed_ref"],
        "capture_producer_ref":bundle["capture_producer_ref"],"baseline_receipt_ref":bundle["baseline_receipt_ref"],
        "gsize":gsize,"n_cluster":ncluster,"layers":layers,"dataset":bundle["dataset"],
        "feature_input_mode":feature_mode,"feature_dtype":feature_name,
        "BF16_CPU32_precision_adaptation_not_author_FP16_calibration":feature_mode=="bf16-exact-cpu32",
        "named_Qwen16FA_adaptation":True,"teacher_required_for_this_default":False,
        "smooth_alpha_is_not_clipping_alpha":True,"formal_start":None,"formal_deadline":None,
        "portfolio_deadline":"2026-10-12T07:00:25Z","native_ready":False,"model_ready":False}
    result.update(rank=bundle["rank"],capture_whole_ref=bundle["capture_whole_ref"],unified_clip=.95,smooth_enabled=False,runtime_pre_rope=False,TP_local_not_global_equivalence=True)
    publish(out/"PRODUCER_RESULT.json",result);return result

def main():
    import argparse,json,sys
    from common import source,cpu_only,output_root,author_sources,reference,publish,LAYERS
    from calibration_inputs import inputs,split_rank
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true");ap.add_argument("--source-manifest-sha256")
    ap.add_argument("--whole-ref-json");ap.add_argument("--output");ap.add_argument("--library-ref-json");ap.add_argument("--feature-mode",choices=("original","bf16-exact-cpu32"))
    a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,native_ready=False,model_ready=False)));return
    need(a.whole_ref_json and a.output and a.feature_mode and a.library_ref_json,"actual whole capture/new output/explicit fitting precision/dependency preflight")
    packet=source(a.source_manifest_sha256);cpu_only();whole_ref=json.loads(Path(a.whole_ref_json).read_bytes())
    bundle=inputs(whole_ref);library_ref=json.loads(Path(a.library_ref_json).read_bytes())
    from library_probe import verify,match_loaded
    dependency=verify(library_ref,packet);match_loaded(dependency)
    out=output_root(a.output);refs=author_sources(out);ranks=[]
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1) # once, before any fit; never repeatedly reset interop
    for rank in range(4):
        stage=out/("rank-"+str(rank));stage.mkdir()
        local=dict(bundle,rank=rank,author_raw_refs=refs,sides={side:split_rank(bundle["sides"][side],rank)for side in("k","v")})
        run(local,stage,64,packet,a.feature_mode,library_ref);ranks.append(reference(stage/"PRODUCER_RESULT.json"))
    result=dict(schema="skvq.default-tp-local.producer/v1",status="AUTHOR_FUNCTION_ALL4_TP_LOCAL_RETURNED_PENDING_INDEPENDENT_CONSUMER",
      source_ref=packet,capture_whole_ref=whole_ref,actual_library_probe_ref=library_ref,rank_results=ranks,author_raw_refs=refs,global_channels=1024,local_channels=256,TP=4,
      groups_per_side=4,mean_group_size=64,unified_clip=.95,smooth_enabled=False,runtime_pre_rope=False,
      feature_mode=a.feature_mode,named_TP_local_Qwen_adaptation=True,author_global_grouping_equivalent=False,
      original_256_capture_repeated=False,teacher_required_for_this_default=False,native_ready=False,model_ready=False,performance_ready=False)
    print(json.dumps(publish(out/"PRODUCER_RESULT.json",result),sort_keys=True))
if __name__=="__main__":main()
