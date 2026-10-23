"""Strict same-frame state evidence codec; no model computation or publication."""
import dataclasses
import hashlib
import io
import os
from pathlib import Path

FLAG = 'BOLE_STATE_CAPTURE_CODEC_ENABLE'
TAG = 'bole.same-frame-state-ref/v1'
HEADER = 'bole.two-base-state-capture/v1'
CAP = 384 * 2**20
RAW_CAP = 2**30
STATE_BYTES = 12 * 128 * 128 * 4
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
ROLES = ('canonical_input', 'staged_before', 'staged_after', 'observed_after')
CONTRACT = dict(schema=HEADER, enabled=True, bases=2, roles_per_layer=4,
                state_layers=48, state_refs=192, logical_frame_cap=CAP,
                joint_raw_cap=RAW_CAP, candidate_math_unchanged=True,
                numerical_qualified=False, runtime_joint_fit=False)


def need(v, s):
    if not v:
        raise ValueError(s)


def primitive(x):
    if dataclasses.is_dataclass(x):
        return {f.name: primitive(getattr(x, f.name)) for f in dataclasses.fields(x)}
    if type(x) is dict:
        return {k: primitive(v) for k, v in x.items()}
    if type(x) in (list, tuple):
        return [primitive(v) for v in x]
    need(x is None or type(x) in (str, int, float, bool), 'primitive owner only')
    return x


def owner_key(owner):
    need(type(owner) is dict and set(owner) == {'request', 'generation', 'slot', 'length', 'version'},
         'exact actual Owner identity')
    need(type(owner['request']) is str and bool(owner['request']) and
         all(type(owner[k]) is int for k in ('generation', 'slot', 'length', 'version')) and
         owner['generation'] in (1, 2) and owner['slot'] == 0 and
         owner['length'] >= 131 and owner['version'] >= 0, 'strict actual owner counters')
    return dict(owner)


def checked_digest(d, canonical=False):
    shape = [1, 12, 128, 128] if canonical else [12, 128, 128]
    need(type(d) is dict and set(d) == {'dtype', 'shape', 'bytes', 'sha256', 'finite'} and
         d['dtype'] == 'torch.float32' and type(d['shape']) is list and
         all(type(v) is int for v in d['shape']) and d['shape'] == shape and
         type(d['bytes']) is int and d['bytes'] == STATE_BYTES and
         type(d['sha256']) is str and len(d['sha256']) == 64 and
         all(c in '0123456789abcdef' for c in d['sha256']) and d['finite'] is True,
         'complete finite FP32 state witness with exact view')
    return dict(d)


def tensor_shape(t, x, canonical=False, device='npu'):
    need(isinstance(x, t.Tensor) and x.device.type == device and
         x.dtype == t.float32 and tuple(x.shape) ==
         ((1, 12, 128, 128) if canonical else (12, 128, 128)) and
         x.numel() * x.element_size() == STATE_BYTES, 'actual complete state tensor ABI')


def view(base, canonical):
    return base.transpose(-1, -2).unsqueeze(0) if canonical else base


def by_layer(rows):
    need(type(rows) is list and len(rows) == 48, 'all48 actual state bases')
    need(all(type(r) is dict and type(r.get('layer')) is int for r in rows),
         'state layer IDs are integers, never bool')
    result = {r['layer']: r['native_state'] for r in rows}
    need(len(result) == 48 and set(result) == set(LAYERS), 'only48 actual GDN layers')
    return result


def enabled(O):
    need(os.environ.get(FLAG) == '1' and O.m.get('state_capture_codec') == CONTRACT,
         'state evidence codec default OFF/source declared')
    need(O.C.ref(__file__) == O.m['files']['state_capture_codec.py'],
         'actual source-owned codec')
    import short_state_digest as D
    need(O.C.ref(D.__file__) == O.m['files']['short_state_digest.py'],
         'original full NPU digest witness source')
    return D.tensor_digest


class CaptureMismatch(ValueError):
    def __init__(self, message, *, actual, base, metadata):
        super().__init__(message)
        self.actual = actual
        self.base = base
        self.metadata = metadata


def mismatch(O, actual, base, layer, role, phase, error):
    raise CaptureMismatch('state evidence mismatch: ' + str(error), actual=actual, base=base,
        metadata=dict(source=O.source, rank=O.rank, owner=owner_key(O.current['owner']),
                      layer=layer, role=role, phase=phase,
                      partial_failure=True, numerical_qualified=False, acknowledged=False))


def witnessed(O, actual, base, layer, role, phase, *, prior=None):
    need(type(layer) is int and layer in LAYERS and role in ROLES, 'fixed state role/layer')
    canonical = role == 'canonical_input'
    try:
        D = enabled(O)
        tensor_shape(O.t, actual, canonical)
        tensor_shape(O.t, base)
        # D performs a full finite check and complete D2H/contiguous byte digest.
        # Only the original stage-after witness may be reused; it was made
        # synchronously before the actual transaction.publish call.
        actual_digest = checked_digest(D(O.t, actual), canonical) if prior is None else checked_digest(prior)
        base_digest = checked_digest(D(O.t, view(base, canonical)), canonical)
        need(actual_digest == base_digest, 'actual role equals actual base, all bytes')
        return dict(tag=TAG, source=O.source, rank=O.rank, owner=owner_key(O.current['owner']),
                    layer=layer, role=role, view='canonical' if canonical else 'identity',
                    witness=actual_digest, phase=phase, actual_npu_full_witness=True)
    except Exception as error:
        mismatch(O, actual, base, layer, role, phase, error)


