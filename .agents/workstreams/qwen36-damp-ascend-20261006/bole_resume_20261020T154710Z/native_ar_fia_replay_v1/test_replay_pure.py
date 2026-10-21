"""Stdlib protocol/source controls only; no actual device or Torch execution."""
import ast
import hashlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent;W=P.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=module('_fia_test_common',P/'replay_common.py');C=R.common()
A=module('_fia_test_layout',P/'arena_layout.py');L=module('_fia_test_maps',P/'library_maps.py')
SINGLE=module('_fia_test_singleton',P/'singleton_profile.py')


class Tests(unittest.TestCase):
    def test_all_actual_fsum23_provenance19_dispatch3_copy_hashes(self):
        for name,folder,count in [('ACTUAL_FSUM_REFS.json','native_ar_fsum_v1_actual',23),
                ('INSTALLED_PROVENANCE_REFS.json','installed_operator_provenance_v1',19),
                ('INSTALLED_DISPATCH_REFS.json','installed_operator_dispatch_v1',3),
                ('INSTALLED_LINKED_REFS.json','installed_operator_linked_metadata_v1',12)]:
            refs=json.loads((P/name).read_bytes());self.assertEqual(len(refs),count)
            for n,r in refs.items():
                actual=C.ref(W/'g1_review_v2'/folder/n);self.assertEqual((actual['bytes'],actual['sha256']),(r['bytes'],r['sha256']))
    def test_exact_both_full_table_geometries_and_shared_storage(self):
        self.assertEqual(A.STORAGE_ELEMENTS,303350784);self.assertEqual(A.STORAGE_ELEMENTS*2,606701568)
        self.assertEqual(A.K_OFFSET+A.VIEW_ELEMENTS,A.V_OFFSET)
        self.assertEqual(len(A.KWARGS),13);self.assertEqual(tuple(sorted(A.KWARGS)),A.KWARGS)
        for start in(12,60):
            table=[*range(start,start+12),*([0]*24)];indices=A.rows(table)
            self.assertEqual(len(indices),132);self.assertEqual(len(set(indices)),132)
            self.assertEqual(indices[:128],list(range(start*128,(start+1)*128)))
            self.assertEqual(indices[-4:],list(range((start+1)*128,(start+1)*128+4)))
        with self.assertRaises(ValueError):A.rows([0,1]+[0]*34)
    def test_singleton_derivation_restores_exact_readonly_source_and_full_function_bodies(self):
        E=module('_fia_test_external',W/'g1_review_v2/external025.py');body=(W/'g1_review_v2/safety_host.py').read_bytes()
        text,pairs=E.derive(body)
        previous,next_,proof=SINGLE.derive_external_singleton(E,body,'/exact/original/safety_host.py',{})
        self.assertEqual(len(proof['readonly_pairs']),4);self.assertTrue(proof['whole_singleton_inverse'])
        before=ast.parse(text);after=ast.parse(text.replace('len(dev)==(0 if cpu else 7)','len(dev)==(0 if cpu else 4)'))
        old=next(n for n in ast.walk(before)if isinstance(n,ast.FunctionDef)and n.name=='create_argv')
        new=next(n for n in ast.walk(after)if isinstance(n,ast.FunctionDef)and n.name=='create_argv')
        self.assertEqual(ast.dump(old),ast.dump(new))
        with self.assertRaises(ValueError):SINGLE.derive_external_singleton(E,body+b'\n','/x',{})
    def test_singleton_private_context_preserves_original_method_objects_and_inverse(self):
        E=module('_fia_test_external_context',W/'g1_review_v2/external025.py');path=W/'g1_review_v2/safety_host.py'
        body=path.read_bytes();text,_=E.derive(body)
        S=types.ModuleType('_isolated_original025_source');S.__file__=str(path)
        namespace=vars(S);namespace.update(dict(c=types.SimpleNamespace(GIB=2**30,IMAGE=C.IMAGE,ROOT=Path('/offline'),require=C.need),
            PHYSICAL=(4,5,6,7),PHASE=3600,CLEANUP=180,MEM=32*2**30,RESERVE=8*2**30,HOST_MEM=512*2**20,WORKSPACE=32*2**30,
            _EXTERNAL=types.SimpleNamespace(environment=E.environment,LOG=E.LOG)))
        tree=ast.parse(body)
        env=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='environment')
        dev=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='device_map')
        exec(compile(ast.Module(body=[env,dev],type_ignores=[]),S.__file__,'exec'),namespace)
        for name,fn in SINGLE.derive_external_singleton(E,body,S.__file__,namespace)[0].items():
            namespace[name]=types.FunctionType(fn.__code__,namespace,name)
        class OriginalController:
            def observe(self):raise AssertionError('never actual observe')
            def resources(self):raise AssertionError('never resource admission')
            def remaining(self):raise AssertionError('never actual remaining')
            def create_owned(self):raise AssertionError('never Docker')
            def inspect(self):raise AssertionError('never Docker')
            def cleanup(self):raise AssertionError('never cleanup')
        S.Controller=OriginalController
        before={n:getattr(S,n)for n in('device_map','environment','create_argv','validate_inspect')}
        on=dict(files={'external025.py':C.ref(Path(E.__file__))})
        with patch.dict(sys.modules,{'external025':E}):
            with SINGLE.install(C,None,S,None,on)as proof:
                self.assertEqual(S.PHYSICAL,(4,5,6,7));self.assertEqual(S.environment(False)['ASCEND_RT_VISIBLE_DEVICES'],'0')
                self.assertEqual(S.environment(True)['ASCEND_RT_VISIBLE_DEVICES'],'')
                self.assertEqual(len(S.device_map()),4);self.assertIs(S.Controller,OriginalController)
                self.assertTrue(proof['cap32_and_seven_CPU_budget_unchanged'])
        for name,value in before.items():self.assertIs(getattr(S,name),value)
    def test_maps_exact_file_identity_unknown_and_anonymous_rejection(self):
        with tempfile.TemporaryDirectory(dir=P)as td:
            path=Path(td)/'file';path.write_bytes(b'fixture');s=path.stat()
            line='1000-2000 r-xp 00000000 %x:%x %d %s\n'%(os.major(s.st_dev),os.minor(s.st_dev),s.st_ino,path)
            self.assertEqual(set(L.executable_paths(line)),{str(path)})
            allowed={str(path):L.fingerprint(path)};self.assertEqual(set(L.check(line,allowed,rehash=True)),{str(path)})
            self.assertEqual(L.bind(allowed)[str(path)]['ref'],allowed[str(path)]['ref'])
            with self.assertRaises(ValueError):L.check(line,{})
            with self.assertRaises(ValueError):L.executable_paths('1000-2000 rwxp 00000000 00:00 0\n')
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError):L.check(line,allowed)
    def test_bounded_elf_GNU_build_id_and_nonELF(self):
        with tempfile.TemporaryDirectory(dir=P)as td:
            path=Path(td)/'ELF';name=b'GNU\0';desc=b'\x01\x23\x45\x67';note=struct.pack('<III',len(name),len(desc),3)+name+desc
            header=b'\x7fELF'+bytes([2,1,1])+bytes(9)+struct.pack('<HHIQQQIHHHHHH',3,183,1,0,64,0,0,64,56,1,64,0,0)
            ph=struct.pack('<IIQQQQQQ',4,0,120,0,0,len(note),len(note),4)
            path.write_bytes(header+ph+note)
            self.assertEqual(L.elf(path),dict(ELF=True,machine=183,build_ids=['01234567']))
            path.write_bytes(b'not ELF');self.assertEqual(L.elf(path),dict(ELF=False,build_ids=[]))

    def test_frozen_math_original025_and_prior_packets_byteequal(self):
        for folder in('native_ar_fsum_oracle_v1','native_ar_numeric_diagnostic_v1',
                'native_ar_saved_requalification_repair_v4','gdn_service_probe_g1_v3'):
            manifest=W/'bole_service_proposals'/folder/'ADVISORY_MANIFEST.json'
            value=json.loads(manifest.read_text())
            for r in value['files'].values():
                actual=C.ref(r['path']);self.assertEqual(actual['sha256'],r['sha256'])
                self.assertEqual(actual['bytes'],r['bytes'])
        for name in('ar_owner_common.py','ar_saved_namespace.py'):
            self.assertEqual((P/name).read_bytes(),(W/'bole_service_proposals/native_ar_fsum_oracle_v1'/name).read_bytes())
    def test_all128_actual_mask_metadata_supports_complete_reconstruction_geometry(self):
        p=W/'g1_review_v2/native_ar_mask_v4_actual/cpu-consumer/MASKS.json'
        ref=C.ref(p);self.assertEqual((ref['bytes'],ref['sha256']),(645804,'d02ba959d52c019ef2b185979fb7f4bde9801732b2c4ac06c88770959db0b621'))
        report=json.loads(p.read_text());frames=[f for rank in report['ranks']for f in rank['frames']]
        self.assertEqual(len(frames),128)
        for frame in frames:
            kw=frame['parameters'];self.assertEqual(frame['explicit_kwargs_keys'],list(A.KWARGS))
            self.assertEqual(frame['mask']['contiguous_byte_sha256'],'d016ca7be6be829fd102f03317c3eed915d3df3d3fd54279a8858caea2dd57de')
            self.assertEqual(kw['actual_seq_lengths_kv'],[132]);self.assertEqual(kw['actual_seq_lengths'],[1])
            self.assertEqual((kw['input_layout'],kw['sparse_mode'],kw['scale']),('TND',3,.0625))
            for name,offset in(('key',A.K_OFFSET),('value',A.V_OFFSET)):
                ident=kw[name]['tensor_identity'];self.assertEqual(tuple(ident['shape']),A.SHAPE)
                self.assertEqual(tuple(ident['stride']),A.STRIDE);self.assertEqual(ident['storage_offset'],offset)
            self.assertEqual(kw['key']['tensor_identity']['storage_ptr'],kw['value']['tensor_identity']['storage_ptr'])
            self.assertEqual(len(A.rows(kw['block_table']['complete_values'][0])),132)
        self.assertFalse(report['native_FA_math_qualified']);self.assertFalse(report['mathematics_recomputed'])
    def test_actual_fsum_terminal_complete_and_original_failure_preserved(self):
        root=W/'g1_review_v2/native_ar_fsum_v1_actual'
        owner=json.loads((root/'RESULT.json').read_text());report=json.loads((root/'cpu-consumer/FSUM-ORACLE.json').read_text())
        unit=json.loads((root/'UNIT_TERMINAL.json').read_text());release=json.loads((root/'cpu-consumer/cleanup.json').read_text())
        self.assertIsNone(owner['primary']);self.assertEqual(owner['secondary'],[])
        self.assertEqual(len(owner['source_before']),913);self.assertEqual(owner['source_before'],owner['source_after'])
        self.assertTrue(report['all128_independent_oracle_join_pass']);self.assertEqual(report['independent_violation_count'],32)
        self.assertEqual(report['scalar_product_terms'],51904512);self.assertFalse(report['native_FA_math_qualified'])
        self.assertEqual(unit['properties']['ExecMainStatus'],'0');self.assertEqual(unit['properties']['MainPID'],'0')
        self.assertTrue(release['stopped']);self.assertEqual(release['errors'],[])
        after_ref=release['after_inspect'];refs=json.loads((root/'ACTUAL_REFS.json').read_text())
        rel=next(n for n,r in refs.items()if r['path']==after_ref['path']and r['sha256']==after_ref['sha256']);value=json.loads((root/rel).read_text())
        after=json.loads(value['stdout'])[0];self.assertFalse(after['State']['Running']);self.assertEqual(after['State']['Pid'],0)
    def test_real_copied_module_full_path_identity_and_schema_roundtrip(self):
        with tempfile.TemporaryDirectory(dir=P)as td:
            leaf=Path(td)
            for name in R.FILES:(leaf/name).write_bytes((P/name).read_bytes())
            E=C.load(C.ref(leaf/'replay_common.py'),'_fia_actual_prepared_identity_regression')
            old=json.loads((W/'g1_review_v2/native_ar_fsum_v1_actual/INPUTS.json').read_bytes())
            y=dict(schema='bole.native-ar-FIA-replay-inputs/v1',actual_fsum_refs=json.loads((P/'ACTUAL_FSUM_REFS.json').read_text()),
                original_fsum_inputs=json.loads((P/'ACTUAL_FSUM_REFS.json').read_text())['INPUTS.json'],
                files={n:C.ref(leaf/n)for n in R.FILES},MAIN_lock=R.LOCK,default_enabled=False,prepared_only=True,
                output_root='/opt/host/vnf/austinov/run-bole-native-ar-fia-regression',phase_seconds=3600,cleanup_seconds=180,
                metadata_cap_seconds=600,replay_cap_seconds=900,consumer_cap_seconds=900,physical=[4],logical=[0],
                frames=128,actual_operator_calls_required=256,preregistered_fillers=['all_zero','finite_alternating'],
                unused_arena_reconstruction=True,precision_change=False,original_numerical_failure_preserved=True,
                AR_source=old['AR_source'],authority=old['authority'],extra_copy_refs=[])
            ir=C.write(leaf/'INPUTS.json',y)
            self.assertEqual(E.source(C,ir),y)
            with self.assertRaisesRegex(ValueError,'source'):R.source(C,ir)
            self.assertNotEqual(E.__file__,R.__file__)
            self.assertEqual(C.ref(E.__file__)['sha256'],C.ref(R.__file__)['sha256'])
    def test_original_lifecycle_observe_sets_cpu_before_profile_and_create(self):
        source=(P/'replay_cpu_owner.py').read_text();tree=ast.parse(source)
        owner=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='open_owner')
        body=ast.unparse(owner)
        self.assertLess(body.index('ctl.observe('),body.index("ctl.cpu['guest_cpus']"))
        self.assertLess(body.index("ctl.cpu['guest_cpus']"),body.index('owned_create.create('))
        self.assertIn('self.cpu is None',(W/'g1_review_v2/safety_host.py').read_text())
        self.assertIn('self.cpu=allocation',(W/'g1_review_v2/safety_host.py').read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        self.assertEqual(ast.unparse(main.body[0]),'entry_start = time.monotonic()')
        self.assertIn('H.Joint(entry_start)',source);self.assertIn('),entry_start)',source)
        context_end=source.index('namespace_restored=True')
        self.assertLess(context_end,source.index("C.write(root/'RESULT.json'"))
        fake=types.SimpleNamespace(cpu=None)
        with self.assertRaises(TypeError):fake.cpu['guest_cpus']
        def actual_observation_assignment():fake.cpu={'guest_cpus':[0,1,2,3]}
        actual_observation_assignment();self.assertEqual(fake.cpu['guest_cpus'][:1],[0])
    def test_remaining_original_clock_no_renewal_and_original_protected_scope(self):
        O=module('_fia_test_owner',P/'replay_cpu_owner.py')
        with patch.object(O.time,'monotonic',return_value=1000),patch.object(O.time,'time',return_value=10000):
            self.assertEqual(O.remaining_phase(C,900,14000),3500)
            with self.assertRaises(ValueError):O.remaining_phase(C,-1000,14000)
            with self.assertRaises(ValueError):O.remaining_phase(C,900,12000)
        text=(P/'singleton_profile.py').read_text()
        self.assertNotIn('PHYSICAL=(4,)',text);self.assertIn('resource_PHYSICAL_unchanged=[4,5,6,7]',text)
        self.assertIn("('enumerate(PHYSICAL)','enumerate((4,))')",text)
    def test_all256_calls_full_original13_kwargs_and_no_precision_defaults(self):
        source=(P/'replay_fia.py').read_text();tree=ast.parse(source)
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='npu_fused_infer_attention_score']
        self.assertEqual(len(calls),1);self.assertEqual(calls[0].args,[])
        self.assertEqual(len(calls[0].keywords),1);self.assertIsNone(calls[0].keywords[0].arg)
        self.assertEqual(ast.unparse(calls[0].keywords[0].value),'kw')
        self.assertIn('for filler in A.FILLERS:',source);self.assertIn('calls==256 and old_failed==16',source)
        self.assertNotIn("kw['inner_precise']",source)
        self.assertLess(source.index("tag+'-BEFORE'"),source.index('result=n.npu_fused_infer_attention_score(**kw)'))
        self.assertLess(source.index('result=n.npu_fused_infer_attention_score(**kw)'),source.index("tag+'-AFTER'"))
        self.assertIn('snapshots={name:value.clone()',source);self.assertIn('storage_elements=A.STORAGE_ELEMENTS',source)
        consumer=(P/'consume_replay.py').read_text();self.assertIn('map_count==515',consumer)
        self.assertIn('old_failed==16 and old_violations==32',consumer)
        self.assertIn('N.error_details(t,out,truth)',consumer);self.assertIn("native_FA_math_qualified=False",consumer)
    def test_exact_installed_fullRef_projection_unknown_path_or_digest_rejected(self):
        # Pure route test, not an actual CPU/admission proof: the runtime gate
        # is explicitly replaced, then the REAL metadata_readset walker runs.
        with tempfile.TemporaryDirectory(dir=P)as td:
            leaf=Path(td);empty=C.write(leaf/'empty.json',{})
            known=dict(path='/not-available-on-host/explicit.so',bytes=123,sha256='0'*64)
            value=dict(allowed_executable_libraries={known['path']:dict(ref=known)},static_installed_aliases=[])
            h=dict(report=empty,child=empty,owned=empty,release=empty);hr=C.write(leaf/'handoff.json',h)
            with patch.object(R,'metadata_gate',return_value=(h,value)):
                refs,proof=R.metadata_readset(C,{}, {},hr)
                self.assertTrue(proof['exact_full_Ref_projection_only']);self.assertFalse(proof['host_claims_installed_file_hash'])
                self.assertNotIn(known['path'],[r['path']for r in refs])
                value['unknown']=dict(known,sha256='1'*64)
                with self.assertRaises(ValueError):R.metadata_readset(C,{}, {},hr)
                value['unknown']=dict(known,path='/another-location/explicit.so')
                with self.assertRaises(ValueError):R.metadata_readset(C,{}, {},hr)
    def test_actual_original_H8_host_NSpid_join_required_after_operator_child(self):
        source=(P/'replay_cpu_owner.py').read_text();driver=(P/'replay_fia.py').read_text()
        self.assertIn("v['namespace_pids'][-1]==process['pid']",source)
        self.assertIn("v['start_ticks']==process['start_ticks']",source)
        self.assertIn("ctl.cid in v['cgroup']",source)
        self.assertIn('ctl.process_proofs',source);self.assertIn("actual_compute=matches,observations=ctl.observations",source)
        self.assertIn("cgroup_contains_CID=admission['owned_CID']in process['cgroup']",driver)
        self.assertNotIn("C.need(admission['owned_CID']in process['cgroup']",driver)
        original=(W/'g1_review_v2/host_full_matrix.py').read_text()
        self.assertIn('proof["namespace_pids"]',original)
        self.assertIn("p in actual and p['physical']==4",(P/'replay_common.py').read_text())
    def test_default_help_cold_tripwire_all_five_CLIs(self):
        scripts=['prepare_replay_owner.py','replay_cpu_owner.py','metadata_cpu.py','replay_fia.py','consume_replay.py']
        wrapper="""import sys,runpy
class Tripwire:
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in ('torch','torch_npu','triton','vllm','vllm_ascend'):
   raise AssertionError('cold import forbidden: '+fullname)
sys.meta_path.insert(0,Tripwire());sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
"""
        for name in scripts:
            for flags in([],['--help']):
                result=subprocess.run([sys.executable,'-I','-B','-c',wrapper,str(P/name),*flags],capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,0,(name,flags,result.stderr))
                self.assertNotIn('Traceback',result.stderr)
        # Actual CLI execute without exact metadata exits before importing Torch.
        for name in scripts[1:]:
            result=subprocess.run([sys.executable,'-I','-B','-c',wrapper,str(P/name),'--execute'],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,2,(name,result.stderr))
            self.assertNotIn('cold import forbidden',result.stderr)

if __name__=='__main__':unittest.main()
