import unittest
from independent_material_readiness import materials_ready
class ReadinessTests(unittest.TestCase):
    def events(self):
        return [{"event":kind,"manifest_sha256":"source","tokens_sha256":"A","rank":rank,"pid":100+rank,
                 "layer":prefix+str(i)} for rank in range(4)
                for kind,prefix,count in (("compact_public_state_published","linear",48),
                                          ("compact_public_kv_published","kv",16))
                for i in range(count)]
    def test_all4_complete_and_missing_layer(self):
        e=self.events();self.assertTrue(materials_ready(e,"source"))
        self.assertFalse(materials_ready(e[:-1],"source"))
    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):materials_ready(self.events(),"other")
    def test_segments_cannot_supply_each_others_layers(self):
        e=self.events()
        for x in e:
            x["tokens_sha256"]="A" if x["event"]=="compact_public_state_published" else "B"
        self.assertFalse(materials_ready(e,"source","A"))
        self.assertFalse(materials_ready(e,"source","B"))
        with self.assertRaises(ValueError):materials_ready(e,"source")
    def test_explicit_complete_segment_and_unrelated_segment(self):
        e=self.events()
        for x in e:x["tokens_sha256"]="A"
        other=dict(e[0],tokens_sha256="B")
        self.assertTrue(materials_ready(e+[other],"source","A"))
        self.assertFalse(materials_ready(e+[other],"source","B"))
    def test_missing_digest_cannot_complete_selected_segment(self):
        e=self.events()
        for x in e:x["tokens_sha256"]="A"
        del e[-1]["tokens_sha256"]
        self.assertFalse(materials_ready(e,"source","A"))
    def test_all_missing_digest_rejected(self):
        e=self.events()
        for x in e:del x["tokens_sha256"]
        with self.assertRaises(ValueError):materials_ready(e,"source")
    def test_no_materials_not_ready(self):
        self.assertFalse(materials_ready([],"source"))
if __name__=="__main__":unittest.main()
