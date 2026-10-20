"""Stdlib source/chain checks for a future MAIN-owned finite timing unit.

No tensor, container, subprocess or device API is imported or called here.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

IMAGE = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
FILES = ('timing_owner.py', 'timing_boot.py', 'consume_timing.py', 'timing_owner_common.py')
CONFIG = dict(warmup_pairs=4, sample_pairs=20, batch_iterations=4, cpu_threads=1,
    order='alternate-AB-BA-by-global-frame-and-pair-parity',
    clock='perf_counter_ns-with-symmetric-NPU-synchronize',
    terminal_policy='actual-r23-selected', frames='all192',
    layouts=['contiguous', 'column_strided'])
RUNTIME = {
    'triton_jit': ('/usr/local/python3.12.13/lib/python3.12/site-packages/triton/runtime/jit.py',
        36630, '8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad'),
    'triton_compiled': ('/usr/local/python3.12.13/lib/python3.12/site-packages/triton/compiler/compiler.py',
        18714, '4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b'),
    'ascend_compiler': ('/usr/local/python3.12.13/lib/python3.12/site-packages/triton/backends/ascend/compiler.py',
        53431, '253bdb0d9bf2d092c8c1ae40cc610b2d00c534b127f9d258e9e8e1a221934002')}
PINNED_TIMING = {
    'time_gdn.py': (30256, 'babb3d4f6e2c286229ba056060e023054237ea8bc826672350cd42a7157c82ff'),
    'timing_paths.py': (3481, '538c4d487c09cafe6f0cf0ce55bef01c25752d77a95fab32299dfae7d90fa121')}
PHASE = 1800
CLEANUP = 120
HANDOFF = 60
CAP = 192 * 2**20
ENV = dict(TORCH_DEVICE_BACKEND_AUTOLOAD='0', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
    ASCEND_RT_VISIBLE_DEVICES='0', BOLE_GDN3_TIMING_ENABLE='1', BOLE_GDN3_TRITON_ENABLE='1',
    TRITON_CACHE_DIR='/tmp/triton', VLLM_CACHE_ROOT='/tmp/vllm',
    ASCEND_PROCESS_LOG_PATH='/tmp/ascend/log')


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path); before = path.stat(); h = hashlib.sha256(); count = 0
    with path.open('rb') as f:
        for b in iter(lambda: f.read(2**20), b''):
            h.update(b); count += len(b)
    after = path.stat()
    need((before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_ino, after.st_size, after.st_mtime_ns) and count == after.st_size,
         'stable evidence read')
    return dict(path=str(path), bytes=count, sha256=h.hexdigest())


def checked(r):
    need(type(r) is dict and set(r) == {'path', 'bytes', 'sha256'} and
         type(r['path']) is str and type(r['bytes']) is int and r['bytes'] >= 0 and
         type(r['sha256']) is str and re.fullmatch('[0-9a-f]{64}', r['sha256']), 'exact Ref3')
    p = Path(r['path'])
    need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p, *p.parents))
         and ref(p) == r, 'exact ordinary absolute evidence bytes')
    return p


def obj(r):
    p = checked(r); need(r['bytes'] <= 16*2**20, 'bounded JSON evidence')
    def pairs(rows):
        d = {}
        for k, v in rows:
            need(k not in d, 'no duplicate JSON keys'); d[k] = v
        return d
    return json.loads(p.read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('finite JSON')))


def write(p, value):
    p = Path(p)
    with p.open('x') as f:
        json.dump(value, f, sort_keys=True, allow_nan=False, separators=(',', ':')); f.write('\n')
    return ref(p)


def load(r, name):
    p = checked(r)
    if name in sys.modules:
        m = sys.modules[name]; need(ref(m.__file__) == r, 'no ambient helper'); return m
    s = importlib.util.spec_from_file_location(name, str(p)); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    try:
        s.loader.exec_module(m); need(ref(p) == r, 'source stable across import')
    except BaseException:
        sys.modules.pop(name, None); raise
    return m


def inspection(r):
    x = obj(r)
    if type(x) is list:
        need(len(x) == 1, 'singleton raw inspection'); x = x[0]
    need(type(x) is dict, 'actual raw inspection dictionary')
    return x


def runtime_refs():
    return {k: dict(path=p, bytes=n, sha256=h) for k, (p, n, h) in RUNTIME.items()}


def package(reference, own_file):
    """Bootstrap only our stdlib module, after checking all executable bytes."""
    x = obj(reference)
    need(x['schema'] == 'bole.gdn3-timing-owner-inputs/v1' and x['authority'] == 'MAIN' and
         set(x['files']) == set(FILES), 'exact reviewed owner source closure')
    for r in x['files'].values():
        checked(r)
    need(ref(__file__) == x['files']['timing_owner_common.py'] and
         ref(own_file) == x['files'][Path(own_file).name] and
         all(Path(r['path']).parent == Path(own_file).parent for r in x['files'].values()),
         'one new private source leaf, no mixed source imports')
    need(x['phase_seconds'] == PHASE and x['cleanup_seconds'] == CLEANUP and
         x['handoff_seconds'] == HANDOFF and x['output_cap_bytes'] == CAP and
         x['image'] == IMAGE, 'finite preregistered owner limits and exact same image')
    return x


def prior_chain(x, *, installed):
    """Independent successful replay chain is required BEFORE new admission.

    installed=False checks host copies; installed=True also reopens installed
    container paths. Host evidence and runtime refs deliberately stay distinct.
    """
    checked(x['baseline_owner'])
    need(x['baseline_owner']['sha256'] ==
         '18ce957ef0a8130e64d73f7c73a99536e19f283ea68e09620c6b328fd089a195', 'exact actual V2 owner baseline')
    checked(x['replay_audit'])
    need((x['replay_audit']['bytes'], x['replay_audit']['sha256']) ==
         (2942, '76ab5d53fe7bd2156b42803ca6e328343a74aa43226b9c5dbb6d9d50b75c516a'),
         'exact locally supplied actual V2 audit bytes')
    audit = obj(x['replay_audit']); m = x['timing_template']
    need(audit['schema'] == 'bole.gdn3-actual-independent-audit/v1' and
         audit['primary'] is None and audit['secondary'] == [] and
         audit['source_before_after_equal'] is True and audit['all_owned_containers_stopped_retained'] is True and
         audit['actual_frames'] == 192 and audit['actual_frame_layouts'] == 384 and
         audit['component_replay_independent_pass'] is True, 'actual independently successful v2 audit')
    need(m['schema'] == 'bole.gdn3-warmed-timing-manifest/v1' and m['configuration'] == CONFIG and
         m['admission'] is None and set(m['files']) == set(PINNED_TIMING) and
         all(m[k] == audit[a] for k, a in (('replay_manifest', 'manifest'), ('replay_result', 'replay'),
             ('replay_independent', 'independent'), ('replay_release', 'release'))),
         'frozen timing template joins exact actual successful chain; admission awaits real inspection')
    for k, (n, h) in PINNED_TIMING.items():
        checked(m['files'][k]); need((m['files'][k]['bytes'], m['files'][k]['sha256']) == (n, h),
                                   'frozen timing executable bytes ' + k)
    need(m['runtime_sources'] == runtime_refs() and set(x['runtime_host_evidence']) == set(RUNTIME),
         'exact installed runtime path mapping')
    for k, r in x['runtime_host_evidence'].items():
        checked(r); p, n, h = RUNTIME[k]
        need(r['path'] != p and (r['bytes'], r['sha256']) == (n, h),
             'host copy must match content and remain a distinct path')
        if installed:
            checked(m['runtime_sources'][k])
    driver = load(m['files']['time_gdn.py'], '_bole_owner_frozen_timing')
    # bootstrap expects a manifest ref; before admission, load H by exact replay closure.
    replay = obj(m['replay_manifest'])
    H = load(replay['files']['replay_common.py'], '_bole_owner_replay_common')
    replay, receipts, admission = driver.successful_replay(H, m)
    need(admission['image_digest'] == IMAGE and replay['admission'] == audit['admission'],
         'same actual replay admission/image')
    owner = obj(audit['owner'])
    need(owner['schema'] == 'bole.gdn3-finite-owner/v1' and owner['primary'] is None and
         owner['secondary'] == [] and owner['manifest'] == m['replay_manifest'] and
         owner['admission'] == audit['admission'] and owner['replay_result'] == m['replay_result'] and
         owner['release'] == m['replay_release'] and owner['physical'] == [4] and
         owner['protected'] == [0, 1, 2, 3] and owner['source_before'] == owner['source_after'],
         'exact successful actual owner/replay/release/source chain')
    for r in owner['source_before'].values():
        checked(r)
    need(owner['owner_source']['sha256'] == x['baseline_owner']['sha256'], 'actual owner bytes equal baseline')
    checked(owner['owner_source'])
    for cid in (owner['cid'], owner['cpu_cid']):
        need(type(cid) is str and re.fullmatch('[0-9a-f]{64}', cid), 'actual prior owned identities')
    return driver, H, replay, receipts, admission, audit


def device_inspection(x, *, cid, running, name, cpu=False):
    need(x['Id'] == cid and x['Image'] == IMAGE and x['State']['Running'] is running and
         x['Config']['Labels']['model-tuning-lab.owner'] == name, 'actual exact owned identity/image/label/state')
    hc = x['HostConfig']
    need(hc['Privileged'] is False and hc['ReadonlyRootfs'] is True and hc['NetworkMode'] == 'none' and
         hc['Memory'] == (2**30 if cpu else 8*2**30) and hc['MemorySwap'] == hc['Memory'] and
         hc['CpusetCpus'] == ('145' if cpu else '0,1,2,3') and
         hc['PidsLimit'] == (128 if cpu else 512), 'bounded owner resources, read-only root, no network')
    devices = hc['Devices'] or []
    expected = set() if cpu else {('/dev/davinci4', '/dev/davinci0'),
        ('/dev/davinci_manager', '/dev/davinci_manager'), ('/dev/devmm_svm', '/dev/devmm_svm'), ('/dev/hisi_hdc', '/dev/hisi_hdc')}
    need({(d['PathOnHost'], d['PathInContainer']) for d in devices} == expected and len(devices) == len(expected),
         'exact singleton physical4-to-guest0 or Devices[] mapping')
    need(hc.get('CapDrop') == ['ALL'] and 'no-new-privileges' in hc.get('SecurityOpt', []), 'same no-privilege protections')
    opts = hc['Tmpfs']['/tmp'].split(',')
    need('rw' in opts and 'exec' in opts and 'noexec' not in opts and
         'size=' + str(64*2**20 if cpu else 2**30) in opts, 'explicit executable bounded private tmpfs')
    need(hc['ShmSize'] == (64*2**20 if cpu else 2**30), 'bounded private shared memory')
    if not running:
        need(x['State']['Pid'] == 0 and not x.get('ExecIDs'), 'owned process stopped and no exec children')
    return x


def admission(x, m, *, current):
    a = obj(m['admission']); run = inspection(a['controller_inspection'])
    need(a['schema'] == 'bole.gdn3-timing-owned-admission/v1' and a['authority'] == 'MAIN' and
         a['actual_source'] == obj(m['replay_manifest'])['actual_source'] and
         a['replay_result'] == m['replay_result'] and a['independent_replay'] == m['replay_independent'] and
         a['image_digest'] == IMAGE and a['physical_devices'] == [4] and a['logical_devices'] == [0] and
         a['guest_device_path'] == '/dev/davinci0' and a['allow_hf32'] is False and a['environment'] == ENV,
         'new actual source-bound same-image HF32-off timing admission')
    device_inspection(run, cid=a['owned_container_id'], running=True, name=x['name'])
    env = dict(v.split('=', 1) for v in run['Config']['Env'] if '=' in v)
    need(all(env.get(k) == v for k, v in ENV.items()), 'actual inspect environment matches admission')
    # Every source/evidence mount must be read-only; only the new output is writable.
    mounts = run['Mounts']; output = str(Path(m['admission']['path']).parent)
    need(sum(z['Destination'] == output and z['RW'] is True and z['Type'] == 'bind' for z in mounts) == 1,
         'one dedicated actual writable output bind')
    need(all(z['RW'] is False or (z['Type'] == 'bind' and z['Destination'] == output) or
             (z['Type'] == 'tmpfs' and z['Destination'] == '/tmp') for z in mounts),
         'all mounted successful chain/source/driver evidence read-only')
    if current:
        need(a['owned_container_id'] in Path('/proc/self/cgroup').read_text(), 'actual admitted cgroup before tensor import')
        need(all(os.environ.get(k) == v for k, v in ENV.items()), 'current exact admitted environment')
    return a


def final_manifest(x, manifest_ref, *, current):
    m = obj(manifest_ref); template = dict(x['timing_template']); template['admission'] = m['admission']
    need(m == template and m['admission'] is not None, 'only post-inspection admission differs from reviewed template')
    admission(x, m, current=current)
    return m


def snapshot(x, inputs_ref):
    """All referenced sources/evidence, raw captures and original replay exports."""
    refs = {}
    def walk(v):
        if type(v) is dict:
            if set(v) == {'path', 'bytes', 'sha256'}:
                # Installed paths do not exist on the host; distinct host evidence is checked instead.
                if v not in runtime_refs().values():
                    checked(v); refs[v['path']] = v
            else:
                for value in v.values(): walk(value)
        elif type(v) in (list, tuple):
            for value in v: walk(value)
    walk(inputs_ref); walk(x)
    audit = obj(x['replay_audit']); walk(audit)
    for r in (audit['manifest'], audit['owner'], audit['replay'], audit['independent'], audit['release'], audit['admission']):
        walk(obj(r))
    replay = obj(audit['manifest'])
    # The original source ticket itself and the exact seven mathematical helper
    # refs are in replay; unrelated model-server files are not read by timing.
    for pair in replay['receipts']: walk(obj(pair['receipt']))
    for rr in obj(audit['replay'])['ranks']: walk(obj(rr))
    for key in ('controller_inspection', 'r23_controller_inspection'):
        walk(obj(audit['admission'])[key])
    return refs


def unchanged(before):
    return all(ref(path) == r for path, r in before.items())
