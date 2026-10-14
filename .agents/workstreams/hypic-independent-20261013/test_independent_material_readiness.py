import unittest
from independent_material_readiness import materials_ready
class ReadinessTests(unittest.TestCase):
    def events(self):
        return [{"event":kind,"manifest_sha256":"source","rank":rank,"pid":100+rank,
                 "layer":prefix+str(i)} for rank in range(4)
                for kind,prefix,count in (("compact_public_state_published","linear",48),
                                          ("compact_public_kv_published","kv",16))
                for i in range(count)]
    def test_all4_complete_and_missing_layer(self):
        e=self.events();self.assertTrue(materials_ready(e,"source"))
        self.assertFalse(materials_ready(e[:-1],"source"))
    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):materials_ready(self.events(),"other")
if __name__=="__main__":unittest.main()
