"""Execute actual routing and snapshot AST blocks without importing device APIs."""
import ast,copy,json,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import torch
from independent_compact_activation import c1_install_route

class NoRead:
    def __getitem__(self,index):raise AssertionError("redundant cache read")

class RuntimeSnapshotTests(unittest.TestCase):
    def run_block(self,*,lazy,batched=False,packed=False,shadow=False):
        tree=ast.parse(Path(__file__).with_name("independent_compact_gdn_hook.py").read_text())
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.If)
                  and isinstance(n.test,ast.Name) and n.test.id=="lazy_initial_snapshot")
        caches=(torch.ones(2,3,4),torch.ones(2,2,3)) if shadow or not lazy or not(batched or packed) else (NoRead(),NoRead())
        env=dict(lazy_initial_snapshot=lazy,state_cache=caches[0],conv_cache=caches[1],
            slot=0,assoc=NS(has_initial_state=True),plan=NS(request_id="r"),
            batched={"r":1} if batched else {},packed={"r":1} if packed else {},
            check_packed_shadow=shadow,skipped_initial_snapshots=set())
        exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],
            type_ignores=[])),"actual-runtime-snapshot","exec"),env)
        return env
    def test_actual_batched_skips(self):
        e=self.run_block(lazy=True,batched=True)
        self.assertIsNone(e["state"]);self.assertEqual(e["skipped_initial_snapshots"],{"r"})
    def test_actual_packed_skips(self):
        self.assertIsNone(self.run_block(lazy=True,packed=True)["state"])
    def test_actual_shadow_preserves_initial(self):
        self.assertIsInstance(self.run_block(lazy=True,packed=True,shadow=True)["state"],torch.Tensor)
    def test_actual_fallback_preserves_initial(self):
        self.assertIsInstance(self.run_block(lazy=True)["state"],torch.Tensor)
    def test_default_route_unchanged(self):
        self.assertIsInstance(self.run_block(lazy=False,packed=True)["state"],torch.Tensor)
    def config(self):
        return json.loads(Path(__file__).with_name("FORMAL_COMPACT_CONFIG_R18_PERFORMANCE.json").read_text())
    def test_activation_default_and_enabled(self):
        for enabled in (False,True):
            c=self.config()
            if enabled:c["c1_lazy_initial_snapshot"]=True
            calls=[]
            with patch("independent_compact_gdn_hook.install_compact_gdn",
                       side_effect=lambda *a,**kw:calls.append(kw)):
                rest,install,_=c1_install_route(c);install(NS(),enabled=True,emit=lambda e:None)
            self.assertIs(install.c1_lazy_initial_snapshot,enabled)
            self.assertIs(calls[0]["lazy_initial_snapshot"],enabled)
            self.assertNotIn("c1_lazy_initial_snapshot",rest)
    def test_activation_rejects_ambiguous_or_unpacked(self):
        for value in (1,None,"true"):
            c=self.config();c["c1_lazy_initial_snapshot"]=value
            with self.assertRaises(ValueError):c1_install_route(c)
        c=self.config();c["c1_lazy_initial_snapshot"]=True;c["c1_packed_wave"]=False
        with self.assertRaises(ValueError):c1_install_route(c)
