"""Actual cold/layout/dispatcher interfaces; software receipts never authorize NPU."""
import copy,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import common116 as C

def load(name):
    spec=importlib.util.spec_from_file_location('_test116_'+name,P/(name+'.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

def fixture(root):
    m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());m.update(root=str(P),prepared_only=False,prepared_template=C.ref(P/'SOURCE_TEMPLATE.json'))
    m['files']={n:C.ref(P/n)for n in m['files']};m['authority_ref']=C.ref(P/'common116.py');m['cann_helper_ref']=C.ref(P/'abi116.py');m['donor_host']=C.ref(P/'owner116.py');m['dependencies']={'pipeline':C.ref(P/'common116.py'),'cpu':C.ref(P/'abi116.py')};donor=root/'donor.json';C.write(donor,{'files':{'host.py':m['donor_host'],'scope_adapter.py':C.ref(P/'scope_adapter112.py'),'patch_scope.py':C.ref(P/'patch_scope112.py'),'terminal_fence.py':C.ref(P/'common116.py')}});m['donor_source']=C.ref(donor);p=root/'BOUND.json';C.write(p,m);return C.ref(p),m

class Tests(unittest.TestCase):
    def test_real_dispatcher_reflection(self):
        import torch as t,abi116 as A
        (name,schema),family=A.select(t.ops.aten.mm,('self','mat2'),'aten::mm')
        self.assertEqual(name,'');self.assertFalse(schema.is_mutable);self.assertEqual(family[name],str(schema))
        with self.assertRaises(ValueError):A.select(t.ops.aten.mm,('not_an_argument',),'aten::mm')

    def test_actual_cold_OFF(self):
        for name in('owner116','owned_cpu116','guest116','cpu116','consume116','ticket116','bind116','run116'):
            r=subprocess.run([sys.executable,'-I','-B',str(P/(name+'.py'))],capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,0,(name,r.stderr));self.assertFalse(json.loads(r.stdout)['NPU'])

    def test_actual_template_mount_and_source_read(self):
        H=load('owned_cpu116')
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);sr,m=fixture(root)
            self.assertEqual(C.source(sr)['root'],str(P));self.assertIn(m['prepared_template'],H.guest_closure(m));self.assertNotIn('SOURCE_TEMPLATE.json',m['files'])
            for bad in(dict(m['prepared_template'],sha256='0'*64),dict(m['prepared_template'],path=str(root/'absent.json'))):
                v=copy.deepcopy(m);v['prepared_template']=bad
                with self.assertRaises((ValueError,FileNotFoundError)):H.guest_closure(v)
                p=root/('bad'+str(len(list(root.iterdir())))+'.json');C.write(p,v)
                with self.assertRaises((ValueError,FileNotFoundError)):C.source(C.ref(p))

    def test_actual_host_receive_outer_inner(self):
        H=load('owner116')
        S=load('scope_adapter112');self.assertEqual(S.scoped_cards('numeric',True,4),(4,))
        for bad in(0,1,2,3,5,6,7):
            with self.assertRaises(ValueError):S.scoped_cards('numeric',True,bad)
        self.assertIn("adapter=load(own['files']['scope_adapter112.py']",(P/'owner116.py').read_text())
        # Derivation must never mutate byte counts or hashes containing node IDs.
        tree=__import__('ast').parse((P/'guest116.py').read_bytes())
        calls=[n for n in __import__('ast').walk(tree)if isinstance(n,__import__('ast').Call)and isinstance(n.func,__import__('ast').Attribute)and n.func.attr=='file_identity']
        self.assertEqual(calls[0].args[1].value,5112)
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p=root/'raw';p.write_bytes(b'software-only');inner=root/'inner.json';C.write(inner,dict(schema='bole.FIA-stage/v115',source={'software':True},rows=[dict(raw=C.ref(p))for _ in range(6)]))
            outer=dict(schema='bole.tree-stage/v116',source={'software':True},authority=1,plan=2,primary=None,NPU=True,qualified=False,result=C.ref(inner))
            self.assertIs(H.receive(outer,{'software':True},1,2),outer)
            with self.assertRaises(ValueError):H.receive(dict(outer,primary='failed'),{'software':True},1,2)
            with self.assertRaises(ValueError):H.receive(dict(outer,source={'wrong':True}),{'software':True},1,2)

    def test_ticket_exact_future_and_source_rejection(self):
        import ticket116 as T
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);sr,m=fixture(root)
            abi=dict(schema='bole.actual-FIA-installed-ABI/v115',source=sr,NPU=False,Devices=[],no_device_fds=True,operator_executed=False,operator='npu::npu_fused_infer_attention_score',argument_names=list(T.REQUIRED),header_ref=m['header_ref'],overload='',schema_family={'':'software layout only'},actual_schema='software layout only')
            C.write(root/'ABI.json',abi);stage=dict(schema='bole.tree-CPU-stage/v116',source=sr,NPU=False,primary=None,actual_meta={'pass_gate':True},actual_abi_ref=C.ref(root/'ABI.json'));C.write(root/'STAGE.json',stage)
            owner=dict(schema='bole.tree-owned-CPU/v116',source=sr,primary=None,secondary=[],resource_release_verified=True,stage_ref=None,Devices=[],NPU=False,stage_result=C.ref(root/'STAGE.json'));C.write(root/'OWNER.json',owner);cr=C.ref(root/'OWNER.json')
            ticket=T.from_cpu(sr,cr);C.write(root/'TICKET.json',ticket);self.assertEqual(T.consume(C.ref(root/'TICKET.json'),sr,cr),ticket)
            owner['primary']='failed';C.write(root/'FAILED.json',owner)
            with self.assertRaises(ValueError):T.from_cpu(sr,C.ref(root/'FAILED.json'))
            ticket['source']={'future':True};C.write(root/'BADTICKET.json',ticket)
            with self.assertRaises(ValueError):T.consume(C.ref(root/'BADTICKET.json'),sr,cr)

    def test_real_six_raw_consumer_both_independent_references(self):
        import torch as t,tree_fa115 as F,consume116 as V
        t.set_num_threads(1)
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);sr={'software_fixture_not_authority':True};rows=[]
            for case,(b,p,w)in enumerate(((1,[0],True),(1,[7],False),(16,[i%9 for i in range(16)],False))):
                raw=F.recipe(t,b,p,w)
                for mode in(1,0):
                    path=root/('%s-%s.pt'%(case,mode));t.save(dict(source=sr,case=case,mode=mode,inputs=raw,output=F.path_reference(t,raw).bfloat16(),primary=None),path);rows.append(dict(raw=C.ref(path)))
            C.write(root/'INNER.json',dict(schema='bole.FIA-stage/v115',source=sr,rows=rows));outer=dict(schema='bole.tree-stage/v116',source=sr,primary=None,NPU=True,result=C.ref(root/'INNER.json'),actual_abi_ref=None,abi_ticket_ref=None)
            value=V.consume(t,sr,outer);self.assertTrue(value['pass_gate']);self.assertTrue(all(r['independent_FP32']['preregistered_allclose']for r in value['rows']))
            path=Path(rows[0]['raw']['path']);bad=t.load(path,weights_only=True);bad['output'].fill_(42);t.save(bad,path);rows[0]['raw']=C.ref(path);C.write(root/'BADINNER.json',dict(schema='bole.FIA-stage/v115',source=sr,rows=rows));outer['result']=C.ref(root/'BADINNER.json');self.assertNotIn(1,V.consume(t,sr,outer)['observed_mask_modes_supported_on_exact_test_matrix'])

    def test_actual_cpu_frontdoor_trace_before_backend(self):
        # Run the real CPU main with only source/window/suite plumbing redirected.
        # The actual bootstrap is NOT replaced: a source-bound ordinary helper
        # whose ROOT is invalid must fail and preserve its complete traceback.
        E=load('cpu116')
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);helper=root/'helper.py';helper.write_bytes(b"ROOT='not-installed-CANN'\n")
            suite=root/'suite.py';suite.write_bytes(b'raise SystemExit(0)\n')
            m={'authority_ref':{'software':True},'files':{'suite116.py':C.ref(suite)},'cann_helper_ref':C.ref(helper)}
            oldsource,oldwindow=E.C.source,E.C.window;oldargv=sys.argv;env={k:os.environ.get(k)for k in('ASCEND_RT_VISIBLE_DEVICES','TORCH_DEVICE_BACKEND_AUTOLOAD')}
            try:
                E.C.source=lambda sr:m;E.C.window=lambda m:None;os.environ.update(ASCEND_RT_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0');sys.argv=[str(P/'cpu116.py'),'--execute','--source-ref','{}','--output',str(root/'out')]
                self.assertEqual(E.main(),3);v=json.loads((root/'out/FAILURE.json').read_bytes());self.assertIn('actual CANN source path',v['traceback']);self.assertFalse(json.loads((root/'out/STAGE_RESULT.json').read_bytes())['actual_meta']['pass_gate'])
            finally:
                E.C.source, E.C.window=oldsource,oldwindow;sys.argv=oldargv
                for k,v in env.items():
                    if v is None:os.environ.pop(k,None)
                    else:os.environ[k]=v

if __name__=='__main__':unittest.main()
