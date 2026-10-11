"""Complete synthetic32768 file->writer consumption, plus retained guard diff.
Expected code/scale/minimum bytes are made by the pinned OLD scalar codec.
These are labelled fixtures, NOT actual018/NPU/model evidence.
"""
import argparse, ast, copy, hashlib, importlib.util, json, sys, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGINAL=SCALAR=NEW=None
PRODUCER=None
VECTOR=None
FIXTURE_ROOT=None


def load(path,name):
    assert name not in sys.modules
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module


class Files:
    def __init__(self):
        self.temp=tempfile.TemporaryDirectory(prefix="kivi-writer-equivalence-",dir=FIXTURE_ROOT or HERE)
        self.root=Path(self.temp.name).resolve()
        self.bytes_written=0
    def close(self):self.temp.cleanup()
    def put(self,name,value):
        wire=value if type(value)is bytes else json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        path=self.root/name
        with path.open("xb")as stream:stream.write(wire)
        self.bytes_written+=len(wire)
        return dict(path=str(path),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
    def changed(self,ref,name,mutate):
        value=json.loads(Path(ref["path"]).read_bytes());mutate(value)
        return self.put(name,value)


def fixture():
    f=Files();bits=2;dtype="bfloat16";pages=276;records=pages*128;slots=16
    names=ORIGINAL.FIELDS
    sizes=dict(key_codes=pages*128*256*bits//8,key_scales=pages*2048,key_minima=pages*2048,
       value_codes=records*64,value_scales=records*16,value_minima=records*16,
       key_residual=slots*128*512,value_residual=slots*129*512)
    pools={name:bytearray(size)for name,size in sizes.items()}
    raw=SCALAR.scalar_bytes([((i*17)%257-128)/16 for i in range(32768)],dtype)
    vals=SCALAR.scalars(raw,dtype);rows=[vals[t*256:(t+1)*256]for t in range(128)]
    key=SCALAR.pack(rows,"K",bits,dtype);value=SCALAR.pack(rows,"V",bits,dtype)
    kp=[i*11%pages for i in range(256)]
    vp=[i*13%records for i in range(32640)]
    slot=3;tiles=[]
    for i in range(256):
        tiles.append(dict(start=i*128,stop=(i+1)*128,key_ref=f.put("K-%03d.bin"%i,raw),
                          value_ref=f.put("V-%03d.bin"%i,raw)))
        for field,width,data in (("key_codes",8192,key.payload),("key_scales",2048,key.scales),
                                 ("key_minima",2048,key.minima)):
            pools[field][kp[i]*width:(kp[i]+1)*width]=data
        if i<255:
            for t,record in enumerate(vp[i*128:(i+1)*128]):
                for field,width,data in (("value_codes",64,value.payload),("value_scales",16,value.scales),
                                         ("value_minima",16,value.minima)):
                    pools[field][record*width:(record+1)*width]=data[t*width:(t+1)*width]
    append=SCALAR.scalar_bytes([0.125]*256,dtype)
    pools["key_residual"][slot*128*512:slot*128*512+512]=append
    pools["value_residual"][slot*129*512:slot*129*512+65536]=raw
    pools["value_residual"][(slot*129+128)*512:(slot*129+129)*512]=append
    ident=dict(pid=123,start_ticks=456,cgroup="/synthetic-not-device")
    layer="fixture.layer.11";rid="synthetic-request";base=2**32
    native_bytes=records*256*2
    fields=[("key_codes",[pages,8,256],"torch.int32"),("key_scales",[pages,4,256],"torch.bfloat16"),
       ("key_minima",[pages,4,256],"torch.bfloat16"),("value_codes",[records,16],"torch.int32"),
       ("value_scales",[records,8],"torch.bfloat16"),("value_minima",[records,8],"torch.bfloat16"),
       ("key_residual",[16,128,256],"torch.bfloat16"),("value_residual",[16,129,256],"torch.bfloat16"),
       ("shifts",[16],"torch.int32")]
    total=2*native_bytes+sum(sizes.values())+64
    def descriptor(shape,dtype,start):
        width={"torch.int32":4,"torch.bfloat16":2,"torch.uint8":1}[dtype]
        stride=[];count=1
        for n in reversed(shape):stride.insert(0,count);count*=n
        return dict(shape=shape,stride=stride,dtype=dtype,contiguous=True,element_size=width,
           logical_bytes=count*width,storage_base=base,storage_bytes=total,
           storage_offset_elements=start//width,data_ptr=base+start,device="npu:0",
           layout="ND_CONTIGUOUS",observed_format_code=2)
    shape=[23,1536,1,256]
    views=[descriptor(shape,"torch.bfloat16",offset)for offset in(0,native_bytes)]
    pool=dict(size=total,raw=descriptor([total],"torch.uint8",0),shared_by=[layer])
    layers={"fixture.gdn.%02d"%i:dict(kind="GDN")for i in range(63)}
    layers[layer]=dict(kind="FA",block_size=1536,views=views)
    event=f.put("event.json",dict(rank=0,identity=ident,num_blocks=23,layers=layers,pools=[pool]))
    cursor=2*native_bytes;descriptors=[]
    for name,shape_,kind in fields:
        desc=descriptor(shape_,kind,cursor);descriptors.append(dict(name=name,descriptor=desc))
        cursor+=desc["logical_bytes"]
    geometry=dict(schema="kivi.actual-disjoint-field-geometry/v1",rank=0,identity=ident,
       layer=layer,pages=pages,slots=slots,bits=bits,dtype="torch.bfloat16",
       newly_allocated_device_bytes=0,original_dense_storage_still_live=True,
       packing_checked=False,reader_checked=False,allocation_replaced=False,
       native_ready=False,model_ready=False,run_authority=False,original_parent_bytes=total,
       fields=descriptors,region=dict(pool=pool,base=base,start=2*native_bytes,stop=cursor,
       field_bytes=cursor-2*native_bytes,all_original_native_writers_enabled=True,
       allocation_replaced=False,run_authority=False))
    gref=f.put("geometry.json",geometry)
    pf=f.put("prefill.json",dict(schema="kivi.actual-packed-qwen-frame/v1",kind="prefill",
       rank=0,identity=ident,req_ids=[rid],epoch=1,computed_tokens=[0],scheduled_counts=[32768]))
    df=f.put("decode.json",dict(schema="kivi.actual-packed-qwen-frame/v1",kind="decode",
       rank=0,identity=ident,req_ids=[rid],epoch=2,computed_tokens=[32768],scheduled_counts=[1]))
    p=dict(schema="kivi.actual-original-prefill/v1",status="ORIGINAL_PREFILL_CAPTURED",
       rank=0,identity=ident,layer=layer,request_id=rid,slot=slot,slot_epoch=7,
       dtype=dtype,bits=bits,installer_source_sha256="a"*64,capture_source_sha256="b"*64,
       prompt_length=32768,original_bytes=33554432,original_attention_calls=1,
       allocation_replaced=False,graph_checked=False,model_ready=False,performance_ready=False,
       run_authority=False,writer_arithmetic_checked=False,frame_ref=pf,event_ref=event,
       geometry_ref=gref,native_shape=shape,native_views=views,native_block_row=list(range(23)),tiles=tiles)
    p.update(ORIGINAL.PINS);pref=f.put("original-prefill.json",p)
    owner=f.put("owner.json",dict(schema="kivi.actual-qwen-slot-owner/v1",rank=0,identity=ident,
       layer=layer,request_id=rid,slot=slot,epoch=7,computed=32768,generation=1,
       frame_ref=df,original_prefill_ref=pref))
    pool_refs={k:f.put(k+".bin",bytes(v))for k,v in pools.items()}
    frame=dict(schema="kivi.actual-packed-qkav-frame/v1",kernel_source_sha256=ORIGINAL.KERNEL_SHA,
       snapshot_is_live_alias=False,model_ready=False,run_authority=False,bits=bits,dtype=dtype,
       rows=[dict(controls=[32769,32768,32640,slot],computed=32768,generation=1,
                  slot=slot,epoch=7,kp=kp,vp=vp,request_id=rid,identity_refs=dict(slot_owner=owner))],
       pool_geometry=[pages,records,16],pool_fields=pool_refs,
       live_alias_descriptors_before_snapshot={row["name"]:row["descriptor"]for row in descriptors if row["name"]in names},
       whole_prewrite_input_refs=dict(query=f.put("query.bin",append*6),key=f.put("append-key.bin",append),value=f.put("append-value.bin",append)))
    f.frame=f.put("frame.json",frame);f.frame_object=frame;f.provenance=pref;f.owner=owner
    return f


class FullReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f=fixture()
    @classmethod
    def tearDownClass(cls):cls.f.close()
    def run_reader(self,module,frame=None):
        return module.consume(frame or self.f.frame,SCALAR_REF,installer_sha256="a"*64,capture_sha256="b"*64)
    def test01_original_scalar_to_complete_vector_files(self):
        old=self.run_reader(ORIGINAL);new=self.run_reader(NEW)
        for key in("independent_vector_source","numpy_version","scalar_reference_preserved","candidate_math_called"):
            new.pop(key)
        self.assertEqual(old,new)
        self.assertEqual(new["rows"][0]["original_tokens"],32768)
    def test02_changed_code_with_matching_file_hash_rejected(self):
        frame=copy.deepcopy(self.f.frame_object);r=frame["pool_fields"]["key_codes"]
        wire=bytearray(Path(r["path"]).read_bytes());wire[0]^=1
        frame["pool_fields"]["key_codes"]=self.f.put("changed-codes.bin",bytes(wire))
        ref=self.f.put("changed-code-frame.json",frame)
        with self.assertRaisesRegex(ValueError,"writer bytes key_codes"):self.run_reader(NEW,ref)
    def test03_omitted_original_tile_rejected(self):
        pref=self.f.changed(self.f.provenance,"short-prefill.json",lambda p:p["tiles"].pop())
        owner=self.f.changed(self.f.owner,"short-owner.json",lambda o:o.update(original_prefill_ref=pref))
        frame=copy.deepcopy(self.f.frame_object);frame["rows"][0]["identity_refs"]["slot_owner"]=owner
        with self.assertRaisesRegex(ValueError,"whole original32768"):
            self.run_reader(NEW,self.f.put("short-frame.json",frame))
    def test04_last_residual_byte_with_new_hash_rejected(self):
        frame=copy.deepcopy(self.f.frame_object);r=frame["pool_fields"]["value_residual"]
        wire=bytearray(Path(r["path"]).read_bytes());wire[(3*129+128)*512+511]^=1
        frame["pool_fields"]["value_residual"]=self.f.put("changed-residual.bin",bytes(wire))
        with self.assertRaisesRegex(ValueError,"writer bytes value_residual"):
            self.run_reader(NEW,self.f.put("residual-frame.json",frame))
    def test05_duplicate_physical_page_rejected(self):
        frame=copy.deepcopy(self.f.frame_object);frame["rows"][0]["kp"][1]=frame["rows"][0]["kp"][0]
        with self.assertRaisesRegex(ValueError,"prefix maps"):
            self.run_reader(NEW,self.f.put("duplicate-frame.json",frame))
    def test06_wrong_full_geometry_rejected(self):
        frame=copy.deepcopy(self.f.frame_object);frame["pool_geometry"][0]-=1
        with self.assertRaisesRegex(ValueError,"native-derived"):
            self.run_reader(NEW,self.f.put("geometry-frame.json",frame))
    def test07_scalar_original_source_identity(self):
        self.assertEqual(hashlib.sha256((PRODUCER/"consume_prefill.py").read_bytes()).hexdigest(),
          "3e4a100be9225c3ec464e1d256761a780648fad3dfd4b1dc79db8f883fd092f1")


class SourceAndProgress(unittest.TestCase):
    def test08_all_original_need_predicates_identical(self):
        def guards(path):
            return [ast.dump(n)for n in ast.walk(ast.parse(path.read_bytes()))if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Name)and n.func.id=="need"]
        old=guards(PRODUCER/"consume_prefill.py")
        new=guards(HERE/"consume_prefill_vector.py")
        new.remove(ast.dump(ast.parse('need(module.SCALAR_REFERENCE_SHA == CODEC_SHA, "same exact scalar cross-reference")').body[0].value))
        self.assertEqual(old,new)
    def test09_unchanged_functions_byte_AST(self):
        def funcs(path):return {n.name:ast.dump(n)for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        old=funcs(PRODUCER/"consume_prefill.py");new=funcs(HERE/"consume_prefill_vector.py")
        for name in old:
            if name!="consume":self.assertEqual(old[name],new[name],name)
    def test10_aggregate_keeps_every_gate_and_numeric_call(self):
        old=ast.parse((PRODUCER/"consume_first_decode.py").read_bytes())
        new=ast.parse((HERE/"consume_first_decode_progress.py").read_bytes())
        def calls(tree,name):
            return [ast.dump(n)for n in ast.walk(tree)if isinstance(n,ast.Call)and
              (isinstance(n.func,ast.Name)and n.func.id==name or isinstance(n.func,ast.Attribute)and
              isinstance(n.func.value,ast.Name)and n.func.value.id==name)]
        for name in("need","pin","writer_reader","output_reader","fields","spans","journal"):
            self.assertEqual(calls(old,name),calls(new,name),name)
    def test11_actual_progress_stdout_coverage_is_not_PASS(self):
        import contextlib,io,time
        module=load(HERE/"consume_first_decode_progress.py","_progress_actual_fixture")
        target=io.StringIO()
        with contextlib.redirect_stdout(target):
            for rank in range(4):
                for layer in range(16):
                    count=rank*16+layer
                    for phase,done in (("writer-start",count),("writer-complete-output-start",count),("FA-complete",count+1)):
                        module.progress(phase,rank,"synthetic.%d"%layer,dict(path="/fixture",bytes=1,sha256="0"*64),done,time.monotonic())
        records=[json.loads(x)for x in target.getvalue().splitlines()]
        self.assertEqual(len(records),192);self.assertEqual(records[-1]["completed_FA"],64)
        self.assertTrue(all(x["numeric_acceptance"]is False for x in records))
    def test12_actual_source_load_rejects_drift(self):
        with unittest.mock.patch.object(NEW,"VECTOR_SHA","0"*64):
            with self.assertRaisesRegex(ValueError,"whole Ref SHA"):NEW.vector_module()


def main():
    global ORIGINAL,SCALAR,NEW,PRODUCER,SCALAR_REF
    import time
    from unittest import mock
    p=argparse.ArgumentParser();p.add_argument("--producer-archive",type=Path,required=True);p.add_argument("--scalar-source",type=Path,required=True)
    args=p.parse_args();PRODUCER=args.producer_archive
    data=args.scalar_source.read_bytes()
    assert hashlib.sha256(data).hexdigest()=="45ccb0c2fff417e518cb591aaf5ba201645551a1aeafc9d8bdc3c97ce6a8fd49"
    SCALAR_REF=dict(path=str(args.scalar_source.resolve()),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    SCALAR=load(args.scalar_source,"_file_fixture_actual_scalar")
    ORIGINAL=load(PRODUCER/"consume_prefill.py","_file_fixture_original_reader")
    NEW=load(HERE/"consume_prefill_vector.py","_file_fixture_new_reader")
    start=time.perf_counter()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(FullReader),unittest.defaultTestLoader.loadTestsFromTestCase(SourceAndProgress)]))
    print(json.dumps(dict(schema="kivi.vector-writer-full-file-fixture/v1",tests=result.testsRun,
          failures=len(result.failures),errors=len(result.errors),elapsed=time.perf_counter()-start,
          original_prompt_tokens=32768,original_K_tiles=256,original_V_tiles=256,
          all_original_reference_paths=512,synthetic=True,actual018=False,NPU=False,
          scalar_to_vector_full_file_positive=True if result.wasSuccessful()else None)),flush=True)
    return 0 if result.wasSuccessful()else 1

if __name__=="__main__":raise SystemExit(main())
