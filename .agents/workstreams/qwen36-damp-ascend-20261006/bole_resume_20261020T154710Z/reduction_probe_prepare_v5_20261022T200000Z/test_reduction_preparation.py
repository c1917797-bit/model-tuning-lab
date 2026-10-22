"""Device-free regression for saved full reduction operands and paired source renderers."""
import ast
import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest

HERE = pathlib.Path(__file__).resolve().parent
V4 = HERE.parent / 'boundary_probe_prepare_v4_textonly_20261022T171000Z'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ref(path):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class Files:
    def ref(self, path):
        return ref(path)


class Budget:
    def actual(self, C, manifest, rank):
        root = pathlib.Path(manifest['model_receipt_root']) / ('PROJECTION-R%d' % rank)
        size = sum(x.stat().st_size for x in root.iterdir()) if root.exists() else 0
        return dict(bytes=size, charges=dict(projection_raw=size))


class Tests(unittest.TestCase):
    def writer(self, directory, arm='ON', budget=None):
        PR = load('projection_raw_v1', HERE/arm/'projection_raw_v1.py')
        owner = types.SimpleNamespace(C=Files(), B=budget or Budget(), rank=0,
            manifest=dict(model_receipt_root=str(directory), files={'projection_raw_v1.py':ref(PR.__file__)}),
            G=types.SimpleNamespace(METADATA_CAP=64*2**20, RAW_CAP=2**30,
              FRAME_LOGICAL_CAP=384*2**20, FRAME_WIRE_CAP=448*2**20, CHECKPOINT_CAP=128*2**20),failed=False)
        return PR, owner, PR.Writer(owner)

    def geometry(self):
        return dict(shape=[131,5120],dtype='torch.bfloat16',logical_bytes=131*5120*2)

    def test_full_four_raw_refs(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            PR, owner, writer = self.writer(directory)
            data = bytes(PR.TENSOR_BYTES)
            refs = [writer.put(g,s,data,self.geometry()) for g in (1,2) for s in PR.STAGES]
            self.assertEqual(writer.complete()['bytes'], 5365760)
            self.assertEqual(len(refs),4)
            for r in refs:
                self.assertEqual(ref(r['path']),r)
            pathlib.Path(refs[0]['path']).write_bytes(data[:-2]+b'xx')
            with self.assertRaisesRegex(ValueError,'unchanged'):
                writer.complete()

    def test_short_dtype_shape_rejected(self):
        for arm in ('ON','OFF'):
            with tempfile.TemporaryDirectory(dir=HERE) as directory:
                PR, owner, writer = self.writer(directory,arm)
                for data,geom in [(b'x',self.geometry()),(bytes(PR.TENSOR_BYTES),dict(self.geometry(),dtype='torch.float16'))]:
                    with self.assertRaises(ValueError):
                        PR.validate_geometry(geom,data)
                self.assertFalse(any(writer.root.iterdir()))

    def test_duplicate_sticky_and_exclusive(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            PR, owner, writer = self.writer(directory)
            data=bytes(PR.TENSOR_BYTES)
            r=writer.put(1,'pre_reduce',data,self.geometry())
            with self.assertRaises(ValueError):
                writer.put(1,'pre_reduce',data,self.geometry())
            self.assertTrue(writer.failed and owner.failed)
            self.assertEqual(ref(r['path']),r)
            with self.assertRaises(ValueError):
                writer.put(1,'post_reduce',data,self.geometry())

    def test_preexisting_operand_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            PR, owner, writer=self.writer(directory)
            path=writer.root/'G1-pre_reduce.bin'
            path.write_bytes(b'preserve')
            with self.assertRaises((ValueError,FileExistsError)):
                writer.put(1,'pre_reduce',bytes(PR.TENSOR_BYTES),self.geometry())
            self.assertEqual(path.read_bytes(),b'preserve')

    def test_prospective_original_budget(self):
        class Full(Budget):
            def actual(self,C,m,rank):
                return dict(bytes=60*2**20,charges=dict(projection_raw=0))
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            PR, owner, writer=self.writer(directory,budget=Full())
            with self.assertRaisesRegex(ValueError,'original'):
                writer.put(1,'pre_reduce',bytes(PR.TENSOR_BYTES),self.geometry())
            self.assertFalse(any(writer.root.iterdir()))

    def test_unexpected_and_symlink_retained_reject(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            PR,owner,writer=self.writer(directory)
            p=writer.root/'unknown.bin';p.write_bytes(b'x')
            with self.assertRaises(ValueError):PR.retained_files(owner.C,owner.manifest,0)
            p.unlink();p=writer.root/'G1-pre_reduce.bin';p.symlink_to(pathlib.Path(directory)/'absent')
            with self.assertRaises(ValueError):PR.retained_files(owner.C,owner.manifest,0)

    def test_paired_arm_default_off_and_hash_delta(self):
        old_pp=ast.parse((V4/'projection_probe_v1.py').read_text())
        def function(tree,name):
            nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
            self.assertEqual(len(nodes),1);return ast.dump(nodes[0],include_attributes=False)
        for arm in ('ON','OFF'):
            PP=load('projection_probe_'+arm,HERE/arm/'projection_probe_v1.py')
            BP=load('boundary_probe_'+arm,HERE/arm/'boundary_probe_v1.py')
            self.assertIsNone(PP.select({},None))
            self.assertIsNone(PP.create(None,{}))
            self.assertIsNone(BP.create(None,None,None,{}, {},None,None,None))
            self.assertEqual(PP.DECLARATION['arm'],arm)
            self.assertEqual(BP.DECLARATION['arm'],arm)
            opposite=dict(PP.DECLARATION,arm='OFF' if arm=='ON' else 'ON')
            with self.assertRaises(ValueError):PP.select({PP.FLAG:'1'},opposite)
            self.assertEqual(function(old_pp,'_trace'),function(ast.parse((HERE/arm/'projection_probe_v1.py').read_text()),'_trace'))
            text=(HERE/arm/'projection_probe_v1.py').read_text()
            self.assertIn("current['stages'][stage]['raw'] = self.raw_writer.put",text)
            self.assertIn('full_actual_tensor=True',text)
            self.assertNotIn('torch.distributed',text)

    def test_actual_hash_writer_integration(self):
        PP=load('projection_probe_actual',HERE/'ON'/'projection_probe_v1.py')
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            PR,owner,writer=self.writer(directory)
            native=object();owner.read_bytes=0
            geometry=self.geometry();data=bytes(PR.TENSOR_BYTES)
            owner._geometry=lambda tensor:geometry
            def read(tensor):
                owner.read_bytes+=len(data);return object(),data,geometry
            owner._read=read;owner._finite=lambda value:None
            observer=PP.Observer.__new__(PP.Observer)
            observer.owner=owner;observer.raw_writer=writer;observer.extra_read_bytes=0
            observer._scope=lambda:(1,'rid',native)
            observer.current=dict(generation=1,request='rid',request_object=id(native),stages={},read_bytes=0)
            observer._hash('pre_reduce',object(),'projection.generic_forward',1556)
            saved=observer.current['stages']['pre_reduce']
            self.assertEqual(saved['raw'],ref(saved['raw']['path']))
            self.assertEqual(saved['raw']['sha256'],saved['sha256'])
            self.assertTrue(saved['full_actual_tensor'])
            self.assertEqual(owner.read_bytes,len(data))

    def test_renderer_budget_and_no_math_change(self):
        # Load the exact old parent solely for pure source transformations.
        parent_path=V4.parent/'bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2/SOURCE_BOUND.json'
        parent=json.loads(parent_path.read_bytes())
        lineage=json.loads(pathlib.Path(parent['short_parent_source']['path']).read_bytes())
        names=('service_runner.py','live_owner.py','bole_performance_profile.py','performance_service_client.py',
               'host_service.py','performance_host.py','command_contract.py','prefill_tail.py','model_process_calibration.py','g3_budget.py')
        originals={n:pathlib.Path(lineage['files'][n]['path']).read_text() for n in names}
        sys.path.insert(0,str(pathlib.Path(parent['root'])))
        try:
            old_short=load('old_short_delta_test',pathlib.Path(parent['files']['short_binding_delta.py']['path']))
            # Its pure runtime imports the original qualified renderer.
            old_out=old_short.runtime({n:originals[n] for n in old_short.RUNTIME})
            for arm in ('ON','OFF'):
                BD=load('boundary_delta_'+arm,HERE/arm/'boundary_delta.py')
                out=BD.runtime(originals,old_out)
                for n,t in out.items():compile(t,n,'exec')
                text=out['g3_budget.py']
                fake=types.ModuleType('sourceio');fake.need=lambda v,m: None if v else (_ for _ in()).throw(ValueError(m))
                fakeg=types.ModuleType('g2_contract')
                for k,v in dict(MAX_OUTPUT=1024,METADATA_CAP=64*2**20,RAW_CAP=2**30,FRAME_LOGICAL_CAP=384*2**20,FRAME_WIRE_CAP=448*2**20,CHECKPOINT_CAP=128*2**20).items():setattr(fakeg,k,v)
                saved={n:sys.modules.get(n) for n in ('sourceio','g2_contract')}
                sys.modules['sourceio']=fake;sys.modules['g2_contract']=fakeg
                try:
                    namespace={};exec(compile(text,'budget','exec'),namespace)
                    r=namespace['reservation']()
                    self.assertLessEqual(r['maximum_metadata_bytes'],64*2**20)
                    self.assertEqual(r['projection_raw_bytes'],8*2**20)
                    self.assertEqual(r['other_rank_bytes'],3*2**20)
                finally:
                    for n,v in saved.items():
                        if v is None:sys.modules.pop(n,None)
                        else:sys.modules[n]=v
                self.assertIn("PROJECTION_RAW=8*2**20",text)
                self.assertEqual(set(out),set(names))
        finally:sys.path.pop(0)

    def test_authority_and_exact_off_profile(self):
        parent_path=V4.parent/'bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2/SOURCE_BOUND.json'
        parent=json.loads(parent_path.read_bytes())
        class C:
            @staticmethod
            def obj(r):return json.loads(pathlib.Path(r['path']).read_bytes())
        for arm in ('ON','OFF'):
            I=load('boundary_integration_'+arm,HERE/arm/'boundary_integration.py')
            self.assertTrue(I.require_frozen_inputs())
            self.assertEqual(ref(I.AUTHORIZATION_REF['path']),I.AUTHORIZATION_REF)
            self.assertEqual(ref(I.AUTHORIZATION_DOCUMENT_REF['path']),I.AUTHORIZATION_DOCUMENT_REF)
            I.check_continuation_payload(C.obj(I.AUTHORIZATION_REF))
            self.assertEqual(I.CUTOFF_EPOCH,1792710600)
            self.assertEqual(I.expected_profile(parent),dict(parent['short_state_digest_profile'],observation=arm))
            self.assertEqual(I.expected_observation_profile(C,parent),C.obj(parent['short_parent_source'])['observation_only_profile'])
            auth=C.obj(I.AUTHORIZATION_REF);auth['internal_batch_cutoff_epoch']+=1
            with self.assertRaises(ValueError):I.check_continuation_payload(auth)

    def test_actual_worker_flags_whitelist(self):
        import os
        from unittest.mock import patch
        PP=load('projection_probe_flags',HERE/'ON'/'projection_probe_v1.py')
        observer=PP.Observer.__new__(PP.Observer)
        observer.owner=types.SimpleNamespace(t=types.SimpleNamespace(
            are_deterministic_algorithms_enabled=lambda:True,
            is_deterministic_algorithms_warn_only_enabled=lambda:False))
        with patch.dict(os.environ,{'HCCL_DETERMINISTIC':'true','HCCL_ALGO':'level0:NA;level1:ring','ASCEND_LAUNCH_BLOCKING':'0','PRIVATE_UNRELATED':'must-not-export'},clear=True):
            value=observer._runtime_execution()
            self.assertEqual(set(value['environment']),{'HCCL_DETERMINISTIC','HCCL_ALGO','ASCEND_LAUNCH_BLOCKING'})
            self.assertTrue(value['torch_deterministic_enabled'])
            self.assertFalse(value['torch_deterministic_warn_only'])
            self.assertNotIn('must-not-export',json.dumps(value))
        with patch.dict(os.environ,{'HCCL_ALGO':'x'*129},clear=True):
            with self.assertRaises(ValueError):observer._runtime_execution()

    def test_actual_retained_envelope_capacity(self):
        root=pathlib.Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v4-textonly_20261022T171000Z/dense/receipts')
        for rank in range(4):
            for generation in (1,2):
                value=json.loads((root/('BOUNDARY-R%d'%rank)/('G%d-PROJECTION-INTERNAL.json'%generation)).read_bytes())
                for stage in ('pre_reduce','post_reduce'):
                    row=value['record']['stages'][stage]
                    row['raw']=dict(path='/opt/host/vnf/austinov/run-bole-reduction-OFF-v5_20261022T200000Z/dense/receipts/PROJECTION-R%d/G%d-%s.bin'%(rank,generation,stage),
                        bytes=row['bytes'],sha256=row['sha256'])
                value['record']['runtime_execution']=dict(torch_deterministic_enabled=False,torch_deterministic_warn_only=False,
                    environment={key:'x'*128 for key in ('HCCL_DETERMINISTIC','HCCL_ALGO','ASCEND_LAUNCH_BLOCKING')})
                # Re-evaluate the real retained full envelope with exact new path sizes
                # and maximum admitted flags; these added bytes are fabricated capacity evidence.
                encoded=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
                self.assertLessEqual(len(encoded),8192)

if __name__=='__main__':
    unittest.main()
