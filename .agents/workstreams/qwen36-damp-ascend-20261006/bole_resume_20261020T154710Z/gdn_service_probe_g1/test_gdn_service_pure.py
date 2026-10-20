"""Pure ownership/control tests. Tensor-like values below are CONTROL STUBS.

No Torch/NPU API, real tensor numerical result or qualification is exercised.
"""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS
import types
import unittest


P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_gdn_seam_control_tests', P / 'gdn_service_seam.py')
S = importlib.util.module_from_spec(spec); sys.modules[spec.name] = S
spec.loader.exec_module(S)
LAYERS = {i for i in range(64) if i % 4 != 3}


class C:
    @staticmethod
    def need(value, message):
        if not value:
            raise ValueError(message)


class Value:
    """Opaque control identity, not a tensor and never used for arithmetic."""
    dtype = 'CONTROL_ONLY_F32'
    shape = (1, 12, 128, 128)
    def __init__(self, pointer):
        self.pointer = pointer
    def untyped_storage(self):
        return self
    def data_ptr(self):
        return self.pointer


class Core:
    def __init__(self):
        self.calls = 0
    def commit(self, *args):
        self.calls += 1
        return Value(100000 + self.calls)


class Live:
    def current(self):
        return ('control-owner', 1, 0, 131, 0)


class Bridge:
    def _gdn(self, *args):
        raise AssertionError('original control placeholder must not execute')
    def stage_selected_path(self, *args, **kwargs):
        raise AssertionError('original control placeholder must not execute')


def stage_fixture(fail_after=None, hijack=False):
    b = Bridge(); core = Core(); live = Live(); b.K = core
    captures = {i: dict(kind='gdn', state=Value(1000+i), keys=Value(2000+i),
        factors=(Value(3000+i), Value(4000+i)), gdn_extension=dict(selected=None)) for i in LAYERS}
    ctx = NS(owner=live.current(), phase='FORWARD_COMPLETE_NOT_QUALIFIED', captures=captures, first_fault=None)
    t = NS(float32=Value.dtype, isfinite=lambda value: NS(all=lambda: True))
    ctl = NS(E=NS(BUS=NS(get=lambda: None)), C=C, core=core, live=live,
        mode='matched_original', staging=False, active=dict(ctx=ctx, owner=ctx.owner, seen=set(LAYERS), selected=set()),
        bridge=b, m=dict(files={'core112.py': 'CONTROL_SOURCE_ID_ONLY'}))
    b._bole_gdn_extension = ctl; b.bindings = [dict(state=Value(100+i)) for i in range(64)]
    primary = RuntimeError('CONTROL_ONLY_ORIGINAL_STAGE_FAILURE'); replacement = object()
    def original(this, context, terminal, *, current_owner):
        if hijack:
            this.K = replacement
            raise primary
        for count, row in enumerate(context.captures.values(), 1):
            this.K.commit(t, row['state'], row['keys'], row['factors'], None, terminal)
            if count == fail_after:
                raise primary
        context.phase = 'STAGED_NOT_PUBLISHED'
        return dict(writes=[None]*128, published=False)
    ctl.original_stage = types.MethodType(original, b)
    return b, ctl, ctx, primary, replacement


