"""Opt-in source draft: bounded observations, never numerical/performance admission.

No torch import, device setup, launcher, mathematical replacement, native state
write, or observer installation occurs on the disabled factory path.  A blocking
D2H observation can change scheduling: its results cannot exclude a race merely
because the repeatability difference disappears under observation.
"""
import hashlib
import json
import os
from pathlib import Path

FLAG = 'BOLE_NATIVE_BOUNDARY_PROBE_ENABLE'
SCHEMA = 'bole.native-prefill-boundary-repeatability/v1'
GDN_LAYERS = tuple(i for i in range(64) if i % 4 != 3)
PHASES = ('post_native_prefill_registered', 'calibration_before',
          'calibration_after', 'initial_mtp_before', 'initial_mtp_after')
RAW_SHAPES = {
    'layer0_core_output': (131, 12, 128),
    'layer0_gated_norm': (131 * 12, 128),
    'layer0_out_projection': (131, 5120),
    'layer0_post_norm_hidden': (131, 5120),
    'layer0_post_norm_residual': (131, 5120),
    'layer0_mlp': (131, 5120),
    'layer1_mixed_qkv': (131, 2560),
    'layer1_b': (131, 12),
    'layer1_a': (131, 12),
}
RAW_CAP = 836352  # Exactly two generations of the nine last-eight-token slices.
META_CAP = 512 * 1024
DEVICE_READ_CAP = 512 * 2**20
OTHER_HEADROOM = 64 * 1024
DECLARATION = dict(schema=SCHEMA, enabled=True, arm='ON', generations=2,
    input_tokens=131, output_tokens=8, raw_actual_token_slice=[123, 131],
    raw_names=list(RAW_SHAPES), phases=list(PHASES), native_gdn_layers=48,
    hash_native0_inputs=True,
    raw_bytes_cap_per_rank=RAW_CAP, metadata_bytes_cap_per_rank=META_CAP,
    device_read_bytes_cap_per_rank=DEVICE_READ_CAP,
    existing_other_cap_bytes=3 * 2**20, other_headroom_bytes=OTHER_HEADROOM,
    formal_performance=False, numerical_qualified=False)


def need(value, why):
    if not value:
        raise ValueError(why)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       allow_nan=False, ensure_ascii=True) + '\n').encode()


def bounded_text(value, limit):
    return type(value) is str and len(json.dumps(value, ensure_ascii=True)) <= limit + 2


def select(environ, declaration):
    flag = environ.get(FLAG)
    if flag in (None, '', '0'):
        need(declaration is None, 'declared boundary probe requires its explicit flag')
        return None
    need(flag == '1' and type(declaration) is dict and
         canonical(declaration) == canonical(DECLARATION),
         'exact typed boundary source declaration and explicit opt-in')
    return declaration


def retained_files(C, manifest, rank):
    """Called by the amended g3 accounting; no import or observation recursion."""
    root = Path(manifest['model_receipt_root']) / ('BOUNDARY-R%d' % rank)
    if not root.exists():
        return set()
    C.need(root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)),
           'ordinary owned boundary evidence directory')
    files = set(root.iterdir())
    C.need(len(files) <= 160 and all(p.is_file() and not p.is_symlink() for p in files),
           'bounded direct ordinary boundary files, including incomplete writes')
    return files


