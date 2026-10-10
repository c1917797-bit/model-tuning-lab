"""Source-derived original preprocessing and complete input-provenance regressions.
All tensors/requests here are explicit software surrogates, not native authority.
"""
import argparse,ast,copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import current_contract as C
import text_input_current as T
import consume_text_input_current as U
REVIEW=None
def raw(module):
    m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
    ref=next(r["snapshot"]for r in m["native_text_input_runtime_sources"]if r["module"]==module)
    if REVIEW:
        names={T.GPU:"runner.py",T.NPU:"runner-94d75.py",T.QWEN:"qwen3_5.py"}
        p=REVIEW/names[module]
        if not p.exists()and module==T.QWEN:p=REVIEW.parent.parent.parent.parent.parent/"Temp"/"c152-native-config/qwen3_5.py"
        if not p.exists()and module==T.QWEN:p=Path("C:/Users/Huawei/AppData/Local/Temp/c152-native-config/qwen3_5.py")
    else:p=Path(ref["path"])
    b=p.read_bytes()
    if len(b)==ref["bytes"]+1 and b.endswith(b"\n")and hashlib.sha256(b[:-1]).hexdigest()==ref["sha256"]:b=b[:-1]
    C.require(len(b)==ref["bytes"]and hashlib.sha256(b).hexdigest()==ref["sha256"],"whole actual original source")
    return b.decode(),ref
def native(module,cls,names):
    text,ref=raw(module);node=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef)and n.name==cls)
    node=copy.deepcopy(node);node.bases=[];node.keywords=[];node.decorator_list=[]
    node.body=[n for n in node.body if isinstance(n,ast.FunctionDef)and n.name in names]
    ns={"__name__":module,"get_pp_group":lambda:types.SimpleNamespace(is_first_rank=True)}
    tree=ast.Module(body=[ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0),node],type_ignores=[])
    runtime=next(x["runtime_path"]for x in json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())["native_text_input_runtime_sources"]if x["module"]==module)
    exec(compile(ast.fix_missing_locations(tree),runtime,"exec"),ns)
    return ns[cls],ns
class Tensor:
    def __init__(self,values,shape=None,device="npu:0",dtype="torch.bfloat16",ptr=100):
        self.values=values;self.shape=shape or (len(values),);self.device=types.SimpleNamespace(type=device.split(":")[0])
        self.device_text=device;self.dtype=dtype;self.ptr=ptr
    def __getitem__(self,index):
        if isinstance(index,slice):return Tensor(self.values if index.stop==len(self.values)else self.values[:index.stop],(index.stop,)+tuple(self.shape[1:]),self.device_text,self.dtype,self.ptr)
        raise AssertionError("surrogate only native slice")
    def copy_(self,value):self.values[:]=value.values;return self
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return list(self.values)
def descriptor(t):
    return dict(shape=list(t.shape),stride=[t.shape[1],1]if len(t.shape)==2 else [1],
      dtype=t.dtype,device=t.device_text,storage_data_ptr=t.ptr,storage_nbytes=4096*8*2,
      storage_offset_elements=0,element_size=2,numel=4096*8 if len(t.shape)==2 else 4096,data_ptr=t.ptr)
