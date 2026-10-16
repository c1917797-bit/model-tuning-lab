import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import common112 as C,core112 as K,recipe112 as R,oracle112 as O


class Tests(unittest.TestCase):
    def test_cold_off(self):
        for name in('guest112.py','cpu112.py','consume112.py','owner112.py','owned_cpu112.py','bind112.py','run112.py'):
            r=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['enabled'])

    def test_meta_all_real_shapes(self):
        import torch as t,cpu112
        v=cpu112.meta(t);self.assertEqual(len(v['rows']),24)
        self.assertLess(R.logical_raw_upper('full'),768*2**20)

    def test_reference110_and_actual_gqa(self):
        import torch as t
        t.set_num_threads(1)
        s=importlib.util.spec_from_file_location('independent110',P/'independent110.py');ref=importlib.util.module_from_spec(s);s.loader.exec_module(ref)
        for kind in('chain','branch','forest'):
            p,initial,steps=R.recipe(t,1,kind,3,9);mask,inc=R.masks(t,p);e=steps[0]
            q=e['q'].float().repeat_interleave(3,dim=1);k=e['k'].float().repeat_interleave(3,dim=1)
            out,factors=K.verify(t,q,k,e['v'].float(),e['beta'],e['gamma'],initial,mask,3)
            expected,states=O.sequential(t,q.double(),k.double(),e['v'].double(),e['beta'].double(),e['gamma'].double(),initial.double(),p)
            self.assertLess(float((out.double()-expected).abs().max()),2e-6)
            actual=K.commit(t,initial,k,factors,inc,e['terminal'])
            self.assertLess(float((actual.double()-states[e['terminal']]).abs().max()),2e-6)
            # Independent110 small per-head slice runs identical dimensions.
            ro,rs=ref.sequential(p,q[0,0].double().tolist(),k[0,0].double().tolist(),e['v'][0,0].double().tolist(),e['beta'][0,0].double().tolist(),e['gamma'][0,0].double().tolist(),initial[0,0].double().tolist())
            self.assertLess(float((t.tensor(ro,dtype=t.double)-expected[0,0]).abs().max()),1e-12)

    def test_wrong_sibling_and_grouping_rejected(self):
        import torch as t
        from consume112 import metric
        p,s,steps=R.recipe(t,1,'branch',3,2);e=steps[0];mask,inc=R.masks(t,p)
        q=e['q'].float().repeat_interleave(3,1);k=e['k'].float().repeat_interleave(3,1)
        expected,_=O.sequential(t,q.double(),k.double(),e['v'].double(),e['beta'].double(),e['gamma'].double(),s.double(),p)
        wrongmask=t.tril(t.ones_like(mask),diagonal=-1)
        wrong,_=K.verify(t,q,k,e['v'].float(),e['beta'],e['gamma'],s,wrongmask,6)
        self.assertFalse(metric(t,wrong,expected)['passed'])
        wrong,_=K.verify(t,q.roll(3,1),k,e['v'].float(),e['beta'],e['gamma'],s,mask,3)
        self.assertFalse(metric(t,wrong,expected)['passed'])

    def test_commit_noaccept_and_every_terminal(self):
        import torch as t
        p,s,steps=R.recipe(t,1,'forest',1,5);e=steps[0];mask,inc=R.masks(t,p);q=e['q'].float().repeat_interleave(3,1);k=e['k'].float().repeat_interleave(3,1)
        _,f=K.verify(t,q,k,e['v'].float(),e['beta'],e['gamma'],s,mask,1)
        _,states=O.sequential(t,q.double(),k.double(),e['v'].double(),e['beta'].double(),e['gamma'].double(),s.double(),p)
        for a in range(len(p)):self.assertLess(float((K.commit(t,s,k,f,inc,a).double()-states[a]).abs().max()),2e-6)
        self.assertTrue(t.equal(K.commit(t,s,k,f,inc,None).view(t.int32),s.view(t.int32)))

    def test_actual_host_receive_and_ARM_contract(self):
        import owner112 as H
        # Actual receiver/handshake function, no replacement of ownership logic.
        old=H.obj;H.obj=lambda r:dict(profile='smoke')
        with tempfile.TemporaryDirectory()as tmp:
            f=Path(tmp)/'actualraw';f.write_bytes(b'raw');rr=H.ref(f);sr=dict(software=True);ar=dict(authority=True);pr=dict(plan=True)
            v=dict(schema='bole.tree-stage/v112',source=sr,authority=ar,plan=pr,primary=None,NPU=True,qualified=False,result=dict(cases=2,anchors=[rr]*2,rows=[dict(raw=rr)]*6))
            self.assertIs(H.receive(v,sr,ar,pr),v)
            v['result']['rows'].pop()
            with self.assertRaises(ValueError):H.receive(v,sr,ar,pr)
        H.obj=old
        # Linux stat field22 starttime, complete argv and namespacePID match.
        dv=dict(logical=0,physical_declared_by_plan=4,plan=pr,canary=[4.,5.],physical_proof_must_be_host_owned=True,cgroup='cid',pid=7,stat='7 (python) '+ ' '.join(['R']+['0']*18+['123']+['0']*5))
        proof=dict(physical=4,namespace_pids=[99,7],start_ticks=123,cgroup='cid',argv=['exact'])
        self.assertEqual(H.device_proof(dv,dict(owned_process_proofs=[proof]),pr,'cid',['exact']),proof)
        proof['physical']=5
        with self.assertRaises(ValueError):H.device_proof(dv,dict(owned_process_proofs=[proof]),pr,'cid',['exact'])

    def test_actual_CPU_create_inspect_private_no_device(self):
        import owned_cpu112 as H,copy
        mounts={'/exact/source':('/exact/source',False),'/new/owned':('/adakv-results',True)};env={'ASCEND_RT_VISIBLE_DEVICES':'','TORCH_DEVICE_BACKEND_AUTOLOAD':'0'};child=['-I','-B','/exact/source/cpu112.py']
        argv=H.create_argv(2,mounts,env,'name',child)
        self.assertNotIn('--device',argv);self.assertIn('--read-only',argv)
        x=dict(Id='cid',Image=H.IMAGE,Name='/name',ExecIDs=None,HostConfig=dict(Privileged=False,ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*H.GIB,MemorySwap=8*H.GIB,NanoCpus=10**9,CpusetCpus='2',PidsLimit=256,IpcMode='private',NetworkMode='none',LogConfig=dict(Type='none'),Devices=[],DeviceRequests=[],DeviceCgroupRules=[],PortBindings={}),Config=dict(Labels={'qwen36.owner':H.OWNER},Env=[k+'='+v for k,v in env.items()],Entrypoint=['/bin/bash'],Cmd=['-c',H.CANN_WRAPPER,'boletree112',H.PY,*child]),Mounts=[dict(Source=k,Destination=v[0],RW=v[1])for k,v in mounts.items()],State=dict(OOMKilled=False))
        H.inspect_owned(x,'cid',mounts,env,2,'name',child)
        for key,value in(('Devices',[dict(PathOnHost='/dev/davinci4')]),('Memory',9*H.GIB),('ReadonlyRootfs',False)):
            bad=copy.deepcopy(x);bad['HostConfig'][key]=value
            with self.assertRaises(ValueError):H.inspect_owned(bad,'cid',mounts,env,2,'name',child)

    def test_real_produce_to_consume_software_layout(self):
        import torch as t,guest112,consume112,time
        t.set_num_threads(1)
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);out=root/'actualraw';out.mkdir();sr={'software_only':True}
            m=dict(profile='smoke',_actual_source=sr,software_control_only=True)
            result=guest112.execute(t,m,out,time.time()+120,device='cpu')
            stage=dict(schema='bole.tree-stage/v112',source=sr,primary=None,NPU=True,result=result)
            # In-memory NPU marker is ABI fixture only, not a saved NPU receipt.
            report=consume112.consume(t,m,stage,root)
            self.assertTrue(report['pass_gate']);self.assertEqual(len(report['rows']),6)
            rawref=result['rows'][0]['raw'];raw=t.load(C.checked(rawref),weights_only=True);raw['after'][0,0,0,0]+=1
            bad=root/'wrongslot.pt';t.save(raw,bad);result['rows'][0]['raw']=C.ref(bad)
            wrong=consume112.consume(t,m,stage,root)
            self.assertFalse(wrong['pass_gate'])

    def test_actual_main_source_header_schema_and_closure_boundary(self):
        import owner112 as H,owned_cpu112 as U
        template=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
        self.assertEqual(template['schema'],'bole.tree-gdn-source/v112')
        # Execute actual main() with real source files until the explicit donor
        # closure boundary; no Docker/CPU/resource functions may run here.
        class Boundary(Exception):pass
        for module in(H,U):
            with tempfile.TemporaryDirectory()as tmp:
                m=dict(template,prepared_only=False,root=str(P),profile='smoke',output_root=str(module.OUTROOT)+'/smoke')
                m['files']={n:C.ref(P/n)for n in template['files']}
                source=Path(tmp)/'BOUND.json';C.write(source,m);sr=C.ref(source)
                oldargv=sys.argv;oldclosure=module.closure;oldout=module.OUTROOT
                module.closure=lambda *a:(_ for _ in()).throw(Boundary())
                # CPU checks donor before its closure; this exact donor remains
                # external, and software fixture explicitly maps only that Ref.
                oldchecked=module.checked
                if module is U:
                    module.checked=lambda rr:source if rr==m['donor']else oldchecked(rr)
                try:
                    sys.argv=[str(P/('owner112.py'if module is H else'owned_cpu112.py')),'--source-audit','--source-ref',json.dumps(sr)]
                    with self.assertRaises(Boundary):module.main()
                    module.OUTROOT=oldout;m['schema']='wrong-source';source.unlink();C.write(source,m);sys.argv[-1]=json.dumps(C.ref(source))
                    with self.assertRaises(ValueError):module.main()
                finally:module.OUTROOT=oldout;module.closure=oldclosure;module.checked=oldchecked;sys.argv=oldargv

    def test_typed_caller_actual_argv(self):
        import run112 as R112,types
        # Real typed command function; all future values must be explicit.
        a=types.SimpleNamespace(stage='bind',reviewed_template_ref='actual-reviewed-Ref-required',profile='full',smoke_consumer_owner_ref=None)
        self.assertEqual(R112.command(a)[:4],['/usr/bin/python3','-I','-B',str(P/'bind112.py')])
        a=types.SimpleNamespace(stage='numeric',source_ref=None)
        with self.assertRaises(ValueError):R112.command(a)

if __name__=='__main__':unittest.main()