def terminal_accounting(C, manifest):
    """Read-only host check after actual final worker snapshots; no torch import."""
    import g3_budget as B
    import g2_contract as G
    need(C.ref(__file__) == manifest['files']['boundary_probe_v1.py'] and
         C.ref(B.__file__) == manifest['files']['g3_budget.py'] and
         C.ref(G.__file__) == manifest['files']['g2_contract.py'] and
         canonical(manifest['boundary_probe_profile']) == canonical(DECLARATION),
         'exact terminal accounting source and diagnostic declaration')
    need(B.OTHER == 3 * 2**20 and G.METADATA_CAP == 64 * 2**20 and G.RAW_CAP == 2**30,
         'unchanged original terminal accounting caps')
    source = C.ref(Path(manifest['root']) / 'SOURCE_BOUND.json')
    need(C.obj(source) == manifest, 'actual terminal bound source')
    rows = []
    for rank in range(4):
        value = B.actual(C, manifest, rank)
        need(value['charges']['other'] <= B.OTHER and
             value['bytes'] + 8 * 2**20 <= G.METADATA_CAP and
             value['bytes'] + G.FRAME_LOGICAL_CAP + G.FRAME_WIRE_CAP +
             G.CHECKPOINT_CAP <= G.RAW_CAP,
             'actual terminal retained files remain inside all original caps')
        path = Path(manifest['model_receipt_root']) / ('BOUNDARY-R%d' % rank) / 'G2-COMPLETE.json'
        complete_ref = C.ref(path)
        complete = C.obj(complete_ref)
        need(complete['schema'] == SCHEMA and complete['source_sha256'] == source['sha256'] and
             complete['rank'] == rank and complete['generation'] == 2 and complete['event'] == 'COMPLETE' and
             complete['numerical_qualified'] is False and complete['formal_performance'] is False and
             complete['record']['hooks_removed'] is True and complete['record']['observation_complete'] is True
             and complete['record']['projection_observer_restored'] is True
             and complete['record']['projection_records'] == 2
             and len(complete['record']['references']) == 149,
             'actual per-rank complete observation with restored observer hooks')
        rows.append(dict(rank=rank, charges=value['charges'], bytes=value['bytes'],
                         boundary_complete_ref=complete_ref))
    return dict(schema='bole.boundary-terminal-budget/v1', source=source, ranks=rows,
        after_actual_final_worker_snapshots=True, original_other_cap=B.OTHER,
        original_metadata_cap=G.METADATA_CAP, original_raw_cap=G.RAW_CAP,
        probe_raw_and_metadata_charged_inside_other=True, numerical_qualified=False,
        formal_performance=False, device_operations_in_accounting=False)


class Writer:
    """Exclusive single-copy files; a terminal index is required for completeness.

    An interrupted file is deliberately retained and is not a successful record.
    Every byte, including such a partial file, is found by retained_files().
    """
    def __init__(self, root, admission):
        self.root = Path(root)
        need(self.root.parent.is_dir() and
             not any(p.is_symlink() for p in (self.root, *self.root.parents)),
             'existing ordinary parent and new exclusive boundary destination')
        self.root.mkdir(mode=0o700)
        self.admission = admission
        self.raw = self.meta = 0
        self.refs = []
        self.failed = False

    def put(self, name, data, *, raw=False):
        try:
            need(not self.failed and type(data) is bytes and type(name) is str and
                 Path(name).name == name and not name.startswith('.'),
                 'sticky writer and direct ordinary filename')
            cap = 96 * 1024 if raw else 128 * 1024
            need(0 < len(data) <= cap and len(self.refs) < 160,
                 'bounded nonempty boundary artifact')
            need(self.raw + (len(data) if raw else 0) <= RAW_CAP and
                 self.meta + (0 if raw else len(data)) <= META_CAP,
                 'bounded raw and metadata totals; no budget extension')
            self.admission(len(data))  # Real original accounting, before each file.
            path = self.root / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                need(stream.write(data) == len(data), 'complete exclusive write')
                stream.flush()
                os.fsync(stream.fileno())
            ref = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            self.refs.append(ref)
            if raw:
                self.raw += len(data)
            else:
                self.meta += len(data)
            self.admission(0)  # Charge actual retained file entries, not counters alone.
            return ref
        except BaseException:
            self.failed = True
            raise

    def record(self, name, value):
        return self.put(name + '.json', canonical(value))


def create(t, C, source_ref, manifest, environ, rank, worker, model):
    """Disabled means no module hooks, files, source reads or tensor operations."""
    profile = select(environ, manifest.get('boundary_probe_profile'))
    if profile is None:
        return None
    return Probe(t, C, source_ref, manifest, rank, worker, model, environ)


