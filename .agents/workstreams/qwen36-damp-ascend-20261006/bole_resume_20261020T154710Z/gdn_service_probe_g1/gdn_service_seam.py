"""Default-OFF service-only GDN proposal. No launch/admission/publication code."""
import argparse
import json
import os
import sys
import types


def disabled():
    return dict(enabled=False, NPU=False, prepared_only=True,
                actual_service_executed=False, model_ready=False, formal_success=False)


def install(bridge, live, C, m, *, extension_ref, service_source_ref=None,
            software_gate_ref=None, arm_verified=False):
    if os.environ.get('BOLE_GDN_SERVICE_FUSION_ENABLE') != '1':
        return disabled()
    C.need(arm_verified is True and os.environ.get('BOLE_GDN3_TRITON_ENABLE') == '1',
           'existing MAIN-admitted service owner and explicit component opt-in')
    gate_ref = m['files']['gdn_service_gate.py']; C.checked(gate_ref)
    name = '_bole_gdn_service_gate'
    if name not in sys.modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, gate_ref['path'])
        module = importlib.util.module_from_spec(spec); sys.modules[name] = module
        spec.loader.exec_module(module)
    G = sys.modules[name]
    C.need(C.ref(G.__file__) == gate_ref and C.ref(__file__) == m['files']['gdn_service_seam.py'],
           'exact private extension modules')
    x, H, replay, qualification = G.qualify(C, m, extension_ref, service_source_ref, software_gate_ref)
    E = sys.modules.get('model_entry')
    C.need(E is not None and C.ref(E.__file__) == m['files']['model_entry.py'] and
           E.BUS.get() is None and len(bridge.saved) == 64 and bridge._bole_live is live and
           bridge._gdn.__func__ is E.Bridge._gdn and
           bridge.stage_selected_path.__func__ is E.Bridge.stage_selected_path and
           '_bole_gdn_extension' not in bridge.__dict__ and
           C.ref(bridge.K.__file__) == m['files']['core112.py'] and
           bridge.t.npu.is_initialized() and bridge.t.npu.matmul.allow_hf32 is False,
           'fresh source-bound V6 service bridge inside existing owner')
    candidate = H.load_module(replay['candidate']['wrapper'], '_bole_service_gdn3_candidate')
    controller = Controller(bridge, live, C, E, m, x, extension_ref, qualification, candidate, replay)
    controller.install()
    return controller


class Controller:
    def __init__(self, bridge, live, C, E, m, x, ref, qualification, candidate, replay):
        self.bridge, self.live, self.C, self.E = bridge, live, C, E
        self.m, self.x, self.ref, self.qualification, self.candidate = m, x, ref, qualification, candidate
        self.mode = m['gdn_service_extension']['mode']; self.core = bridge.K
        self.original_gdn = bridge._gdn; self.original_stage = bridge.stage_selected_path
        self.active = None; self.staging = False; self.installed = False
        self.saved = {}
        # Candidate refs are the exact successful replay pair (not a caller backend).
        self.refs = dict(implementation=replay['candidate']['wrapper'], kernels=replay['candidate']['kernels'],
                         reference=m['files']['core112.py'])

    def install(self):
        try:
            for name, fn in (('_gdn', _gdn), ('stage_selected_path', _stage)):
                self.saved[name] = (name in self.bridge.__dict__, self.bridge.__dict__.get(name))
                setattr(self.bridge, name, types.MethodType(fn, self.bridge))
            self.bridge._bole_gdn_extension = self
            self.installed = True
        except BaseException:
            for name, (had, value) in self.saved.items():
                if had:
                    setattr(self.bridge, name, value)
                else:
                    self.bridge.__dict__.pop(name, None)
            raise

    def begin_row(self, ctx, layer):
        self.C.need(self.installed and not self.staging and self.live.current() == ctx.owner and
                    ctx.phase == 'FORWARD' and ctx.mode == 'TREE', 'current exclusive TREE owner')
        if self.active is None:
            self.active = dict(ctx=ctx, owner=ctx.owner, seen=set(), selected=set())
        self.C.need(self.active['ctx'] is ctx and layer not in self.active['seen'],
                    'one actual GDN row per layer/context')
        self.active['seen'].add(layer)

    def abort(self, ctx):
        self.C.need(self.E.BUS.get() is None and not self.staging and
                    (self.active is None or self.active['ctx'] is ctx), 'exclusive private abort boundary')
        if self.active is not None:
            self.C.need(ctx.phase.startswith('FAILED'), 'only failed/unpublished context abort')
            self.active = None

    def restore(self):
        self.C.need(self.installed and self.E.BUS.get() is None and not self.staging and
                    self.active is None and self.bridge.K is self.core and
                    self.bridge._bole_gdn_extension is self and
                    self.bridge._gdn.__func__ is _gdn and
                    self.bridge.stage_selected_path.__func__ is _stage,
                    'restore only owned idle service seam')
        for name, (had, value) in self.saved.items():
            if had:
                setattr(self.bridge, name, value)
            else:
                delattr(self.bridge, name)
        del self.bridge._bole_gdn_extension
        self.installed = False


