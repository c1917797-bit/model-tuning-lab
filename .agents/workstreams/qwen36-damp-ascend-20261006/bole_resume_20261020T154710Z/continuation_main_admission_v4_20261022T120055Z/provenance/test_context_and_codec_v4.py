"""Source-derived private-context controls with synthetic owners/inspect only.

Original helper bodies are taken from MAIN's exact saved source projections.
The reference reader and one original safety source-path read are local fixture
transports. No raw historical owner chain or live Docker/NPU is exercised.
"""
import ast
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import types
import unittest
from unittest import mock
import zlib

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), 'exec'), value.__dict__)
    return value


H = module('_history_source_control', HERE/'historical_owner_context_v1.py')
K = module('_codec_source_control', HERE/'complete_inspect_receipt_v1.py')


def source_fixture():
    sources = json.loads((HERE.parent/'continuation_actual/SOURCE_CONTEXTS.json').read_bytes())['record']
    installers = json.loads((HERE.parent/'continuation_actual/CONTEXT_INSTALLERS.json').read_bytes())['record']
    contexts = copy.deepcopy(sources['source_contexts'])
    by_source = {row['source']['path']: row for row in installers['source_contexts']}
    bodies = {}
    for row in [*sources['texts_by_sha256'].values(), *installers['texts_by_sha256'].values()]:
        body = row['text'].encode()
        assert len(body) == row['bytes'] and hashlib.sha256(body).hexdigest() == row['sha256']
        bodies[row['sha256']] = body
    originals = dict(model_contract='boundary_resource_input/original025_model_contract.py',
                     safety_host='formal_review_input/source/base/safety_host.py',
                     host_once='formal_review_input/source/base/host_once.py')
    for key, relative in originals.items():
        body = (HERE.parent/relative).read_bytes()
        assert (len(body), hashlib.sha256(body).hexdigest()) == (H.ORIGINAL[key]['bytes'], H.ORIGINAL[key]['sha256'])
        bodies[H.ORIGINAL[key]['sha256']] = body
    for row in contexts:
        row['files'].update(by_source[row['source']['path']]['files'])
        # These fields are synthetic fixture data. The tested roles are
        # nonconsumers, so the original consumer branch is never entered.
        row['model_receipt_root'] = row['output_root']+'/dense'
        row['stream_channel_root'] = row['model_receipt_root']+'/STREAM'

    class Reader:
        def read(self, reference, keep=True):
            body = bodies[reference['sha256']]
            assert len(body) == reference['bytes'] and hashlib.sha256(body).hexdigest() == reference['sha256']
            return body if keep else reference

    return contexts, bodies, Reader()


def active_fixture(current, bodies):
    raw_c, raw_s = (bodies[H.ORIGINAL[key]['sha256']] for key in ('model_contract', 'safety_host'))
    c = types.ModuleType('_active_fixture_c')
    c.__dict__['Path'] = Path
    H.evaluate(H.assignments(raw_c, {'ROOT', 'GIB', 'IMAGE'}) + H.functions(raw_c, {'require'}), c.__dict__, 'fixture-c')
    c.CUTOFF, c.CUT = 1792692055, '2026-10-22T18:00:55+00:00'
    S = types.ModuleType('_active_fixture_S')
    S.__file__ = H.ORIGINAL['safety_host']['path']
    S.__dict__.update(c=c, Path=Path, re=re)
    H.evaluate(H.assignments(raw_s, {'DOCKER', 'SMI', 'PRLIMIT', 'MEM', 'HOST_MEM', 'RESERVE', 'WORKSPACE',
                                   'PHASE', 'CLEANUP', 'OWNER', 'PHYSICAL'}) +
               H.functions(raw_s, {'environment', 'labels', 'device_map', 'create_argv', 'validate_inspect'}),
               S.__dict__, 'fixture-safety')
    S.MEM, S.RESERVE, S.PHASE, S.CLEANUP, S.OWNER = 32*c.GIB, 8*c.GIB, 3600, 180, 'bole-root-r6-20261017-001'
    S.original_env = S.environment
    H.evaluate(H.functions(bodies[current['files']['owned_substrate.py']['sha256']], {'environment'}, parent='load'),
               S.__dict__, 'fixture-owned-env')
    external = H.module(bodies[current['files']['external025.py']['sha256']], '_active_fixture_external', 'fixture-external')
    external.OUT = Path(current['output_root'])
    S._EXTERNAL = types.SimpleNamespace(environment=external.environment, LOG=external.LOG)
    adapter = {}
    H.evaluate(H.functions(bodies[current['files']['g2_host_adapter.py']['sha256']], {'derive'}), adapter, 'fixture-adapter')
    text, _ = adapter['derive'](raw_s, external)
    H.evaluate(H.functions(text, {'create_argv', 'validate_inspect'}), S.__dict__, 'fixture-derived')
    return S, external


