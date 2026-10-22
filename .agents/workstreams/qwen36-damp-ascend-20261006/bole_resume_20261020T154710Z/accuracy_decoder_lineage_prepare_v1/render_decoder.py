"""Pure reversible decoder owning-layer adaptation. No authority, old-source edits or model launch."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
HISTORICAL_SOURCE=dict(path='/opt/host/vnf/austinov/run-bole-task-cpu-20261020T154710Z-v14/cpu-preflight/TASK_SOURCE_BOUND.json',
    bytes=10686,sha256='8bda8c57d2ee79867de8cbc1783cce9fda09dfd2a0a63438cb81131e1853bb09')
TRANSPORT=WORK/'accuracy_smoke_ready_prepare_v1/transport_candidate_v2'
TRANSPORT_PINS={'http_common.py':'6d24a14c2a49499bd9caf63e0a405a9d5b4c91d79284c4acdc81f9b5b1bf5646',
 'cohort_contract.py':'09c614efc9a17cccf938ad581dd787ccef6eefa77ebd700f014534fac12ed31a',
 'CPU_OWNER_EXPECTED.json':'1b992ab2d3121f4382058f3ff7843591c137dc96d87f4109e570a33fcdf26713'}

def need(v,s):
    if not v:raise ValueError(s)

def refbytes(path,raw):return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def checked(r):
    p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary original source')
    raw=p.read_bytes();need(refbytes(p,raw)==r,'whole exact immutable original source');return raw

def authority_delta(text):
    tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='current_authority')
    old=ast.get_source_segment(text,node)
    legacy=old.replace('def current_authority(','def _historical_current_authority(',1)
    wrapper="""def current_authority(reference,seconds=0,now=None):
    import decoder_replay_contract as REPLAY
    return REPLAY.current_authority(reference,seconds=seconds,now=now)"""
    need(text.count(old)==1,'one complete original authority function')
    result=text.replace(old,legacy+'\n\n'+wrapper,1)
    marker="    m=obj(source_ref)\n"
    need(result.count(marker)==1,'one original source lookup')
    injected=marker+"    import decoder_replay_contract as REPLAY\n    REPLAY.assert_source(m,source_ref)\n"
    result=result.replace(marker,injected,1)
    input_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='verify_inputs')
    original_verify=ast.get_source_segment(text,input_node)
    legacy_verify=original_verify.replace('def verify_inputs(','def _historical_verify_inputs(',1)
    verify_wrapper="""def verify_inputs(m):
    import decoder_replay_contract as REPLAY
    return REPLAY.verify_inputs(m,_historical_verify_inputs)"""
    need(result.count(original_verify)==1,'one complete original input verifier')
    result=result.replace(original_verify,legacy_verify+'\n\n'+verify_wrapper,1)
    compile(result,'task_contract.py','exec')
    return result,dict(original_authority=old,injected=injected,original_verify_inputs=original_verify)

def inverse_authority(text,ledger):
    old=ledger['original_authority'];legacy=old.replace('def current_authority(','def _historical_current_authority(',1)
    wrapper="""def current_authority(reference,seconds=0,now=None):
    import decoder_replay_contract as REPLAY
    return REPLAY.current_authority(reference,seconds=seconds,now=now)"""
    marker=legacy+'\n\n'+wrapper
    need(text.count(marker)==1 and text.count(ledger['injected'])==1,'exact reversible owning-layer seam')
    result=text.replace(marker,old,1).replace(ledger['injected'],"    m=obj(source_ref)\n",1)
    verifier=ledger['original_verify_inputs']
    legacy=verifier.replace('def verify_inputs(','def _historical_verify_inputs(',1)
    wrapper="""def verify_inputs(m):
    import decoder_replay_contract as REPLAY
    return REPLAY.verify_inputs(m,_historical_verify_inputs)"""
    need(result.count(legacy+'\n\n'+wrapper)==1,'exact complete legacy input verifier preserved')
    return result.replace(legacy+'\n\n'+wrapper,verifier,1)

def render(new_root,*,authority_ref=None,binding_ref=None):
    root=Path(new_root);need(root.is_absolute()and '..'not in root.parts,'explicit new source root')
    original=json.loads(checked(HISTORICAL_SOURCE))
    originals={n:checked(r)for n,r in original['files'].items()}
    need(originals['score_tokens.py']and hashlib.sha256(originals['score_tokens.py']).hexdigest()==
         'b795a944f99a6dcb915e05d0e7ccad03097c4453a279fae1e509eae78133eab5','unchanged official scorer')
    files=dict(originals);body,ledger=authority_delta(originals['task_contract.py'].decode());files['task_contract.py']=body.encode()
    for name in ('decoder_replay_contract.py','replay_entry.py','generation_provenance.py'):files[name]=(HERE/name).read_bytes()
    for old,sha in TRANSPORT_PINS.items():
        raw=(TRANSPORT/old).read_bytes();need(hashlib.sha256(raw).hexdigest()==sha,'fixed existing historical CPU proof helper')
        files['lineage_http_common.py'if old=='http_common.py'else old]=raw
    m=copy.deepcopy(original);m.update(root=str(root),files={n:refbytes(root/n,b)for n,b in files.items()},
        authority_ref=authority_ref,decoder_replay_lineage_ref=binding_ref,
        decoder_replay_source_schema='bole.current-CPU-decode-replay-source/v1',
        historical_task_source_ref=HISTORICAL_SOURCE,prepared_only=True,default_enabled=False)
    for name,raw in files.items():
        if name.endswith('.py'):compile(raw,name,'exec')
    need(inverse_authority(body,ledger).encode()==originals['task_contract.py'],'complete exact original authority gate preserved/reconstructable')
    need(all(files[n]==raw for n,raw in originals.items()if n!='task_contract.py'),'all original decoder/scorer/cohort/HE math bytes unchanged')
    return dict(manifest=m,files=files,original_manifest=original,originals=originals,
        source_delta=ledger,source_bound=False,authority_created=False,HTTP=False,NPU=False,
        formal_task_accuracy_accepted=False)

def inverse(bundle):
    result=dict(bundle['files']);result['task_contract.py']=inverse_authority(result['task_contract.py'].decode(),bundle['source_delta']).encode()
    for name in set(result)-set(bundle['originals']):result.pop(name)
    need(result==bundle['originals'],'every old source byte reconstructed, no arithmetic substitution')
    return result

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--review',action='store_true');p.add_argument('--new-root',type=Path);a=p.parse_args()
    if not a.review:print('{"enabled":false,"HTTP":false,"NPU":false}');return
    need(a.new_root,'explicit prospective replay root')
    b=render(a.new_root);inverse(b)
    print(json.dumps(dict(source_files=len(b['files']),changed_original_files=['task_contract.py'],
        scorer_math_unchanged=True,default_enabled=False,source_bound=False,authority_created=False,
        next_entry='replay_entry.py --execute --source EXACT_NEW_SOURCE --binding-ref ACTUAL_CURRENT_BINDING --output FRESH_CPU_OUTPUT',
        pending=['MAIN actual current CPU-only authority/review and process/inspect binding',
                 'actual generation owner/time/source/plan/raw provenance',
                 'MAIN source/template materialization plus exact file/readset gate',
                 'same-image no-device import and original decoder controls',
                 'transport consumer owning-layer integration; stable transport_v2 is unchanged'],
        HTTP=False,NPU=False)))
if __name__=='__main__':main()
