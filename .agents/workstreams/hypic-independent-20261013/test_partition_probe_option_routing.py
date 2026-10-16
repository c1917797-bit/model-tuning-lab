"""Regression of the actual hook's option assembly, without importing device APIs."""
import ast,copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
class PartitionProbeRoutingTests(unittest.TestCase):
    def assembled(self,partitioned,probe,policy):
        tree=ast.parse(Path(__file__).with_name("independent_compact_gdn_hook.py").read_text())
        install=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="install_compact_gdn")
        wrapped=next(n for n in install.body if isinstance(n,ast.FunctionDef) and n.name=="wrapped")
        block=next(n for n in wrapped.body if isinstance(n,ast.With))
        nodes=[];started=False
        for n in block.body:
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="probe" for t in n.targets):started=True
            if started:
                if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=="packed_wave":break
                nodes.append(copy.deepcopy(n))
        self.assertTrue(nodes)
        env=dict(partitioned_render=partitioned,first_divergence=probe,
            first_divergence_head_policy="max_state_residual",short_prefix_policy=policy,
            plans=[NS(rank=0,step=1)],self=NS(prefix="layer"),emit=lambda e:None)
        with patch.dict(sys.modules,{"independent_c1_stage_probe":NS(make_probe=lambda *a,**k:None)}):
            exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),"actual-hook-options","exec"),env)
        return env["probe_kwargs"]
    def test_partition_survives_stage_probe(self):
        options=self.assembled(True,True,"canonical_recurrent_le64")
        self.assertIs(options.get("partitioned_render"),True)
        self.assertIn("probe_factory",options)
        self.assertIn("prefix_route_observer",options)
    def test_partition_without_probe(self):
        self.assertIs(self.assembled(True,False,"chunk64").get("partitioned_render"),True)
    def test_default_disabled(self):
        self.assertNotIn("partitioned_render",self.assembled(False,True,"chunk64"))
if __name__=="__main__":unittest.main()