def owner_fixture(source, arm):
    leaf = source['output_root']+'/'+arm
    return dict(cid=('1' if arm == 'dense' else '2')*64, name='exact-fixture-'+arm,
        image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',
        arm=arm, source=source['source'], host_sha256=H.ORIGINAL['safety_host']['sha256'],
        guest_cpus=[0, 1, 2] if arm == 'dense' else [145],
        mounts={'/adakv-results': [leaf, True], source['root']: [source['root'], False]})


class ContextControls(unittest.TestCase):
    def setup_values(self):
        contexts, bodies, reader = source_fixture()
        S, external = active_fixture(contexts[-1], bodies)
        original_read = Path.read_bytes
        def source_path_read(path):
            if str(path) == H.ORIGINAL['safety_host']['path']:
                return bodies[H.ORIGINAL['safety_host']['sha256']]
            return original_read(path)
        return contexts, bodies, reader, S, external, source_path_read

    def test_six_role_contexts_accept_old_output_leave_active_unchanged(self):
        contexts, bodies, reader, S, external, path_reader = self.setup_values()
        with mock.patch.dict(sys.modules, {'external025': external}), mock.patch.object(Path, 'read_bytes', path_reader):
            baseline = H.active_fingerprint(S)
            for source in contexts[:-1]:
                for arm in ('cpu-preflight', 'dense'):
                    owned = owner_fixture(source, arm)
                    with self.assertRaisesRegex(ValueError, 'exact new064 opt stage'):
                        S.create_argv(owned)
                    context = H.build(reader, source, owned, contexts[-1], S)
                    argv = context.create_argv(owned)
                    self.assertEqual(argv[0:2], ['/usr/bin/docker', 'create'])
                    self.assertIn('HOME=/adakv-results/.runtime/home', argv)
                    self.assertIn('model-tuning-lab.source-manifest-sha256='+source['source']['sha256'], argv)
                    self.assertEqual(H.active_fingerprint(S), baseline)
                    self.assertEqual(context.proof['cap32']['model_initial_GiB'], 40.5)
                    changed = dict(owned, arm='stream-consumer')
                    with self.assertRaisesRegex(ValueError, 'context bound'):
                        context.create_argv(changed)

    def test_wrong_old_output_and_changed_active_output_rejected(self):
        contexts, bodies, reader, S, external, path_reader = self.setup_values()
        with mock.patch.dict(sys.modules, {'external025': external}), mock.patch.object(Path, 'read_bytes', path_reader):
            owned = owner_fixture(contexts[0], 'dense')
            wrong = dict(contexts[0], output_root=contexts[-1]['output_root'])
            with self.assertRaisesRegex(ValueError, 'source/output/owned-leaf'):
                H.build(reader, wrong, owned, contexts[-1], S)
            context = H.build(reader, contexts[0], owned, contexts[-1], S)
            original = external.OUT
            external.OUT = Path('/unexpected-current-context')
            try:
                with self.assertRaisesRegex(ValueError, 'active context unchanged'):
                    context.create_argv(owned)
            finally:
                external.OUT = original
            context.create_argv(owned)

    def test_full_original_inspect_predicates_still_reject_resource_and_env_change(self):
        contexts, bodies, reader, S, external, path_reader = self.setup_values()
        with mock.patch.dict(sys.modules, {'external025': external}), mock.patch.object(Path, 'read_bytes', path_reader):
            owned = owner_fixture(contexts[0], 'dense')
            context = H.build(reader, contexts[0], owned, contexts[-1], S)
            argv = context.create_argv(owned)
            option_values = lambda flag: [argv[i+1] for i, arg in enumerate(argv[:-1]) if arg == flag]
            labels = dict(value.split('=', 1) for value in option_values('--label'))
            value = dict(Id=owned['cid'], Image=owned['image'], Name='/'+owned['name'],
                Config=dict(Image=owned['image'], Entrypoint=['/bin/bash'], Cmd=['-c', 'exec /bin/sleep infinity'],
                            WorkingDir=str(S.c.ROOT), Labels=labels, Env=option_values('--env')),
                HostConfig=dict(ReadonlyRootfs=True, LogConfig=external.LOG, Tmpfs=None,
                    Privileged=False, Memory=32*S.c.GIB, MemorySwap=32*S.c.GIB, NanoCpus=3*10**9,
                    CpusetCpus='0,1,2', IpcMode='private', NetworkMode='none', ShmSize=4*S.c.GIB,
                    PidsLimit=2048, DeviceRequests=None, DeviceCgroupRules=None,
                    CapDrop=['ALL'], SecurityOpt=['no-new-privileges'],
                    Devices=[dict(PathOnHost=k, PathInContainer=v, CgroupPermissions='rwm') for k,v in S.device_map().items()]),
                Mounts=[dict(Type='bind', Destination=k, Source=v[0], RW=v[1]) for k,v in owned['mounts'].items()])
            context.validate_inspect(value, owned)
            for mutate in (lambda v: v['HostConfig'].__setitem__('Memory', 64*S.c.GIB),
                           lambda v: v['HostConfig']['Devices'][0].__setitem__('PathOnHost', '/dev/davinci0'),
                           lambda v: v['Config']['Env'].append('HOME=/wrong'),
                           lambda v: v['Config']['Labels'].__setitem__('model-tuning-lab.owner', 'foreign')):
                bad = copy.deepcopy(value)
                mutate(bad)
                with self.assertRaises(ValueError):
                    context.validate_inspect(bad, owned)