def make(tmp):
    root=Path(tmp);expected=list(range(4096))
    inputs=root/"inputs.json";inputs.write_text("{}")
    input_ref=C.reference(inputs.absolute());source_path=root/"SOURCE_MANIFEST.json"
    manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
    localrows=[]
    for row in manifest["native_text_input_runtime_sources"]:
        text,ref=raw(row["module"]);p=root/(row["module"].replace(".","-")+".py");p.write_bytes(text.encode())
        localrows.append(dict(row,snapshot=C.reference(p.absolute())))
    source_path.write_text(json.dumps({"native_text_input_runtime_sources":localrows}));source=C.reference(source_path.absolute())
    gpu,gns=native(T.GPU,"GPUModelRunner",("_preprocess","_prepare_mm_inputs","_gather_mm_embeddings"))
    qwen,qns=native(T.QWEN,"Qwen3_5ForConditionalGeneration",("embed_input_ids","forward"))
    npu,nns=native(T.NPU,"NPUModelRunner",("_preprocess","_model_forward"))
    model=qwen();model.requires_raw_input_tokens=False;model.language_model=types.SimpleNamespace(embed_input_ids=lambda x:None)
    model._embed_text_input_ids=lambda ids,callback,is_multimodal:Tensor([i+.25 for i in ids.values],(4096,8),ptr=200)
    model.language_model.model=lambda input_ids,positions,intermediate_tensors,inputs_embeds:inputs_embeds
    runner=gpu();runner.model=model;runner.inputs_embeds_size=8
    runner.model_config=types.SimpleNamespace(is_encoder_decoder=False)
    runner.supports_mm_inputs=True;runner.enable_prompt_embeds=False;runner.uses_mrope=False;runner.uses_xdrope_dim=0
    runner.input_ids=types.SimpleNamespace(gpu=Tensor(list(expected),device="npu:0",dtype="torch.int32",ptr=300))
    runner.inputs_embeds=types.SimpleNamespace(gpu=Tensor([0]*4096,(4096,8),ptr=400))
    runner.positions=Tensor(expected,device="npu:0",dtype="torch.int64",ptr=500)
    runner.input_batch=types.SimpleNamespace(req_ids=["actual"],req_prompt_embeds={})
    runner.requests={"actual":types.SimpleNamespace(prompt_token_ids=list(expected),prompt_embeds=None,mm_features=[],num_computed_tokens=0)}
    runner.maybe_get_ec_connector_output=lambda *a,**k: __import__("contextlib").nullcontext(None)
    runner.encoder_cache={};runner._execute_mm_encoder=lambda x:None
    mask=Tensor([False]*4096,device="cpu",dtype="torch.bool",ptr=600)
    runner._gather_mm_embeddings=lambda x:([],mask)
    runner._init_model_kwargs=lambda:{};runner._extract_mm_kwargs=lambda x:{}
    schedule=types.SimpleNamespace(total_num_scheduled_tokens=4096,num_scheduled_tokens={"actual":4096},scheduled_encoder_inputs={})
    identity=dict(pid=123,pid_start_ticks=456,public_TP_rank=0)
    session=types.SimpleNamespace(w=types.SimpleNamespace(rank=0,model_runner=runner),model=model,
      original_root=model.forward,active=0,poisoned=False,closed=False,in_forward=False,input_path=str(inputs),
      input_ref=input_ref,identity=identity,inputs={"samples":[{"token_ids_sha256":hashlib.sha256(__import__("struct").pack("<4096I",*expected)).hexdigest()}]},
      sink=types.SimpleNamespace(path=root))
    originals=U.runtime_sources(source)
    functions={(T.GPU,name):getattr(gpu,name)for name in T.METHODS[T.GPU][1]}
    functions.update({(T.NPU,name):getattr(npu,name)for name in T.METHODS[T.NPU][1]})
    functions.update({(T.QWEN,name):getattr(qwen,name)for name in T.METHODS[T.QWEN][1]})
    # __init__ ownership functions still checked; actual runner shape/control is explicit surrogate.
    runner._preprocess=types.MethodType(npu._preprocess,runner);runner._model_forward=types.MethodType(npu._model_forward,runner)
    torch=types.ModuleType("torch");torch.Tensor=Tensor;torch.int32="torch.int32";torch.int64="torch.int64";torch.bool="torch.bool"
    torch.equal=lambda a,b:a.values==b.values
    io=types.ModuleType("io_contract");io.sample_ids=lambda p,s:expected
    post=types.ModuleType("post_rope_current");post.tensor_description=descriptor
    def publish(path,value):
        with Path(path).open("xb")as f:f.write(json.dumps(value,sort_keys=True).encode()+b"\n")
        return C.reference(Path(path).absolute())
    def run(mutate=None,root_mutate=None):
        with patch.dict(sys.modules,{"torch":torch,"io_contract":io,"post_rope_current":post}),patch.object(T,"qualified",return_value=(originals,functions)):
            tracking=T.TextInputs(session,source,publish);original=tracking.original
            def embed(this,*args,**kwargs):
                frame=__import__("inspect").currentframe().f_back
                record=tracking.begin(frame,args[0],kwargs["multimodal_embeddings"],kwargs["is_multimodal"])
                return tracking.returned(record,original(*args,**kwargs))
            model.embed_input_ids=types.MethodType(embed,model)
            if mutate:mutate(runner,schedule,mask)
            # Execute actual unmodified native GPU preprocess body, including original Qwen embed.
            ids,embeds,positions,intermediate,kw,_=gpu._preprocess(runner,schedule,4096)
            if root_mutate:ids,embeds,positions,intermediate=root_mutate(ids,embeds,positions,intermediate)
            bound=__import__("inspect").signature(session.original_root).bind(ids,positions,intermediate,embeds,**kw);bound.apply_defaults()
            ref=tracking.root(bound)
            result=session.original_root(ids,positions,intermediate,embeds,**kw)
            return tracking,ref,result
    return types.SimpleNamespace(root=root,source=source,input_ref=input_ref,expected=expected,session=session,
      runner=runner,schedule=schedule,mask=mask,gpu=gpu,torch=torch,run=run,publish=publish,originals=originals,functions=functions)