def guarded(O, function, *args):
    try:
        return function(O, *args)
    except CaptureMismatch as error:
        # No ACK or successful raw release is possible after a mismatch.
        import fastpath_numeric_sink as S
        try:
            ref = S.state_partial_failure(O, error)
            O.state_codec_failure_ref = ref
        except Exception as preservation:
            error.preservation_error = repr(preservation)
        raise


def canonical_input(O, b, state):
    return guarded(O, _canonical_input, b, state)


def _canonical_input(O, b, state):
    base = by_layer(O.current['before_GDN'])[b['index']]
    return witnessed(O, state, base, b['index'], 'canonical_input', 'actual_gdn_input')


def before_publication(O, proposal):
    return guarded(O, _before_publication, proposal)


def _before_publication(O, proposal):
    D = enabled(O)
    need(O.current is not None and primitive(proposal['owner']) == O.current['owner'] and
         proposal.get('published') is False, 'actual unpublished same-owner proposal')
    need(not hasattr(O, '_state_before_publish'), 'exactly one before-publication witness per frame')
    bases = by_layer(O.current['before_GDN'])
    rows = proposal['writes']
    need(type(rows) is list and len(rows) == 128, 'original128 staged writes retained')
    selected = [r for r in rows if r['kind'] == 'state']
    need(len(selected) == 48 and all(type(r['layer']) is int for r in selected) and
         {r['layer'] for r in selected} == set(LAYERS), 'all48 staged states before publish')
    witnesses = {}
    for r in selected:
        i = r['layer']
        before = witnessed(O, r['before'], bases[i], i, 'staged_before', 'before_transaction_publish')
        try:
            tensor_shape(O.t, r['after'])
            after = checked_digest(D(O.t, r['after']))
        except Exception as error:
            mismatch(O, r['after'], bases[i], i, 'staged_after', 'before_transaction_publish', error)
        witnesses[i] = dict(before=before, after=after)
    O._state_before_publish = witnesses


def encode_publication(O, proposal, after):
    return guarded(O, _encode_publication, proposal, after)


def _encode_publication(O, proposal, after):
    enabled(O)
    need(hasattr(O, '_state_before_publish') and
         set(O._state_before_publish) == set(LAYERS), 'actual prepublication witness required')
    bases = by_layer(after[0])
    writes = []
    for r in proposal['writes']:
        if r['kind'] != 'state':
            writes.append(r)
            continue
        i = r['layer']
        wr = dict(r)  # Never mutate the actual publish/rollback proposal.
        wr['before'] = O._state_before_publish[i]['before']
        wr['after'] = witnessed(O, r['after'], bases[i], i, 'staged_after',
                               'before_transaction_publish', prior=O._state_before_publish[i]['after'])
        writes.append(wr)
    staged = dict(proposal)
    staged['writes'] = writes
    return staged


def observed(O, row, actual, after):
    if row['kind'] != 'state':
        return actual
    return guarded(O, _observed, row, actual, after)


def _observed(O, row, actual, after):
    return witnessed(O, actual, by_layer(after[0])[row['layer']], row['layer'],
                     'observed_after', 'actual_published_arena_read')


def finish(O, frame):
    enabled(O)
    frame['state_capture_codec'] = dict(schema=HEADER, source=O.source, rank=O.rank,
        owner=owner_key(frame['owner']), refs=192, base_count=96, runtime_joint_fit=False)
    del O._state_before_publish