class CodecControls(unittest.TestCase):
    def sample(self):
        return dict(requested_argv=['/usr/bin/docker', 'inspect', 'a'*64], exit_code=0,
                    error=None, stderr='', rss=dict(aggregate_rss_kib=1234),
                    stdout=json.dumps({'full': ('完整/unchanged/source/'*20000), 'repeat': [1, 2, 1]}, ensure_ascii=False))

    def test_complete_roundtrip_preserves_whole_receipt(self):
        original = self.sample()
        saved = copy.deepcopy(original)
        envelope = K.pack(original)
        self.assertEqual(K.unpack(json.loads(json.dumps(envelope))), original)
        self.assertEqual(original, saved)
        self.assertLess(len(K.canonical(envelope)), len(K.canonical(original)))

    def test_bad_base64_sizes_metadata_and_stream_boundaries_rejected(self):
        envelope = K.pack(self.sample())
        bads = []
        for change in (lambda v: v.__setitem__('data', v['data']+'\n'),
                       lambda v: v.__setitem__('stdout_utf8_bytes', v['stdout_utf8_bytes']-1),
                       lambda v: v['metadata'].__setitem__('exit_code', 2)):
            bad = copy.deepcopy(envelope); change(bad); bads.append(bad)
        packed = base64.b64decode(envelope['data'])
        for altered in (packed[:-1], packed+b'trailing', packed+zlib.compress(b'extra')):
            bad = copy.deepcopy(envelope)
            bad.update(data=base64.b64encode(altered).decode(), compressed_bytes=len(altered),
                       compressed_sha256=hashlib.sha256(altered).hexdigest())
            bads.append(bad)
        for bad in bads:
            with self.assertRaises((ValueError, zlib.error)):
                K.unpack(bad)
        with self.assertRaises(ValueError):
            K.pack(dict(stdout='ambiguous\ufffd'))


if __name__ == '__main__':
    unittest.main()
