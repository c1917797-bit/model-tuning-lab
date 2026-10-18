"""CPU-only consumer successor; original R36 model/data identities stay frozen.

The original H017/008 controller is source-derived exactly as in R36.  The
independent consumer manifest and all its files join H.bind's complete readset;
they are never represented as bytes of an old model or payload file.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
import time
from pathlib import Path, PurePosixPath

ROOT = Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-geometry-consumer-renew24h-20261018-001')
MODEL_ROOT = Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001')
OUT = Path('/opt/host/vnf/austinov/run-deltalog-R36-geometry-consumer-MAIN-RENEW24H_001')
PAYLOAD_LEAF = Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-renew24h-R36publication-20261017-001')
IDENTITY = dict(owner='NEW24H_R36_GEOMETRY_CONSUMER_001', run_id='NEW24H_R36_GEOMETRY_CONSUMER_001', container_prefix='deltalog-R36-geometry-consumer-')
AUTHORITY = dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/RENEW24H_AUTHORITY_20261017_084320.json', bytes=3012, sha256='cdba34641b429a6132e7af5a6a88a93b63faf7d0834a9313a8b948e2a4907b6d')
MODEL_TEMPLATE = dict(path=str(MODEL_ROOT / 'SOURCE_TEMPLATE.json'), bytes=290569, sha256='fc4fbbcd1846a247717ffaf5883ff77ade4fee045f965e78034a4b45cf881ac3')
BUDGET = dict(cutoff_epoch=1792313000, whole_seconds=3600, cleanup_seconds=270, postverify_seconds=900, margin_seconds=90, child_max_seconds=900)


def need(value, message):
    if not value:
        raise ValueError(message)


def ref_shape(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    need(type(value['path']) is str and Path(value['path']).is_absolute()
         and '..' not in Path(value['path']).parts and str(Path(value['path'])) == value['path'], 'canonical absolute Ref path')
    need(type(value['bytes']) is int and value['bytes'] >= 0, 'integer Ref byte count')
    digest = value['sha256']
    need(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'canonical Ref SHA256')
    return value


def checked(value):
    ref_shape(value)
    path = Path(value['path'])
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and not any(p.is_symlink() for p in (path, *path.parents)), 'ordinary exact source/evidence file')
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
            size += len(chunk)
    after = path.lstat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(fields(before) == fields(after) and size == value['bytes'] and digest.hexdigest() == value['sha256'], 'stable complete immutable Ref bytes')
    return path


def obj(value):
    path = checked(value)
    need(value['bytes'] <= 4 * 2**20, 'bounded source/control JSON')
    body = path.read_bytes()
    need(len(body) == value['bytes'] and hashlib.sha256(body).hexdigest() == value['sha256'], 'same JSON bytes after complete Ref check')

    def pairs(rows):
        result = {}
        for key, item in rows:
            need(key not in result, 'duplicate JSON key')
            result[key] = item
        return result

    def constant(value):
        raise ValueError('nonfinite JSON constant ' + value)

    return json.loads(body, object_pairs_hook=pairs, parse_constant=constant)


def module(value, name):
    path = checked(value)
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, 'loadable declared source')
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    checked(value)
    return result


def consumer_source(source_ref):
    source = obj(source_ref)
    need(source_ref['path'] == str(ROOT / 'SOURCE_MANIFEST.json'), 'actual new consumer manifest, not a template or replay path')
    need(source['schema'] == 'deltalog.geometry-consumer-source/v1' and source['root'] == str(ROOT), 'exact independent consumer source identity')
    need(source['default_enabled'] is False and source['prepared_only'] is False, 'bound default-OFF consumer source')
    need(source.get('qualified', False) is False and source.get('NPU', False) is False, 'consumer source grants no qualification or NPU admission')
    need(source['output_root'] == str(OUT) and source['runtime_identity'] == IDENTITY, 'exact new owner/output identity')
    need(source['authority_ref'] == AUTHORITY, 'unchanged renewal authority')
    for key, value in BUDGET.items():
        need(type(source[key]) is int and source[key] == value, 'unchanged consumer resource clock: ' + key)
    ref_shape(source['model_source'])
    ref_shape(source['payload_source'])
    need(source['model_source']['path'] == str(MODEL_ROOT / 'SOURCE_MANIFEST.json'), 'original actual R36 model source')
    files = source['files']
    required = {'host_consumer.py', 'postconsume_recipe_new.py', 'postconsume_entry_new.py',
                'consumer_cli.py', 'consume_rank_new.py', 'geometry_witness.py', 'test_geometry_witness.py'}
    need(type(files) is dict and required <= set(files), 'complete consumer entry/recipe/CLI source closure')
    total = 0
    for name, value in files.items():
        need(type(name) is str, 'source leaf name')
        relative = PurePosixPath(name)
        need(str(relative) == name and not relative.is_absolute() and '..' not in relative.parts, 'ordinary declared relative source leaf')
        need(value['path'] == str(ROOT / name) and value['bytes'] <= 4 * 2**20, 'source leaf exact path and small-source cap')
        checked(value)
        total += value['bytes']
    need(total <= 64 * 2**20, 'bounded complete consumer source closure')
    need(Path(__file__).resolve() == checked(files['host_consumer.py']), 'actual independent host source file')
    checked(AUTHORITY)
    return source


def original_model(source):
    model = obj(source['model_source'])
    need(model['root'] == str(MODEL_ROOT) and model['prepared_only'] is False and model['default_enabled'] is False, 'actual frozen bound R36 model')
    need(model['prepared_template'] == MODEL_TEMPLATE, 'same reviewed R36 publication template')
    need(model['firstdecode_contract']['payload_source'] == source['payload_source'], 'original frozen model/payload join')
    need(model['authority'] == source['authority_ref'] and model['cutoff_epoch'] == BUDGET['cutoff_epoch'], 'unchanged model authority and cutoff')
    for value in model['files'].values():
        checked(value)
    sys.path.insert(0, str(MODEL_ROOT))
    overlay = module(model['files']['owner_overlay.py'], 'owner_overlay')
    need(overlay.current(source['model_source']) == model, 'original model source checker unchanged')
    return model, overlay


def old_output_absent(model):
    old = Path(model['postconsumer_output_root'])
    need(old.is_absolute() and old != OUT and old.parent == OUT.parent, 'distinct original and new CPU output roots')
    need(not any(p.is_symlink() for p in old.parents), 'ordinary original CPU output parents')
    need(not os.path.lexists(old), 'original postconsumer output must remain absent; never omit retained CPU output from accounting')
    return old


def geometry_readset(consumer_ref, source, post, geometry_ref):
    sidecar = obj(geometry_ref)
    need(type(sidecar) is dict and set(sidecar) == {'schema', 'consumer_source', 'model_source', 'payload_source', 'reports_ref', 'geometry'}, 'exact independent geometry sidecar')
    need(sidecar['schema'] == 'deltalog.geometry-witness-refs/v1' and sidecar['consumer_source'] == consumer_ref, 'source-bound geometry witness sidecar')
    need(sidecar['model_source'] == source['model_source'] and sidecar['payload_source'] == source['payload_source'] and sidecar['reports_ref'] == post['reports_ref'], 'same original model/payload/report witness relation')
    reports = obj(post['reports_ref'])['reports']
    rows = sidecar['geometry']
    need(type(rows) is list and len(rows) == 4 and [r['rank'] for r in rows] == [0, 1, 2, 3], 'all four geometry ranks exactly once in order')
    seen_reports, seen_geometry = set(), set()
    refs = [geometry_ref]
    for row in rows:
        need(type(row) is dict and set(row) == {'rank', 'namespace_pid', 'report_ref', 'geometry_ref'}, 'exact geometry witness row')
        need(type(row['rank']) is int and type(row['namespace_pid']) is int and row['namespace_pid'] > 0, 'actual rank/namespace PID types')
        need(row['report_ref'] in reports, 'geometry witness joins an original report Ref')
        report_key = json.dumps(ref_shape(row['report_ref']), sort_keys=True)
        geometry_key = json.dumps(ref_shape(row['geometry_ref']), sort_keys=True)
        need(report_key not in seen_reports and geometry_key not in seen_geometry, 'distinct report and geometry witnesses')
        seen_reports.add(report_key)
        seen_geometry.add(geometry_key)
        path = Path(row['geometry_ref']['path'])
        need(PAYLOAD_LEAF in path.parents, 'actual geometry witness within original retained payload')
        checked(row['geometry_ref'])
        refs.append(row['geometry_ref'])
    return refs


def unique_refs(refs):
    result = {}
    for value in refs:
        ref_shape(value)
        need(value['path'] not in result or result[value['path']] == value, 'no conflicting Ref for one source/evidence path')
        result[value['path']] = value
    return list(result.values())


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--source-audit', action='store_true')
    parser.add_argument('--source-ref')
    parser.add_argument('--postconsume-input-ref')
    parser.add_argument('--geometry-refs-ref')
    args = parser.parse_args()
    if not (args.execute or args.source_audit):
        print(json.dumps(dict(enabled=False, NPU=False, qualified=False)))
        return 0
    begun = time.monotonic()
    need(args.source_ref is not None, 'independent consumer source Ref required')
    need(bool(args.postconsume_input_ref) == bool(args.geometry_refs_ref), 'actual INPUT and independent geometry sidecar must be supplied together')
    need(not args.execute or args.postconsume_input_ref is not None, 'CPU-only execute requires actual postconsumer inputs; no model fallback')
    consumer_ref = json.loads(args.source_ref)
    source = consumer_source(consumer_ref)
    model, O = original_model(source)
    model_ref = source['model_source']
    old_output_absent(model)
    for value in model['dependencies']:
        O.obj_file(value)
    FR = module(model['files']['firstdecode_refs.py'], 'firstdecode_refs')
    input_ref = json.loads(args.postconsume_input_ref) if args.postconsume_input_ref else None
    geometry_ref = json.loads(args.geometry_refs_ref) if args.geometry_refs_ref else None
    post_refs = []
    if input_ref is not None:
        post, post_refs = FR.post(O, model, input_ref)
        need(post['model_source'] == model_ref, 'same original R36 model source in actual INPUT')
        post_refs += geometry_readset(consumer_ref, source, post, geometry_ref)
    H = module(model['host017_ref'], '_geometry_consumer_original017_host')
    W = module(model['files']['window_overlay.py'], 'window_overlay')
    O.obj_file(W.AUTHORITY)
    W.install(H, model)
    original_adapt = H.adapt

    def adapted(text, sr, pr):
        value, original_pairs = original_adapt(text, sr, pr)
        value = W.transform(value)
        before = value
        identity = model['runtime_identity']
        changes = [
            ('lowbit/deltalog-service-empirical-owned-v1-017', 'lowbit/' + MODEL_ROOT.name),
            ('OUT = PREP / "lowbit/run-deltalog-service-empirical-main-NEW48H_017_001"', 'OUT = Path(' + json.dumps(str(OUT)) + ')'),
            ('need(free >= S.RESERVE + (S.WORKSPACE if initial else 0), "actual Docker root storage reserve")', '_EXTERNAL.docker_gate(self, S, free, initial)'),
            ('S.OWNER = ' + json.dumps(identity['owner']), 'S.OWNER = ' + json.dumps(IDENTITY['owner'])),
            ('self.name = ' + json.dumps(identity['container_prefix']) + ' + leaf.name', 'self.name = ' + json.dumps(IDENTITY['container_prefix']) + ' + leaf.name'),
            ('run_id = ' + json.dumps(identity['run_id']), 'run_id = ' + json.dumps(IDENTITY['run_id'])),
        ]
        for old, new in changes:
            need(value.count(old) == 1, 'single declared consumer output/identity/policy source seam')
            value = value.replace(old, new)
        inverse = value
        for old, new in reversed(changes):
            need(inverse.count(new) == 1, 'unique consumer adaptation inverse')
            inverse = inverse.replace(new, old)
        need(inverse == before, 'whole consumer delta inverse; original resource/cleanup code unchanged')
        return value, [*original_pairs, *((old, new, 1) for old, new in changes)]

    def leaf(name):
        value = model['files'].get(name, model['owner017_files'].get(name))
        need(value is not None, 'original model/donor-declared helper only')
        return module(value, '_geometry_original_' + name[:-3])

    def original_source(digest):
        need(digest == model_ref['sha256'], 'original model source digest retained')
        return O.current(model_ref)

    H.HERE = MODEL_ROOT
    H.DEPLOY = MODEL_ROOT
    H.OUT = OUT
    H.adapt = adapted
    H.leaf = leaf
    H.source = original_source
    refs = unique_refs([model_ref, *model['files'].values(), *model['dependencies'], *FR.refs(O, model), *post_refs, *O.transitive_refs(model), consumer_ref, *source['files'].values()])
    O.model_gate(model)
    component_owner = model['bridge024_owner_ref']
    h, pairs = H.bind(model_ref, component_owner, refs)
    h._EXTERNAL = leaf('external_output_policy.py')
    if args.source_audit:
        need(not any(name in sys.modules for name in ('torch', 'torch_npu', 'vllm', 'vllm_ascend')), 'host source-only audit')
        print(json.dumps(dict(schema='deltalog.geometry-consumer-source-audit/v1', consumer_source=consumer_ref, model_source=model_ref, payload_source=source['payload_source'], readset=refs, actual_inputs_checked=input_ref is not None, actual_owned_controller=model['host017_ref'], output_root=str(OUT), runtime_identity=IDENTITY, registered_inverse_deltas=len(pairs), NPU=False, resources_admitted=False, qualified=False)))
        return 0
    need(sys.platform == 'linux' and Path(__file__).resolve() == ROOT / 'host_consumer.py', 'actual reviewed Linux consumer deployment')
    need(not os.path.lexists(OUT), 'exclusive new consumer output root; retain earlier attempts')
    H.protect_cleanup(h)
    original_safety = h.safety
    secondary = []

    def absence(terminal=False):
        try:
            return old_output_absent(model)
        except BaseException as error:
            message = 'original postconsumer absence violation: ' + repr(error)
            if message not in secondary:
                secondary.append(message)
            if not terminal:
                raise
            return Path(model['postconsumer_output_root'])

    def safety(source_ref, policy, started):
        absence()
        base, S, Owned, state = original_safety(source_ref, policy, started)
        need(S.MEM == 32 * base.GIB and S.HOST_MEM == 512 * 1024**2 and S.RESERVE == 8 * base.GIB, 'unchanged original CPU8/model32 host/reserve machinery')
        state['stage_resource_contract'].update(model_initial_GiB=40.5, model_guest_GiB=32, actual_model_guest_GiB=32, host_GiB=.5, reserve_GiB=8)
        FD = module(model['files']['firstdecode_output_policy.py'], 'firstdecode_output_policy')
        B = module(model['files']['model_snapshot_budget.py'], 'model_snapshot_budget')
        extra = FR.payload_roots(O, model) + (model['output_root'], str(B.LEAF))
        state['external_output_policy'] = FD.install(h._EXTERNAL, S, Owned, base, h.OUT, model['ownership_observation_refs']['safety'], B.LEAF, extra)
        original_create = Owned.create_native

        def cpu_create(ctl, model_value, cpu):
            absence()
            need(cpu is True and Path(ctl.out) == OUT / 'cpu-consumer', 'consumer-only original Devices-empty creation, no NPU branch')
            result = original_create(ctl, model_value, cpu)
            absence()
            return result

        Owned.create_native = cpu_create
        return base, S, Owned, state

    h.safety = safety
    FD = module(model['files']['firstdecode_owner.py'], 'firstdecode_owner')
    lease = FD.lease(O, model, model_ref)
    original_opt_bytes = lease.opt_bytes
    original_check = lease.check

    def opt_bytes():
        old = absence(terminal=lease.terminal)
        value = original_opt_bytes()
        # A violated absence predicate never yields PASS.  During emergency
        # cleanup, charge an appearing old tree too; do not mask owned stop by
        # pretending that retained output is unaccounted free space.
        if lease.terminal and os.path.lexists(old):
            value += lease.opt_usage(old)
        absence(terminal=lease.terminal)
        return value

    def lease_check():
        absence(terminal=lease.terminal)
        value = original_check()
        absence(terminal=lease.terminal)
        return value

    lease.opt_bytes = opt_bytes
    lease.check = lease_check
    h._SNAPSHOT = lease
    h._CONSUMER_SOURCE = consumer_ref
    h._CONSUMER_MANIFEST = source
    h._CONSUMER_MODEL = model
    h._CONSUMER_SECONDARY = secondary
    h._CONSUMER_ABSENCE = absence
    recipe = module(source['files']['postconsume_recipe_new.py'], '_source_bound_geometry_consumer_recipe')
    h.run = lambda sr, started: recipe.run(h, sr, component_owner, min(started, begun), input_ref, consumer_ref, geometry_ref)
    # The generated original controller remains model-source-bound.  H.bind's
    # immutable source fence also checks the independent consumer and all new
    # code/evidence refs, and the new RESULT records both identities explicitly.
    need(min(BUDGET['whole_seconds'] - (time.monotonic() - begun), BUDGET['cutoff_epoch'] - time.time()) > 1260, 'positive original work budget after whole preparation and cleanup/postverify/margin')
    return h.main(['--execute', '--source-sha256', model_ref['sha256']])


if __name__ == '__main__':
    raise SystemExit(main())
