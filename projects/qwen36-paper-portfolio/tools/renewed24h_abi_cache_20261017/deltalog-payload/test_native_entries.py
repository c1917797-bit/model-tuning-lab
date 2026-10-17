"""Real local Torch wrapper controls; actual-image source evidence kept separate."""
import ast,copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import native_entries as N,live_adapter as A,firstdecode_cli as C,firstdecode_gate as Q

class Controls(unittest.TestCase):
    def test_real_Torch_single_wrapper_and_wrong_mode_body_extra_wrapper(self):
        import torch,torch.utils._contextlib as ctx,torch.autograd.grad_mode as grad
        pins={n:dict(path=m.__file__,bytes=Path(m.__file__).stat().st_size,sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest())for n,m in(('contextlib',ctx),('grad_mode',grad))}
        if sys.platform=='linux':
            m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes())
            self.assertEqual(pins,m['native_torch_sources'],'actual same-image software validates the installed pair, not Windows Torch')
        def inner():return None
        good=torch.inference_mode()(inner)
        self.assertIs(N.inference_wrapper(torch,good,inner,pins),good)
        for fn,body in((torch.inference_mode(False)(inner),inner),(good,lambda:None),(torch.inference_mode()(good),inner)):
            with self.assertRaises(ValueError):N.inference_wrapper(torch,fn,body,pins)
    def test_actual660_source_evidence_all_bytes_and_declared_pins(self):
        x=json.loads((P/'NATIVE_TORCH_SOURCES.json').read_bytes())
        expected={'_contextlib.py':(6402,'f22c21a037c4b26a431112138fa66a5108c5e9cfe4c9169e732c1d15ea7a8406'),'grad_mode.py':(14193,'ac56e9849d2e8b996e9e8fb923e28d35f564b44063eaa5e88c46d47555209804')}
        self.assertTrue(x['stopped_before_after']);self.assertEqual(len(x['files']),2)
        for f in x['files']:
            b=f['text'].encode();r=f['ref'];self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),expected[Path(r['path']).name]);self.assertEqual((r['bytes'],r['sha256']),expected[Path(r['path']).name]);ast.parse(b)
        m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes())
        self.assertEqual(m['native_torch_sources'],dict(zip(('contextlib','grad_mode'),[f['ref']for f in x['files']])))
        self.assertIn('native_entries.py',m['files']);self.assertIn('test_native_entries.py',m['files'])
    def test_actual_FA_source_uses_layer_name_not_GDN_prefix(self):
        b=(P/'software_fixtures/attention.py').read_bytes()
        self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(31208,'06f49836a73d058c6d38f826bc6c794c3b7ae9751d12d71dfff9e5c2dbdbcd28'))
        tree=ast.parse(b);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Attention')
        init=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='__init__')
        self.assertTrue(any(isinstance(x,ast.Assign)and any(isinstance(y,ast.Attribute)and y.attr=='layer_name'for y in x.targets)and isinstance(x.value,ast.Name)and x.value.id=='prefix'for x in ast.walk(init)))
        self.assertEqual(A.static_layer_name(SimpleNamespace(layer_name='fa'), 'FA'),'fa')
        self.assertEqual(A.static_layer_name(SimpleNamespace(prefix='gdn'), 'GDN'),'gdn')
        with self.assertRaises(AttributeError):A.static_layer_name(SimpleNamespace(prefix='not-FA'),'FA')
    def test_actual_nested_alias_only_use_hashes_once_and_bad_mount_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stage=root/'control';payload=root/'payload';stage.mkdir();payload.mkdir();f=payload/'x';f.write_bytes(b'abc');r=dict(Q.ref(f),path='/adakv-results/model/capture/x')
            budget=dict(guest_stage_root='/adakv-results',guest_payload_root='/adakv-results/model/capture',host_stage_root=str(stage),host_payload_root=str(payload))
            inspect=dict(Mounts=[dict(Destination=k,Source=budget[v],RW=True)for k,v in(('/adakv-results','host_stage_root'),('/adakv-results/model/capture','host_payload_root'))])
            inspect['Mounts'].append(dict(Destination=str(stage),Source=str(stage),RW=True))
            io=C.AliasIO(inspect,budget,None)
            with self.assertRaises(ValueError):io.actual_ref(dict(r,path='/adakv-results/model/capture/../x'))
            with patch.object(Q,'checked',wraps=Q.checked)as checked:
                self.assertEqual(io.actual_ref(r)['path'],str(f));self.assertEqual(checked.call_count,0)
                self.assertEqual(io(r,kind='streamed-bytes'),Q.ref(f));self.assertEqual(checked.call_count,1)
            original=list(inspect['Mounts'])
            for wrong in(original[:-1],original+[dict(Destination='/foreign',Source=str(stage),RW=True)],original[:-1]+[dict(Destination=str(stage),Source=str(payload),RW=True)]):
                with self.assertRaises(ValueError):C.AliasIO(dict(Mounts=wrong),budget,None)
    def test_retained_actual_R17_identity_alias_plus_new_configuration_not_actual(self):
        x=json.loads((P/'software_fixtures/R17_ACTUAL_RW_MOUNTS.json').read_bytes())
        self.assertTrue(x['before_after_same']);self.assertFalse(x['State']['Running']);self.assertEqual(x['State']['Pid'],0);self.assertIsNone(x['ExecIDs'])
        self.assertEqual(x['Image'],'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1')
        rw=x['Mounts'];self.assertEqual(len(rw),2);self.assertEqual(len({m['Source']for m in rw}),1)
        stage=rw[0]['Source'];self.assertEqual({m['Destination']for m in rw},{stage,'/adakv-results'})
        payload='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-20261017-001'
        budget=dict(host_stage_root=stage,guest_stage_root='/adakv-results',host_payload_root=payload,guest_payload_root='/adakv-results/model/capture')
        # This appended third entry is a source-proven NEW preparation fixture,
        # not a statement that the old stopped CID had this mount.
        prepared=copy.deepcopy(x);prepared['Mounts'].append(dict(Type='bind',Source=payload,Destination='/adakv-results/model/capture',RW=True))
        C.AliasIO(prepared,budget,None)
        bad=copy.deepcopy(prepared);bad['Mounts'].append(copy.deepcopy(bad['Mounts'][-1]))
        with self.assertRaises(ValueError):C.AliasIO(bad,budget,None)
        with self.assertRaises(ValueError):C.AliasIO(x,budget,None)
        bad=copy.deepcopy(prepared);bad['Mounts'][0]['Source']=payload
        with self.assertRaises(ValueError):C.AliasIO(bad,budget,None)

if __name__=='__main__':unittest.main(verbosity=2)
