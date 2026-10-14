import unittest
from types import SimpleNamespace
import torch
from independent_public_pool import PublicPool
from independent_compact_stage import pin_complete_material,CompactCanonicalStage


class CompleteMaterialTests(unittest.TestCase):
    def test_mixed_admission_is_opt_in_and_requires_all_layers(self):
        from independent_request_map import RequestSlice
        from independent_runner_context import CURRENT_REQUEST_SLICES,CURRENT_PROMPT_TOKENS,CURRENT_RUNTIME_SNAPSHOT
        from independent_linear_material_pool import identity_key
        public=tuple(range(16))
        stage=CompactCanonicalStage(model_identity='m',code_identity='c',
            public_tokens=public,capacity_bytes=1024,enable_mixed=True)
        layers=[(SimpleNamespace(layer_type='full_attention',self_attn=SimpleNamespace(attn=SimpleNamespace(layer_name=f'f{i}')))
                 if i%4==3 else SimpleNamespace(layer_type='linear_attention',linear_attn=SimpleNamespace(prefix=f'l{i}')))
                for i in range(64)]
        model=SimpleNamespace(start_layer=0,end_layer=64,layers=layers)
        linear,full=stage.layer_inventory(model)
        reqs=(RequestSlice('d',0,7,100,1,0,0,1),
              RequestSlice('h',0,7,0,32,1,1,33),
              RequestSlice('p',0,7,0,8,2,33,41))
        prompts={'d':(900,), 'h':tuple(range(100,108))+public+tuple(range(200,208)),
                 'p':tuple(range(100,104))+public}
        snap=SimpleNamespace(request_ids=('d','h','p'),rank=0,step=7,
            sampled_rows=(0,32,40),prompt_logprobs=False,cache_slices=(),
            attention_groups=((0,full),),writable_kv_slots=())
        tokens=[(ctx,ctx.set(value)) for ctx,value in
            ((CURRENT_REQUEST_SLICES,reqs),(CURRENT_PROMPT_TOKENS,prompts),(CURRENT_RUNTIME_SNAPSHOT,snap))]
        try:
            self.assertIsNone(stage.select_compact(model,None,None,None,None))
            for pool,names in ((stage.compact_store.pool,linear),(stage.compact_kv_store,full)):
                for name in names:pool.entries[identity_key(stage.identity(name,0))]={'pins':0}
            selected=stage.select_compact(model,None,None,None,None)
            self.assertEqual([p.skipped_tokens for p in selected.plans],[0,8,0])
            with selected.material_guard:
                self.assertTrue(all(v['pins']==1 for v in stage.compact_store.pool.entries.values()))
            self.assertTrue(all(v['pins']==0 for v in stage.compact_store.pool.entries.values()))
            stage.enable_mixed=False
            self.assertIsNone(stage.select_compact(model,None,None,None,None))
        finally:
            for ctx,token in reversed(tokens):ctx.reset(token)

    def test_all_layers_pinned_and_eviction_blocked_during_model(self):
        a=PublicPool(8);b=PublicPool(8)
        a.publish('linear',{'x':torch.ones(2)});b.publish('kv',{'x':torch.ones(2)})
        with pin_complete_material(a,b,('linear',),('kv',)):
            with self.assertRaises(BufferError):a.publish('next',{'x':torch.ones(2)})
            self.assertEqual(b.entries['kv']['pins'],1)
        self.assertEqual(a.entries['linear']['pins'],0);self.assertEqual(b.entries['kv']['pins'],0)
        a.publish('next',{'x':torch.ones(2)})
    def test_missing_late_layer_unpins_every_previous_entry(self):
        a=PublicPool(8);b=PublicPool(8);a.publish('linear',{'x':torch.ones(2)})
        with self.assertRaises(KeyError):
            with pin_complete_material(a,b,('linear',),('missing',)):self.fail()
        self.assertEqual(a.entries['linear']['pins'],0)
    def test_full_27b_inventory_and_wrong_partition_rejected(self):
        stage=CompactCanonicalStage(model_identity='m',code_identity='c',public_tokens=tuple(range(16)),capacity_bytes=1024)
        layers=[]
        for i in range(64):
            if i%4==3:
                layers.append(SimpleNamespace(layer_type='full_attention',self_attn=SimpleNamespace(attn=SimpleNamespace(layer_name=f'full{i}'))))
            else:layers.append(SimpleNamespace(layer_type='linear_attention',linear_attn=SimpleNamespace(prefix=f'linear{i}')))
        model=SimpleNamespace(start_layer=0,end_layer=64,layers=layers)
        l,f=stage.layer_inventory(model);self.assertEqual((len(l),len(f)),(48,16))
        model.start_layer=32
        with self.assertRaises(ValueError):stage.layer_inventory(model)


if __name__=='__main__':unittest.main()
