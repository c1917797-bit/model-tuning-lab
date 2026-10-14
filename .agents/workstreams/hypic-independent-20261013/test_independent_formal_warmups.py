import unittest
from independent_formal_warmups import build_warmups,execute_warmups

class WarmupTests(unittest.TestCase):
    def artifact(self):
        return {"native_prefix":[1]*8192,"public_segment":[2]*16384,
                "requests":[{"segment_end":30000,"token_ids":[3+i]*32768} for i in range(40)]}
    def test_separate_unscored_material_before_native(self):
        w=build_warmups(self.artifact());events=[];checks=[]
        execute_warmups(w,send=lambda p:{"ok":True},guard=lambda:None,
                       record=events.append,require_material_ready=lambda:checks.append(len(events)))
        self.assertEqual(checks,[2]);self.assertEqual(len(events),4)
        self.assertTrue(all(x["scored"] is False for x in events))
        self.assertEqual([len(x["payload"]["prompt"]) for x in w],[16384,16384,8448,8448])
    def test_missing_material_aborts_before_native_warmup(self):
        events=[]
        def fail():raise RuntimeError("missing rank")
        with self.assertRaises(RuntimeError):
            execute_warmups(build_warmups(self.artifact()),send=lambda p:{},guard=lambda:None,
                           record=events.append,require_material_ready=fail)
        self.assertEqual(len(events),2)

if __name__=="__main__":unittest.main()
