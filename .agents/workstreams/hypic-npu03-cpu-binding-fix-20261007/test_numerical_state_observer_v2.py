import hashlib
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import numerical_state_observer as old
import numerical_state_observer_v2 as new


class AliasTests(unittest.TestCase):
    def fixture(self, root):
        sources={
            "gdn":"def _position_independent_gdn_core(ctx, layer_name, ssm_cache):\n    cache_composes = 0\n    ssm_cache.index_copy_(0, 0, 1)\n",
            "attention":"def _repair_position_independent_kv(ctx, layer_name):\n    value = 1\n",
            "runner":"def _rewrite_position_independent_inputs(ctx, layer_name):\n    value = 1\n"}
        modules,hashes={},{}
        for k,s in sources.items():
            p=Path(root)/(k+".py");p.write_text(s)
            m=types.ModuleType(k);m.__file__=str(p)
            exec(compile(s,str(p),"exec"),m.__dict__)
            modules[k]=m;hashes[k]=hashlib.sha256(s.encode()).hexdigest()
        return modules,hashes

    def exercise(self, api):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ,{old.SWITCH:"1"}):
            modules,hashes=self.fixture(root)
            ctx=types.SimpleNamespace(req_ids=("target",),
                plans={"target":types.SimpleNamespace(entries=(object(),))})
            events=[]
            handle=api.install(modules,lambda *a:events.append(a[0]),
                request_id="target",layers={"L"},source_hashes=hashes)
            alias=modules["gdn"]._position_independent_gdn_core
            cache=types.SimpleNamespace(index_copy_=lambda *a:None)
            alias(ctx,"L",cache)
            self.assertEqual(events,["gdn_initial","gdn_committed"])
            handle.uninstall()
            if api is old:
                with self.assertRaisesRegex(NameError,"_hypic_diagnostic_state_observer"):
                    alias(ctx,"L",cache)
                return
            before=len(events)
            alias(ctx,"L",cache)
            self.assertEqual(len(events),before)
            # A fresh generation must not reactivate retained aliases.
            second=api.install(modules,lambda *a:events.append("new"),
                request_id="target",layers={"L"},source_hashes=hashes)
            alias(ctx,"L",cache)
            self.assertEqual(len(events),before)
            modules["gdn"]._position_independent_gdn_core(ctx,"L",cache)
            self.assertEqual(events[before:],["new","new"])
            second.uninstall()
            second.uninstall()
            self.assertTrue(all(v.callback is None for m in modules.values()
                for k,v in vars(m).items() if k.startswith(old.HOOK+"_v2_")))

    def test_old_retained_alias_failure_reproduced(self):
        self.exercise(old)

    def test_fixed_alias_safe_and_reinstall_does_not_reactivate_old(self):
        self.exercise(new)

    def test_disabled_no_access(self):
        with patch.dict(os.environ,{old.SWITCH:"0"}):
            new.install(None,None,request_id=None,layers=None).uninstall()


if __name__=="__main__":
    unittest.main()
