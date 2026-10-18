"""Reviewed preparation draft: new templates/tickets only, never a binding.

Default is a read-only plan. --emit-patch composes both trees in memory and
prints UTF8 contents for the authorized structured patch writer; it creates no
file or directory. --prepare reads only complete frozen own-source
files and writes two exclusive fresh preparation trees. It never starts a
process, imports model/owner code, reads closed raw, writes a ledger or creates
any SOURCE_MANIFEST.json. Actual early/binder/owner gates remain separate.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import stat

PREP = '/cache/cch/qwen36-paper-preparation-20261007/lowbit/'
MODEL_OLD = PREP + 'deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001'
MODEL_NEW = PREP + 'deltalog-first-real-decode-owned-renew24h-v1-101-repair38-closed-admission-identity-20261018-001'
EARLY_OLD = PREP + 'deltalog-early-software-owned-renew24h-v1-36-all4-publication'
EARLY_NEW = PREP + 'deltalog-early-software-owned-renew24h-v1-38-closed-admission-identity'
OPT = '/opt/host/vnf/austinov/'
EARLY_OUT_OLD = OPT + 'run-dl-R36publication-early-software-MAIN-RENEW24H_001'
EARLY_OUT_NEW = OPT + 'run-dl-R38identity-early-software-MAIN-RENEW24H_001'
P_ROOT = '/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/'
P_OLD = 'first-real-decode-model-snapshots-renew24h-R36publication-20261017-001'
P_NEW = 'first-real-decode-model-snapshots-renew24h-R38identity-20261018-001'
J_OLD = 'MODEL_SNAPSHOTS_LEDGER.R36publication.json'
J_NEW = 'MODEL_SNAPSHOTS_LEDGER.R38identity.json'
M_OLD_REF = dict(path=MODEL_OLD+'/SOURCE_TEMPLATE.json', bytes=290569,
    sha256='fc4fbbcd1846a247717ffaf5883ff77ade4fee045f965e78034a4b45cf881ac3')
E_OLD_REF = dict(path=EARLY_OLD+'/SOURCE_TEMPLATE.json', bytes=3757,
    sha256='85ce4c5c9981dee941b444eba03fc07acb83cc67dae030e13721045c5ccb64c5')
R37_MODEL_ROOT = PREP + 'deltalog-first-real-decode-owned-renew24h-v1-101-repair37-closed-admission-20261018-001'
R37_EARLY_ROOT = PREP + 'deltalog-early-software-owned-renew24h-v1-37-closed-admission'
R37_MODEL_REF = dict(path=R37_MODEL_ROOT+'/SOURCE_TEMPLATE.json', bytes=292409,
    sha256='f7bdde5f958f0aba8085a7321e99b45a417bb52c7ebdcb7ac71284f24488b97f')
R37_EARLY_REF = dict(path=R37_EARLY_ROOT+'/SOURCE_MANIFEST.json', bytes=3678,
    sha256='97075fae32d3fe0bd9a1650a4aa0e4ff8379051dc406b09888ffdf41d3b8f1a7')
R37_RESULT_REF = dict(path=OPT+'run-dl-R37admission-early-software-MAIN-RENEW24H_001/software/consumer/RESULT.json', bytes=703,
    sha256='7c9c59343ce7613d9cd95167f68f8d3bb148a513ced34410e3b7a0593fd7aec9')
PATCH_NAMES = ('firstdecode_refs.py', 'bind_source.py',
               'readonly_closed_admission.py', 'test_readonly_closed_admission.py')
MARK = '__R21_REVIEWED_TEMPLATE_SHA256__'
CUT = 1792313000


def need(v, why):
    if not v:
        raise ValueError(why)


def serialize(v):
    return (json.dumps(v, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def ref(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(r):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'}, 'exact source Ref3')
    p=Path(r['path'])
    need(p.is_absolute() and '..' not in p.parts and type(r['bytes']) is int
         and 0<r['bytes']<=4*2**20, 'bounded ordinary source only')
    a=p.lstat()
    need(stat.S_ISREG(a.st_mode) and all(not q.is_symlink() for q in (p,*p.parents)),
         'ordinary frozen source file')
    raw=p.read_bytes();b=p.lstat()
    key=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    need(key(a)==key(b) and ref(p,raw)==r, 'whole stable frozen original source bytes')
    return raw


def own_bytes(m):
    result={}
    for name,r in m['files'].items():
        n=Path(name)
        need(not n.is_absolute() and '..' not in n.parts
             and r['path']==m['root']+'/'+name, 'complete exact own-source closure')
        result[name]=checked(r)
    return result


def replace_once(raw, before, after):
    a,b=before.encode(),after.encode()
    need(raw.count(a)==1, 'single reviewed preparation seam: '+before)
    value=raw.replace(a,b)
    need(value.count(b)==1 and value.replace(b,a)==raw, 'whole source inverse seam')
    return value


def identity_text(value):
    mappings=((MODEL_OLD,MODEL_NEW),(EARLY_OLD,EARLY_NEW),
              (EARLY_OUT_OLD,EARLY_OUT_NEW),(P_OLD,P_NEW),(J_OLD,J_NEW),
              ('FIRSTDECODE101R36publication','FIRSTDECODE101R38identity'),
              ('R36publication','R38identity'),
              ('dl-software36publication-cpu-','dl-software38identity-cpu-'),
              ('ACTUAL_BOUND_FIRSTDECODE_R36_REF3','ACTUAL_BOUND_FIRSTDECODE_R38_REF3'),
              ('FINAL_R36_MODEL_TEMPLATE_REF3','FINAL_R38_MODEL_TEMPLATE_REF3'))
    for old,new in mappings:
        value=value.replace(old,new)
    return value


def rewrite(value, replacements, *, strings=False):
    if type(value) is dict:
        if set(value)=={'path','bytes','sha256'} and value['path'] in replacements:
            old,new=replacements[value['path']]
            need(value==old, 'no stale same-path Ref during preparation')
            return copy.deepcopy(new)
        return {k:rewrite(v,replacements,strings=strings) for k,v in value.items()}
    if type(value) is list:
        return [rewrite(v,replacements,strings=strings) for v in value]
    if strings and type(value) is str:
        return identity_text(value)
    return value


def refresh_active_fixtures(mt, old_owner, new_owner, old_early, new_early):
    """Update only the active owner/template pair and two path fixtures."""
    owner_name='software_dependencies/early_scan_owner.py'
    template_name='software_dependencies/early_scan_template.json'
    need(mt[owner_name]==old_owner and mt[template_name]==old_early,
         'exact original active early owner/template fixture pair')
    mt[owner_name]=new_owner
    mt[template_name]=new_early
    name='test_firstdecode_owner.py'
    original=mt[name]
    a,b=P_OLD.encode(),P_NEW.encode()
    need(original.count(a)==2 and b not in original,
         'exact two original owner metadata fixture paths')
    changed=original.replace(a,b)
    need(changed.count(b)==2 and a not in changed
         and changed.replace(b,a)==original,
         'same full owner test source with two reversible metadata paths')
    ast.parse(changed)
    mt[name]=changed


def module_constant(raw, name):
    values=[]
    for node in ast.parse(raw).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            value=node.value
            if isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=='Path':
                need(len(value.args)==1 and not value.keywords, 'exact Path constant')
                value=value.args[0]
            if isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=='dict':
                need(not value.args and all(k.arg is not None for k in value.keywords), 'literal identity dict')
                values.append({k.arg:ast.literal_eval(k.value) for k in value.keywords})
            else:values.append(ast.literal_eval(value))
    need(len(values)==1, 'one exact active source constant: '+name)
    return values[0]


def failed_r37(original_recover):
    model=json.loads(checked(R37_MODEL_REF))
    early=json.loads(checked(R37_EARLY_REF))
    result=json.loads(checked(R37_RESULT_REF))
    need(model['root']==R37_MODEL_ROOT and model['prepared_only'] is True
         and model['software_cases']==255, 'actual unbound R37 prepared predecessor')
    need(early['root']==R37_EARLY_ROOT and early['prepared_only'] is False
         and early['schema']=='deltalog.prebind-software-source/v22'
         and early['prepared_template']==model['early_software_policy']['prepared_owner_source'],
         'actual R37 early source/model prepared-template join')
    need(result['schema']=='deltalog.prebind-software-owned/v22'
         and result['source']==R37_EARLY_REF and type(result['primary']) is str and result['primary']
         and result['secondary']==[] and result['resource_release_verified'] is True
         and result['stopped_retained'] is True and result['stage_result'] is None
         and result['stage_ref'] is None and result['numeric_owner'] is None
         and result['Devices']==[] and result['NPU'] is False and result['qualified'] is False,
         'actual failed released R37 early attempt is retained, never qualified')
    need(checked(early['files']['recover.py'])==original_recover
         and module_constant(original_recover,'MODEL_ROOT')==MODEL_OLD,
         'exact demonstrated R37 child still pinned to original R36 root')
    checked(early['prepared_template'])
    return dict(model_template=R37_MODEL_REF,early_source=R37_EARLY_REF,
                early_template=early['prepared_template'],result=R37_RESULT_REF,
                outcome='failed-before-actual-software-stage',old_failures_preserved=True,
                qualified=False)


def active_identity_audit(mt,et,model,early,early_ref):
    need(module_constant(mt['packet_contract.py'],'ROOT')==MODEL_NEW
         and module_constant(mt['packet_contract.py'],'OUTPUT')==model['output_root']
         and module_constant(mt['packet_contract.py'],'IDENTITY')==model['runtime_identity']
         and module_constant(mt['packet_contract.py'],'SOFTWARE_CASES')==model['software_cases']==255,
         'one exact current model root/output/owner/run/case identity')
    need(module_constant(et['owner.py'],'ROOT')==EARLY_NEW
         and module_constant(et['owner.py'],'OUTROOT')==EARLY_OUT_NEW
         and module_constant(et['owner.py'],'OWNER')=='deltalog-R38identity-early-software'
         and module_constant(et['recover.py'],'MODEL_ROOT')==MODEL_NEW,
         'actual early owner and actual child agree on current model and output')
    need(early['root']==EARLY_NEW and early['output_root']==EARLY_OUT_NEW+'/software'
         and model['early_software_policy']['prepared_owner_source']==early_ref
         and model['early_software_policy']['owner_output_root']==early['output_root']
         and mt['software_dependencies/early_scan_owner.py']==et['owner.py']
         and mt['software_dependencies/early_scan_template.json']==et['SOURCE_TEMPLATE.json'],
         'complete active early owner/child/template/model-policy/fixture pairing')
    for name,r in early['files'].items():
        need(ref(EARLY_NEW+'/'+name,et[name])==r, 'complete final actual early own-source closure')
    need(P_NEW.encode() in mt['model_snapshot_budget.py']
         and J_NEW.encode() in mt['model_snapshot_budget.py']
         and et['owner.py'].count(b'dl-software38identity-cpu-')==1,
         'new P leaf/journal and actual early child CID namespace')
    forbidden=(MODEL_OLD,EARLY_OLD,P_OLD,J_OLD,'R36publication','dl-software36publication-cpu-',
               R37_MODEL_ROOT,R37_EARLY_ROOT,'R37admission','dl-software37admission-cpu-')
    findings={};python_count=0
    # Whole historical donor files and .txt/.b64 fixtures retain their original
    # identities. Every runnable .py in both new trees is otherwise scanned.
    historical={('early','DONOR_OWNER.py')}
    for alias,tree in (('model',mt),('early',et)):
        for name,body in sorted(tree.items()):
            if name.endswith('.py'):
                ast.parse(body);python_count+=1
                tokens=[token for token in forbidden if token.encode() in body]
                if tokens and (alias,name) not in historical:findings[alias+'/'+name]=tokens
    need(not findings,'stale identity in complete active model/early Python closure: '+json.dumps(findings,sort_keys=True))
    return dict(schema='deltalog.complete-active-preparation-identity/v1',
                model_root=MODEL_NEW,early_root=EARLY_NEW,
                model_cases=255,early_cases=253,payload_cases=26,
                actual_child_model_root=module_constant(et['recover.py'],'MODEL_ROOT'),
                python_files_syntax_and_identity_checked=python_count,
                active_stale_identity_tokens=findings,
                preserved_historical_python=['early/DONOR_OWNER.py'],
                model_source_created=False,NPU=False,qualified=False)


def put(tree, logical_root, name, raw):
    tree[name]=raw
    return ref(logical_root+'/'+name,raw)


def source_refs(root, tree):
    return {name:ref(root+'/'+name,raw) for name,raw in tree.items()}


def map_old(old, new):
    return {r['path']:(r,new[name]) for name,r in old.items()}


def exclusive_tree(root, tree):
    need(root.is_absolute() and not root.exists()
         and all(not p.is_symlink() for p in root.parents), 'exclusive new preparation tree')
    root.mkdir(mode=0o700,parents=True)
    for name,raw in sorted(tree.items()):
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:
            f.write(raw)


def prepare(patch_ref, model_out=None, early_out=None, *, emit=False):
    old_m=json.loads(checked(M_OLD_REF));old_e=json.loads(checked(E_OLD_REF))
    need(old_m['prepared_only'] is True and old_e['prepared_only'] is True,
         'only frozen prepared predecessors; never copy a bound manifest')
    mt=own_bytes(old_m);et=own_bytes(old_e)
    need(len(mt)==278 and len(et)==10, 'complete frozen R36 model/early own-file inventories')
    patch=json.loads(checked(patch_ref))
    need(patch['schema']=='deltalog.r37-preparation-patches/v1'
         and patch['predecessor_model_template']==M_OLD_REF
         and set(patch['files'])==set(PATCH_NAMES), 'exact separately reviewed patch closure')
    cases=patch['new_software_cases']
    need(type(cases) is int and cases>0 and patch['pure_cpu_controls_passed']==cases,
         'actual new helper controls and explicit unchanged old243 count')
    need(cases==12, 'same exact twelve readonly-admission controls; full255/early253 retained')
    total=old_m['software_cases']+cases
    need(old_m['software_cases']==243, 'original full243 gate retained')
    for name,r in patch['files'].items():
        mt[name]=checked(r);ast.parse(mt[name])

    predecessor=failed_r37(et['recover.py'])
    original_recover=et['recover.py']
    et['recover.py']=replace_once(original_recover,MODEL_OLD,MODEL_NEW)

    # The exact early owner has only identity/path substitutions. Its complete
    # donor inverse is regenerated, preserving the original donor source.
    old_owner=et['owner.py'];new_owner=identity_text(old_owner.decode()).encode()
    edits=json.loads(et['OWNER_EDITS.json'])
    need(edits['after']=={k:ref('',old_owner)[k] for k in ('bytes','sha256')}
         and len(edits['edits'])==1 and edits['edits'][0]['count']==1
         and edits['edits'][0]['after'].encode()==old_owner
         and edits['edits'][0]['before'].encode()==et['DONOR_OWNER.py'],
         'original complete early donor inverse')
    edits['edits'][0]['after']=new_owner.decode()
    edits['after']={k:ref('',new_owner)[k] for k in ('bytes','sha256')}
    et['owner.py']=new_owner;et['OWNER_EDITS.json']=serialize(edits)
    emap=map_old(old_e['files'],source_refs(EARLY_NEW,et))
    early=rewrite(old_e,emap)
    early['root']=EARLY_NEW;early['output_root']=EARLY_OUT_NEW+'/software'
    early['files']=source_refs(EARLY_NEW,et)
    early_ref=put(et,EARLY_NEW,'SOURCE_TEMPLATE.json',serialize(early))
    emap[E_OLD_REF['path']]=(E_OLD_REF,early_ref)

    # These are the only extra execution-source identity/counter deltas.
    mt['packet_contract.py']=identity_text(mt['packet_contract.py'].decode()).encode()
    mt['packet_contract.py']=replace_once(mt['packet_contract.py'],
        'SOFTWARE_CASES=243','SOFTWARE_CASES='+str(total))
    mt['model_snapshot_budget.py']=replace_once(mt['model_snapshot_budget.py'],P_OLD,P_NEW)
    mt['model_snapshot_budget.py']=replace_once(mt['model_snapshot_budget.py'],J_OLD,J_NEW)
    refresh_active_fixtures(mt,old_owner,new_owner,checked(E_OLD_REF),et['SOURCE_TEMPLATE.json'])

    # Preserve mathematical/plugin code and historical inverse/fixture bodies.
    # Rebuild only the plugin template's own Ref paths, then the model template.
    plugin=json.loads(mt['plugin/SOURCE_TEMPLATE.json'])
    pmap=map_old(old_m['files'],source_refs(MODEL_NEW,mt))
    plugin=rewrite(plugin,pmap);plugin['root']=MODEL_NEW+'/plugin'
    mt['plugin/SOURCE_TEMPLATE.json']=serialize(plugin)

    spec=json.loads(mt['COMMANDS_SPEC.json'])
    spec=rewrite(spec,emap,strings=True)
    spec['skeleton']['all_existing_cpu_controls']=total
    spec['skeleton']['early_software']['source_template']=early_ref
    # Early COMMANDS is derived after its own template and is not self-pinned.
    # A reviewed predecessor command packet is explicit input, never guessed.
    old_commands=patch['early_commands_ref']
    commands=json.loads(checked(old_commands))
    for key in ('bind',):
        for i,part in enumerate(commands[key]):
            if part.startswith('{'):
                candidate=json.loads(part)
                if candidate==E_OLD_REF:commands[key][i]=json.dumps(early_ref,separators=(',',':'))
    commands=rewrite(commands,emap,strings=True)
    commands['prepared_owner_source']=early_ref
    early_commands_ref=put(et,EARLY_NEW,'COMMANDS.json',serialize(commands))
    spec['skeleton']['early_software']['commands_ref']=early_commands_ref
    mt['COMMANDS_SPEC.json']=serialize(spec)

    mrefs=source_refs(MODEL_NEW,mt)
    allmaps=dict(emap);allmaps.update(map_old(old_m['files'],mrefs))
    model=rewrite(old_m,allmaps)
    model['root']=MODEL_NEW
    model['output_root']=identity_text(old_m['output_root'])
    model['postconsumer_output_root']=identity_text(old_m['postconsumer_output_root'])
    model['runtime_identity']=rewrite(old_m['runtime_identity'],{},strings=True)
    model['software_cases']=total;model['files']=mrefs
    model['early_software_policy']['prepared_owner_source']=early_ref
    model['early_software_policy']['owner_output_root']=early['output_root']
    model['firstdecode_contract']['closed_readset']=None
    model['firstdecode_contract']['closed_evidence_ref']=None
    model['plugin_source']=None
    model['storage_admission_repair']=dict(schema='deltalog.readonly-closed-admission-repair/v1',
        predecessor_template=M_OLD_REF, helper=mrefs['readonly_closed_admission.py'],
        original_storage061_unchanged=True, original_closed15_gates_retained=True,
        numerical_changes=False, qualified=False)
    model['prepared_identity_repair']=dict(schema='deltalog.complete-early-identity-repair/v1',
        predecessor=predecessor,actual_child=early['files']['recover.py'],
        original_child_execution_logic_unchanged=True,qualified=False)
    for previous in (predecessor['model_template'],predecessor['early_source'],
                     predecessor['early_template'],predecessor['result']):
        if previous not in model['dependencies']:model['dependencies'].append(previous)
    # Old source and retained failed attempts remain readable provenance.
    if M_OLD_REF not in model['dependencies']:model['dependencies'].append(M_OLD_REF)
    identity_audit=active_identity_audit(mt,et,model,early,early_ref)
    model_ref=put(mt,MODEL_NEW,'SOURCE_TEMPLATE.json',serialize(model))
    skeleton=copy.deepcopy(spec['skeleton'])
    need(skeleton['template']=={'$reviewed_template_ref':True}
         and skeleton['bind']['argv'][6]==skeleton['cheap_prebind']['argv'][6]==MARK,
         'same original exact ticket derivation seams')
    skeleton['template']=model_ref
    skeleton['bind']['argv'][6]=skeleton['cheap_prebind']['argv'][6]=model_ref['sha256']
    put(mt,MODEL_NEW,'COMMANDS_FINAL.json',serialize(skeleton))
    # Deferred source names are forbidden anywhere in prepared own-file maps.
    need('SOURCE_MANIFEST.json' not in mt and 'plugin/SOURCE_MANIFEST.json' not in mt
         and 'SOURCE_MANIFEST.json' not in et, 'preparation creates no bound source')
    need(model['cutoff_epoch']==CUT and model['phase_budget_registration']['whole_seconds']==3600
         and model['phase_budget_registration']['cleanup_seconds']==270
         and model['phase_budget_registration']['postverify_seconds']==900
         and model['phase_budget_registration']['margin_seconds']==90,
         'no changed clock or cleanup gate')
    for r in model['files'].values():
        name=Path(r['path']).relative_to(MODEL_NEW).as_posix()
        need(ref(r['path'],mt[name])==r,'complete final own-source closure')
    # Report remaining old current-identity tokens for review; historical copies
    # may legitimately contain them. This never silently rewrites old evidence.
    retained={name:[token for token in (MODEL_OLD,'R36publication',P_OLD,J_OLD)
                    if token.encode() in raw]
              for name,raw in mt.items()
              if any(token.encode() in raw for token in (MODEL_OLD,'R36publication',P_OLD,J_OLD))}
    receipt=dict(schema='deltalog.r38-prepared-only-package/v1',model_template=model_ref,
        early_template=early_ref,early_commands=early_commands_ref,
        software_cases=total,early_cases=total-2,payload_cases=26,
        patch_source=patch_ref,retained_old_identity_tokens=retained,
        active_identity_audit=identity_audit,failed_predecessor=predecessor,
        preparation_repair='complete-active-identity-closure-including-actual-early-child',
        prepared_only=True,model_source_created=False,NPU=False,qualified=False,
        cutoff_epoch=CUT,latest_actual_host_main_epoch=CUT-3600,
        requires=['review retained identity tokens','cheap_prebind new own closure',
                  'bind22 actual new early source','new same-image early suite and payload26',
                  'new full readonly closed15 bind and original component admission',
                  'bound-source audit','fresh original full3600 owner admission'])
    # Output trees must be reviewed before issuing any command. The original
    # source checks independently reject incomplete or mismatched closures.
    if emit:
        return dict(receipt=receipt, trees={
            EARLY_NEW:{name:raw.decode('utf8') for name,raw in sorted(et.items())},
            MODEL_NEW:{name:raw.decode('utf8') for name,raw in sorted(mt.items())}})
    exclusive_tree(early_out,et);exclusive_tree(model_out,mt)
    return receipt


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--emit-patch',action='store_true')
    p.add_argument('--patch-manifest-ref')
    p.add_argument('--model-output',type=Path)
    p.add_argument('--early-output',type=Path)
    a=p.parse_args()
    if not (a.prepare or a.emit_patch):
        print(json.dumps(dict(prepared_only=True,execute=False,NPU=False,
            model_root=MODEL_NEW,early_root=EARLY_NEW,payload_leaf=P_ROOT+P_NEW,
            journal=P_ROOT+J_NEW,model_source_created=False,
            original_full_cases=243,new_cases_pending=True,
            latest_actual_host_main_epoch=CUT-3600),sort_keys=True));return 0
    need(a.patch_manifest_ref and (a.emit_patch or (a.model_output and a.early_output)),
         'explicit reviewed patch Ref; preparation also needs exclusive destinations')
    need(not a.emit_patch or (a.model_output is None and a.early_output is None),
         'read-only emit mode accepts no filesystem output destination')
    result=prepare(json.loads(a.patch_manifest_ref),a.model_output,a.early_output,emit=a.emit_patch)
    print(json.dumps(result,sort_keys=True,allow_nan=False));return 0


if __name__=='__main__':raise SystemExit(main())
