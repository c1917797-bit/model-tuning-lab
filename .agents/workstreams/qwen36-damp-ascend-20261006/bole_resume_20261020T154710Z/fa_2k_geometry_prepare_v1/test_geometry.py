"""Explicit synthetic metadata/source tests only; never NPU evidence."""
import copy
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fa_native_geometry as G
import render_geometry as R

def values():
    # Synthetic values selected to exercise two1536 blocks, NOT an observation.
    blocks=[3,7];table=[p*12+j for p in blocks for j in range(12)]
    slots=[table[p//128]*128+p%128 for p in range(2048)]
    return dict(prefix=2048,output_tokens=1024,physical_blocks=blocks,ratio=12,physical_size=1536,
        kernel_size=128,use_hybrid=True,pcp=1,dcp=1,cpu_table=table,gpu_table=table,
        metadata_table=table,native_slots=slots,metadata_slots=slots,
        cache_shape=(128,128,1,256),cache_dtype='torch.bfloat16',
        num_prefills=1,num_decodes=0,num_actual_tokens=2048,seq_lens=[2048],query_lens=[2048])

class Metadata(unittest.TestCase):
    def test_native24_private25_are_distinct(self):
        p=G.plan(2048,1024)
        self.assertEqual((p['max_before'],p['maximum_publication_pages'],p['maximum_scratch_pages']),(3070,24,25))
        self.assertFalse(p['NPU_observed']);self.assertFalse(p['allocation_proven'])
        for length in range(2048,3071):
            publication=(length+2+127)//128;scratch=(length+3+127)//128
            self.assertLessEqual(publication,24);self.assertLessEqual(scratch,25)
            self.assertLessEqual((length+1)//128,23)
        # All legal commits publish at most two of the three private nodes.
        for child in (-1,1,2):
            path=[0]+([]if child==-1 else[child])
            destinations=list(range(3070,3070+len(path)))
            self.assertLessEqual(max(destinations),3071)
        self.assertEqual(3072//128,24) # Third private branch row is never native publication.
    def test_short_and160_plans(self):
        self.assertEqual(G.plan(2048,8)['maximum_publication_pages'],17)
        self.assertEqual(G.plan(2048,160)['maximum_publication_pages'],18)
    def test_full_metadata_mapping(self):
        result=G.metadata(**values())
        self.assertEqual(len(result['table']),24)
        self.assertFalse(result['allocation_proven'])
    def test_table_and_mapping_mismatch(self):
        for key in ('gpu_table','metadata_table','cpu_table','native_slots','metadata_slots'):
            bad=values();bad[key]=list(bad[key]);bad[key][0]+=1
            with self.assertRaises(ValueError):G.metadata(**bad)
    def test_bool_duplicate_oob_ids_rejected(self):
        for blocks in ([True,7],[3,3],[3,-1],[3,999]):
            bad=values();bad['physical_blocks']=blocks
            with self.assertRaises(ValueError):G.metadata(**bad)
    def test_insufficient_native_pages_not_guessed(self):
        bad=values();table=list(range(12));bad.update(physical_blocks=[0],cpu_table=table,gpu_table=table,metadata_table=table)
        bad['native_slots']=bad['metadata_slots']=list(range(2048))
        with self.assertRaises(ValueError):G.metadata(**bad)
    def test_no_prefill_no_geometry(self):
        for key,value in (('num_prefills',0),('num_decodes',1),('num_actual_tokens',131),('seq_lens',[131]),
                          ('cache_dtype','torch.float16'),('pcp',2),('use_hybrid',False)):
            bad=values();bad[key]=value
            with self.assertRaises(ValueError):G.metadata(**bad)
    def test_unobserved_JSON_plan_never_runtime_geometry(self):
        for x in (None,{},G.plan(2048,1024),G.metadata(**values())):
            with self.assertRaises(ValueError):G.shape(2048,x)
    def test_native_binding_default_OFF(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'default OFF'):
                G.bind_all(None,None,None,None,None,None,request_id=None,request=None,metadata=None,
                           context=None,get_attention_context=None,input_ids=None,positions=None,generation=1)
    def test_typed_registration_not_metadata_packet(self):
        with self.assertRaises(ValueError):G.require_registration({},None,'r',None,2048,1)

class Lifetime(unittest.TestCase):
    def fixture(self):
        # Synthetic Python objects exercise lifetime predicates only. They do
        # NOT call native bind_layer, run an NPU, or become persisted receipts.
        f=G.metadata(**values());key=object();value=object();group=object()
        class Row:
            def __init__(self,x):self.x=x
            def tolist(self):return self.x
        class CPU:
            device=types.SimpleNamespace(type='cpu')
            def __getitem__(self,item):return Row(list(f['table'])[:item[1].stop])
        block=types.SimpleNamespace(num_blocks_per_row=[24],get_cpu_tensor=lambda:CPU(),
            blocks_per_phys_block=12,physical_block_size=1536,logical_block_size=128,
            block_size=128,use_hybrid_blocks=True,pcp_world_size=1,dcp_world_size=1)
        request=types.SimpleNamespace(block_ids={0:[3,7]})
        batch=types.SimpleNamespace(req_ids=['r'],req_id_to_index={'r':0},block_table=[block])
        runner=types.SimpleNamespace(requests={'r':request},input_batch=batch,
            kv_cache_config=types.SimpleNamespace(kv_cache_groups=[group]))
        layer=types.SimpleNamespace(kv_cache=[key,value],impl=types.SimpleNamespace(key_cache=key,value_cache=value))
        return G.NativeGeometry(G._TOKEN,{'synthetic':True},runner,request,'r',1,0,group,block,layer,
                                key,value,id(key),id(value),f,id)
    def test_private25_with_native24_live_predicates(self):
        g=self.fixture();shape=g.check(3070)
        self.assertEqual((shape['scratch_kernel_pages'],shape['publication_kernel_pages'],shape['initial_kernel_pages']),(25,24,24))
    def test_slot_reuse_request_and_table_growth_rejected(self):
        for change in ('request','row','group'):
            g=self.fixture()
            if change=='request':g.runner.requests['r']=object()
            if change=='row':g.block.num_blocks_per_row[0]=25
            if change=='group':g.runner.kv_cache_config.kv_cache_groups[0]=object()
            with self.assertRaises(ValueError):g.check(2048)
    def test_cache_alias_rebound_and_out_of_scope_rejected(self):
        g=self.fixture();g.layer.impl.key_cache=object()
        with self.assertRaises(ValueError):g.check(2048)
        for length in (131,2047,3071,True):
            with self.assertRaises(ValueError):self.fixture().check(length)
    def test_runtime_does_not_expand_native_allocation(self):
        g=self.fixture();f=g.facts
        self.assertTrue(g.allocation(table=f['table'],physical_blocks=f['physical_blocks'],
            ratio=12,physical_size=1536,kernel_size=128,use_hybrid=True))
        with self.assertRaises(ValueError):
            g.allocation(table=tuple(range(36)),physical_blocks=[0,1,2],
                ratio=12,physical_size=1536,kernel_size=128,use_hybrid=True)

class Source(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=R.read_parent();cls.bundle=R.adapt(cls.parent)
    def test_whole_inverse_and_exact_math_preserved(self):
        self.assertEqual(R.inverse(self.bundle),self.parent)
        for n in ('adapter.py','core112.py','oracle112.py','g2_numeric.py','independent_model.py','transaction.py','tp_consensus.py'):
            self.assertEqual(self.bundle['files'][n],self.parent[n])
    def test_legacy131_geometry_stays_exact(self):
        sourceio=types.ModuleType('sourceio');sourceio.need=G.need
        with patch.dict(sys.modules,{'sourceio':sourceio}):
            old={};new={}
            exec(compile(self.parent['g3_fia_contract.py'],'original','exec'),old)
            exec(compile(self.bundle['files']['g3_fia_contract.py'],'derived','exec'),new)
            for length in range(131,1154):self.assertEqual(old['shape'](length),new['shape'](length))
            kwargs=dict(table=tuple(range(12)),physical_blocks=[0],ratio=12,physical_size=1536,kernel_size=128,use_hybrid=True)
            self.assertEqual(old['allocation'](**kwargs),new['allocation'](**kwargs))
            with self.assertRaises(ValueError):new['shape'](2048)
            with self.assertRaises(ValueError):new['shape'](3070,{})
    def test_actual_source_has_prefill_and_view_gate(self):
        model=self.bundle['files']['model_entry.py'].decode()
        self.assertIn("NG.require(b.get('native_geometry')).check(o.length)",model)
        self.assertIn("trial['native_geometry']=b['native_geometry']",model)
        self.assertIn('native_geometry.attach(rows)',self.bundle['files']['cache_registry.py'].decode())
        self.assertIn("DOMAIN.shape(length,trial.get('native_geometry'))",self.bundle['files']['service_fia.py'].decode())
    def test_inverse_rejects_modified_source(self):
        b=copy.deepcopy(self.bundle);b['files']['service_fia.py']+=b'\n'
        with self.assertRaises(ValueError):R.inverse(b)
    def test_no_whole_source_or_NPU_claim(self):
        self.assertFalse(self.bundle['whole_source_ready']);self.assertFalse(self.bundle['NPU'])
        self.assertTrue(self.bundle['prepared_only'])

if __name__=='__main__':
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: software --check only')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if not result.wasSuccessful():raise SystemExit(1)