def consume(f,ref):
    return U.consume(ref,f.source,f.input_ref,0,0,f.session.identity,f.expected,
      f.session.inputs["samples"][0]["token_ids_sha256"])
class NativeText(unittest.TestCase):
    def test01_actual_native_text_preprocess_embedding_root_and_independent_consumer(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp);tracking,ref,result=f.run();v=consume(f,ref)
            self.assertIs(result.values,f.runner.inputs_embeds.gpu.values)
            self.assertTrue(v["original_embedding_return_bitwise_equal"]);self.assertIsNone(f.gpu._prepare_mm_inputs(f.runner,4096)[0])
            tracking.release();self.assertIsNone(tracking.pending)
    def test02_media_mask_rejected_after_actual_raw_saved(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"all-false"):f.run(lambda r,s,m:m.values.__setitem__(2,True))
            self.assertTrue((f.root/"sample-000-EMBED_RAW_BEFORE.json").is_file())
    def test03_external_prompt_embeddings_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"external embeddings"):f.run(lambda r,s,m:setattr(r.requests["actual"],"prompt_embeds",object()))
    def test04_changed_native_ids_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"frozen token-ID"):f.run(lambda r,s,m:r.input_ids.gpu.values.__setitem__(4,9))
    def test05_chunked_schedule_or_padding_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"complete fresh"):f.run(lambda r,s,m:setattr(s,"total_num_scheduled_tokens",2048))
    def test06_root_embedding_value_mutation_rejected_with_raw(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            def mutation(ids,e,p,it):e.values[4]+=1;return ids,e,p,it
            with self.assertRaisesRegex(ValueError,"bitwise"):f.run(root_mutate=mutation)
            self.assertTrue((f.root/"sample-000-ROOT_RAW_BEFORE.json").is_file())
    def test07_root_foreign_storage_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"typed alias"):f.run(root_mutate=lambda i,e,p,t:(i,Tensor(e.values,e.shape,ptr=999),p,t))
    def test08_pipeline_intermediate_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"PP1"):f.run(root_mutate=lambda i,e,p,t:(i,e,p,object()))
    def test09_independent_consumer_rejects_mutated_ids_extra_ref_and_source(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp);_,ref,_=f.run();v=consume(f,ref)
            for mutator in (lambda x:x["actual_token_ids"].__setitem__(3,9),
              lambda x:x["runtime_sources"][T.GPU]["origin"].update(sha256="f"*64),
              lambda x:x["embed_raw_ref"].update(origin="fake")):
                bad=copy.deepcopy(v);mutator(bad)
                p=f.root/("bad%d.json"%len(list(f.root.glob("bad*"))));r=f.publish(p,bad)
                with self.assertRaises(ValueError):consume(f,r)
    def test10_actual_original_class_method_sources_no_tensor_or_import_claim(self):
        for module,(cls,names)in T.METHODS.items():
            body,_=raw(module);tree=ast.parse(body);actual=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cls)
            self.assertEqual(set(names),{n.name for n in actual.body if isinstance(n,ast.FunctionDef)and n.name in names})
            for name in names:self.assertFalse(next(n for n in actual.body if isinstance(n,ast.FunctionDef)and n.name==name).decorator_list)
        body,_=raw(T.GPU);self.assertIn("even when the input is text.",body)
    def test11_real_session_hook_retains_original_embedding_call_and_all35_install_consumer(self):
        body=(HERE/"runtime_capture_current.py").read_text()
        self.assertIn('result=session.text_input.original(*args,**kwargs)',body)
        self.assertIn('self.bind(self.model,"embed_input_ids",embed)',body)
        self.assertIn('session.text_input.release()',body)
        install=(HERE/"spawn_startup.py").read_text()
        self.assertIn('len(patches)==35',install);self.assertIn('sum(name=="embed_input_ids"',install)
        self.assertIn('"embed":1',install)
        consumer=(HERE/"consume_capture_current.py").read_text()
        self.assertIn('text_ref=proof["actual_input"]["native_text_input_provenance_ref"]',consumer)
        self.assertIn('consume_text(text_ref,producer["current_source_ref"]',consumer)
        self.assertIn('all16 FA share one exact original input provenance',consumer)
    def test12_preweights_qualification_called_and_default_import_has_no_hardware(self):
        n1=(HERE/"n1_check.py").read_text()
        self.assertIn('text_input.preweights(source',n1)
        self.assertNotIn('import torch\n',(HERE/"text_input_current.py").read_text())
        self.assertNotIn('import torch',(HERE/"consume_text_input_current.py").read_text())
    def test13_foreign_preprocess_caller_rejected_after_raw(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with patch.object(T,"qualified",return_value=(f.originals,f.functions)):
                tracking=T.TextInputs(f.session,f.source,f.publish)
            with patch.dict(sys.modules,{"torch":f.torch,"post_rope_current":types.SimpleNamespace(tensor_description=descriptor)}):
                with self.assertRaisesRegex(ValueError,"original GPU superclass"):
                    tracking.begin(__import__("inspect").currentframe(),f.runner.input_ids.gpu,[],f.mask)
            self.assertTrue((f.root/"sample-000-EMBED_RAW_BEFORE.json").is_file())
    def test14_actual_method_qualification_and_foreign_wrapped_negative(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp);modules={};origref=C.reference
            for name,(cls,names)in T.METHODS.items():
                fn=f.functions[(name,names[0])];klass=fn.__globals__[cls]
                m=types.ModuleType(name);m.__file__=f.originals[name]["origin"]["path"]
                m.__spec__=types.SimpleNamespace(name=name,origin=m.__file__,loader=object());m.__loader__=m.__spec__.loader
                setattr(m,cls,klass);modules[name]=m
            def reference(path):
                for value in f.originals.values():
                    if str(path)==value["origin"]["path"]:return value["origin"]
                return origref(path)
            with patch.dict(sys.modules,modules),patch.object(T.importlib,"import_module",side_effect=lambda n:modules[n]),patch.object(C,"reference",side_effect=reference):
                origins,_=T.qualified(f.source);self.assertEqual(origins,f.originals)
                cls=modules[T.QWEN].Qwen3_5ForConditionalGeneration;old=cls.embed_input_ids
                try:
                    cls.embed_input_ids=lambda *a,**k:None
                    with self.assertRaisesRegex(ValueError,"foreign wrapper"):T.qualified(f.source)
                finally:cls.embed_input_ids=old
    def test15_actual_media_feature_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp)
            with self.assertRaisesRegex(ValueError,"media"):f.run(lambda r,s,m:r.requests["actual"].mm_features.append(object()))
    def test16_independent_consumer_rejects_nonzero_positions_and_old_hook_count(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp);_,ref,_=f.run();v=consume(f,ref)
            bad=copy.deepcopy(v);bad["actual_positions"][0]=1
            with self.assertRaises(ValueError):consume(f,f.publish(f.root/"bad-position.json",bad))
            from spawn_startup import installed
            self.assertIn("len(patches)==35",__import__("inspect").getsource(installed))

    def test17_actual_Session_install_embed_and_root_wrappers_run_original_native_body(self):
        with tempfile.TemporaryDirectory()as tmp:
            f=make(tmp);text=(HERE/"runtime_capture_current.py").read_text()
            cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef)and n.name=="Session")
            cls=copy.deepcopy(cls);cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name in ("bind","install","restore")]
            ns=dict(types=types,inspect=__import__("inspect"),sys=sys,require=C.require,OUTER_NAMES=set(range(16)),
              traceback=__import__("traceback"),record_failure=lambda *a:None)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),"actual-Session-wrapper","exec"),ns)
            session=ns["Session"].__new__(ns["Session"]);session.__dict__.update(f.session.__dict__)
            session.registry={};session.patches=[];session.linear=[];session.seen=set();session.next_id=0
            session.context_guard=lambda:None;session.sink.events=[]
            ns["deployed_sources"]=lambda:{};session.sources={}
            def root(input_ids,positions,intermediate_tensors,inputs_embeds):
                session.seen=set(range(16));return inputs_embeds
            session.model.language_model.model=root
            io=types.ModuleType("io_contract");io.sample_ids=lambda p,s:f.expected
            post=types.ModuleType("post_rope_current");post.tensor_description=descriptor
            with patch.dict(sys.modules,{"torch":f.torch,"io_contract":io,"post_rope_current":post}),patch.object(T,"qualified",return_value=(f.originals,f.functions)):
                session.text_input=T.TextInputs(session,f.source,f.publish);session.install()
                ids,embeds,positions,intermediate,kw,_=f.gpu._preprocess(f.runner,f.schedule,4096)
                result=session.model.forward(ids,positions,intermediate,embeds,**kw)
                self.assertIs(result.values,f.runner.inputs_embeds.gpu.values)
                self.assertEqual(session.next_id,1);self.assertIsNone(session.active);self.assertIsNone(session.text_input.pending)
                self.assertEqual(len(session.patches),2) # only new embed/root seam in explicit zero-FA software fixture
                ref=C.reference(f.root/"sample-000-TEXT_INPUT_PROVENANCE.json");consume(f,ref)
                self.assertEqual(session.restore(),[]);self.assertNotIn("embed_input_ids",session.model.__dict__)
def main(argv=None):
    global REVIEW
    p=argparse.ArgumentParser();p.add_argument("--review-root",type=Path);a=p.parse_args(argv);REVIEW=a.review_root
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeText))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
