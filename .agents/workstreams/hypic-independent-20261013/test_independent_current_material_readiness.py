import unittest
from independent_current_material_readiness import current_materials_ready
class CurrentReadinessTests(unittest.TestCase):
    def events(self):
        return [{"event":kind,"pool":pool,"rank":rank,"pid":100+rank,
            "manifest_sha256":"m","tokens_sha256":"A","layer":pool+str(i),
            "key":pool+str(i),"generation":i+1} for rank in range(4)
            for kind,pool,count in (("compact_public_state_published","linear",48),
                ("compact_public_kv_published","kv",16)) for i in range(count)]
    def eviction(self,event):
        return dict(event,event="compact_public_material_evicted")
    def test_eviction_invalidates_and_new_generation_restores(self):
        events=self.events()
        self.assertTrue(current_materials_ready(events,"m","A"))
        victim=events[-1];events.append(self.eviction(victim))
        self.assertFalse(current_materials_ready(events,"m","A"))
        events.append(dict(victim,generation=99))
        self.assertTrue(current_materials_ready(events,"m","A"))
    def test_wrong_generation_and_pid_rejected(self):
        for override in ({"generation":99},{"pid":999}):
            events=self.events();events.append(dict(self.eviction(events[-1]),**override))
            with self.assertRaises(ValueError):current_materials_ready(events,"m","A")
if __name__=="__main__":unittest.main()