def _gdn(self, b, obj, mixed_qkv, ba, aa, output):
    ctl = self._bole_gdn_extension; ctx = ctl.E.BUS.get(); t = self.t
    if ctx is not None and ctx.mode == 'AR':
        return ctl.original_gdn(b, obj, mixed_qkv, ba, aa, output)
    ctl.C.need(ctx is not None, 'actual service context before GDN override')
    ctl.begin_row(ctx, b['index']); ctx.visit(b['index'], 'gdn')
    ctl.C.need(mixed_qkv.shape == (3, 2560) and output.shape == (3, 12, 128), 'unchanged projected ABI')
    owner = ctx.owner; slot = self._physical_slot(b, owner)
    ctl.C.need(0 <= slot < b['state'].shape[0] and slot < b['conv'].shape[0], 'owned physical slot')
    tree = self.N.NodeRows(owner.request, owner.generation, slot, owner.length, ctx.tokens).metadata(self.M.Tree)
    owners = (self.V.Owner(owner.request, owner.generation, slot, owner.length, owner.version),)
    trial = self.V.prepare(t, tree, owners, b['conv'], mixed_qkv, width=4, node_budget=3)
    weight = obj.conv1d.weight.view(obj.conv1d.weight.size(0), obj.conv1d.weight.size(2))
    row = dict(kind='gdn', phase='BEFORE_NATIVE_TREE_CONV', conv_trial=trial,
               raw_projected=mixed_qkv.clone(), a=aa.clone(), b=ba.clone(), weight=weight.clone(),
               activation=bool(obj.activation))
    ctx.captures[b['index']] = row
    op = t.ops._C_ascend.npu_causal_conv1d_custom.default
    ctl.C.need(op is self.calibrated_conv_op, 'unchanged calibrated native convolution object')
    convolved, tail = self.N.native_tree_conv(t, self.C, self.V, self.reader, self.actual118c,
        trial, weight, obj.conv1d.bias, activation=bool(obj.activation), op=op,
        actual_abi=self.conv_abi, arm_verified=True)
    row.update(actual_convolved=convolved.clone(), actual_conv_tail=tail.clone())
    q, k, v = obj.rearrange_mixed_qkv(convolved); mod = b['_original_module']
    g, beta = mod.DeviceOperator.fused_gdn_gating(obj.A_log, aa, ba, obj.dt_bias)
    q = mod.l2norm_fwd(q); k = mod.l2norm_fwd(k)
    ctl.C.need(q.shape == k.shape == (1, 3, 4, 128) and v.shape == (1, 3, 12, 128) and
                g.shape == beta.shape == (1, 3, 12), 'unchanged normalization/GQA/gate ABI')
    qh = q.permute(0, 2, 1, 3).float().repeat_interleave(3, dim=1) * (128**-.5)
    kh = k.permute(0, 2, 1, 3).float().repeat_interleave(3, dim=1)
    vh = v.permute(0, 2, 1, 3).float(); bh = beta.transpose(1, 2).float(); gamma = g.transpose(1, 2).float().exp()
    ctl.C.need(bool(t.isfinite(gamma).all() and (gamma > 0).all()), 'original positive decay domain')
    state = self.N.gdn_canonical_view(t, b['state'], layout='slot,H,Dv,Dk')[slot:slot+1].clone()
    ancestor = t.tensor([[False, False, False], [True, False, False], [True, False, False]], device=q.device)
    row.update(state=state, keys=kh, normalized_inputs=(qh, kh, vh, bh, gamma), phase='BEFORE_TREE_GDN')
    if ctl.mode == 'candidate':
        result = ctl.candidate.execute_verify(t, qh, kh, vh, bh, gamma, state, ancestor, 1,
            enabled=True, arm_verified=True, C=ctl.C, source_refs=ctl.refs, tile_v=32)
        value, factors, receipt = result['output'], result['factors'], result['receipt']
    else:
        value, factors = ctl.core.verify(t, qh, kh, vh, bh, gamma, state, ancestor, 1)
        receipt = dict(reference=ctl.m['files']['core112.py'], original_math=True)
    ctl.C.need(bool(t.isfinite(value).all() and t.isfinite(factors[0]).all() and t.isfinite(factors[1]).all()),
                'finite complete O/P/U before output boundary')
    output.copy_(value.permute(0, 2, 1, 3).squeeze(0).to(output.dtype))
    row.update(factors=factors, precast_output=value.clone(), output=output.clone(), phase='TREE_GDN_COMPLETE',
        gdn_extension=dict(schema='bole.service-private-gdn/v1', source=ctl.ref, mode=ctl.mode,
            owner=owner, layer=b['index'], prerequisites=ctl.qualification, forward=receipt,
            selected=None, actual_node_states_omitted=True, persistent_cache_written=False,
            model_ready=False, formal_success=False))


