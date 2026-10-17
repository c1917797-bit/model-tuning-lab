"""C1 diagnostic lifecycle adapter. No geometry relaxation or qualification."""
import ast
import contextvars
import functools
import hashlib
import inspect
import os
from dataclasses import dataclass, field
from pathlib import Path

ENABLE = 'DL_NATIVE_LIFECYCLE_ADAPTER_ENABLE'
ACTIVE = contextvars.ContextVar('dl_native_lifecycle_core', default=None)
PINS = {
    'mirror': '32dedd1fae3f93e6dd8a9b6a3d23229448b30b022b9c3182b931e5f7c1f76677',
    'helper': '913fa9514bc0509babaf81565ab46fa4b746967e7c0deb7d06849f4d42672465',
    'primitives': '1b9a2e53ce137f319ca5939be6e21fa293735edd363cdc37f7b438626e985470',
    'gdn': 'd6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816',
    'runner': '94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968',
    'clear': '4dfc30c479f8a740a965174a4f56706c4c3a95362dd77d2e708cdbaf1c9873d4',
    'integration': 'f79c59a28bc626e8efe583baf0c8adf879cc87649c81f31a0e6fbe1cc88307a8',
    'runtime': '785a9ae27c98178daa9e9a56071560cec3a2e717a41a968872311093db603316',
    'chunk': '6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5',
    'base_runner': '6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666',
}


class Refusal(RuntimeError):
    pass


def need(value, message):
    if not value:
        raise Refusal(message)


def same_key(a, b):
    return a is not None and a[0] == b[0] and a[1] is b[1]


def ids(values):
    need(type(values) in (list, tuple, set) and all(type(x) is str for x in values), 'native CPU request IDs')
    need(len(values) == len(set(values)), 'unique request IDs')
    return tuple(values)


def batch_rows(r):
    """Already-native CPU row map; an unscheduled row is not retirement."""
    rows = tuple(r.input_batch.req_ids)
    mapping = dict(r.input_batch.req_id_to_index)
    need(all(x is None or type(x) is str for x in rows), 'actual CPU request row names')
    active = tuple(x for x in rows if x is not None)
    need(len(active) == len(set(active)) and set(mapping) == set(active), 'exact native CPU input_batch map')
    need(all(type(i) is int and 0 <= i < len(rows) and rows[i] == rid for rid, i in mapping.items()),
         'post-native persistent row mapping')
    return mapping


@dataclass(eq=False)
class Generation:
    request_id: str
    request: object
    ordinal: int
    retired: bool = False
    reset_complete: set = field(default_factory=set)


@dataclass(eq=False)
class Intent:
    generation: Generation
    group: int
    slot: int
    step: object
    fresh: bool


