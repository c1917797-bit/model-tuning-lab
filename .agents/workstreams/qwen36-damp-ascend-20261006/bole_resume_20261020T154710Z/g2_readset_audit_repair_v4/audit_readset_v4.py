"""Default-OFF, source-owned read-only Ref/command/readset audit supplement."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ACTUAL_V3 = dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v3/SOURCE_BOUND.json',
                 bytes=220181,sha256='91002bf0dbda04826db5a1c4d3264b36da0bfaf4f4464feb50ce8ee05435c874')
ORIGINAL_V3_PREPARER = dict(bytes=16199,sha256='59ecabb021eb77493d9d6a9f328680f45028d92a438e7e4506c472b54f7f1e2b')
ACTUAL_G1 = dict(path='/opt/host/vnf/austinov/bole-g1-two-request-20261020T154710Z-v2/SOURCE_BOUND.json',
                 bytes=109479,sha256='010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677')


def need(v, message):
    if not v:
        raise ValueError(message)


def ref(path):
    path=Path(path)
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path,*path.parents)),
         'ordinary absolute file with no symlink path component')
    before=path.stat();h=hashlib.sha256();size=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):
            h.update(block);size+=len(block)
    after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and size==after.st_size,
         'stable exact ordinary file read')
    return dict(path=str(path),bytes=size,sha256=h.hexdigest())


def checked(value):
    need(type(value) is dict and set(value)=={'path','bytes','sha256'} and
         type(value['path']) is str and type(value['bytes']) is int and value['bytes']>=0 and
         type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']),
         'exact well-typed Ref3')
    need(ref(value['path'])==value,'exact supplied Ref3 path/bytes/SHA')
    return Path(value['path'])


def obj(value):
    return json.loads(checked(value).read_bytes())


def unique(references):
    result={}
    for value in references:
        checked(value)
        need(value['path'] not in result or result[value['path']]==value,
             'no conflicting Ref3 for one exact path')
        result[value['path']]=value
    return list(result.values())


# Each source gets an isolated Python process. Only insertion order is rebuilt;
# source-owned readset/command functions remain byteexact and enforce literal argv.
READSET_PROGRAM = r'''
import hashlib,json,re,sys
from pathlib import Path

def need(v,s):
 if not v:raise ValueError(s)
def actual(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),"ordinary absolute file/no symlink")
 before=p.stat();h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for block in iter(lambda:f.read(2**20),b''):h.update(block);size+=len(block)
 after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and size==after.st_size,"stable file read")
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def check(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),"exact typed Ref3")
 need(actual(r['path'])==r,"exact supplied path/bytes/SHA before any import")
 return Path(r['path'])
provided=json.loads(sys.argv[1]);raw=check(provided).read_bytes();m=json.loads(raw)
root=Path(m['root']);need(root.is_absolute()and root==Path(provided['path']).parent,"source Ref is its exact owned root")
for name,r in m['files'].items():
 need(Path(r['path'])==root/name,"exact source-owned file operand");check(r)
for name in('sourceio.py','bind_model.py','command_contract.py'):need(name in m['files'],"explicit source-owned audit helper pin")
sys.path.insert(0,str(root))
import sourceio as C,bind_model as B,command_contract as CC
for name,module in(('sourceio.py',C),('bind_model.py',B),('command_contract.py',CC)):
 need(actual(module.__file__)==m['files'][name],"imported exact original source-owned helper")
C.checked(provided)
sr=C.ref(provided['path'])
need(sr==provided and list(sr)==['path','bytes','sha256'],"same fully validated Ref rebuilt by exact source-owned C.ref")
commands_ref=C.ref(root/'COMMANDS.json');commands=C.obj(commands_ref)
proofs={}
for key in('model','CPU'):
 argv=commands[key];need(type(argv)is list and argv.count('--source-ref')==1,"single exact source argv")
 value=argv[argv.index('--source-ref')+1]
 need(json.loads(value)==provided,"original COMMANDS argv Ref has same exact source semantics")
 need(value==json.dumps(sr),"original COMMANDS argv remains exact canonical source-owned C.ref serialization")
 proofs[key]=dict(argument=value,semantic_equal=True,literal_equal_to_sourceio_ref=True,
  literal_equal_to_supplied_serialization=value==json.dumps(provided))
# These are the original source functions, with no monkeypatch or relaxed contract.
refs=[*B.readset(sr),*m['dependencies'],*CC.validate(C,sr,m)]
serialization_differs=any(not item['literal_equal_to_supplied_serialization']for item in proofs.values())
try:
 CC.validate(C,provided,m)
except ValueError as error:
 need(serialization_differs,"provided original contract failed beyond the diagnosed serialization order")
 old_call=dict(rejected=True,reason=str(error),serialization_differs=True)
else:
 need(not serialization_differs,"original contract unexpectedly accepted altered literal source argv")
 old_call=dict(rejected=False,reason=None,serialization_differs=False)
by_path={} 
for r in refs:
 check(r);C.checked(r)
 need(r['path']not in by_path or by_path[r['path']]==r,"no conflicting exact prerequisite path")
 by_path[r['path']]=r
for r in by_path.values():check(r)
need(actual(sr['path'])==sr and actual(commands_ref['path'])==commands_ref,"unchanged source and COMMANDS after original functions")
print(json.dumps(dict(source=sr,refs=list(by_path.values()),commands=commands_ref,
 helper_sources={name:m['files'][name]for name in('sourceio.py','bind_model.py','command_contract.py')},
 supplied_key_order=list(provided),sourceio_key_order=list(sr),original_command_source_arguments=proofs,
 source_owned_original_functions=['bind_model.readset','command_contract.validate'],
 serialization_only_reconstruction=True,original_unreconstructed_call=old_call,source_and_commands_unchanged=True)))
'''


def source_readset(source_ref):
    checked(source_ref)
    result=subprocess.run(['/usr/bin/python3','-I','-B','-c',READSET_PROGRAM,json.dumps(source_ref)],
                          capture_output=True,text=True,timeout=120)
    need(result.returncode==0,'original source-owned readset/command audit failed: '+result.stderr[-6000:])
    value=json.loads(result.stdout)
    need(value['source']==source_ref,'exact returned original source identity')
    unique(value['refs'])
    return value


def parent_rank_reports(parent_source,qualification_ref):
    qualification=obj(qualification_ref);references=qualification['ranks']
    need(type(references)is list and len(references)==4 and len({r['path']for r in references})==4,
         'four distinct actual independent parent rank report Refs')
    requests=None
    for rank,reference in enumerate(references):
        checked(reference)
        need(Path(reference['path'])==Path(qualification_ref['path']).parent/('RANK-%d.json'%rank),
             'exact parent qualification sibling rank report')
        row=obj(reference);items=row['requests']
        need(row['source']==parent_source and len(items)==2 and
             [v['generation']for v in items]==[1,2] and
             all(v['rank']==rank and v['actual_final_retirement_observed']is True and
                 v['component_checks_pass']is True and v['actual_next_counter_acknowledgements']==0 and
                 len(v['output_token_ids'])==2 and v['model_ready']is False for v in items),
             'actual both G1-v2 generations retired with original component gates on exact source/rank')
        identities=[(v['request'],v['output_token_ids'])for v in items]
        need(len({v['request']for v in items})==2 and(requests is None or identities==requests),
             'same two distinct request/output identities across all four actual reports')
        requests=identities
    return references


def audit(source_ref):
    current=obj(source_ref);p=current['g2_predecessor'];obj(p['source'])
    checked(p['owner_result']);ranks=parent_rank_reports(p['source'],p['qualification'])
    historical=source_readset(p['source']);actual=source_readset(source_ref)
    required=unique([*historical['refs'],p['source'],p['owner_result'],p['qualification'],*ranks])
    by_path={r['path']:r for r in actual['refs']}
    missing=[r for r in required if by_path.get(r['path'])!=r]
    need(not missing,'historical exact prerequisite closure missing/conflicting: '+json.dumps(missing))
    preparer=current['g2_parent_prerequisites_v3']['actual_preparer'];checked(preparer)
    for value in required+actual['refs']:checked(value)
    need(ref(source_ref['path'])==source_ref,'actual v3 source unchanged by read-only audit')
    digest=hashlib.sha256(json.dumps(sorted(required,key=lambda r:r['path']),sort_keys=True).encode()).hexdigest()
    return dict(schema='bole.G2-readonly-source-preparation-audit-supplement/v4',
        source=source_ref,parent_source=p['source'],audit_source=ref(Path(__file__).absolute()),
        original_v3_audit_preparer=preparer,
        original_failure=dict(stage='v3 final readonly READSET_PROGRAM',
          cause='audit passed parsed sorted-key Ref to exact command_contract; json.dumps key order differed from original sourceio.C.ref argv',
          source_or_COMMANDS_defect_claimed=False,original_failure_preserved=True),
        correction='verify complete supplied Ref, then rebuild insertion order using each exact source-owned C.ref(path)',
        original_contract_unmodified=True,original_source_and_COMMANDS_unmodified=True,
        historical=historical,current=actual,independently_validated_parent_rank_reports=ranks,
        required_refs=required,required_refs_sha256=digest,missing=[],
        source_preparation_supplement_only=True,CPU242_preflight_still_required=True,
        CPU_or_NPU_execution_qualified=False,directory_mounts_added=False,NPU=False)


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--source-ref')
    args=parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false}');return 0
    need(args.source_ref,'explicit actual v3 source Ref3')
    sr=json.loads(args.source_ref)
    need(sr==ACTUAL_V3,'only the preserved actual v3 SOURCE is authorized by this supplement')
    value=obj(sr)
    need(value['g2_predecessor']['source']==ACTUAL_G1,'exact actually qualified G1-v2 predecessor')
    preparer=value['g2_parent_prerequisites_v3']['actual_preparer'];checked(preparer)
    need(all(preparer[k]==v for k,v in ORIGINAL_V3_PREPARER.items()),'exact retained original v3 preparer containing failed read-only audit')
    print(json.dumps(audit(sr),sort_keys=True,allow_nan=False));return 0


if __name__=='__main__':raise SystemExit(main())