def decode(t, frame, *, digest, expected_source, rank):
    """Restore only views of complete actual bases; caller runs original oracle."""
    need(type(frame) is dict and type(rank) is int and 0 <= rank < 4 and
         frame['source'] == expected_source and frame['rank'] == rank, 'exact source/rank frame')
    owner = owner_key(frame['owner'])
    need(frame.get('state_capture_codec') == dict(schema=HEADER, source=expected_source, rank=rank,
         owner=owner, refs=192, base_count=96, runtime_joint_fit=False), 'exact encoded frame header')
    before, after = by_layer(frame['before_GDN']), by_layer(frame['after_GDN'])
    for x in tuple(before.values()) + tuple(after.values()):
        tensor_shape(t, x, device='cpu')
    rows = frame['staged']['writes']
    need(type(rows) is list and len(rows) == 128 and len(frame['observed_applied']) == 128,
         'original complete128 order')
    expected = {(i, k) for i in range(64) for k in
                (('key', 'value') if i % 4 == 3 else ('state', 'conv'))}
    need(all(type(r['layer']) is int for r in rows) and
         len({(r['layer'], r['kind']) for r in rows}) == 128 and
         {(r['layer'], r['kind']) for r in rows} == expected, 'exact original128 typed destinations')
    count = 0

    def restore(r, i, role):
        nonlocal count
        canonical = role == 'canonical_input'
        phase = {'canonical_input': 'actual_gdn_input', 'staged_before': 'before_transaction_publish',
                 'staged_after': 'before_transaction_publish', 'observed_after': 'actual_published_arena_read'}[role]
        need(type(r) is dict and set(r) == {'tag', 'source', 'rank', 'owner', 'layer', 'role',
             'view', 'witness', 'phase', 'actual_npu_full_witness'} and
             r['tag'] == TAG and r['source'] == expected_source and type(r['rank']) is int and
             r['rank'] == rank and r['owner'] == owner and type(r['layer']) is int and
             r['layer'] == i and r['role'] == role and
             r['view'] == ('canonical' if canonical else 'identity') and r['phase'] == phase and
             r['actual_npu_full_witness'] is True, 'strict same-frame/layer typed state Ref')
        recorded = checked_digest(r['witness'], canonical)
        base = before[i] if role in ('canonical_input', 'staged_before') else after[i]
        result = view(base, canonical)
        need(checked_digest(digest(t, result), canonical) == recorded,
             'reopened complete CPU base/view bytes match recorded real NPU witness')
        count += 1
        return result

    # New shallow containers only: never alias-modify the reopened encoded raw.
    out = dict(frame)
    out['captures'] = dict(frame['captures'])
    need(set(out['captures']) == set(range(64)) and
         all(type(k) is int for k in out['captures']), 'all64 actual capture keys')
    for i in LAYERS:
        r = dict(out['captures'][i])
        r['state'] = restore(r['state'], i, 'canonical_input')
        out['captures'][i] = r
    staged = dict(frame['staged'])
    staged['writes'] = []
    out['observed_applied'] = list(frame['observed_applied'])
    for ordinal, r in enumerate(rows):
        new = dict(r)
        if r['kind'] == 'state':
            i = r['layer']
            new['before'] = restore(r['before'], i, 'staged_before')
            new['after'] = restore(r['after'], i, 'staged_after')
            out['observed_applied'][ordinal] = restore(frame['observed_applied'][ordinal], i, 'observed_after')
        staged['writes'].append(new)
    need(count == 192, 'exact192 state roles restored; no arbitrary paths or references')
    out['staged'] = staged
    return out


def require_runtime_admission(*_args):
    raise ValueError('actual joint clone/wire/CPU/checkpoint/first/failed/temporary budget unbound')


def partial_failure(c, O, error, X):
    """Exclusive bounded first-bad evidence, never a numerical result or ACK."""
    t, C = c['t'], c['C']
    need(isinstance(error, CaptureMismatch) and c['source'] == O.source and
         c['rank'] == O.rank and O.current is not None, 'actual configured failure owner')
    for value in (error.actual, error.base):
        # Nonfinite is deliberately allowed in this failure-only full payload.
        need(isinstance(value, t.Tensor) and value.device.type == 'npu' and
             value.dtype == t.float32 and value.numel() * value.element_size() == STATE_BYTES and
             tuple(value.shape) in ((12, 128, 128), (1, 12, 128, 128)), 'bounded actual bad/base state')
    need(O.used + 2 * STATE_BYTES <= CAP, 'failure payload inside unchanged producer cap')
    need(c['used'] + c['metadata_bytes'] + 8 * STATE_BYTES + 128 * 2**20 + 64 * 2**20 <= RAW_CAP,
         'failed payload plus CPU/serialization/checkpoint/metadata before allocation')
    payload = dict(error.metadata, actual_bad=error.actual, actual_base=error.base,
                   error=str(error), source_codec=C.ref(__file__), partial_failure=True,
                   no_ack=True, source_is_not_qualified=True)
    raw = X.export(t, payload, cap_bytes=2 * STATE_BYTES)
    need(raw['logical_tensor_bytes'] == 2 * STATE_BYTES, 'two complete actual failed states')
    stream = io.BytesIO()
    t.save(raw, stream)
    wire = stream.getvalue()
    need(len(wire) <= 4 * STATE_BYTES and
         c['used'] + c['metadata_bytes'] + len(wire) <= RAW_CAP, 'actual bounded failure wire before write')
    stem = 'G%d-O%d-STATE-ALIAS-FAIL' % (O.current['owner']['generation'], O.current['owner']['version'])
    path = c['root'] / (stem + '.pt')
    need(path.parent == c['root'] and not path.exists(), 'fresh this-frame failure file only')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(wire)
        output.flush()
        os.fsync(output.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    ref = C.ref(path)
    C.checked(ref)
    need(ref['bytes'] == len(wire) and ref['sha256'] == hashlib.sha256(wire).hexdigest(),
         'actual reopened failed payload complete Ref')
    c['used'] += ref['bytes']
    # No success RELEASE path ever receives this filename. The actual raw remains
    # preserved through ordinary source-container cleanup, in its host receipt leaf.
    return ref
