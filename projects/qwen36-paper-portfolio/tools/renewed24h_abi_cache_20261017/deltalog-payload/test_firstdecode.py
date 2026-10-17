"""Explicit software rules/real CPU oracle checks, never hardware evidence."""
import copy,hashlib,importlib.util,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import firstdecode as D,firstdecode_gate as Q,firstdecode_consume as C

ORIGINAL=P/'software_fixtures'
def load(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def software_metadata():
    """All64 pure integer fixture; not a live tensor or executable grant."""
    pools=[];ss=[];nextptr=1000000
    def add(prefix,gid,kind,role,shape,dtype,rows,physical=(),writes=()):
        nonlocal nextptr
        e={'bf16':2,'f32':4,'i32':4}[dtype];st=[];n=1
        for x in reversed(shape):st.insert(0,n);n*=x
        index=len(pools);pools.append(dict(index=index,pointer=nextptr,nbytes=n*e))
        ss.append(dict(prefix=prefix,group=gid,kind=kind,role=role,pool=index,geometry=dict(pointer=nextptr,storage_offset=0,element_bytes=e,dtype=dtype,shape=list(shape),strides=st,format_code=2),cpu_rows=list(rows),gpu_rows=list(rows),physical_rows=list(physical),physical_block_tokens=128 if kind=='FA' else 0,kernel_block_tokens=128 if kind=='FA' else 0,writes=[list(x)for x in writes]))
        nextptr+=n*e+4096
    for i in range(48):
        for role,shape,dtype in(('conv',(2,2560,3),'bf16'),('base',(2,12,128,128),'f32'),('K',(2,4,7,128),'bf16'),('U',(2,12,7,128),'f32'),('lambda_log',(2,12,16),'f32'),('decay',(2,12,16),'f32'),('length',(2,12,16),'i32')):add('gdn'+str(i),1+i%3,'GDN',role,shape,dtype,[1])
    for i in range(16):
        for role in('K','V'):add('fa'+str(i),0,'FA',role,(18,128,1,256),'bf16',range(17),range(17),[(16,0,512)])
    return dict(pools=pools,selections=ss)

def zero_raw(t):
    before=dict(base=t.zeros((1,12,128,128)),k_log=t.zeros((1,4,7,128),dtype=t.bfloat16),u_log=t.zeros((1,12,7,128)),lambda_log=t.zeros((1,12,16)),decay=t.zeros((1,12,16)),length=t.zeros((1,12,16),dtype=t.int32))
    after={n:v.clone()for n,v in before.items()};after['length'][:,:,0]=1
    inputs=dict(query=t.zeros((1,4,128),dtype=t.bfloat16),key=t.zeros((1,4,128),dtype=t.bfloat16),value=t.zeros((1,12,128),dtype=t.bfloat16),g=t.zeros((1,12)),beta=t.zeros((1,12),dtype=t.bfloat16))
    seq=t.tensor([0,1],dtype=t.int32);ids=t.tensor([3],dtype=t.int32)
    b=[inputs[n]for n in('query','key','value','g','beta')]+list(before.values())+[seq,ids]
    a=[v.clone()for v in b[:5]]+list(after.values())+[seq.clone(),ids.clone()]
    db=[v.clone()for v in b];da=[v.clone()for v in a];db[12].zero_();da[12].zero_()
    out=t.zeros((1,12,128),dtype=t.bfloat16);ptr={n:v.data_ptr()for n,v in inputs.items()}
    side=dict(before=b,after=a,debug_before=db,debug_after=da,actual_production_slot=3,compact_debug_id=0,production_output=out,debug_output=out.clone(),actual_precast_FP32=t.zeros((1,12,128)),pointers_before=[{'p':i}for i in range(13)],pointers_after=[{'p':i}for i in range(13)],debug_pointers_before=[{'p':i+13}for i in range(13)],debug_pointers_after=[{'p':i+13}for i in range(13)],sidecar_guards_before=t.full((256,),13.),sidecar_guards_after=t.full((256,),13.),production_debug_bitwise=True,inputs_unchanged=True,sidecar_redzones_pass=True)
    raw=dict(actual_NPU=True,actual_ids=[3],scale=128**-.5,inputs=inputs,input_after={n:v.clone()for n,v in inputs.items()},before=before,after=after,output=out,native_before=before['base'].clone(),native_after=before['base'].clone(),native_output=out.clone(),pointer_before=ptr,pointer_after=ptr.copy(),compact_sidecar=side)
    return raw

class Controls(unittest.TestCase):
    def test_OFF_and_cli_actual_I_no_backend_import(self):
        for leaf in('firstdecode_cli.py',):
            for flags in([],['--help']):
                z=subprocess.run([sys.executable,'-I','-B',str(P/leaf),*flags],capture_output=True,text=True);self.assertEqual(z.returncode,0,z.stderr)
        code="import importlib.util,sys; s=importlib.util.spec_from_file_location('_actual_OFF',"+repr(str(P/'firstdecode_plugin.py'))+"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.register(); assert 'torch' not in sys.modules and 'torch_npu' not in sys.modules and 'firstdecode_gate' not in sys.modules"
        env=dict(os.environ);env.pop(D.ENABLE,None)
        z=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True);self.assertEqual(z.returncode,0,z.stderr)
        old=os.environ.pop(D.ENABLE,None)
        try:self.assertEqual(D.install(),dict(installed=False,default_OFF=True))
        finally:
            if old is not None:os.environ[D.ENABLE]=old
    def test_public_optin_still_rejects_without_actual_entry(self):
        old=os.environ.get(D.ENABLE);os.environ[D.ENABLE]='1'
        try:
            with self.assertRaisesRegex(Exception,'public installation blocked'):D.install()
        finally:
            if old is None:os.environ.pop(D.ENABLE)
            else:os.environ[D.ENABLE]=old
    def test_actual_loaded_fixture_exact_bytes_host_not_namespace(self):
        p=P/'software_fixtures/ALL4-LOADED.json';raw=p.read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(9209,'fb3c150d79fd47879c839bda2f63f0054dc95f1126db6ba7f604405a37699fdf'))
        import selected_core as F
        loaded=json.loads(raw);row=loaded['rows'][0];h=row['actual_host_process'];cid=h['cgroup'].split('/docker/')[1].split()[0]
        # The stat input here is an explicit software fixture; actual runtime
        # takes it only from current /proc/self/stat, never this JSON.
        fields=['R']+['0']*18+[str(h['start_ticks'])]
        d,r=D.domain_from_actual_loaded(F,loaded,loaded['source'],cid,0,row['namespace_pid'],'438 (worker) '+' '.join(fields),h['cgroup'])
        self.assertEqual(d.host_pid,3039148);self.assertNotEqual(d.host_pid,438)
        wrong=copy.deepcopy(loaded);wrong['rows'][0]['actual_host_process']['namespace_pids'][-1]=439
        with self.assertRaises(RuntimeError):D.domain_from_actual_loaded(F,wrong,loaded['source'],cid,0,438,'438 (worker) '+' '.join(fields),h['cgroup'])
    def test_all64_union_recomputes_FA_exact_position_and_wholeblock_reads(self):
        x=software_metadata();u=C.metadata_union(x);self.assertEqual(len(u),len(x['pools']))
        for s in x['selections']:
            if s['kind']=='FA':self.assertEqual(u[s['pool']],((16*65536,16*65536+512),))
    def test_unknown_missing_or_wide_FA_write_rejected(self):
        for mutate in(lambda x:x['selections'].pop(),lambda x:x['selections'][-1].update(writes=[[16,0,65536]]),lambda x:x['selections'][-1]['gpu_rows'].__setitem__(0,17),lambda x:x['selections'][0]['geometry'].update(format_code=29)):
            x=software_metadata();mutate(x)
            with self.assertRaises(ValueError):C.metadata_union(x)
    def test_actual_selected_crosslayer_collision_rejected(self):
        x=software_metadata();a=x['selections'][0];b=x['selections'][7];b['pool']=a['pool'];b['geometry']=copy.deepcopy(a['geometry'])
        with self.assertRaisesRegex(ValueError,'simultaneously active'):C.metadata_union(x)
    def test_original_decode_math_positive_and_negative_software_only(self):
        import torch
        sys.path.insert(0,str(ORIGINAL));T=load(ORIGINAL/'tensor_consumer.py','_firstdecode_original_test');R=T.module();decode=C.unchanged_decode(T)
        raw=zero_raw(torch);state,metrics=decode(torch,R,raw,torch.zeros((12,128,128),dtype=torch.float64),3)
        self.assertTrue(metrics['passed']);self.assertTrue(metrics['actual_precast']['passed']);self.assertEqual(metrics['state_error'],0)
        for mutate in(lambda x:x.update(scale=1.),lambda x:x.update(actual_ids=[4]),lambda x:x['after']['base'].__setitem__((0,0,0,0),float('nan')),lambda x:x['compact_sidecar']['actual_precast_FP32'].fill_(1),lambda x:x['compact_sidecar']['debug_output'].fill_(1)):
            wrong=copy.deepcopy(raw);mutate(wrong)
            try:_,r=decode(torch,R,wrong,torch.zeros((12,128,128),dtype=torch.float64),3)
            except (ValueError,RuntimeError):continue
            self.assertFalse(r['passed'])
    def test_budget_not_old4_or_wrong_alias_or_future_source(self):
        b=dict(schema='deltalog.first-decode-owned-budget/v1',source={},payload_source={},cid='a'*64,workspace_cap_bytes=32*Q.GIB,per_worker_cap_bytes=8*Q.GIB,allocated_worker_cap_bytes=15*Q.GIB//2,opt_total_cap_bytes=2*Q.GIB,payload_total_cap_bytes=30*Q.GIB,total_cap_bytes=80*Q.GIB,disk_reserve_bytes=int(8.5*Q.GIB),ledger_advanced=False,guest_stage_root='/adakv-results',guest_payload_root='/adakv-results/model/capture',host_stage_root='/control/candidate',host_payload_root='/payload/new',storage_proof={'actual':'software-only'})
        Q.validate_budget(b,{},{},'a'*64)
        for k,v in(('workspace_cap_bytes',4*Q.GIB),('allocated_worker_cap_bytes',8*Q.GIB),('opt_total_cap_bytes',4*Q.GIB),('payload_total_cap_bytes',32*Q.GIB),('ledger_advanced',True),('payload_source',{'future':True}),('guest_payload_root','/model'),('storage_proof',{})):
            x=copy.deepcopy(b);x[k]=v
            with self.assertRaises(ValueError):Q.validate_budget(x,{},{},'a'*64)
        # Actual CPU serialization/write functions, but no native tensor or
        # permission is synthesized. Rejected writes leave the leaf empty.
        import torch
        from types import SimpleNamespace as NS
        from firstdecode_capture import Collector,RAW_CAP,CONTROL_RESERVE
        self.assertEqual(4*b['allocated_worker_cap_bytes']+b['opt_total_cap_bytes'],32*Q.GIB)
        with tempfile.TemporaryDirectory() as td:
            c=Collector(NS(reader=NS(torch=torch)),None,None,{}, {},{}, {},None)
            c.root=Path(td);c.worker_cap=b['allocated_worker_cap_bytes']
            c.control_used=CONTROL_RESERVE
            with self.assertRaises(RuntimeError):c.write('control.json',{'x':1})
            c.control_used=0;c.raw_used=RAW_CAP
            with self.assertRaises(RuntimeError):c.save('raw.pt',torch.zeros(1))
            c.raw_used=0;c.store=NS(used=c.worker_cap)
            with self.assertRaises(RuntimeError):c.save('raw.pt',torch.zeros(1))
            with self.assertRaises(RuntimeError):c.write('control.json',{'x':1})
            self.assertEqual(list(c.root.iterdir()),[])

if __name__=='__main__':unittest.main(verbosity=2)