class PureTests(unittest.TestCase):
    def test_default_off_touches_no_bridge(self):
        old = os.environ.pop('BOLE_GDN_SERVICE_FUSION_ENABLE', None)
        try:
            self.assertEqual(S.install(None, None, None, None, extension_ref=None), S.disabled())
        finally:
            if old is not None:
                os.environ['BOLE_GDN_SERVICE_FUSION_ENABLE'] = old

    def test_owned_control_calls_once_per_layer(self):
        b, ctl, ctx, _, _ = stage_fixture()
        result = S._stage(b, ctx, 2, current_owner=ctl.live.current)
        self.assertEqual(len(result['writes']), 128)
        self.assertEqual(ctl.core.calls, 48)
        self.assertIs(b.K, ctl.core); self.assertIsNone(ctl.active); self.assertFalse(ctl.staging)
        self.assertTrue(all(r['gdn_extension']['selected']['terminal'] == 2 for r in ctx.captures.values()))

    def test_stage_failure_restores_private_facade(self):
        b, ctl, ctx, primary, _ = stage_fixture(fail_after=2)
        with self.assertRaises(RuntimeError) as caught:
            S._stage(b, ctx, 1, current_owner=ctl.live.current)
        self.assertIs(caught.exception, primary); self.assertEqual(ctl.core.calls, 2)
        self.assertIs(b.K, ctl.core); self.assertIsNone(ctl.active); self.assertFalse(ctl.staging)
        self.assertEqual(ctx.phase, 'FAILED_NO_PUBLICATION')

    def test_live_alias_is_rejected_before_plan_return(self):
        b, ctl, ctx, _, _ = stage_fixture()
        first = next(iter(ctx.captures))
        ctl.core.commit = lambda *args: b.bindings[first]['state']
        with self.assertRaises(ValueError):
            S._stage(b, ctx, 0, current_owner=ctl.live.current)
        self.assertIs(b.K, ctl.core); self.assertIsNone(ctl.active); self.assertFalse(ctl.staging)

    def test_unknown_replacement_is_not_clobbered(self):
        b, ctl, ctx, primary, replacement = stage_fixture(hijack=True)
        with self.assertRaises(RuntimeError) as caught:
            S._stage(b, ctx, 0, current_owner=ctl.live.current)
        self.assertIs(caught.exception, primary); self.assertIs(b.K, replacement)
        self.assertTrue(any('ownership changed' in text for text in primary.__notes__))
        self.assertIsNone(ctl.active); self.assertFalse(ctl.staging)

    def test_owned_install_restore_preserves_inherited_methods(self):
        b = Bridge(); b.K = object()
        ctl = S.Controller.__new__(S.Controller)
        ctl.bridge=b; ctl.core=b.K; ctl.E=NS(BUS=NS(get=lambda: None)); ctl.C=C
        ctl.saved={}; ctl.active=None; ctl.staging=False; ctl.installed=False
        ctl.install()
        self.assertIs(b._gdn.__func__, S._gdn)
        self.assertIs(b.stage_selected_path.__func__, S._stage)
        ctl.restore()
        self.assertIs(b._gdn.__func__, Bridge._gdn)
        self.assertIs(b.stage_selected_path.__func__, Bridge.stage_selected_path)
        self.assertNotIn('_gdn', b.__dict__); self.assertNotIn('_bole_gdn_extension', b.__dict__)

    def test_abort_only_drops_failed_private_bookkeeping(self):
        ctx = NS(phase='FORWARD', captures={'control': object()})
        ctl = S.Controller.__new__(S.Controller)
        ctl.C=C; ctl.E=NS(BUS=NS(get=lambda: None)); ctl.staging=False; ctl.active=dict(ctx=ctx)
        with self.assertRaises(ValueError):
            ctl.abort(ctx)
        captured = ctx.captures; ctx.phase='FAILED_NO_PUBLICATION'
        ctl.abort(ctx)
        self.assertIsNone(ctl.active); self.assertIs(ctx.captures, captured)

    def test_forward_has_no_all_three_state_commit(self):
        tree = ast.parse((P/'gdn_service_seam.py').read_text())
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == '_gdn')
        calls = [x.func.attr for x in ast.walk(fn) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)]
        self.assertNotIn('commit', calls); self.assertNotIn('execute_commit', calls); self.assertNotIn('stack', calls)

    def test_cold_default_off_and_help(self):
        env = {k:v for k,v in os.environ.items() if not k.startswith('BOLE_')}
        for name in ('gdn_service_seam.py', 'consume_gdn_service.py'):
            for mode in ([], ['--help']):
                value = subprocess.run([sys.executable, '-I', '-B', str(P/name), *mode],
                    env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(value.returncode, 0, value.stderr)
                if not mode:
                    self.assertIs(json.loads(value.stdout)['enabled'], False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