class Manager:
    """Retains strong native objects; called even for finished-only updates."""
    def __init__(self, runner):
        self.runner = runner
        self.live = {}
        self.retired = []
        self.leases = {}
        self.ordinal = 0
        self.poison = None
        self.updating = False
        self.events = []

    def healthy(self):
        need(self.poison is None, 'lifecycle poisoned: ' + str(self.poison))

    def update(self, original, scheduler):
        self.healthy()
        need(not self.updating, 'no reentrant native update')
        self.updating = True
        try:
            r = self.runner
            before = dict(r.requests)  # Strong CPU objects; no tensor values.
            before_rows = batch_rows(r)
            finished = ids(scheduler.finished_req_ids)
            new = ids([x.req_id for x in scheduler.scheduled_new_reqs])
            need(not ids(scheduler.scheduled_cached_reqs.resumed_req_ids), 'resumed history not qualified')
            for rid, gen in self.live.items():
                need(before.get(rid) is gen.request, 'native live strong request drift before update')
            need(set(before) == set(self.live), 'install before first real request; no unknown existing history')
            need(all(rid not in before or rid in finished for rid in new), 'streaming/in-place new session unsupported')
            state = getattr(r, '_deltalog018_state', None)
            current = None if state is None else state['current']
            need(current is None or current.get('forward_complete') is True, 'no retirement before actual forward finish')
            result = original(r, scheduler)
            after = dict(r.requests)
            after_rows = batch_rows(r)
            for rid in finished:
                gen = self.live.get(rid)
                if gen is None:
                    continue  # No old log owner to retire; not an invented lease.
                need(rid not in after or rid in new and after[rid] is not gen.request,
                     'actual finished removal/new strong object required')
                need(rid not in after_rows or rid in new and after[rid] is not gen.request,
                     'actual old input_batch row removed or source-proven new generation rebound')
                gen.retired = True
                self.retired.append(gen)
                del self.live[rid]
                if state is not None:
                    for owners in state['owners'].values():
                        for slot, key in list(owners.items()):
                            if same_key(key, (rid, gen.request)):
                                del owners[slot]  # Private logs invalid, NEVER flush to base.
                self.events.append(dict(event='native-finished-removal', request_id=rid, generation=gen.ordinal,
                                        finished_marker=True, old_request_removed_or_replaced=True,
                                        old_input_batch_removed_or_rebound=True,
                                        prior_row=before_rows.get(rid), current_row=after_rows.get(rid),
                                        same_id_new_object=rid in new, EOS_observed=None))
            for rid, gen in self.live.items():
                need(after.get(rid) is gen.request, 'absence from native requests is not proved retirement')
            for data in scheduler.scheduled_new_reqs:
                rid = data.req_id
                request = after.get(rid)
                need(request is not None and rid not in self.live and request is not before.get(rid),
                     'actual new strong CachedRequestState')
                need(data.num_computed_tokens == request.num_computed_tokens == 0,
                     'new external/prefix-initialized state not qualified')
                self.ordinal += 1
                self.live[rid] = Generation(rid, request, self.ordinal)
                self.events.append(('new-object', rid, self.ordinal))
            need(set(after) == set(self.live), 'no undeclared request addition/removal')
            return result  # Preserve actual native deferred return value unchanged.
        except BaseException as error:
            self.poison = repr(error)
            raise
        finally:
            self.updating = False

    def generation(self, key):
        self.healthy()
        gen = self.live.get(key[0])
        need(gen is not None and gen.request is key[1] and not gen.retired,
             'same actual live strong generation')
        return gen

    def admit(self, previous, keys, slots, nd, has_initial, step, gid):
        self.healthy()
        need(len(keys) == len(slots) == 1 and nd in (0, 1), 'C1 only; batching not extended')
        need(type(gid) is int and gid >= 0 and type(slots[0]) is int and slots[0] >= 0, 'actual group/slot')
        need(len(has_initial) == 1 - nd and all(type(x) is bool for x in has_initial), 'source CPU initial mask')
        key, slot = keys[0], slots[0]
        gen = self.generation(key)
        old = self.leases.get((gid, slot))
        out = dict(previous)
        if nd or has_initial[0]:
            need(old is gen and same_key(previous.get(slot), key), 'decode/continuation same generation/group/slot')
            required = {p for p, row in step['state']['layers'].items() if row['group'] == gid}
            need(required and required <= gen.reset_complete, 'original native reset/writeback must complete before state is live')
            fresh = False
        else:
            required = {p for p, row in step['state']['layers'].items() if row['group'] == gid}
            need(required and not (required & gen.reset_complete), 'fresh false cannot reset a live existing group')
            need(old is None or old.retired, 'fresh reuse requires actual previous removal, not absence')
            need(previous.get(slot) is None, 'unretired mirror owner cannot be overwritten')
            self.leases[(gid, slot)] = gen
            fresh = True
        out[slot] = key
        intent = Intent(gen, gid, slot, step, fresh)
        plans = step.setdefault('_native_lifecycle_plans', {})
        need(gid not in plans, 'one group intent per actual metadata build')
        plans[gid] = intent
        self.events.append(('reset-intent' if fresh else 'same-history', key[0], gid, slot))
        return out


