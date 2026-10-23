"""Pure Python metadata/source controls, never Torch or NPU numerical evidence."""
import ast,copy,importlib.util,io,json,os,sys,types,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import render_capacity as R
raw=R.checked(R.GEOMETRY['path'],R.GEOMETRY)
spec=importlib.util.spec_from_file_location('fa_native_geometry',R.GEOMETRY['path'])
G=importlib.util.module_from_spec(spec);sys.modules['fa_native_geometry']=G
exec(compile(raw,R.GEOMETRY['path'],'exec'),G.__dict__)

class FakeTensor:
    device=types.SimpleNamespace(type='npu') # synthetic metadata label, not a real tensor
    def index_select(self,axis,index):return FakeTensor()
    def detach(self):return self
    def clone(self):return FakeTensor()

def geometry():
    # INTERNAL unit fixture only. Native bind_layer/bind_all are NOT invoked and
    # no serialized native observation or numerical PASS is generated.
    key=FakeTensor();value=FakeTensor();group=object();blocks=[3,7]
    table=tuple(p*12+j for p in blocks for j in range(12))
    facts=dict(prefix=2048,output_tokens=1024,max_before=3070,table=table,
        physical_blocks=tuple(blocks),ratio=12,physical_size=1536)
    class Row:
        def tolist(self):return list(table)
    class CPU:
        device=types.SimpleNamespace(type='cpu')
        def __getitem__(self,item):return Row()
    block=types.SimpleNamespace(num_blocks_per_row=[24],get_cpu_tensor=lambda:CPU(),
        blocks_per_phys_block=12,physical_block_size=1536,logical_block_size=128,
        block_size=128,use_hybrid_blocks=True,pcp_world_size=1,dcp_world_size=1)
    request=types.SimpleNamespace(block_ids={0:blocks})
    batch=types.SimpleNamespace(req_ids=['r'],req_id_to_index={'r':0},block_table=[block])
    runner=types.SimpleNamespace(requests={'r':request},input_batch=batch,
        kv_cache_config=types.SimpleNamespace(kv_cache_groups=[group]))
    layer=types.SimpleNamespace(kv_cache=[key,value],impl=types.SimpleNamespace(key_cache=key,value_cache=value))
    return G.NativeGeometry(G._TOKEN,{'synthetic':True},runner,request,'r',1,0,group,block,layer,
                            key,value,id(key),id(value),facts,id)

