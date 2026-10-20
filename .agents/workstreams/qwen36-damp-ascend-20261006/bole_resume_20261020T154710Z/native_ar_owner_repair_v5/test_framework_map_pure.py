"""Offline exact Ref/catalogue controls only; no real admission or device import."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

P=Path(__file__).resolve().parent;V2=P.parent/'native_ar_owner_repair_v3';W=P.parents[1]
s=importlib.util.spec_from_file_location('_offline_framework_common',str(P/'ar_owner_common.py'))
C=importlib.util.module_from_spec(s);s.loader.exec_module(C)


class Controls(unittest.TestCase):
    def test_default_help_and_new_parameter(self):
        for name in('native_ar_host.py','ar_sameimage_preflight.py','consume_pair_entry.py','prepare_native_owner.py'):
            for args in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,r.stderr)
                if not args:self.assertFalse(json.loads(r.stdout)['enabled'])
                elif name=='prepare_native_owner.py':
                    self.assertIn('--framework-host-evidence-json',r.stdout)
                    self.assertIn('--observer-runtime-host-evidence-json',r.stdout)

    def test_actual_catalogue_all4_equal_and_exact_sources(self):
        b=json.loads((W/'g1_review_v2/qualification/CONSUMER_INPUTS.json').read_bytes())
        declared=C.framework_sources(b);self.assertEqual(len(declared),4)
        self.assertEqual((declared['vllm_ascend.ops.triton.fla.chunk']['bytes'],declared['vllm_ascend.ops.triton.fla.chunk']['sha256']),
            (16312,'6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'))
        self.assertEqual((declared['vllm_ascend.ops.triton.fla.solve_tril']['bytes'],declared['vllm_ascend.ops.triton.fla.solve_tril']['sha256']),
            (14809,'2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0'))
        changed=copy.deepcopy(b);changed['snapshots'][3]['framework_sources'][next(iter(declared))]['bytes']+=1
        with self.assertRaises(ValueError):C.framework_sources(changed)
        changed=copy.deepcopy(b);changed['snapshots'][1]['framework_sources'].pop(next(iter(declared)))
        with self.assertRaises(ValueError):C.framework_sources(changed)

    def test_exact_identity_only_no_prefix_path_or_ref2_exemption(self):
        ref=dict(path='/vllm-workspace/a.py',bytes=100,sha256='1'*64);runtime={'one':ref};framework={}
        self.assertTrue(C.declared_installed(dict(ref),runtime,framework))
        mutations=[dict(ref,path='/vllm-workspace/unknown.py'),dict(ref,bytes=101),dict(ref,sha256='2'*64),
                   dict(path=ref['path'],sha256=ref['sha256'])]
        for r in mutations:self.assertFalse(C.declared_installed(r,runtime,framework))
        with self.assertRaises(ValueError):C.checked(mutations[0])

    def fixture(self,directory):
        framework={};copies={}
        for i,module in enumerate(sorted(C.FRAMEWORK_MODULES)):
            guest=Path(directory)/('installed%d.py'%i);host=Path(directory)/('host%d.py'%i)
            guest.write_text('x='+str(i)+'\n');host.write_bytes(guest.read_bytes())
            framework[module]=C.ref(guest);copies[module]=C.ref(host)
        return framework,copies

    def test_complete_host_map_guest_reopen_and_content_mutations(self):
        with tempfile.TemporaryDirectory(dir=P)as directory:
            declared,copies=self.fixture(directory)
            C.framework_copies(declared,copies,installed=False);C.framework_copies(declared,copies,installed=True)
            changed=copy.deepcopy(copies);changed.pop(next(iter(copies)))
            with self.assertRaises(ValueError):C.framework_copies(declared,changed,installed=False)
            changed=copy.deepcopy(copies);key=next(iter(changed));changed[key]=declared[key]
            with self.assertRaises(ValueError):C.framework_copies(declared,changed,installed=False)
            changed=copy.deepcopy(copies);changed[key]['sha256']='0'*64
            with self.assertRaises(ValueError):C.framework_copies(declared,changed,installed=False)
            # Host check can succeed with installed bytes absent; guest check MUST reopen them.
            Path(declared[key]['path']).unlink();C.framework_copies(declared,copies,installed=False)
            with self.assertRaises(ValueError):C.framework_copies(declared,copies,installed=True)

    def test_only_runtime_exact_overlaps_can_be_filled_automatically(self):
        with tempfile.TemporaryDirectory(dir=P)as directory:
            declared,copies=self.fixture(directory);keys=sorted(declared);shared=keys[:2];extra=keys[2:]
            on=dict(runtime_sources={k:declared[k]for k in shared},files={k:copies[k]for k in shared})
            assembled=C.assemble_framework_copies(declared,{k:copies[k]for k in extra},on)
            self.assertEqual(assembled,copies)
            with self.assertRaises(ValueError):C.assemble_framework_copies(declared,{extra[0]:copies[extra[0]]},on)
            with self.assertRaises(ValueError):C.assemble_framework_copies(declared,dict(copies,unknown=copies[keys[0]]),on)
            drift=copy.deepcopy(on);drift['runtime_sources'][shared[0]]['bytes']+=1
            with self.assertRaises(ValueError):C.assemble_framework_copies(declared,copies,drift)

    def test_original_runtime_and_exact_diagnostic_host_inverse(self):
        for name in('ar_host_namespace.py','ar_snapshot_bindings.py','ar_sameimage_preflight.py'):
            self.assertEqual((P/name).read_bytes(),(V2/name).read_bytes())
        text=(P/'native_ar_host.py').read_text()
        insertion="    F=C.load(x['files']['fd_inventory_diagnostic.py'],'_native_ar_fd_diagnostic')\n"
        self.assertEqual(text.count(insertion),1)
        text=text.replace(insertion,'')
        for label in('native-ar-startup','native-ar-two-request'):
            new='F.observe(C,ctl,'+repr(label)+',summary,out)'
            self.assertEqual(text.count(new),1)
            text=text.replace(new,'ctl.observe('+repr(label)+')')
        self.assertEqual(text,(V2/'native_ar_host.py').read_text())
        for p in P.glob('*.py'):compile(ast.parse(p.read_bytes()),str(p),'exec')
        self.assertNotIn('import_module(', (P/'ar_sameimage_preflight.py').read_text())


if __name__=='__main__':unittest.main()