class Bridge:
    """Actual callbacks, but installer stays OFF without external actual admission."""
    def __init__(self, mirror, integration, synchronize):
        self.M = mirror
        self.W = integration
        self.synchronize = synchronize

    def manager(self, r):
        value = getattr(r, '_native_lifecycle_adapter', None)
        if value is None:
            value = Manager(r)
            r._native_lifecycle_adapter = value
        need(value.runner is r, 'same strong runner')
        return value

    def lifecycle(self, previous, keys, slots, nd):
        step = self.M._BUILD.get()
        need(step is not None and step['runner']._deltalog018_state is step['state'], 'real original builder scope')
        # Different groups can have equal numeric slots. Do NOT select by slots.
        gid = step.get('_native_lifecycle_build_gid')
        need(gid is not None and gid in step['tables'] and tuple(step['tables'][gid]['values']) == tuple(slots),
             'source-bound current builder gid, never infer from equal slot IDs')
        return self.manager(step['runner']).admit(previous, keys, slots, nd,
                tuple(x > 0 for x in step['computed'][nd:]), step, gid)

    def context(self, layer, meta):
        r = self.W.runner_for(layer)
        need(r is not None, 'actual registered runner lookup required')
        self.M.guard(r)
        receipt = getattr(meta, '_deltalog018_cpu_receipt', None)
        state = r._deltalog018_state
        need(receipt is not None and receipt['state'] is state and state['current'] is receipt['step']
             and receipt['metadata'] is meta and (layer.prefix, 'core') in receipt['seen'],
             'original real core receipt consumed before lifecycle adapter')
        step, gid = receipt['step'], receipt['group']
        plan = step.get('_native_lifecycle_plans', {}).get(gid)
        need(plan is not None and plan.step is step and plan.generation is self.manager(r).generation(step['keys'][0]),
             'actual current group/generation intent')
        need(state['layers'][layer.prefix]['layer'] is layer and state['layers'][layer.prefix]['group'] == gid,
             'actual same strong layer/group')
        need(meta.num_prefills + meta.num_decodes == 1 and meta.num_decodes in (0, 1), 'C1 actual metadata')
        return dict(manager=self.manager(r), layer=layer, meta=meta, plan=plan,
                    clear_returned=False, chunk_returned=False, initial=None)

    def before_prefill(self, torch, legacy, layer, meta, aux, emit=None):
        c = ACTIVE.get()
        need(c is not None and c['layer'] is layer and c['meta'] is meta, 'one actual prefill scope')
        plan = c['plan']
        cpu = meta._deltalog018_cpu_receipt['cpu']
        need(cpu.prefill == (plan.slot,) and cpu.prefill_has_initial == (not plan.fresh,),
             'same source-bound actual CPU prefill mask and selected slot')
        if plan.fresh:
            legacy._reset_selected(aux, meta.prefill_state_indices)  # Private aux ONLY.
        else:
            legacy._flush_slots(torch, layer, aux, meta.prefill_state_indices, 'same-generation-prefill-only')
        (emit or (lambda *a, **kw: None))(
            'fresh_aux_dropped_reset_pending' if plan.fresh else 'same_generation_prefill_materialized',
            prefix=layer.prefix, prefill_slots=1, native_reset_complete=False,
            group=plan.group, slot=plan.slot, generation=plan.generation.ordinal)

    def clear(self, original, initial, mask):
        c = ACTIVE.get()
        if c is None:
            return original(initial, mask)
        need(not c['clear_returned'] and mask is c['meta'].prefill_has_initial_state,
             'sole original native clear with exact original mask object')
        result = original(initial, mask)
        c['initial'], c['clear_returned'] = initial, True
        return result

    def chunk(self, original, *args, **kwargs):
        c = ACTIVE.get()
        if c is None:
            return original(*args, **kwargs)
        need(c['clear_returned'] and not c['chunk_returned'] and kwargs.get('initial_state') is c['initial']
             and kwargs.get('output_final_state') is True
             and kwargs.get('prebuilt_meta') is c['meta'].non_spec_prefill_metadata.chunk,
             'original chunk consumes same native-cleared initial copy and prebuilt metadata')
        result = original(*args, **kwargs)
        need(type(result) is tuple and len(result) == 2 and result[1] is not None, 'actual native output/final-state ABI')
        c['chunk_returned'] = True
        return result

    def execute(self, adapted, torch, legacy, gdn, specialized, original, layer, mixed_qkv, b, a, core, emit=None):
        meta = gdn.get_forward_context().attn_metadata[layer.prefix]
        context = self.context(layer, meta)
        need(ACTIVE.get() is None, 'nonreentrant actual core')
        token = ACTIVE.set(context)
        try:
            result = adapted(torch, legacy, gdn, specialized, original, layer, mixed_qkv, b, a, core, emit=emit)
            if meta.num_prefills:
                need(context['clear_returned'] and context['chunk_returned'], 'native clear/chunk cannot be skipped')
                # DIAGNOSTIC ONLY. Clear, chunk writeback and original post-aux
                # reset must actually complete, not merely be enqueued. No timing
                # or no-sync production qualification is claimed by this adapter.
                self.synchronize(torch)
                context['plan'].generation.reset_complete.add(layer.prefix)
                context['manager'].events.append((
                    'native-reset-complete' if context['plan'].fresh else 'native-continuation-complete',
                    layer.prefix, context['plan'].generation.ordinal))
            return result
        except BaseException as error:
            context['manager'].poison = repr(error)
            raise
        finally:
            ACTIVE.reset(token)