class Probe:
    def __init__(self, t, C, source_ref, manifest, rank, worker, model, environ):
        need(type(rank) is int and rank in range(4) and C.obj(source_ref) == manifest,
             'actual TP4 worker and exact source manifest')
        need(C.ref(__file__) == manifest['files']['boundary_probe_v1.py'],
             'source-bound actual boundary observer')
        need(bounded_text(manifest['model_receipt_root'], 200) and bounded_text(source_ref['path'], 1024),
             'bounded exact owned paths for complete metadata/index reservation')
        need(manifest['short_state_digest_profile']['observation'] == 'ON' and
             ('observation_only_profile' not in manifest),
             'exact source-bound ON short arm')
        self.t, self.C, self.source, self.manifest = t, C, source_ref, manifest
        self.rank, self.worker, self.runner, self.model = rank, worker, worker.model_runner, model
        need(worker._bole_model_objects['inner'] is model and
             tuple(layer.layer_idx for layer in model.layers if layer.layer_type == 'linear_attention') == GDN_LAYERS,
             'strong actual target identity and all48 ordered GDN layers')
        import g3_budget as B
        import g2_contract as G
        import bole_performance_profile as PERF
        need(C.ref(B.__file__) == manifest['files']['g3_budget.py'] and
             C.ref(G.__file__) == manifest['files']['g2_contract.py'] and
             C.ref(PERF.__file__) == manifest['files']['bole_performance_profile.py'] and
             B.OTHER == 3 * 2**20 and G.METADATA_CAP == 64 * 2**20 and G.RAW_CAP == 2**30,
             'unchanged original aggregate budget constants and exact accounting')
        self.B, self.G = B, G
        self.metadata_value = PERF.metadata_value
        self.generation = 0
        self.active = None
        self.requests = []
        self.phase = -1
        self.scope = False
        self.failed = False
        self.pending = None
        self.native = {}
        self.bindings = None
        self.raw_seen = set()
        self.read_bytes = 0
        self.handles = []
        self.hook_owners = []
        self.retirements = []
        self.projection = None
        self.writer = Writer(Path(manifest['model_receipt_root']) / ('BOUNDARY-R%d' % rank), self._budget)
        self._budget(RAW_CAP + META_CAP)
        try:
            self._install_hooks()
            import projection_probe_v1 as PP
            need(C.ref(PP.__file__) == manifest['files']['projection_probe_v1.py'],
                 'exact projection observer loaded before explicit installation')
            self.projection = PP.create(self, environ)
            need(self.projection is not None, 'projection diagnostic explicit opt-in required')
            self.projection.install()
            self._emit('INSTALL', dict(source=self.source, worker=id(worker), runner=id(self.runner), model=id(model),
                hooks=len(self.handles), hooks_return_none=True, native_math_replaced=False,
                blocking_D2H_observation=True, explicit_stream_or_event_manipulation=False))
        except BaseException as primary:
            self.failed = True
            try:
                self.uninstall()
            except BaseException as restore_error:
                primary.add_note('partial boundary-hook installation restoration: ' + repr(restore_error))
            raise

    def _budget(self, prospective):
        value = self.B.actual(self.C, self.manifest, self.rank)
        need(value['charges']['other'] + prospective + OTHER_HEADROOM <= self.B.OTHER,
             'real existing other files plus all probe files and headroom within original3MiB')
        need(value['bytes'] + prospective + 8 * 2**20 <= self.G.METADATA_CAP,
             'all charged files retain original final-summary64MiB headroom')
        need(value['bytes'] + prospective + self.G.FRAME_LOGICAL_CAP +
             self.G.FRAME_WIRE_CAP + self.G.CHECKPOINT_CAP <= self.G.RAW_CAP,
             'new binaries charged inside existing metadata allocation and original1GiB')
        return value

    def _emit(self, event, record):
        need(not self.failed, 'sticky boundary observer failure')
        return self.writer.record('G%d-%s' % (self.generation, event), dict(
            schema=SCHEMA, source_sha256=self.source['sha256'], rank=self.rank, pid=os.getpid(),
            generation=self.generation, event=event, record=record,
            numerical_qualified=False, formal_performance=False))

    def _identity(self):
        need(not self.failed and self.worker.model_runner is self.runner and
             self.worker._bole_model_objects['inner'] is self.model,
             'same strongly held actual worker/runner/target')
        if self.active is not None:
            rid, request = self.active
            need(self.runner.requests.get(rid) is request and
                 self.runner.input_batch.req_id_to_index.get(rid) == 0 and
                 [x for x in self.runner.input_batch.req_ids if x is not None] == [rid],
                 'same actual live C1 request object and CPU row')

    def _geometry(self, tensor):
        need(isinstance(tensor, self.t.Tensor) and tensor.device.type == 'npu',
             'actual NPU tensor; no synthesized tensor identity')
        storage = tensor.untyped_storage()
        row = dict(object=id(tensor), storage_ptr=storage.data_ptr(), storage_bytes=storage.nbytes(),
            data_ptr=tensor.data_ptr(), offset=tensor.storage_offset(), shape=list(tensor.shape),
            stride=list(tensor.stride()), dtype=str(tensor.dtype), device=str(tensor.device),
            logical_bytes=tensor.numel() * tensor.element_size())
        need(len(row['shape']) <= 5 and len(row['dtype']) <= 24 and len(row['device']) <= 16 and
             all(type(n) is int and 0 <= n < 2**64 for n in
                 [row[k] for k in ('object', 'storage_ptr', 'storage_bytes', 'data_ptr', 'offset', 'logical_bytes')]
                 + row['shape'] + row['stride']), 'finite metadata geometry encoding bounds')
        return row

    def _read(self, tensor):
        before = self._geometry(tensor)
        size = before['logical_bytes']
        need(0 < size <= 2 * 2**20 and self.read_bytes + size <= DEVICE_READ_CAP,
             'bounded complete logical read, no unused token padding')
        self.read_bytes += size
        cpu = tensor.detach().cpu().contiguous()
        raw = cpu.view(self.t.uint8).numpy().tobytes()
        need(len(raw) == size and self._geometry(tensor) == before,
             'complete logical bytes and unchanged tensor object/storage/geometry')
        return cpu, raw, before

    def _finite(self, cpu):
        need(cpu.device.type == 'cpu' and bool(self.t.isfinite(cpu).all()),
             'finite actual logical numerical range; no NPU finite-reduction inserted')

    @staticmethod
    def _sha(raw):
        return hashlib.sha256(raw).hexdigest()

    def _slot(self, obj, slot, *, geometry):
        conv, state = obj.kv_cache[0], obj.kv_cache[1]
        need(type(slot) is int and 0 <= slot < state.shape[0] and 0 <= slot < conv.shape[0] and
             state.dtype == self.t.float32 and tuple(state.shape[1:]) == (12, 128, 128) and
             conv.dtype == self.t.bfloat16 and conv.ndim == 3 and
             3 <= conv.shape[1] <= 16 and conv.shape[2] == 2560,
             'actual bounded TP4 state and full convolution slot geometry')
        selected_state, selected_conv = state[slot], conv[slot]
        s_cpu, s_raw, s_geometry = self._read(selected_state)
        self._finite(s_cpu)
        c_cpu, c_raw, c_geometry = self._read(selected_conv)
        self._finite(c_cpu[:3])
        row = dict(state=self._sha(s_raw), conv_full=self._sha(c_raw),
            conv_leading3=self._sha(c_raw[:3 * 2560 * 2]),
            state_finite=True, conv_leading3_finite=True,
            conv_extra_numerical_gate=False)
        if geometry:
            row['geometry'] = dict(state_arena=self._geometry(state),
                conv_arena=self._geometry(conv), selected_state=s_geometry,
                selected_conv=c_geometry, selected_slot=slot,
                conv_numerical_active_extent=[0, 3], conv_full_storage_extent=[0, int(conv.shape[1])])
        return row

    def _raw(self, name, value):
        need(self.scope and name in RAW_SHAPES and name not in self.raw_seen,
             'one actual selected raw stage per native prefill')
        expected = RAW_SHAPES[name]
        need(value.dtype == self.t.bfloat16 and value.ndim == len(expected) and
             tuple(value.shape[1:]) == expected[1:] and value.shape[0] >= expected[0],
             'actual BF16 stage geometry with explicit logical131 token extent')
        logical = value[:expected[0]]
        cpu, raw, geometry = self._read(logical)
        self._finite(cpu)
        token_bytes = len(raw) // 131
        need(token_bytes * 131 == len(raw), 'logical token grouping has no padding')
        retained = raw[123 * token_bytes:]
        ref = self.writer.put('G%d-%s.bin' % (self.generation, name), retained, raw=True)
        self.raw_seen.add(name)
        self._emit('RAW-' + name, dict(name=name, logical_shape=list(expected),
            logical_sha256=self._sha(raw), logical_bytes=len(raw), logical_finite=True,
            logical_geometry=geometry, actual_token_slice=[123, 131], raw=ref,
            raw_slice_is_full_tensor=False, raw_slice_numerical_qualification=False,
            element_encoding='little-endian IEEE bfloat16; contiguous logical order'))

    def _native0_inputs(self, mixed_qkv, b, a):
        rows = {}
        for name, value in (('mixed_qkv', mixed_qkv), ('b', b), ('a', a)):
            expected = RAW_SHAPES['layer1_' + name]
            need(value.dtype == self.t.bfloat16 and value.ndim == len(expected) and
                 tuple(value.shape[1:]) == expected[1:] and value.shape[0] >= expected[0],
                 'actual native0 projected core input, exactly131 logical rows')
            cpu, raw, geometry = self._read(value[:131])
            self._finite(cpu)
            rows[name] = dict(sha256=self._sha(raw), bytes=len(raw), shape=list(expected),
                              dtype='torch.bfloat16', finite=True, geometry=geometry)
        self._emit('NATIVE-INPUT-L00', dict(rows=rows, layer=0,
            before_original_native_core=True, full_actual131_inputs=True,
            raw_values_preserved=False))

    def _output_signature(self, output):
        if isinstance(output, self.t.Tensor):
            return ('tensor', self._geometry(output))
        if isinstance(output, (tuple, list)):
            return (type(output).__name__, id(output), tuple(self._output_signature(x) for x in output))
        return (type(output).__name__, id(output))

    def _install_hooks(self):
        layer = self.model.layers[0]
        specifications = (
            (layer.linear_attn.norm, (('layer0_gated_norm', None),)),
            (layer.linear_attn.out_proj, (('layer0_out_projection', 0),)),
            (layer.post_attention_layernorm, (('layer0_post_norm_hidden', 0), ('layer0_post_norm_residual', 1))),
            (layer.mlp, (('layer0_mlp', None),)),
        )
        for module, stages in specifications:
            def observer(actual_module, args, output, *, _module=module, _stages=stages):
                try:
                    if not self.scope:
                        return None
                    self._identity()
                    need(actual_module is _module, 'actual strongly retained hook module')
                    before = self._output_signature(output)
                    for name, item in _stages:
                        value = output if item is None else output[item]
                        self._raw(name, value)
                    need(self._output_signature(output) == before,
                         'observer preserves original output object and all return shapes/storage')
                    return None
                except BaseException:
                    self.failed = True
                    raise
            handle = module.register_forward_hook(observer)
            self.handles.append(handle)
            self.hook_owners.append((module, handle, observer))

    def native_core_enter(self, index, obj, metadata, slot, request_id, request, mixed_qkv, b, a):
        try:
            self._identity()
            if index == 0:
                need(self.active is None and self.generation == len(self.retirements) and self.generation < 2,
                     'next bounded request after actual native retirement')
                need(all(request is not prior and request_id != rid for rid, prior in self.requests),
                     'distinct actual native request strongly retained across generations')
                need(request_id and bounded_text(request_id, 128),
                     'bounded genuine request identifier, never an inferred owner')
                self.generation += 1
                self.active = (request_id, request)
                self.requests.append(self.active)
                self.native, self.raw_seen = {}, set()
                self.bindings = None
                self.phase = -1
                self.scope = True
                self._identity()
            need(self.scope and self.pending is None and self.active[0] == request_id and self.active[1] is request and
                 index == GDN_LAYERS[len(self.native)] and metadata.num_actual_tokens == 131,
                 'actual next ordered native GDN core and exact131 tokens')
            need(self.model.layers[index].linear_attn is obj,
                 'actual target layer owns observed native core')
            need(obj.prefix and bounded_text(obj.prefix, 128),
                 'bounded actual registered layer prefix')
            self.pending = (index, obj, metadata, slot, request)
            if index == 0:
                self._native0_inputs(mixed_qkv, b, a)
            if index == 1:
                self._raw('layer1_mixed_qkv', mixed_qkv)
                self._raw('layer1_b', b)
                self._raw('layer1_a', a)
        except BaseException:
            self.failed = True
            raise

    def native_core_return(self, index, obj, metadata, slot, request, core_attn_out):
        try:
            self._identity()
            need(self.pending is not None and self.pending[0] == index and
                 self.pending[1] is obj and self.pending[2] is metadata and
                 self.pending[3] == slot and self.pending[4] is request,
                 'same actual native invocation returned exactly once')
            row = self._slot(obj, slot, geometry=True)
            self.native[index] = (obj, metadata, slot, request, row)
            self._emit('NATIVE-L%02d' % index, dict(layer=index, prefix=obj.prefix,
                request=self.active[0], request_object=id(request), metadata_object=id(metadata),
                core_return_observed_before_registration=True, slot=row))
            if index == 0:
                self._raw('layer0_core_output', core_attn_out)
            self.pending = None
        except BaseException:
            self.failed = True
            raise

    def registered(self, bindings, window):
        try:
            self._identity()
            need(self.scope and self.pending is None and tuple(self.native) == GDN_LAYERS and
                 self.raw_seen == set(RAW_SHAPES) and len(bindings) == 64 and
                 window['request'] is self.active[1] and window['request_id'] == self.active[0] and
                 window['request_epoch'] == self.generation and window['length'] == 131,
                 'complete native prefill witnesses joined to genuine registration')
            for binding in bindings:
                if binding['kind'] != 'gdn':
                    continue
                obj, metadata, slot, request, _ = self.native[binding['index']]
                need(binding['layer'].linear_attn is obj and binding['physical_slot'] == slot and
                     binding['conv_arena'] is obj.kv_cache[0] and binding['state'] is obj.kv_cache[1] and
                     binding['tail'].request is request and binding['tail'].metadata is metadata and
                     window['metadata'][binding['prefix']] is metadata,
                     'true registered arena/metadata/request ownership, not names alone')
            self.bindings = bindings
            self.scope = False
            self.capture(PHASES[0])
        except BaseException:
            self.failed = True
            raise

    def capture(self, phase, **context):
        try:
            self._identity()
            need(self.bindings is not None and not self.scope and self.phase + 1 < len(PHASES) and
                 phase == PHASES[self.phase + 1], 'exact ordered registered cache boundary')
            rows = []
            for binding in self.bindings:
                if binding['kind'] != 'gdn':
                    continue
                obj = binding['layer'].linear_attn
                need(obj.kv_cache[0] is binding['conv_arena'] and obj.kv_cache[1] is binding['state'],
                     'registered actual arenas remain strongly owned')
                digest = self._slot(obj, binding['physical_slot'], geometry=False)
                native = self.native[binding['index']][4]
                need(self._geometry(obj.kv_cache[0]) == native['geometry']['conv_arena'] and
                     self._geometry(obj.kv_cache[1]) == native['geometry']['state_arena'],
                     'same actual tensor storage/offset/stride as native-return witness')
                rows.append(dict(layer=binding['index'], slot=binding['physical_slot'],
                    digest={k: digest[k] for k in ('state', 'conv_full', 'conv_leading3')}))
            need(len(rows) == 48, 'complete actual48 selected GDN state/conv boundaries')
            self.phase += 1
            self._emit(phase, dict(rows=rows, context=context,
                state_finite=True, conv_leading3_finite=True,
                conv_extra_numerical_gate=False, storage_geometry_equal_native=True,
                numerical_equality_is_observed_not_required=True))
        except BaseException:
            self.failed = True
            raise

    def mtp_inventory(self, drafter):
        """Describe real storage, never infer the native draft write footprint."""
        self._identity()
        need(drafter is self.runner.drafter and drafter.runner is self.runner,
             'actual runner-owned MTP drafter')
        rows = []
        for name, module in drafter.model.named_modules():
            cache = getattr(module, 'kv_cache', None)
            if not isinstance(cache, (tuple, list)):
                continue
            for item, tensor in enumerate(cache):
                if isinstance(tensor, self.t.Tensor):
                    need(bounded_text(name, 128),
                         'bounded actual draft-module name')
                    rows.append(dict(module=name, module_object=id(module), item=item,
                                     geometry=self._geometry(tensor)))
        need(len(rows) <= 8, 'bounded actual draft cache storage inventory')
        return dict(drafter_object=id(drafter), draft_model_object=id(drafter.model),
            cache_storage_inventory=rows, draft_actual_write_footprint_known=False,
            alias_exclusion_proven=False,
            shared_allocation_alone_is_not_alias_bug_evidence=True,
            limitation='active draft slots/write extents not source-proved by this observer')

    def retire(self, record):
        try:
            need(not self.failed and self.active is not None and self.phase == len(PHASES) - 1 and
                 record['generation'] == self.generation and record['request'] == self.active[0],
                 'boundary retirement only after original LiveOwner native-retirement proof')
            # Do not re-run the live-request check: original native retirement has removed it.
            need(self.runner.requests.get(self.active[0]) is None and
                 self.active[0] not in self.runner.input_batch.req_id_to_index,
                 'native retirement already removed actual request and CPU row')
            normalized = self.metadata_value(record)
            need(len(record['output_token_ids']) == 8 and all(type(v) is int and 0 <= v < 2**64
                 for v in record['output_token_ids']), 'actual bounded8 retired token IDs')
            self.projection.before_retire(self.generation)
            self._emit('RETIRE', dict(original_record_sha256=self._sha(canonical(normalized)),
                request=record['request'], generation=record['generation'],
                original_retirement_schema=record['retirement']['schema'],
                original_retirement_steps=record['retirement']['steps'],
                output_token_ids=list(record['output_token_ids']), actual_native_request_absent=True,
                device_read_bytes=self.read_bytes, raw_bytes=self.writer.raw,
                metadata_bytes_before_record=self.writer.meta))
            self.retirements.append(self.active[0])
            self.active = None
            self.bindings = None
            self.native = {}
            if self.generation == 2:
                self.uninstall()
                need(self.writer.raw == RAW_CAP and len(self.retirements) == 2,
                     'all18 actual bounded raw slices and two genuine retirements')
                self._emit('COMPLETE', dict(source=self.source, references=list(self.writer.refs),
                    requests=list(self.retirements), hooks_removed=True,
                    projection_observer_restored=True, projection_records=2,
                    device_read_bytes=self.read_bytes, raw_bytes=self.writer.raw,
                    metadata_bytes_before_index=self.writer.meta,
                    observation_complete=True, draft_actual_write_footprint_known=False,
                    alias_exclusion_proven=False, diagnostic_only=True))
        except BaseException:
            self.failed = True
            raise

    def uninstall(self):
        projection_error = None
        if getattr(self, 'projection', None) is not None:
            try:
                self.projection.uninstall()
            except BaseException as exc:
                projection_error = exc
        for module, handle, observer in reversed(self.hook_owners):
            need(module._forward_hooks.get(handle.id) is observer,
                 'only remove the same actual observer hook handle')
            handle.remove()
            need(handle.id not in module._forward_hooks, 'actual observer hook removed')
        self.handles = []
        self.hook_owners = []
        if projection_error is not None:
            raise projection_error