class _CommitView:
    """Per-call instance facade, never a module patch or cache publisher."""
    def __init__(self, controller, ctx, terminal):
        self.ctl, self.ctx, self.terminal = controller, ctx, terminal
        self.rows = {id(row['state']): (layer, row) for layer, row in ctx.captures.items()
                     if row['kind'] == 'gdn'}

    def commit(self, t, state, k, factors, inclusive, terminal):
        ctl = self.ctl
        ctl.C.need(ctl.staging and ctl.live.current() == self.ctx.owner and terminal == self.terminal and
                    id(state) in self.rows, 'owned private selected commit')
        layer, row = self.rows[id(state)]
        ctl.C.need(row['state'] is state and row['keys'] is k and row['factors'] is factors and
                    layer not in ctl.active['selected'], 'exact layer/state/key/factor object join once')
        if ctl.mode == 'candidate':
            result = ctl.candidate.execute_commit(t, state, k, factors, terminal, enabled=True,
                arm_verified=True, C=ctl.C, source_refs=ctl.refs, tile_k=32, tile_v=32)
            private, receipt = result['selected_state'], result['receipt']
        else:
            private = ctl.core.commit(t, state, k, factors, inclusive, terminal)
            receipt = dict(reference=ctl.m['files']['core112.py'], original_math=True)
        arena = ctl.bridge.bindings[layer]['state']
        ctl.C.need(private.dtype == t.float32 and private.shape == state.shape and
                    bool(t.isfinite(private).all()) and
                    private.untyped_storage().data_ptr() not in
                    {arena.untyped_storage().data_ptr(), state.untyped_storage().data_ptr(),
                     k.untyped_storage().data_ptr(), factors[0].untyped_storage().data_ptr(),
                     factors[1].untyped_storage().data_ptr()},
                    'actual private canonical FP32 selected state, never live arena/preimage')
        row['gdn_extension']['selected'] = dict(terminal=terminal, receipt=receipt,
            canonical_layout='B,H,Dk,Dv', native_after_layout='H,Dv,Dk', private=True,
            source_inputs_written=False, persistent_cache_written=False, scheduler_committed=False)
        ctl.active['selected'].add(layer)
        return private


def _stage(self, ctx, terminal, *, current_owner):
    ctl = self._bole_gdn_extension
    ctl.C.need(ctl.E.BUS.get() is None and not ctl.staging and self.K is ctl.core and
                ctl.active is not None and ctl.active['ctx'] is ctx and
                ctl.active['owner'] == ctx.owner == current_owner() == ctl.live.current() and
                getattr(current_owner, '__self__', None) is ctl.live and
                getattr(current_owner, '__func__', None) is type(ctl.live).current and
                ctx.phase == 'FORWARD_COMPLETE_NOT_QUALIFIED' and type(terminal) is int and terminal in (0, 1, 2) and
                ctl.active['seen'] == {i for i in range(64) if i % 4 != 3},
                'complete owned service O/P/U before one selected-path stage')
    facade = _CommitView(ctl, ctx, terminal); ctl.staging = True; self.K = facade; primary = None
    try:
        proposal = ctl.original_stage(ctx, terminal, current_owner=current_owner)
        ctl.C.need(ctl.active['selected'] == ctl.active['seen'] and len(proposal['writes']) == 128 and
                    proposal['published'] is False, 'all48 selected states, original complete128-write plan')
        return proposal
    except BaseException as error:
        primary = error; ctx.phase = 'FAILED_NO_PUBLICATION'; ctx.first_fault = repr(error)
        raise
    finally:
        owned = self.K is facade
        if owned:
            self.K = ctl.core
        ctl.staging = False
        # The context retains actual factors/receipts; no controller pins all frames.
        ctl.active = None
        if not owned:
            error = ValueError('private commit facade ownership changed; unknown replacement not overwritten')
            if primary is not None:
                primary.add_note(str(error))
            else:
                raise error


def main():
    argparse.ArgumentParser(description=__doc__, allow_abbrev=False).parse_args()
    print(json.dumps(disabled()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
