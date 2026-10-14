import unittest
from types import SimpleNamespace
import torch
from independent_public_pool import PublicPool
from independent_compact_stage import pin_complete_material,CompactCanonicalStage


class CompleteMaterialTests(unittest.TestCase):
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
