"""Default-OFF short8 source/command producer. No owner, Docker, NPU or approval creation."""
import argparse
import json
import hashlib
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def need(v,s):
    if not v:raise ValueError(s)

def write_json(path,value):
    raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
    with Path(path).open('xb')as out:out.write(raw)
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def checked_manifest(reference):
    import qualification_source_validate as V
    return json.loads(V.read_ref(reference))

def prepare_mapping(base_root,authority_ref=None):
    import runtime_lossless_imports as Q
    b=Q.render(base_root=Path(base_root),authority_ref=authority_ref)
    Q.inverse(b)
    return b

def materialize(base_root,authority_ref=None):
    # Prepared source only. MAIN may later separately review/freeze/bind.
    base=Path(base_root)
    need(base.is_absolute()and base.is_dir()and not any(p.is_symlink()for p in(base,*base.parents)),
         'ordinary existing explicit preparation root')
    need(base==HERE or HERE in base.parents,'only this independent preparation scope')
    b=prepare_mapping(base,authority_ref);root=Path(b['manifest']['root'])
    root.mkdir(mode=0o700)
    for name,raw in b['files'].items():
        path=root/name
        need(root in path.parents and '..'not in Path(name).parts,'exact contained prepared file')
        path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with path.open('xb')as out:out.write(raw)
    template=write_json(root/'SOURCE_TEMPLATE.json',b['manifest'])
    ledger=write_json(root/'SOURCE_DELTA.json',b['inverse_delta'])
    return dict(prepared_template=template,inverse_delta=ledger,prepared_only=True,
                bound_source_created=False,authority_created=False,NPU=False)

def bind(template_ref):
    import sourceio as C
    import qualification_source_validate as V
    m=checked_manifest(template_ref);root=Path(m['root'])
    need(root==HERE and Path(template_ref['path'])==root/'SOURCE_TEMPLATE.json'and
         m['prepared_only']is True and not(root/'SOURCE_BOUND.json').exists(),
         'actual own fresh prepared template only')
    V.qualification_shape(m)
    # Requires a real already-reviewed new authority. The producer neither
    # writes approval nor changes start/cutoff nor borrows expired authority.
    V.execution_window(m,clock=True,require_phase=True)
    for name,ref in m['files'].items():
        need(Path(ref['path'])==root/name and C.ref(root/name)==ref,'all prepared source files unchanged before import')
    for ref in m['qualification_parent_preparation_readset'].values():V.read_ref(ref)
    import runtime_lossless_imports as Q
    expected=Q.render(base_root=Path(m['qualification_preparation_root']),permit_materialized=True,
        parent_pair_preparation_root=Path(m['qualification_parent_pair_preparation_root']),
        historical_short_source_ref=m['qualification_historical_short_source'],
        authority_ref=m['qualification_authority_ref'],
        parent_preparation_readset=m['qualification_parent_preparation_readset'])
    Q.inverse(expected)
    need(m==expected['manifest'],'full reviewed experiment reconstruction before binding, not source hashes alone')
    actual=dict(m);actual['prepared_only']=False;actual['prepared_template']=template_ref
    actual['qualification_source_binding_pending']=False
    sr=C.write(root/'SOURCE_BOUND.json',actual)
    commands=write_commands(sr)
    return dict(source=sr,commands=commands,source_only=True,authority_created=False,NPU=False,
                numerical_qualified=False,performance_admitted=False)

def write_commands(source_ref):
    import sourceio as C
    import command_contract as K
    import qualification_source_validate as V
    m=checked_manifest(source_ref);root=Path(m['root'])
    need(root==HERE and m['prepared_only']is False and
         Path(source_ref['path'])==root/'SOURCE_BOUND.json'and
         C.ref(__file__)==m['files']['qualification_source_producer.py']and
         C.ref(K.__file__)==m['files']['command_contract.py'],
         'actual source-bound post-binding command producer')
    V.qualification_shape(m)
    V.execution_window(m,clock=False,require_phase=False)
    template=C.ref(root/'SOURCE_TEMPLATE.json')
    need(template==m['prepared_template'],'exact actual immutable prepared template')
    historical=C.obj(m['command_scope']['historical_ref'])
    commands=K.expected(m['root'],m['output_root'],source_ref,template,m['component_refs'])
    value=dict(schema='bole.performance-actual-bound-commands/v1',source=template,bound_source=source_ref,
        required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
        historical_required_sameimage_software_cases=historical['required_sameimage_software_cases'],
        G3_stream_protocol=False,actual_G3_execution_claimed=False,actual_G1_execution_claimed=False,
        legacy_entrypoints_retained_for_inverse_tests_only=True,**commands)
    K.validate_value(value,m,source_ref,template,historical)
    ref=C.write(root/'COMMANDS.json',value)
    mirror=dict(source=source_ref,template=template,commands=ref,model=value['model'],CPU=value['CPU'],
                required_sameimage_software_cases=m['service_required_sameimage_software_cases'])
    C.write(root/m['command_scope']['compatibility_file'],mirror)
    return ref

def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    modes=p.add_mutually_exclusive_group()
    modes.add_argument('--prepare',action='store_true');modes.add_argument('--bind',action='store_true')
    modes.add_argument('--write-commands',action='store_true')
    p.add_argument('--base-root');p.add_argument('--authority-ref')
    p.add_argument('--template-ref');p.add_argument('--source-ref')
    a=p.parse_args()
    if not any((a.prepare,a.bind,a.write_commands)):
        need(not any((a.base_root,a.authority_ref,a.template_ref,a.source_ref)),'mode required for operands')
        print(json.dumps(dict(enabled=False,NPU=False,source_bound=False)));return
    if a.prepare:
        need(a.base_root and not a.template_ref and not a.source_ref,'exact preparation operands')
        result=materialize(a.base_root,None if a.authority_ref is None else json.loads(a.authority_ref))
    elif a.bind:
        need(a.template_ref and not any((a.base_root,a.authority_ref,a.source_ref)),'exact bind operands')
        result=bind(json.loads(a.template_ref))
    else:
        need(a.source_ref and not any((a.base_root,a.authority_ref,a.template_ref)),'exact command operands')
        result=dict(commands=write_commands(json.loads(a.source_ref)),NPU=False)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
