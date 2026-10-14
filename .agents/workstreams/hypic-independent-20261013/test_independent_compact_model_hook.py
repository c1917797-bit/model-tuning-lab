import unittest
import torch
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries
from independent_compact_model_hook import CompactModelSelection,install_compact_model,CURRENT_COMPACT_MODEL


class ModelHookTests(unittest.TestCase):
    def classes(self):
        class Base:
            def forward(self,ids,positions,intermediate_tensors=None,inputs_embeds=None):
                self.rows=len(ids);self.context=CURRENT_COMPACT_MODEL.get()
                if getattr(self,'fail',False):raise RuntimeError('layer failed')
                return ids[:,None].float()+positions.reshape(-1,1).float()
        class Model(Base):pass
        return Base,Model
    def selection(self,sampled=(11,)):
        req=RequestSlice('r',0,1,0,12,0,0,12)
        plan=plan_c2_queries(req,SegmentSelection(2,10,False,'x'),seam_tokens=3,public_length=8)
        return CompactModelSelection((plan,),sampled)
    def test_real_forward_receives_only_retained_rows_and_sampler_is_restored(self):
        Base,Model=self.classes();events=[];selection=self.selection()
        stop=install_compact_model(Model,enabled=True,verify_source=lambda c:None,
            select=lambda *args:selection,emit=events.append)
        try:
            model=Model();out=model.forward(torch.arange(12),torch.arange(12))
            self.assertEqual(model.rows,7);self.assertEqual(float(out[11,0]),22.)
            self.assertEqual(float(out[6,0]),0.)
            self.assertIs(model.context,selection);self.assertIsNone(CURRENT_COMPACT_MODEL.get())
            self.assertEqual(events[0]['retained_rows'],7)
        finally:stop()
        self.assertNotIn('forward',Model.__dict__)
        self.assertIs(Model.forward,Base.forward)
    def test_pruned_sampler_and_prompt_logprobs_rejected_before_model(self):
        Base,Model=self.classes()
        stop=install_compact_model(Model,enabled=True,verify_source=lambda c:None,
            select=lambda *args:self.selection((7,)),emit=lambda e:None)
        try:
            model=Model()
            with self.assertRaises(ValueError):model.forward(torch.arange(12),torch.arange(12))
            self.assertFalse(hasattr(model,'rows'))
        finally:stop()
    def test_exception_restores_context_and_disabled_is_unchanged(self):
        Base,Model=self.classes();original=Model.forward
        install_compact_model(Model,enabled=False)()
        self.assertIs(Model.forward,original)
        stop=install_compact_model(Model,enabled=True,verify_source=lambda c:None,
            select=lambda *args:self.selection(),emit=lambda e:None)
        try:
            model=Model();model.fail=True
            with self.assertRaises(RuntimeError):model.forward(torch.arange(12),torch.arange(12))
            self.assertIsNone(CURRENT_COMPACT_MODEL.get())
        finally:stop()


if __name__=='__main__':unittest.main()