def module(raw,name):
    ns={'__name__':name};exec(compile(raw,name,'exec'),ns);return types.SimpleNamespace(**ns)

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=R.parent();cls.bundle=R.adapt(cls.parent)
        cls.old=module(cls.parent['g2_contract.py'],'old_contract')
        cls.new=module(cls.bundle['files']['g2_contract.py'],'derived_contract')
    def test_legacy131_original_function_and_domain_unchanged(self):
        def fn(raw,name):
            return next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef)and x.name==name)
        a=fn(self.parent['g2_contract.py'],'capacity')
        b=fn(self.bundle['files']['g2_contract.py'],'_capacity_131');b.name=a.name
        self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
        def result(call):
            try:return ('return',call())
            except Exception as e:return(type(e).__name__,str(e))
        for length in (True,0,130,131,137,1153,1154,2047):
            for pages in (1,2,12,24):
                for budget in (8,1024):
                    self.assertEqual(result(lambda:self.old.capacity(length,pages,budget=budget)),
                                     result(lambda:self.new.capacity(length,pages,budget=budget)))
    def test_native2048_3070_native24_private25(self):
        g=geometry()
        for length in (2048,3070):
            v=self.new.capacity(length,24,geometry=g)
            self.assertEqual(v['native_publication_end_exclusive'],length+2)
            self.assertEqual(v['private_end_exclusive'],length+3)
            self.assertEqual(v['active_kernel_pages'],(length+129)//128)
            self.assertEqual(v['private_scratch_required_pages'],(length+130)//128)
            self.assertFalse(v['private_scratch_allocation_proven'])
        self.assertEqual(self.new.capacity(3070,24,geometry=g)['private_scratch_required_pages'],25)
    def test_unknown_geometry_and_scratch_count_not_native_allocation(self):
        for value in (None,{},G.plan(2048,1024)):
            with self.assertRaises(ValueError):self.new.capacity(2048,24,geometry=value)
        for pages in (23,25,True):
            with self.assertRaises(ValueError):self.new.capacity(3070,pages,geometry=geometry())
    def test_real_binding_guards_batch_request_table_alias(self):
        for kind in ('batch','request','table','alias'):
            g=geometry()
            if kind=='batch':g.runner.input_batch.req_ids.append('other')
            if kind=='request':g.runner.requests['r']=object()
            if kind=='table':g.block.num_blocks_per_row[0]=23
            if kind=='alias':g.layer.impl.value_cache=object()
            with self.assertRaises(ValueError):self.new.capacity(2048,24,geometry=g)
    def test_output_and_private_domain_not_relaxed(self):
        with self.assertRaises(ValueError):self.new.capacity(2048,24,budget=8,geometry=geometry())
        with self.assertRaises(ValueError):self.new.capacity(3071,24,geometry=geometry())
        g=geometry();actual=g.check(3070);actual['scratch_kernel_pages']=24
        with patch.object(G.NativeGeometry,'check',lambda *a:actual):
            with self.assertRaisesRegex(ValueError,'PRIVATE'):self.new.capacity(3070,24,geometry=g)
    def test_actual_snap_function_calls_live_capacity_before_gather(self):
        fn=next(x for x in ast.parse(self.bundle['files']['service_runner.py']).body
                if isinstance(x,ast.FunctionDef)and x.name=='_snap')
        ns=dict(G2=self.new,E=types.SimpleNamespace(need=R.need))
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-derived-snapshot','exec'),ns)
        g=geometry();b=dict(kind='fa',index=3,table=g.facts['table'],key=g.key,value=g.value,native_geometry=g)
        bridge=types.SimpleNamespace(bindings=[b],_validate_bindings=lambda owner:None,
            _bole_live=types.SimpleNamespace(fa_proof=lambda b:dict(synthetic=True)))
        torch=types.SimpleNamespace(tensor=lambda pages,**kw:tuple(pages),long='synthetic-long')
        gd,fa=ns['_snap'](torch,bridge,types.SimpleNamespace(length=3070))
        self.assertEqual(gd,[]);self.assertEqual(fa[0]['physical_pages'],g.facts['table'])
        b.pop('native_geometry')
        with self.assertRaises(ValueError):ns['_snap'](torch,bridge,types.SimpleNamespace(length=3070))
    def test_whole_inverse_and_only_two_source_files(self):
        self.assertEqual(R.inverse(self.bundle),self.parent)
        self.assertEqual(set(self.bundle['inverse_delta']),{'g2_contract.py','service_runner.py'})
        self.assertFalse(self.bundle['whole_source_ready']);self.assertFalse(self.bundle['NPU'])
        bad=copy.deepcopy(self.bundle);bad['files']['g2_contract.py']+=b'\n'
        with self.assertRaises(ValueError):R.inverse(bad)

    def test_explicit_native2048_scope_keeps_original_other_fields_and_caps(self):
        self.assertEqual(self.old.scope()['prefix'],131)
        expected=dict(self.old.scope(),prefix=2048)
        self.assertEqual(self.new.scope(),expected);self.assertEqual(self.new.SCOPE,expected)
        for name in('MAX_OUTPUT','RAW_CAP','METADATA_CAP','FRAME_LOGICAL_CAP','CHECKPOINT_CAP','FRAME_WIRE_CAP'):
            self.assertEqual(getattr(self.new,name),getattr(self.old,name))
        with self.assertRaises(ValueError):self.new.scope('smoke4')
        # Real source validator/math remain unmodified and deliberately pending.
        base=R.PARENT
        tree=ast.parse((base/'g3_validate.py').read_bytes())
        fixed=next(x.value for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(y,ast.Name)and y.id=='SCOPE'for y in x.targets))
        old_scope={x.arg:ast.literal_eval(x.value)for x in fixed.keywords}
        self.assertNotEqual(old_scope,self.new.SCOPE);self.assertEqual(old_scope['prefix'],131)
    def test_actual_channel_scope_join_rejects_legacy_or_mixed_metadata(self):
        base=R.PARENT;tree=ast.parse((base/'g2_channel.py').read_bytes())
        function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='contract')
        class ReachedHostVerifier(Exception):pass
        def stop(*a):raise ReachedHostVerifier()
        handoff=types.ModuleType('g2_handoff');handoff.verify=stop
        sr={'path':'source'};cr={'path':'channel'}
        manifest={'stream_consumer_source':{'path':'consumer'}}
        channel=dict(schema='bole.owned-independent-stream-channel/v2',source=sr,scope=self.new.SCOPE,
            consumer_source=manifest['stream_consumer_source'],consumer_Devices=[],
            consumer_container_independent=True,host_ownership_audited=True,
            actual_worker_identities=[{'pid':i+1}for i in range(4)],
            consumer_owner_ref={'path':'cpu-owner'},model_owner_ref={'path':'model-owner'})
        checks=[]
        C=types.SimpleNamespace(obj=lambda ref:manifest if ref==sr else channel,checked=lambda ref:checks.append(ref))
        ns=dict(G2=self.new,need=R.need,Path=Path)
        exec(compile(ast.Module(body=[function],type_ignores=[]),'actual-channel-contract','exec'),ns)
        with patch.dict(sys.modules,{'g2_handoff':handoff}):
            # Success stops BEFORE real ownership proof; this grants no channel.
            with self.assertRaises(ReachedHostVerifier):ns['contract'](C,sr,cr)
            self.assertEqual(len(checks),3)
            for wrong in(self.old.SCOPE,dict(self.new.SCOPE,prefix=True),dict(self.new.SCOPE,max_output_tokens=160)):
                checks.clear();channel['scope']=wrong
                with self.assertRaises(ValueError):ns['contract'](C,sr,cr)
                self.assertFalse(checks)
        consumer=ast.parse((base/'g2_consumer.py').read_bytes())
        main=next(x for x in consumer.body if isinstance(x,ast.FunctionDef)and x.name=='main')
        gate=next(x for x in main.body if isinstance(x,ast.Expr)and isinstance(x.value,ast.Call)and
            isinstance(x.value.func,ast.Attribute)and x.value.func.attr=='need')
        path='source-owned-consumer'
        m=dict(service_experiment=self.new.SCOPE,stream_consumer_source=path,files={'g2_consumer.py':path})
        ns=dict(C=types.SimpleNamespace(need=R.need,ref=lambda p:p),G2=self.new,m=m,os=os,__file__=path)
        with patch.dict(os.environ,{self.new.FLAG:'1'}):
            exec(compile(ast.Module(body=[gate],type_ignores=[]),'actual-consumer-scope-prefix','exec'),ns)
            m['service_experiment']=self.old.SCOPE
            with self.assertRaises(ValueError):
                exec(compile(ast.Module(body=[gate],type_ignores=[]),'actual-consumer-mixed-scope','exec'),ns)
    def test_scope_label_cannot_pass_original131_numeric_registration(self):
        tree=ast.parse((R.PARENT/'g2_state.py').read_bytes())
        fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='open_rank')
        ns=dict(C=types.SimpleNamespace(need=R.need),
            N=types.SimpleNamespace(equal=lambda *a:None,mtp_join=lambda *a:None),
            G1=types.SimpleNamespace(REQUEST_SCHEMA='original-request'))
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-original-numeric-open','exec'),ns)
        raw=dict(schema='original-request',request=dict(generation=1,slot=0,length=2048,version=0))
        with self.assertRaisesRegex(ValueError,'registration'):ns['open_rank'](None,{},raw)

if __name__=='__main__':
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: source-only --check')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if not result.wasSuccessful():raise SystemExit(1)
