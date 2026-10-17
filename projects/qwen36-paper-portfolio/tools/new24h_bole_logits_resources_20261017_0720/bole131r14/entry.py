"""Cold source/software entry, never a model or device launcher."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-audit',action='store_true');p.add_argument('--software',action='store_true');p.add_argument('--component-refs-json');a=p.parse_args()
 if not(a.source_audit or a.software or a.component_refs_json):print('{"enabled":false,"model_ready":false,"NPU":false}');return 0
 m=json.loads((P/'SOURCE.json').read_bytes())
 for n,r in m['files'].items():
  b=(P/n).read_bytes()
  if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('source closure '+n)
 if a.software:
  import unittest,test_model_entry,test_native_seams,test_mtp_entry,test_prefill_tail,test_cache_registry,test_tp_consensus,test_whole_frontdoor,test_declared_layout,test_patch_identity,test_context_identity,test_native_input,test_cache_observation,test_fault_receipt,test_owned_ref131r7,test_output_scan131r8,test_fa_mapping131r10,test_layer_slots131r10,test_registration_audit131r11,test_model_calibration131r12,test_logits_observation131r13,test_native_dtype131r13,test_resource131r14
  s=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(x)for x in(test_model_entry,test_native_seams,test_mtp_entry,test_prefill_tail,test_cache_registry,test_tp_consensus,test_whole_frontdoor,test_declared_layout,test_patch_identity,test_context_identity,test_native_input,test_cache_observation,test_fault_receipt,test_owned_ref131r7,test_output_scan131r8,test_fa_mapping131r10,test_layer_slots131r10,test_registration_audit131r11,test_model_calibration131r12,test_logits_observation131r13,test_native_dtype131r13,test_resource131r14))
  r=unittest.TextTestRunner().run(s);return 0 if r.wasSuccessful()and r.testsRun==90 else 3
 if a.component_refs_json:
  import sourceio as C,component_gate as G
  G.consume(C,json.loads(a.component_refs_json),gdn_math=C.ref(P/'core112.py'),paged_math=C.ref(P/'adapter.py'))
  print('{"actual_component_inputs_admitted":true,"model_ready":false,"NPU":false}');return 0
 print('{"source_audited":true,"model_ready":false,"NPU":false}');return 0
if __name__=='__main__':raise SystemExit(main())
