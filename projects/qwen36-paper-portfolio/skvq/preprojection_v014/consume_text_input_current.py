"""Independent stdlib consumption of native pure-text input provenance.
No Torch, candidate embedding calculation or native imports. Never grants math PASS.
"""
import ast,hashlib,json,struct
from pathlib import Path
import current_contract as C
MODULES={"vllm.v1.worker.gpu_model_runner":("GPUModelRunner",("_preprocess","_prepare_mm_inputs","_gather_mm_embeddings")),
 "vllm_ascend.worker.model_runner_v1":("NPUModelRunner",("_preprocess","_model_forward")),
 "vllm.model_executor.models.qwen3_5":("Qwen3_5ForConditionalGeneration",("embed_input_ids","forward"))}
def obj(ref):
    C.checked(ref);return json.loads(Path(ref["path"]).read_bytes())
def runtime_sources(source):
    manifest=obj(source);rows=manifest["native_text_input_runtime_sources"];out={}
    C.require(len(rows)==3 and {r["module"]for r in rows}==set(MODULES),"exact independent native input closure")
    for r in rows:
        C.checked(r["snapshot"]);tree=ast.parse(Path(r["snapshot"]["path"]).read_bytes())
        cls,names=MODULES[r["module"]];classes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cls]
        C.require(len(classes)==1,"one actual original class source")
        methods={}
        for name in names:
            funcs=[n for n in classes[0].body if isinstance(n,ast.FunctionDef)and n.name==name]
            C.require(len(funcs)==1 and not funcs[0].decorator_list,"exact undecorated native method body")
            methods[name]={"qualname":cls+"."+name,"first_line":funcs[0].lineno}
        out[r["module"]]={"origin":dict(path=r["runtime_path"],bytes=r["snapshot"]["bytes"],
          sha256=r["snapshot"]["sha256"]),"methods":methods}
    return out
def consume(ref,source,input_ref,sample,rank,identity,expected,token_sha,*,runtime=None):
    value=obj(ref);embed=obj(value["embed_raw_ref"]);root=obj(value["root_raw_ref"])
    C.require(value["schema"]=="skvq.native-text-input-provenance/v1"and value["source_ref"]==source and
      value["input_ref"]==input_ref and value["sample_id"]==sample and value["rank"]==rank and
      value["identity"]==identity,"same original worker/sample/input source")
    origins=runtime_sources(source)if runtime is None else runtime
    C.require(value["runtime_sources"]==embed["runtime_sources"]==root["runtime_sources"]==origins,
      "source-qualified native preprocessing/embedding/forward methods")
    for record,schema in ((embed,"skvq.native-text-embed-raw/v1"),(root,"skvq.native-root-input-raw/v1")):
        C.require(record["schema"]==schema and record["source_ref"]==source and
          record["rank"]==rank and record["identity"]==identity and record["sample_id"]==sample,
          "actual raw-before same source/rank/sample")
    tokens=value["actual_token_ids"]
    C.require(type(tokens)is list and len(tokens)==4096 and all(type(i)is int and 0<=i<248320 for i in tokens)and
      tokens==expected==value["actual_request_prompt_token_ids"]and
      hashlib.sha256(struct.pack("<4096I",*tokens)).hexdigest()==token_sha==value["token_ids_sha256"],
      "independent full original token IDs and frozen request hash")
    C.require(value["actual_mm_mask"]==[False]*4096 and all(type(i)is bool for i in value["actual_mm_mask"])and
      value["request_checks"]=={"prompt_embeds_is_none":True,"mm_features_empty":True,
        "mm_embeddings_empty":True,"all4096_mm_mask_false":True,"num_computed_tokens":0},
      "no media/external prompt embedding substitution")
    caller=embed["caller"];schedule=embed["scheduler"];req=value["request_id"]
    C.require(caller["qualname"]=="GPUModelRunner._preprocess"and caller["file"]==origins[
      "vllm.v1.worker.gpu_model_runner"]["origin"]["path"]and caller["same_runner"]is True and
      type(caller["line"])is int and 3447<=caller["line"]<=3451 and
      embed["multimodal_embeddings_type"]=="list"and embed["multimodal_embeddings_count"]==0 and
      schedule=={"present":True,"batch_request_ids":[req],"num_scheduled_tokens":{req:4096},
        "total_num_scheduled_tokens":4096,"num_input_tokens":4096,"scheduled_encoder_inputs":{},
        "intermediate_tensors_is_none":True},"actual source original text-only scheduler branch")
    C.require(root["intermediate_tensors"]=={"kind":"None"}and root["pending_original_embedding"]is True and
      root["inputs_embeds"]=={"kind":"tensor","view":value["root_embedding_view"]}and
      value["root_embedding_view"]==value["runner_embedding_buffer_view"]and
      value["original_embedding_return_bitwise_equal"]is True and
      value["retained_original_tensor_no_clone"]is True,"actual original embedding-to-root transport identity")
    root_view=value["root_embedding_view"];original=value["original_embedding_return"]
    C.require(root_view["shape"]==original["shape"]and len(root_view["shape"])==2 and root_view["shape"][0]==4096 and
      root_view["shape"][1]>0 and root_view["dtype"]==original["dtype"]and
      root_view["dtype"]in ("torch.float16","torch.bfloat16")and
      root_view["device"].startswith("npu")and original["device"].startswith("npu"),
      "original full native A16 embedding typed views")
    flag=value["requires_raw_input_tokens"]
    C.require(type(flag)is bool and value["root_input_ids_is_none"]is (not flag)and
      (root["input_ids"]=={"kind":"None"}if not flag else root["input_ids"]["kind"]=="tensor"),
      "original model raw-token policy, not arbitrary representation union")
    positions=value["actual_positions"]
    C.require((positions==list(range(4096))or positions==[list(range(4096))]*3)and
      value["actual_positions_zero_to4095"]is True and value["capture_ready"]is False and
      value["model_ready"]is False,"actual complete text position domain and no authority promotion")
    return value

def consume_preweights(ref,source,reader=obj):
    value=reader(ref);C.require(value["schema"]=="skvq.native-text-input-source-preweights/v1"and
      value["source_ref"]==source and value["runtime_sources"]==runtime_sources(source)and
      value["actual_tensor_path_pending"]is True and value["capture_ready"]is False and
      value["model_ready"]is False,"original native input methods qualified beforeweights, no tensor authority")
    return value
