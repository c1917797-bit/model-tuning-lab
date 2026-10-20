"""Pure controls: exact original G1/G2 command helpers; synthetic readset fixture."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit_v4',P/'audit_readset_v4.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
PROPOSALS=P.parent


def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True)+'\n')
    return A.ref(path)


class AuditTests(unittest.TestCase):
    def fixture(self,g2=False,dependencies=()):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
        (root/'sourceio.py').write_bytes((PROPOSALS/'g2_long_output/sourceio.py').read_bytes())
        helper=PROPOSALS/('g2_long_output'if g2 else'g1_repair_v2')/'command_contract.py'
        (root/'command_contract.py').write_bytes(helper.read_bytes())
        (root/'bind_model.py').write_text("import sourceio as C\ndef readset(sr):\n m=C.obj(sr);return [sr,m['prepared_template'],*m['files'].values()]\n")
        historical=write(root/'HISTORICAL_COMMANDS.json',dict(required_sameimage_software_cases=154))
        template=write(root/'SOURCE_TEMPLATE.json',dict(synthetic_fixture=True))
        files={name:A.ref(root/name)for name in('sourceio.py','bind_model.py','command_contract.py')}
        m=dict(root=str(root),output_root=str(root/'OUTPUT'),files=files,component_refs={},
               prepared_template=template,dependencies=list(dependencies),service_required_sameimage_software_cases=242 if g2 else 214,
               command_scope=dict(schema='bole.post-binding-command-readset/v2',file='COMMANDS.json',
                 generated_after_binding=True,included_in_actual_host_readset=True,
                 historical_ref=historical,compatibility_file='COMMANDS_G2.json'if g2 else'COMMANDS_G1.json'))
        return root,m

    def bind(self,root,m):
        sr=write(root/'SOURCE_BOUND.json',m)
        # Load the exact helper without leaving process-global sourceio aliases behind.
        code="import json,sys;sys.path.insert(0,sys.argv[1]);import sourceio as C,command_contract as CC;m=json.loads(sys.argv[2]);sr=C.ref(sys.argv[1]+'/SOURCE_BOUND.json');print(json.dumps(CC.expected(m['root'],m['output_root'],sr,m['prepared_template'],m['component_refs'])))"
        import subprocess
        q=subprocess.run(['/usr/bin/python3','-I','-B','-c',code,str(root),json.dumps(m)],capture_output=True,text=True)
        self.assertEqual(q.returncode,0,q.stderr);expected=json.loads(q.stdout)
        value=dict(schema='bole.G1-actual-bound-commands/v2',source=m['prepared_template'],bound_source=sr,
          required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
          historical_required_sameimage_software_cases=154,actual_G1_execution_claimed=False,
          legacy_entrypoints_retained_for_inverse_tests_only=True,**expected)
        if m['service_required_sameimage_software_cases']==242:
            value.update(G2_stream_protocol=True,actual_G2_execution_claimed=False)
        commands=write(root/'COMMANDS.json',value)
        write(root/m['command_scope']['compatibility_file'],dict(source=sr,template=m['prepared_template'],commands=commands,
          model=value['model'],CPU=value['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
        # Exact shape/order that caused the previous audit's false failure.
        return json.loads(json.dumps(sr,sort_keys=True))

    def test_original_G1_sorted_Ref_is_semantically_identical_and_rebuilt_without_contract_change(self):
        root,m=self.fixture();sr=self.bind(root,m);before=A.ref(root/'COMMANDS.json')
        row=A.source_readset(sr)
        self.assertEqual(row['supplied_key_order'],['bytes','path','sha256'])
        self.assertEqual(row['sourceio_key_order'],['path','bytes','sha256'])
        for proof in row['original_command_source_arguments'].values():
            self.assertTrue(proof['semantic_equal']);self.assertTrue(proof['literal_equal_to_sourceio_ref'])
            self.assertFalse(proof['literal_equal_to_supplied_serialization'])
        self.assertEqual(before,A.ref(root/'COMMANDS.json'))
        self.assertTrue(row['source_and_commands_unchanged'])
        self.assertTrue(row['original_unreconstructed_call']['rejected'])
        self.assertIn('exact current runnable',row['original_unreconstructed_call']['reason'])
        self.assertEqual((root/'command_contract.py').read_bytes(),(PROPOSALS/'g1_repair_v2/command_contract.py').read_bytes())

    def test_original_G2_source_contract_is_preserved(self):
        root,m=self.fixture(True);sr=self.bind(root,m)
        self.assertTrue(A.source_readset(sr)['serialization_only_reconstruction'])
        self.assertEqual((root/'command_contract.py').read_bytes(),(PROPOSALS/'g2_long_output/command_contract.py').read_bytes())

    def test_wrong_supplied_hash_size_or_nonexistent_path_rejected_before_import(self):
        root,m=self.fixture();sr=self.bind(root,m)
        mutations=[dict(sha256='0'*64),dict(bytes=sr['bytes']+1),dict(path=str(root/'other.json'))]
        for mutation in mutations:
            value=dict(sr,**mutation)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):A.source_readset(value)

    def test_wrong_source_path_with_identical_bytes_is_not_its_owned_root(self):
        root,m=self.fixture();sr=self.bind(root,m)
        other=root/'OTHER';other.mkdir();path=other/'SOURCE_BOUND.json';path.write_bytes((root/'SOURCE_BOUND.json').read_bytes())
        with self.assertRaisesRegex(ValueError,'exact owned root'):A.source_readset(A.ref(path))

    def test_source_symlink_and_symlink_parent_rejected(self):
        root,m=self.fixture();sr=self.bind(root,m)
        link=root/'link.json';link.symlink_to(root/'SOURCE_BOUND.json')
        value=dict(sr,path=str(link))
        with self.assertRaises(ValueError):A.source_readset(value)
        alias=root/'alias';alias.symlink_to(root,target_is_directory=True)
        with self.assertRaises(ValueError):A.source_readset(dict(sr,path=str(alias/'SOURCE_BOUND.json')))

    def test_changed_SOURCE_file_rejected(self):
        root,m=self.fixture();sr=self.bind(root,m);(root/'SOURCE_BOUND.json').write_text('{}')
        with self.assertRaises(ValueError):A.source_readset(sr)

    def test_changed_actual_argv_path_hash_or_output_rejected(self):
        for mutation in('sourcepath','sourcehash','output'):
            root,m=self.fixture();sr=self.bind(root,m);path=root/'COMMANDS.json';value=json.loads(path.read_text())
            argv=value['model'];at=argv.index('--source-ref')+1
            if mutation=='output':argv[-1]+='-foreign'
            else:
                operand=json.loads(argv[at]);operand['path'if mutation=='sourcepath'else'sha256']='foreign'
                argv[at]=json.dumps(operand)
            write(path,value)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):A.source_readset(sr)

    def test_semantically_equal_but_changed_literal_argv_still_rejected(self):
        root,m=self.fixture();sr=self.bind(root,m);path=root/'COMMANDS.json';value=json.loads(path.read_text())
        argv=value['CPU'];at=argv.index('--source-ref')+1;argv[at]=json.dumps(json.loads(argv[at]),sort_keys=True)
        write(path,value)
        with self.assertRaisesRegex(ValueError,'remains exact canonical'):A.source_readset(sr)

    def test_changed_command_helper_hash_rejected_before_import(self):
        root,m=self.fixture();sr=self.bind(root,m)
        (root/'command_contract.py').write_text("raise RuntimeError('must never import foreign helper')\n")
        with self.assertRaisesRegex(ValueError,'exact supplied path/bytes/SHA'):A.source_readset(sr)

    def test_conflicting_dependency_ref_rejected(self):
        root,m=self.fixture();m['dependencies']=[dict(m['files']['sourceio.py'],sha256='0'*64)];sr=self.bind(root,m)
        with self.assertRaises(ValueError):A.source_readset(sr)

    def closure_fixture(self,omit=False):
        root,parent=self.fixture();ps=self.bind(root,parent);old=A.source_readset(ps)['refs']
        qroot=root/'cpu-consumer';qroot.mkdir();ranks=[]
        for rank in range(4):
            rows=[dict(rank=rank,generation=g,request='r'+str(g),output_token_ids=[79091,1204],
              actual_final_retirement_observed=True,component_checks_pass=True,
              actual_next_counter_acknowledgements=0,model_ready=False)for g in(1,2)]
            ranks.append(write(qroot/('RANK-%d.json'%rank),dict(source=ps,requests=rows)))
        qualification=write(qroot/'ATTRIBUTION.json',dict(ranks=ranks));owner=write(root/'RESULT.json',{})
        preparer=root/'PREPARER.py';preparer.write_text('# retained original failed audit\n')
        current,m=self.fixture(True,old+[ps,owner,qualification]+(ranks[:-1]if omit else ranks))
        m.update(g2_predecessor=dict(source=ps,owner_result=owner,qualification=qualification),
          g2_parent_prerequisites_v3=dict(actual_preparer=A.ref(preparer)))
        return self.bind(current,m),ranks

    def test_full_exact_historical_readset_and_all_four_rank_reports_close(self):
        sr,ranks=self.closure_fixture();result=A.audit(sr)
        self.assertEqual(result['missing'],[]);self.assertEqual(result['independently_validated_parent_rank_reports'],ranks)
        self.assertTrue(result['CPU242_preflight_still_required']);self.assertFalse(result['CPU_or_NPU_execution_qualified'])
        self.assertEqual(result['source'],sr);self.assertTrue(result['original_contract_unmodified'])

    def test_missing_one_actual_rank_dependency_still_rejected(self):
        sr,ranks=self.closure_fixture(True)
        with self.assertRaisesRegex(ValueError,'closure missing/conflicting'):A.audit(sr)

    def test_false_parent_retirement_is_rejected(self):
        sr,ranks=self.closure_fixture();m=A.obj(sr);q=A.obj(m['g2_predecessor']['qualification'])
        rankpath=Path(ranks[2]['path']);value=json.loads(rankpath.read_text());value['requests'][1]['actual_final_retirement_observed']=False
        q['ranks'][2]=write(rankpath,value);qr=write(Path(m['g2_predecessor']['qualification']['path']),q)
        with self.assertRaisesRegex(ValueError,'actual both G1'):A.parent_rank_reports(m['g2_predecessor']['source'],qr)

    def test_type_confusion_Ref_rejected(self):
        root,m=self.fixture();sr=self.bind(root,m)
        for value in(dict(sr,bytes=True),dict(sr,sha256=sr['sha256'].upper()),dict(sr,extra=1)):
            with self.assertRaises(ValueError):A.checked(value)


if __name__=='__main__':unittest.main()
