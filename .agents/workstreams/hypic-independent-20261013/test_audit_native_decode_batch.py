import unittest
from copy import deepcopy
from audit_native_decode_batch import audit_native_decode_batch
from audit_native_decode_batch import audit_native_decode_disabled
class AuditTests(unittest.TestCase):
    def events(self):
        xs=[]
        for rank in range(4):
            common={"pid":rank+10,"manifest_sha256":"bound"}
            xs.append(dict(common,event="compact_hypic_hooks_installed",native_decode_batch=True,default_disabled=True))
            for i in range(48):
                c=dict(common,rank=rank,layer="layer"+str(i),step=7)
                xs.append(dict(c,event="compact_public_state_published"))
                g=dict(c,requests=["a","b"],rows=2)
                xs.append(dict(g,event="native_decode_batch_completed",slots=[2,4],private_buffers=True,actual_slot_commit="deferred"))
                metrics=[dict(request_id=r,tensor=t,max_abs=0.,rms=0.,max_scaled=0.,passed=True) for r in ("a","b") for t in ("output","state","conv")]
                xs.append(dict(g,event="native_decode_batch_shadow_checked",metrics=metrics,atol=.01,rtol=.003,passed=True))
                for rid,slot in zip(("a","b"),(2,4)):
                    xs.append(dict(c,event="mixed_native_gdn_completed",request_id=rid,slot=slot,retained_rows=1,skipped_body_tokens=0,finite=True))
        return xs
    def audit(self,xs):return audit_native_decode_batch(xs,{i:i+10 for i in range(4)},manifest_sha256="bound")
    def test_complete(self):self.assertTrue(self.audit(self.events())["native_decode_batch_verified"])
    def test_negative_controls(self):
        for kind,field,value in [
            ("native_decode_batch_completed","slots",[2,2]),
            ("native_decode_batch_completed","actual_slot_commit","early"),
            ("native_decode_batch_shadow_checked","rtol",.1),
            ("native_decode_batch_shadow_checked","passed",False),
            ("mixed_native_gdn_completed","finite",False),
            ("mixed_native_gdn_completed","slot",100),
            ("native_decode_batch_shadow_checked","pid",500)]:
            xs=self.events();next(x for x in xs if x["event"]==kind)[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.audit(xs)
    def test_missing_layer(self):
        xs=self.events();xs.remove(next(x for x in xs if x["event"]=="native_decode_batch_shadow_checked"))
        with self.assertRaises(ValueError):self.audit(xs)
    def test_nonfinite_metrics(self):
        xs=self.events();next(x for x in xs if x["event"]=="native_decode_batch_shadow_checked")["metrics"][0]["max_scaled"]=float("nan")
        with self.assertRaises(ValueError):self.audit(xs)

    def test_disabled_positive_and_marker_negative(self):
        xs=[dict(event='compact_hypic_hooks_installed',pid=i+10,manifest_sha256='off',native_decode_batch=False,default_disabled=True) for i in range(4)]
        workers={i:i+10 for i in range(4)}
        self.assertTrue(audit_native_decode_disabled(xs,workers,manifest_sha256='off')['native_decode_disabled_verified'])
        for marker in ('native_decode_batch_completed','native_decode_batch_shadow_checked'):
            with self.assertRaises(ValueError):audit_native_decode_disabled(xs+[{'event':marker}],workers,manifest_sha256='off')
        xs[0]['native_decode_batch']=True
        with self.assertRaises(ValueError):audit_native_decode_disabled(xs,workers,manifest_sha256='off')
if __name__=="__main__":unittest.main()