HELPER_OLD = '''        legacy._flush_slots(torch, self, aux, ids, "prefill_initial_state_only")
        emit("prefill_materialized", prefix=self.prefix,
               prefill_slots=int(ids.numel()), decode_slots_materialized=0)'''
HELPER_NEW = '        _LIFECYCLE.before_prefill(torch, legacy, self, meta, aux, emit=emit)'
BUILD_OLD = "  owners=lifecycle(step['state']['owners'].get(gid,{}),step['keys'],t['values'],nd);step['state']['owners'][gid]=owners"
BUILD_NEW = "  step['_native_lifecycle_build_gid']=gid\n" + BUILD_OLD


def verified_source(module, name):
    source = Path(module.__file__).read_bytes()
    need(hashlib.sha256(source).hexdigest() == PINS[name], 'whole original ' + name + ' source')
    return source.decode('utf8')


def helper_source(module):
    text = verified_source(module, 'helper')
    need(text.count(HELPER_OLD) == 1 and HELPER_NEW not in text, 'one exact prefill scheduling/event seam')
    adapted = text.replace(HELPER_OLD, HELPER_NEW)
    need(adapted.replace(HELPER_NEW, HELPER_OLD) == text, 'whole helper scheduling inverse')
    return adapted


def clone_helper(module, bridge):
    """Exactly one scheduling call changes; original helper math is retained."""
    tree = ast.parse(helper_source(module))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'execute_mixed_core']
    need(len(nodes) == 1, 'one actual helper entry')
    scope = dict(vars(module), _LIFECYCLE=bridge)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(module.__file__)+'#lifecycle-only', 'exec'), scope)
    return scope['execute_mixed_core']


def clone_build(module):
    """Set exact native-derived gid around old lifecycle call, never slot infer."""
    text = verified_source(module, 'mirror')
    need(text.count(BUILD_OLD) == 1 and "step['_native_lifecycle_build_gid']=gid" not in text, 'exact actual builder gid seam')
    adapted = text.replace(BUILD_OLD, BUILD_NEW)
    need(adapted.replace(BUILD_NEW, BUILD_OLD) == text, 'whole mirror scheduling inverse')
    return adapted


