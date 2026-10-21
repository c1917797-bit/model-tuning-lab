"""Synthetic admission failures only; never an actual factory/sandbox result."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import public_probe_gate as G


class Prerequisite(unittest.TestCase):
    def setUp(self):
        self.owner=dict(schema='bole.actual-finite-task-CPU-owner/v2',primary=None,secondary=[],diagnostic_only=True,
            tokenizer_probe='public-backend',tokenizer_import_diagnostic_completed=True,
            source_image_CPU_owner_software_controls_verified=False,private_namespace_restored_by_identity=True,
            source_input_before={'synthetic':'a'},source_input_after={'synthetic':'a'})
        self.x=dict(schema='bole.task-finite-CPU-owner-inputs/v2',default_enabled=False,diagnostic_only=True,
            tokenizer_probe='public-backend',phase_order=['cpu-preflight'],image_id=C.IMAGE,CPU=145,host_CPU=166,
            guest_memory_bytes=8*C.GIB,reserve_CPU_budget=2,summed_ancestor_CPU_budget=7)
        p=dict(schema='bole.actual-tokenizer-public-factory-diagnostic/v1',entry='public-backend',
            outcome='public-factory-and-original-tiny-controls-completed',error=None,forbidden_attempts=[],
            tokenizer_constructed=True,diagnostic_only=True,software_qualification_accepted=False,
            all15525_provenance_executed=False,task_score_produced=False,
            identity=dict(public_factory='TokenizersBackend.from_pretrained',versions=dict(transformers='5.5.4',tokenizers='0.22.2'),
              tokenizer_class='transformers.tokenization_utils_tokenizers.TokenizersBackend',eos_token_id=248046,
              clean_up_tokenization_spaces=False,decoder_semantic_equivalence_not_yet_qualified=True),
            tiny_original_decoder_controls=dict(schema='bole.actual-decoder-software-controls/v1',
                empty_and_EOS_only_decode_verified=True,task_score_produced=False,task_ready=False))
        proc=dict(pid=17,start_ticks=10,affinity=[145],uid=0,euid=0)
        self.report=dict(schema='bole.actual-task-CPU-child/v1',mode='import-probe',diagnostic_only=True,
            readset_before={'s':'a'},readset_after={'s':'a'},source_image_CPU_owner_software_controls_verified=False,
            NPU=False,model_executed=False,HTTP_executed=False,payload=p,process_before=proc,process_after=dict(proc))
        self.binding=dict(uid=0,Devices=[],cpu=dict(effective_cpus=[145],effective_capacity=1),memory=dict(effective_bytes=8*C.GIB),
            guest_pid=17,start_ticks=10)
        self.terminal=dict(exit_code=0);self.release=dict(stopped=True,retained=True,errors=[])

    def gate(self):return G.successful(self.owner,self.x,self.report,self.terminal,self.binding,self.release)

    def test_synthetic_completed_public_diagnostic_is_prerequisite_only(self):
        self.assertIs(self.gate(),True)
        self.assertIs(self.owner['source_image_CPU_owner_software_controls_verified'],False)

    def test_completed_denial_or_false_equivalence_never_qualifies(self):
        for field,value in [('outcome','forbidden-import-observed-and-denied-before-execution'),('forbidden_attempts',['torch_npu']),
                            ('tokenizer_constructed',False),('software_qualification_accepted',True),('all15525_provenance_executed',True)]:
            before=copy.deepcopy(self.report);self.report['payload'][field]=value
            with self.assertRaises(ValueError,msg=field):self.gate()
            self.report=before

    def test_stale_or_wrong_CPU_lifecycle_and_source_rejected(self):
        for target,field,value in [(self.owner,'secondary',['failure']), (self.owner,'private_namespace_restored_by_identity',False),
                                   (self.terminal,'exit_code',3),(self.release,'stopped',False),(self.binding,'guest_pid',18)]:
            old=target[field];target[field]=value
            with self.assertRaises(ValueError,msg=field):self.gate()
            target[field]=old
        self.owner['source_input_after']={'synthetic':'b'}
        with self.assertRaises(ValueError):self.gate()

    def test_auto_entry_does_not_satisfy_public_prerequisite(self):
        self.x['tokenizer_probe']='auto'
        with self.assertRaises(ValueError):self.gate()

    def test_closed_source_bound_audit_and_denied_attempt_controls(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);source=dict(synthetic=True)
            def save(name,events):
                rows=[dict(schema='bole.actual-tokenizer-import-audit-event/v1',ordinal=n,event=kind,payload=payload)for n,(kind,payload)in enumerate(events)]
                path=root/name;path.write_text(''.join(json.dumps(v)+'\n'for v in rows));return C.ref(path)
            events=[('entry',dict(source_ref=source)),('closed',dict(forbidden_attempts=[],software_qualification_accepted=False))]
            G.audit(save('good',events),source)
            with self.assertRaises(ValueError):G.audit(save('missingclose',events[:1]),source)
            denied=[events[0],('forbidden-import-denied',dict(module='torch_npu')),events[-1]]
            with self.assertRaises(ValueError):G.audit(save('denied',denied),source)
            with self.assertRaises(ValueError):G.audit(save('wrongsource',events),dict(other=True))


if __name__=='__main__':unittest.main()
