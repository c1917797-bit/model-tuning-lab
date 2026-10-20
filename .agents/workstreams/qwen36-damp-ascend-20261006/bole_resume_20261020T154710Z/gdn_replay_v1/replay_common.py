"""Stdlib-only source/primitive/codec helpers; never import a tensor runtime."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import zlib


CAP = 2**30
METADATA_RESERVE = 32 * 2**20
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
LAYOUTS = ('contiguous', 'column_strided')
RESULT_KEYS = ('O', 'P', 'U', 'S0', 'S1', 'S2')
INPUT_KEYS = ('q', 'k', 'v', 'beta', 'gamma', 'state')
REFERENCE_NAMES = ('core112.py', 'oracle112.py', 'independent_model.py',
                   'model_entry.py', 'sourceio.py', 'diagnostic_export.py',
                   'consume_model.py')
LOCAL_NAMES = ('replay_common.py', 'replay_gdn.py', 'consume_gdn.py')


def need(value, message):
    if not value:
        raise ValueError(message)


def disabled(role):
    return dict(schema='bole.gdn3-replay-disabled/v1', role=role, enabled=False,
                NPU=False, tensor_runtime_imported=False, model_ready=False,
                mathematically_qualified=False, formal_success=False)


def ref(path):
    path = Path(path)
    before = path.stat()
    digest = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            digest.update(block)
            count += len(block)
    after = path.stat()
    need((before.st_size, before.st_mtime_ns, before.st_ino) ==
         (after.st_size, after.st_mtime_ns, after.st_ino) and count == after.st_size,
         'stable ordinary source/evidence read')
    return dict(path=str(path), bytes=count, sha256=digest.hexdigest())


def checked(reference):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'},
         'exact Ref3 object')
    path = Path(reference['path'])
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)) and
         ref(path) == reference, 'exact ordinary absolute Ref3 bytes')
    return path


def obj(reference):
    path = checked(reference)
    need(reference['bytes'] <= 16 * 2**20, 'bounded JSON evidence')
    return json.loads(path.read_bytes())


def inspection(reference):
    value = obj(reference)
    if type(value) is list:
        need(len(value) == 1, 'one exact actual Docker controller inspection')
        value = value[0]
    need(type(value) is dict, 'ordinary controller inspection object')
    return value


def owned_environment(admission):
    need(admission['owned_container_id'] in Path('/proc/self/cgroup').read_text(),
         'current process belongs to MAIN-inspected owned container')
    for key, value in admission['environment'].items():
        need(os.environ.get(key) == value, 'owned admission environment: ' + key)


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False,
                       separators=(',', ':')) + '\n').encode('utf8')


def load_module(reference, name):
    """Hash first and load only that path, including canonical dependency names."""
    path = checked(reference)
    if name in sys.modules:
        module = sys.modules[name]
        need(getattr(module, '__file__', None) is not None and
             ref(module.__file__) == reference, 'no ambient imported helper')
        return module
    spec = importlib.util.spec_from_file_location(name, str(path))
    need(spec is not None and spec.loader is not None, 'exact source-file loader')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        need(ref(module.__file__) == reference, 'stable helper across import')
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def manifest(reference, own_file):
    m = obj(reference)
    need(m['schema'] == 'bole.gdn3-actual-replay-manifest/v1' and
         m['output_cap_bytes'] == CAP, 'exact replay schema and total1GiB cap')
    need(set(m['files']) == set(LOCAL_NAMES) and
         set(m['references']) == set(REFERENCE_NAMES) and
         set(m['candidate']) == {'wrapper', 'kernels'}, 'complete explicit source closure')
    for item in (*m['files'].values(), *m['references'].values(),
                 *m['candidate'].values()):
        checked(item)
    own = Path(own_file).resolve()
    need(ref(own) == m['files'][own.name] and
         ref(__file__) == m['files']['replay_common.py'] and
         all(Path(r['path']).parent == own.parent for r in m['files'].values()),
         'all three exact private driver files and own helper')
    need(Path(m['candidate']['wrapper']['path']).name == 'gdn3_fp32.py' and
         Path(m['candidate']['kernels']['path']).name == 'gdn3_triton_kernels.py' and
         Path(m['candidate']['wrapper']['path']).parent ==
         Path(m['candidate']['kernels']['path']).parent,
         'completed exact private candidate pair')
    source = obj(m['actual_source'])
    need(source['schema'] == 'bole.actual-model-three-node-entry/source-prep-v1' and
         source['prepared_only'] is False and
         source['whole_numerical_qualification'] is False,
         'actual executed r23 source, not a prepared qualification assertion')
    for name, r in m['references'].items():
        need(source['files'][name] == r, 'original helper must join actual r23 source: ' + name)
    cfg = m['configuration']
    need(cfg == dict(forward_tile_v=32, commit_tile_k=32, commit_tile_v=32,
                     cpu_threads=1, microtiming=False), 'one immutable untimed32x32 variant')
    need([p['rank'] for p in m['receipts']] == [0, 1, 2, 3], 'four ordered actual ranks')
    receipts = []
    for rank, pair in enumerate(m['receipts']):
        need(set(pair) == {'rank', 'receipt'}, 'explicit rank/receipt pair')
        r = obj(pair['receipt'])
        need(Path(pair['receipt']['path']).name == 'BOLE-TREE-RANK-%d.json' % rank and
             r['schema'] == 'bole.actual-worker-three-node-receipt/v1' and
             r['rank'] == rank and r['source'] == m['actual_source'] and
             r['primary'] is None and r['scheduler_committed'] is False and
             r['model_ready'] is False, 'actual successful uncommitted worker receipt')
        need(Path(r['raw']['path']) == Path(pair['receipt']['path']).with_suffix('.pt') and
             0 < r['raw']['bytes'] <= CAP, 'same-leaf bounded actual raw file')
        checked(r['raw'])
        stat = r['stat']; rest = stat[stat.rfind(')') + 2:].split()
        need(int(stat.split(' ', 1)[0]) == r['pid'] and int(rest[19]) > 0 and
             type(r['cgroup']) is str and r['cgroup'], 'captured PID/start/cgroup provenance')
        receipts.append(r)
    need(len({r['pid'] for r in receipts}) == 4 and
         len({r['raw']['sha256'] for r in receipts}) == 4 and
         len({r['cgroup'] for r in receipts}) == 1, 'four distinct captures of one actual TP4 job')
    admission = obj(m['admission'])
    need(admission['schema'] == 'bole.gdn3-replay-owned-admission/v1' and
         admission['authority'] == 'MAIN' and
         admission['actual_source'] == m['actual_source'] and
         admission['physical_devices'] == [4] and admission['logical_devices'] == [0] and
         admission['guest_device_path'] == '/dev/davinci0' and
         admission['allow_hf32'] is False and
         admission['controller_inspection'] is not None,
         'MAIN-created source-bound singleton physical4-to-logical0 admission')
    current_inspection = inspection(admission['controller_inspection'])
    r23_inspection = inspection(admission['r23_controller_inspection'])
    need(type(admission['image_digest']) is str and
         admission['image_digest'].startswith('sha256:') and
         len(admission['image_digest']) == 71 and
         admission['same_image_as_actual_r23'] is True and
         type(admission['owned_container_id']) is str and
         len(admission['owned_container_id']) == 64,
         'exact image/container identity supplied from MAIN controller inspection')
    need(current_inspection['Id'] == admission['owned_container_id'] and
         current_inspection['Image'] == admission['image_digest'] == r23_inspection['Image'] and
         current_inspection['State']['Running'] is True and
         all(r23_inspection['Id'] in r['cgroup'] for r in receipts),
         'actual inspected replay/r23 container same-image and original worker identity join')
    numbered = [d for d in current_inspection['HostConfig']['Devices']
                if Path(d['PathInContainer']).name.startswith('davinci') and
                Path(d['PathInContainer']).name[len('davinci'):].isdigit()]
    need(len(numbered) == 1 and numbered[0]['PathOnHost'] == '/dev/davinci4' and
         numbered[0]['PathInContainer'] == '/dev/davinci0',
         'actual controller mapping has exactly physical4 -> guest0')
    need(type(admission['environment']) is dict and
         all(type(k) is str and type(v) is str for k, v in admission['environment'].items()),
         'declared exact owned-stage environment')
    return m, receipts, admission


def sources(m, *, with_candidate):
    references = m['references']
    C = load_module(references['sourceio.py'], 'sourceio')
    load_module(references['model_entry.py'], 'model_entry')
    I = load_module(references['independent_model.py'], 'independent_model')
    K = load_module(references['core112.py'], '_bole_replay_core112')
    O = load_module(references['oracle112.py'], '_bole_replay_oracle112')
    candidate = None
    if with_candidate:
        candidate = load_module(m['candidate']['wrapper'], '_bole_replay_gdn3_wrapper')
    return C, I, K, O, candidate


def bits(t, a, b):
    return a.shape == b.shape and a.dtype == b.dtype and bool(t.equal(
        a.contiguous().view(t.uint8), b.contiguous().view(t.uint8)))


def primitive_bytes(t, value):
    """Same logical tensor accounting as the original diagnostic_export.walk."""
    if isinstance(value, t.Tensor):
        need(value.device.type == 'cpu', 'weights_only CPU tensor payload')
        return value.numel() * value.element_size()
    if value is None or type(value) in (str, int, float, bool):
        return 0
    if type(value) in (list, tuple):
        return sum(primitive_bytes(t, x) for x in value)
    need(type(value) is dict and all(type(k) in (str, int) for k in value),
         'primitive raw envelope only, no model/runtime classes')
    return sum(primitive_bytes(t, x) for x in value.values())


def load_raw(t, receipt, m):
    path = checked(receipt['raw'])
    exported = t.load(path, map_location='cpu', weights_only=True)
    need(ref(path) == receipt['raw'], 'raw stable across weights_only CPU load')
    need(exported['schema'] == 'bole.model-diagnostic-primitives/v1' and
         exported['model_ready'] is False and exported['cap_bytes'] == CAP and
         primitive_bytes(t, exported['payload']) == exported['logical_tensor_bytes'] <= CAP,
         'complete original bounded primitive envelope and exact logical byte count')
    raw = exported['payload']
    need(raw['schema'] == 'bole.actual-three-node-model-capture/v1' and
         raw['source'] == m['actual_source'] and raw['rank'] == receipt['rank'] and
         raw['scheduler_committed'] is False,
         'same-source actual rank diagnostic, no scheduler publication')
    tree = raw['tree_context']; owner = raw['request']
    need(tree['owner'] == owner and owner['length'] == 131 and owner['slot'] == 0 and
         type(owner['request']) is str and owner['request'] and
         [tuple(x) for x in tree['order']] ==
         [(i, 'fa' if i % 4 == 3 else 'gdn') for i in range(64)] and
         set(tree['captures']) == set(range(64)), 'complete actual64-layer C1/131 traversal')
    tokens = tree['tokens']
    need(len(tokens) == 3 and all(type(x) is int and x >= 0 for x in tokens) and
         tokens[1] != tokens[2] and list(tree['positions']) == [131, 132, 132],
         'actual root/two-sibling model token/depth positions')
    ids = raw['actual_native_prefill_ids']; observation = raw['actual_native_prefill_input']
    need(ids.dtype == t.int32 and tuple(ids.shape) == (131,) and
         bits(t, ids, observation['actual_token_ids']) and
         ids.tolist() == observation['actual_CPU_token_ids'] == observation['request_prompt_token_ids'] and
         observation['no_mm_features'] is True and observation['no_soft_prompt'] is True,
         'actual native token input ownership, no synthetic model projections')
    anchors = {a['layer']: a for a in raw['actual_native_initial_GDN']}
    slots = raw['layer_slot_bindings']; slotmap = {s['prefix']: s for s in slots}
    need(set(anchors) == set(LAYERS) and len(slots) == len(slotmap) == 48,
         'all48 actual GDN native-prefill anchors and physical slot bindings')
    for layer in LAYERS:
        row = tree['captures'][layer]; anchor = anchors[layer]
        identity = anchor['slot_binding_identity']
        need(slotmap.get(identity['prefix']) == identity and
             identity['group'] == anchor['group'] and
             identity['physical_slot'] == anchor['physical_slot'] and
             identity['logical_owner_slot'] == owner['slot'] and
             identity['request_id'] == owner['request'], 'actual per-layer native slot anchor')
        need(row['kind'] == 'gdn' and row['phase'] == 'TREE_GDN_COMPLETE' and
             bits(t, row['state'], anchor['initial_native_state'].transpose(-1, -2).unsqueeze(0)),
             'canonical state joined to actual native Dv,Dk orientation')
        frame_inputs(t, row)
        for key, tensor in bases(row).items():
            expected = (1, 12, 3) if key == 'P' else (1, 12, 128, 128) if key.startswith('S') else (1, 12, 3, 128)
            need(tensor.dtype == t.float32 and tuple(tensor.shape) == expected and
                 bool(t.isfinite(tensor).all()), 'original complete FP32 outputs/factors/states')
    return exported, raw


def frame_inputs(t, row):
    q, k, v, beta, gamma = row['normalized_inputs']
    values = dict(q=q, k=k, v=v, beta=beta, gamma=gamma, state=row['state'])
    for key, tensor in values.items():
        shape = (1, 12, 128, 128) if key == 'state' else (1, 12, 3) if key in ('beta', 'gamma') else (1, 12, 3, 128)
        need(isinstance(tensor, t.Tensor) and tensor.device.type == 'cpu' and
             tensor.dtype == t.float32 and tuple(tensor.shape) == shape and
             bool(t.isfinite(tensor).all()), 'actual finite original FP32 frame inputs')
    need(bool((gamma > 0).all()) and tuple(row['actual_node_states'].shape) == (3, 1, 12, 128, 128),
         'positive original gates and all three terminal states')
    return values


def bases(row):
    return dict(O=row['precast_output'], P=row['factors'][0], U=row['factors'][1],
                S0=row['actual_node_states'][0], S1=row['actual_node_states'][1],
                S2=row['actual_node_states'][2])


def oracle_values(t, oracle, inputs):
    q, k, v, beta, gamma, state = (inputs[n].double() for n in INPUT_KEYS)
    output, states, updates = oracle.sequential(t, q, k, v, beta, gamma, state,
                                               (-1, 0, 0), return_updates=True)
    product = t.stack((gamma[..., 0], gamma[..., 0] * gamma[..., 1],
                       gamma[..., 0] * gamma[..., 2]), dim=-1)
    return dict(O=output, P=product, U=updates,
                S0=states[0], S1=states[1], S2=states[2])


def metrics(t, I, original, candidate, truth, captured):
    result = dict(original_vs_literal={k: I.old112(t, original[k], truth[k]) for k in RESULT_KEYS},
                  candidate_vs_literal={k: I.old112(t, candidate[k], truth[k]) for k in RESULT_KEYS},
                  candidate_vs_original_device={k: I.old112(t, candidate[k], original[k]) for k in RESULT_KEYS},
                  captured_vs_literal={k: I.old112(t, captured[k], truth[k]) for k in RESULT_KEYS},
                  P_bitwise_original=bits(t, candidate['P'], original['P']))
    result['passed'] = result['P_bitwise_original'] and all(
        metric['passed'] for name, values in result.items() if name.endswith(('_literal', '_device'))
        for metric in values.values())
    return result


def tensor_bytes(t, tensor):
    need(tensor.device.type == 'cpu' and tensor.dtype == t.float32 and
         bool(t.isfinite(tensor).all()), 'finite CPU FP32 export bytes')
    # A uint8 view has no numeric cast. numpy().tobytes() copies these exact bytes.
    return tensor.contiguous().view(t.uint8).numpy().tobytes()


def tensor_hash(t, tensor):
    return hashlib.sha256(tensor_bytes(t, tensor)).hexdigest()


class Budget:
    def __init__(self, output):
        self.output = Path(output)
        need(self.output.is_dir() and not any(self.output.iterdir()),
             'fresh existing empty MAIN-owned output directory')
        need(not any(p.is_symlink() for p in (self.output, *self.output.parents)),
             'ordinary output path')
        self.used = 0

    def append_blob(self, stream, data):
        need(self.used + len(data) <= CAP - METADATA_RESERVE,
             'aggregate compressed output cap exhausted; no omitted frame may pass')
        stream.write(data)
        self.used += len(data)

    def json(self, name, value, *, failure=False):
        data = json_bytes(value)
        # Leave15MiB for the independent report; a failure may use at most1MiB.
        need(not failure or len(data) <= 2**20, 'bounded primary failure receipt')
        limit = CAP - (15 if failure else 16) * 2**20
        need(self.used + len(data) <= limit, 'bounded aggregate output plus failure reserve')
        path = self.output / name
        with path.open('xb') as stream:
            stream.write(data)
        self.used += len(data)
        return ref(path)


def encode(t, stream, budget, tensor, base):
    need(tensor.shape == base.shape and tensor.dtype == base.dtype == t.float32,
         'exact original tensor shape/dtype for lossless bytewise delta')
    actual = tensor_bytes(t, tensor); anchor = tensor_bytes(t, base)
    a = tensor.contiguous().view(t.uint8).reshape(-1)
    b = base.contiguous().view(t.uint8).reshape(-1)
    xor = t.bitwise_xor(a, b).numpy().tobytes()
    compressed = zlib.compress(xor, level=6)
    record = dict(codec='fp32-bytewise-xor-zlib/v1', offset=stream.tell(),
                  bytes=len(compressed), raw_bytes=len(actual), shape=list(tensor.shape),
                  dtype='torch.float32', actual_sha256=hashlib.sha256(actual).hexdigest(),
                  base_sha256=hashlib.sha256(anchor).hexdigest(),
                  compressed_sha256=hashlib.sha256(compressed).hexdigest())
    budget.append_blob(stream, compressed)
    return record


def decode(t, stream, record, base, expected_offset):
    need(record['codec'] == 'fp32-bytewise-xor-zlib/v1' and
         record['dtype'] == 'torch.float32' and record['shape'] == list(base.shape) and
         record['raw_bytes'] == base.numel() * 4 and
         record['offset'] == expected_offset and 0 < record['bytes'] <= record['raw_bytes'] + 2**16,
         'exact bounded contiguous blob segment and source tensor ABI')
    stream.seek(record['offset']); compressed = stream.read(record['bytes'])
    need(len(compressed) == record['bytes'] and
         hashlib.sha256(compressed).hexdigest() == record['compressed_sha256'],
         'actual compressed segment bytes')
    decoder = zlib.decompressobj()
    xor = decoder.decompress(compressed, record['raw_bytes'] + 1)
    need(len(xor) == record['raw_bytes'] and decoder.eof and
         not decoder.unused_data and not decoder.unconsumed_tail,
         'bounded exact-size zlib stream, no decompression padding/tail')
    anchor = tensor_bytes(t, base)
    need(hashlib.sha256(anchor).hexdigest() == record['base_sha256'],
         'lossless codec anchor is this exact captured original tensor')
    delta = t.frombuffer(bytearray(xor), dtype=t.uint8)
    raw = t.bitwise_xor(delta, base.contiguous().view(t.uint8).reshape(-1))
    actual = raw.numpy().tobytes()
    need(hashlib.sha256(actual).hexdigest() == record['actual_sha256'],
         'exact actual FP32 bytes recovered, never numerical reconstruction')
    tensor = raw.view(t.float32).reshape(base.shape)
    need(bool(t.isfinite(tensor).all()), 'actual recovered finite FP32 result')
    return tensor, expected_offset + record['bytes']