def clone_mirror_install(module):
    """Compile only install, retaining original module globals/contextvars.

    Not called on an already installed mirror. No class is modified by this
    preparation function; invoking the returned native installer is deferred.
    """
    tree = ast.parse(clone_build(module))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'install']
    need(len(nodes) == 1, 'one actual mirror installer')
    code = compile(ast.Module(body=nodes, type_ignores=[]), str(module.__file__)+'#lifecycle-gid-only', 'exec')
    scope = dict(vars(module))
    exec(code, scope)
    # Function code must retain M globals (not a second contextvar universe).
    from types import FunctionType
    made = scope['install']
    return FunctionType(made.__code__, vars(module), made.__name__, made.__defaults__, made.__closure__)


def bind_native_update(R, bridge):
    """Build wrapper, without installing it or invoking native initialization."""
    original = R.__dict__.get('_update_states')
    need(original is not None and original.__qualname__ == 'NPUModelRunner._update_states',
         'actual Ascend declaring method, not inherited/previously wrapped')
    need(hashlib.sha256(Path(inspect.getsourcefile(original)).read_bytes()).hexdigest() == PINS['runner'],
         'whole actual Ascend runner defining update source')
    need(tuple(inspect.signature(original).parameters) == ('self', 'scheduler_output'),
         'actual native update ABI')
    @functools.wraps(original)
    def update(r, scheduler_output):
        bridge.M.guard(r)
        return bridge.manager(r).update(original, scheduler_output)
    return original, update


def prepared_callbacks(M, W, H, L, gdn, runner, chunk_module, synchronize):
    """Source-bound callbacks for a later independently admitted integration.

    This performs NO mutation of native modules/classes, no import/HAL probe,
    no geometry grant and no NPU call. Existing source checks and alias guard
    remain in the compiled mirror installer. Installation remains blocked below
    until a real selected-footprint admission API exists.
    """
    for module, name in ((M, 'mirror'), (W, 'integration'), (H, 'helper'),
                         (L, 'primitives'), (gdn, 'gdn'), (runner, 'runner'),
                         (chunk_module, 'chunk')):
        verified_source(module, name)
    clear, chunk = gdn.clear_ssm_states, gdn.chunk_gated_delta_rule
    need(hashlib.sha256(Path(inspect.getsourcefile(clear)).read_bytes()).hexdigest() == PINS['clear'],
         'actual original native clear defining source')
    need(chunk_module.chunk_gated_delta_rule is chunk, 'same actual official chunk callable alias')
    R = runner.NPUModelRunner
    need(R.__bases__ == (runner.GPUModelRunner,), 'same actual native direct GPU base class')
    inherited = runner.GPUModelRunner.__dict__.get('_update_states')
    need(inherited is not None and inherited.__qualname__ == 'GPUModelRunner._update_states'
         and hashlib.sha256(Path(inspect.getsourcefile(inherited)).read_bytes()).hexdigest() == PINS['base_runner'],
         'actual super update/finished removal source, not an invented base')
    need(not getattr(R, '_deltalog018_installed', False) and not getattr(R, '_deltalog023_wired', False),
         'prepare before mirror and actual integration hooks')
    bridge = Bridge(M, W, synchronize)
    adapted_helper = clone_helper(H, bridge)
    original_update, update = bind_native_update(R, bridge)
    @functools.wraps(clear)
    def clear_wrapper(initial_state, has_initial_state):
        return bridge.clear(clear, initial_state, has_initial_state)
    @functools.wraps(chunk)
    def chunk_wrapper(*a, **kw):
        return bridge.chunk(chunk, *a, **kw)
    @functools.wraps(H.execute_mixed_core)
    def execute(*a, **kw):
        return bridge.execute(adapted_helper, *a, **kw)
    return dict(bridge=bridge, mirror_install=clone_mirror_install(M),
                lifecycle=bridge.lifecycle, original_update=original_update,
                update=update, clear=clear_wrapper, chunk=chunk_wrapper,
                execute=execute, actual_install=False, qualification=False)


def install(*args, **kwargs):
    """Preparation cannot install itself: real all64 geometry adapter is missing."""
    if os.environ.get(ENABLE) != '1':
        return dict(installed=False, default_OFF=True, qualification=False)
    raise Refusal('PENDING actual all64/ND/commit geometry admission and source-bound integration; no install authority')
