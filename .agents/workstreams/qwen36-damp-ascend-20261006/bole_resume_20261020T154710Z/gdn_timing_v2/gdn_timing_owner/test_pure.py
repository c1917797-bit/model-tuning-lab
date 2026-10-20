"""Offline controls only. Synthetic JSON fixtures are NEVER device admissions."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

P = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location('_test_'+name, str(P/(name+'.py')))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


C = module('timing_owner_common')
R = module('consume_timing')


def fixture(frame=0):
    rows = [dict(pair=p, order=list(R.ROLES) if (frame+p)%2 == 0 else list(reversed(R.ROLES)),
        batch_elapsed_ns=dict(original=400+4*p, candidate=200+8*p)) for p in range(20)]
    return dict(samples=rows, warmup_order=[list(R.ROLES) if (frame+p)%2 == 0 else list(reversed(R.ROLES))
        for p in range(4)], summary={role: R.stats([r['batch_elapsed_ns'][role] for r in rows], 4) for role in R.ROLES})


def synthetic_inspection(cpu=False):
    return dict(Id='a'*64, Image=C.IMAGE, State=dict(Running=False, Pid=0), ExecIDs=None,
        Config=dict(Labels={'model-tuning-lab.owner': 'synthetic-unit-only'}),
        HostConfig=dict(Privileged=False, ReadonlyRootfs=True, NetworkMode='none',
            Memory=2**30 if cpu else 8*2**30, MemorySwap=2**30 if cpu else 8*2**30,
            CpusetCpus='145' if cpu else '0,1,2,3', PidsLimit=128 if cpu else 512,
            Devices=[] if cpu else [dict(PathOnHost=h, PathInContainer=g) for h, g in
                (('/dev/davinci4','/dev/davinci0'),('/dev/davinci_manager','/dev/davinci_manager'),
                 ('/dev/devmm_svm','/dev/devmm_svm'),('/dev/hisi_hdc','/dev/hisi_hdc'))],
            CapDrop=['ALL'], SecurityOpt=['no-new-privileges'], ShmSize=64*2**20 if cpu else 2**30,
            Tmpfs={'/tmp':'rw,exec,size='+str(64*2**20 if cpu else 2**30)}))


class Controls(unittest.TestCase):
    def test_cold_entrypoints(self):
        for name in ('timing_owner.py', 'timing_boot.py', 'consume_timing.py', 'build_inputs.py'):
            for args in ([], ['--help']):
                result = subprocess.run([sys.executable, '-I', '-B', str(P/name), *args],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                if not args: self.assertFalse(json.loads(result.stdout)['enabled'])

    def test_execute_without_optin_cannot_progress(self):
        for name in ('timing_owner.py', 'timing_boot.py', 'consume_timing.py', 'build_inputs.py'):
            result = subprocess.run([sys.executable, '-I', '-B', str(P/name), '--execute'],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('ModuleNotFoundError', result.stderr)

    def test_ast_no_tensor_or_remote_imports(self):
        for path in P.glob('*.py'):
            tree = ast.parse(path.read_text()); compile(tree, str(path), 'exec')
            for n in ast.walk(tree):
                if isinstance(n, ast.Import): names = [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom): names = [n.module or '']
                else: continue
                self.assertFalse(any(s.split('.')[0] in ('torch','torch_npu','triton','requests','socket') for s in names))

    def test_complete_ab_ba_samples_and_known_stats(self):
        for number in (0, 1, 383):
            result = R.samples(C, fixture(number), number, C.CONFIG)
            self.assertEqual(result['summary']['original']['mean_ns'], 109.5)
            self.assertEqual(result['summary']['candidate']['mean_ns'], 69.0)
            self.assertEqual(result['summary']['original']['count'], 20)
            self.assertEqual(result['order_groups']['AB']['summary']['candidate']['count'], 10)
            self.assertEqual(result['paired_original_over_candidate']['count'], 20)

    def test_sample_count_order_duration_and_summary_tampering_fail(self):
        mutations = [lambda x: x['samples'].pop(),
            lambda x: x['samples'][0].update(order=['candidate','original']),
            lambda x: x['samples'][0]['batch_elapsed_ns'].update(candidate=0),
            lambda x: x['samples'][0]['batch_elapsed_ns'].update(candidate=True),
            lambda x: x['summary']['candidate'].update(mean_ns=1),
            lambda x: x['warmup_order'].pop()]
        for change in mutations:
            x = fixture(); change(x)
            with self.assertRaises(ValueError): R.samples(C, x, 0, C.CONFIG)

    def test_exact_device_maps_and_protections(self):
        for cpu in (False, True):
            original = synthetic_inspection(cpu)
            C.device_inspection(original, cid='a'*64, running=False, name='synthetic-unit-only', cpu=cpu)
            for key, value in (('Privileged',True),('ReadonlyRootfs',False),('NetworkMode','host'),
                               ('CpusetCpus','0-3'),('Memory',1),('CapDrop',[])):
                changed = copy.deepcopy(original); changed['HostConfig'][key] = value
                with self.assertRaises(ValueError):
                    C.device_inspection(changed, cid='a'*64, running=False, name='synthetic-unit-only', cpu=cpu)
            changed = copy.deepcopy(original); changed['HostConfig']['Tmpfs']['/tmp'] = 'rw,noexec,size=1073741824'
            with self.assertRaises(ValueError): C.device_inspection(changed, cid='a'*64, running=False, name='synthetic-unit-only', cpu=cpu)
        changed = synthetic_inspection(); changed['HostConfig']['Devices'][0]['PathOnHost'] = '/dev/davinci0'
        with self.assertRaises(ValueError): C.device_inspection(changed, cid='a'*64, running=False, name='synthetic-unit-only')
        changed = synthetic_inspection(True); changed['HostConfig']['Devices'] = synthetic_inspection()['HostConfig']['Devices']
        with self.assertRaises(ValueError): C.device_inspection(changed, cid='a'*64, running=False, name='synthetic-unit-only', cpu=True)

    def test_exact_ref_and_duplicate_json_guards(self):
        with tempfile.TemporaryDirectory(dir=P) as directory:
            p = Path(directory)/'x.json'; p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError): C.obj(C.ref(p))
            r = C.ref(p); p.write_text('{}')
            with self.assertRaises(ValueError): C.checked(r)
            with self.assertRaises(ValueError): C.checked(dict(path='relative', bytes=0, sha256='0'*64))

    def test_runtime_host_copy_never_substitutes_installed_path(self):
        refs = C.runtime_refs()
        self.assertEqual(refs['triton_jit']['path'],
            '/usr/local/python3.12.13/lib/python3.12/site-packages/triton/runtime/jit.py')
        self.assertTrue(all('/site-packages/triton/' in r['path'] for r in refs.values()))
        local = P.parent.parent/'bole_service_reference'/'installed'
        # Environment-independent test compares supplied primary source bytes if present.
        source = {'triton_jit':'triton_jit.py','triton_compiled':'triton_compiled.py','ascend_compiler':'triton_ascend_compiler.py'}
        local = P.parents[1]/'bole_service_reference'/'installed'
        for name, filename in source.items():
            b = (local/filename).read_bytes()
            self.assertEqual((len(b), hashlib.sha256(b).hexdigest()), (refs[name]['bytes'],refs[name]['sha256']))
            self.assertNotEqual(str(local/filename), refs[name]['path'])


if __name__ == '__main__':
    unittest.main()
