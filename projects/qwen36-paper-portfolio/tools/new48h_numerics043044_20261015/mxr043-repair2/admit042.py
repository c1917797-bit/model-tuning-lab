"""Light source-bound successful/released MXR042 receipt reader; no raw/torch import."""
import hashlib,json
from pathlib import Path
SOURCE042={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-working-domain-heldout-new48h-v1-042/SOURCE_MANIFEST.json','bytes':15593,'sha256':'cf39ca19254a30a82844dd88754da596b33339e33eb7adb60e0b78ae443ecbcb'}
def need(v,m):
 if not v:raise ValueError(m)
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'actual complete Ref3 required')
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual receipt whole hash');return json.loads(b)
def validate(owner,consumer,probe,cleanups):
 need(owner['schema']=='mxr.saved-frame-owned/v042'and owner['source']==SOURCE042 and owner['primary']is None and owner['secondary']==[]and owner['cpu_preflight']is False and owner['released']is True,'actual042 NPU successful owner and release')
 need(len(cleanups)==2 and all(x['stopped']is x['retained']is True and x['errors']==[]for x in cleanups),'both actual042 CIDs stopped retained')
 need(owner['source_hashes_before']==owner['source_hashes_after']and owner['phase_seconds']==2400 and 0<owner['elapsed_seconds']<=2400,'same immutable source/time budget')
 need(probe['source']==SOURCE042 and probe['primary']is None and len(probe['raws'])==9 and len({r['path']for r in probe['raws']})==9 and probe['candidate_hits']==18 and len(probe['teardown'])==3 and all(x.get('pass_release')is True for x in probe['teardown']),'actual042 complete NPU capture')
 need(consumer['schema']=='mxr.three-arm-solve-chain-independent/v042'and consumer['source']==SOURCE042 and consumer['probe']==owner['probe']and consumer['complete']is True and consumer['working_domain_heldout_pass']is True and consumer['actual_native_initial_state_calibration_pass']is True and consumer['numerical_qualification_granted']is False and consumer['original_failures_unchanged']is True,'actual independent new domain and initial-state calibration; bounded not model')
 rows=consumer['rows'];need(len(rows)==9,'all real and calibration rows')
 expected=[('nontrivial_heldout_layer16',r)for r in range(3)]+[('nontrivial_heldout_layer40',r)for r in range(3)]+[('initial_state_rounding_witness',r)for r in range(3)]
 need([(x['role'],x['repeat'])for x in rows]==expected and all(x['working_domain_gate_pass']is True for x in rows),'no missing or failed heldout row')
 need(all(all(y['inputs_unchanged']is True for y in x['arms'].values())for x in rows),'all real inputs unchanged')
 return dict(scope='attempt-untimed-TP4-short129-new-refined-math-only',model_ready=False,performance_ready=False,task_ready=False,binary_provenance_granted=False)
def gate(owner_ref):
 need(owner_ref is not None,'042 actual successful owner missing; no model load')
 owner=obj(owner_ref);source=obj(SOURCE042)
 for r in source['files'].values():obj(r)if r['path'].endswith('.json')else checked_bytes(r)
 consumer=obj(owner['result']);probe=obj(owner['probe']);cleanups=[obj(r)for r in owner['cleanup']]
 value=validate(owner,consumer,probe,cleanups)
 need(consumer['selection']==probe['selection'],'same source-bound selection')
 return dict(value,actual042_owner=owner_ref,source042=SOURCE042,readset=[SOURCE042,owner_ref,owner['result'],owner['probe'],*owner['cleanup'],probe['selection'],*source['files'].values(),*source['native_source_refs']])
def checked_bytes(r):
 p=Path(r['path']);b=p.read_bytes();need(not p.is_symlink()and(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'042 source byte identity');return b
