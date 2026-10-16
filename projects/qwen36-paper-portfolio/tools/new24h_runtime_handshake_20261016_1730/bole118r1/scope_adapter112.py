"""Immutable MAIN host adapter; only numeric observation scope changes."""
import argparse,ast,hashlib,importlib.util,inspect,json,os,stat,sys,textwrap,time
from pathlib import Path
PIPE_SHA='059d48a5e4c3fadf9e4891aa30eb4a85aea88fc1e1f46e7b30e3a7b7da94e6f5'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked(r):
    p=Path(r['path'])
    if set(r)!={'path','bytes','sha256'}or not p.is_absolute()or p.is_symlink()or p.stat().st_size!=r['bytes']or sha(p)!=r['sha256']:raise ValueError('exact immutable adapter/producer Ref')
    return p
def scoped_cards(stage,stop_after_numerics,physical):
    if stage=='numeric'and stop_after_numerics:
        if physical!=4:raise ValueError('this immutable adapter is physical4 only')
        return (4,)
    return (4,5,6,7)
def ownership_reasons(protected,owned,cid,ancestors,fd_devices,protected_devices):
    reasons=[];identities={(p['pid'],p['start_ticks'])for p in owned}
    for p in protected:
        if not p.get('present',True):continue
        identity=(p['pid'],p['start_ticks'])
        if cid and cid in p['cgroup']:reasons.append('owned cgroup on protected physical')
        if identity in identities:reasons.append('owned actual PID/start_ticks on protected physical')
        if identities.intersection(ancestors.get(p['pid'],set())):reasons.append('owned ancestor of protected NPU process')
    if set(fd_devices).intersection(protected_devices):reasons.append('owned open FD addresses physical0-3 device number')
    return reasons
def nonselected_identity(lane,pid,card):
    try:identity=lane.h.gate_process(pid)
    except FileNotFoundError:return dict(pid=pid,present=False,external_exit_during_read=True)
    if lane.active and lane.active in identity['cgroup']:
        _MODULE.save(lane.a.run_root/('owned-offscope-'+str(time.time_ns())+'.json'),dict(physical=card,process=identity,active=lane.active))
        raise ValueError('owned process outside admitted physical4')
    return identity
def protected_observation(lane,raw,smi):
    m=lane._adapter_module if hasattr(lane,'_adapter_module')else _MODULE
    path=lane.a.run_root/('protected-observation-'+str(time.time_ns())+'.json')
    # Persist fresh raw SMI before any potentially racing /proc identity read.
    m.save(path,dict(schema='deltalog-protected-raw/v002',smi=smi,active=lane.active,host_adapter=m._adapter_ref))
    races=[]
    try:values=lane.h.protected(raw)
    except FileNotFoundError:
        values=[]
        for physical,chip,pid in lane.h.legacy().process_rows(raw):
            if physical not in (0,1,2,3):continue
            try:values.append(dict(physical=physical,chip=chip,**lane.h.process_identity(pid)))
            except FileNotFoundError:values.append(dict(physical=physical,chip=chip,pid=pid,present=False));races.append(pid)
    previous=lane.baseline;lane.baseline=values
    owned=[];ancestors={};fd_devices=[];protected_devices=[];inspect_receipt=None;top_receipt=None;error=None
    try:
        if lane.active:
            inspect_receipt,x=lane.inspect(lane.active)
            # Exact original check_inspect proves physical4->logical0 and no0-3
            # mapping. Docker top binds all actual container descendants.
            if x['State']['Running']:
                top_receipt=lane.call([m.DOCKER,'top',lane.active,'-eo','pid,ppid,args'],30)
                pids=[int(line.split()[0])for line in top_receipt['stdout'].splitlines()if line.split()and line.split()[0].isdigit()]
                m.require(x['State']['Pid']in pids,'actual container init included in top')
                for pid in pids:
                    proof=lane.h.gate_process(pid);m.require(lane.active in proof['cgroup'],'actual top PID owned cgroup')
                    for fd in (Path('/proc')/str(pid)/'fd').iterdir():
                        try:entry=fd.stat()
                        except FileNotFoundError:continue # FD closed, no surviving handle
                        if stat.S_ISCHR(entry.st_mode):fd_devices.append(entry.st_rdev)
                    m.require(lane.h.process_identity(pid)=={k:proof[k]for k in ('pid','start_ticks','cgroup','cmdline_sha256')},'own PID stable during FD read')
                    owned.append(proof)
                protected_devices=[Path('/dev/davinci'+str(card)).stat().st_rdev for card in (0,1,2,3)]
        for row in values:
            if not row.get('present',True):continue
            cursor=row['pid'];chain=set();seen=set()
            while cursor>1 and cursor not in seen:
                seen.add(cursor)
                try:
                    ident=lane.h.process_identity(cursor);chain.add((cursor,ident['start_ticks']))
                    text=(Path('/proc')/str(cursor)/'stat').read_text();cursor=int(text[text.rfind(')')+2:].split()[1])
                except FileNotFoundError:break # external exit recorded, not an owned live handle
            ancestors[row['pid']]=chain
        reasons=ownership_reasons(values,owned,lane.active,ancestors,fd_devices,protected_devices)
    except BaseException as exc:error=repr(exc);reasons=['protected ownership observation incomplete']
    verdict=dict(schema='deltalog-protected-ownership/v002',raw_ref=dict(path=str(path),sha256=m.c.sha(path)),
        protected=values,previous=previous,external_lifecycle_changed=previous is not None and previous!=values,
        exited_during_identity_read=races,owned=owned,ancestry={str(k):sorted(v)for k,v in ancestors.items()},
        actual_character_FD_device_numbers=fd_devices,protected_device_numbers=protected_devices,
        exact_owned_inspect=inspect_receipt,actual_owned_top=top_receipt,reasons=reasons,error=error,
        policy='no owned mapping/process/ancestor/FD on0-3; external lifecycle may change')
    m.save(lane.a.run_root/('protected-ownership-'+str(time.time_ns())+'.json'),verdict)
    m.require(not reasons,'owned protected0-3 boundary or incomplete proof: '+repr(reasons))
    return values
def transform_observe(original):
    edits=[('protected=self.h.protected(raw)\n    if self.baseline is None:self.baseline=protected\n    require(protected==self.baseline,"protected0..3 PID/start_ticks/cgroup/argv identity changed")',
            'protected=_adapter_protected(self,raw,smi)'),
      ('for card in (4,5,6,7):','for card in _adapter_scope(stage,self.a.stop_after_numerics,self.a.physical_device):'),
      ('cpu_record=self.cpu_observe(stage)',
       '''nonselected=[]
    scope=_adapter_scope(stage,self.a.stop_after_numerics,self.a.physical_device)
    for card in (4,5,6,7):
        if card not in scope:
            identities=[_adapter_nonselected(self,pid,card) for n,ch,pid in rows if n==card]
            nonselected.append(dict(physical=card,processes=identities,allocation_scope="external-not-admitted-or-managed",blocks_numeric=False))
    _adapter_checked(_adapter_ref)
    cpu_record=self.cpu_observe(stage)'''),
      ('owned_process_proofs=proof,active=self.active,lane_containers=lane_containers,',
       'owned_process_proofs=proof,active=self.active,lane_containers=lane_containers,\n        numeric_observation_scope=list(scope),nonselected_scope=nonselected,host_adapter=_adapter_ref,')]
    source=textwrap.dedent(original)
    for old,new in edits:
        if source.count(old)!=1:raise ValueError('actual original observe anchor drift')
        source=source.replace(old,new)
    restored=source
    for old,new in reversed(edits):restored=restored.replace(new,old)
    if restored!=textwrap.dedent(original):raise ValueError('registered minimal observation inverse')
    ast.parse(source);return source
def reuse_native(m,verdict_ref,lane,root,a):
    path=checked(verdict_ref);oldroot=path.parent
    m.require(path.name=='pipeline-verdict.json'and oldroot!=a.run_root and oldroot.is_relative_to(Path('/cache/cch')),'actual distinct original native-only verdict')
    final=json.loads(path.read_bytes());plan=json.loads((oldroot/'plan.json').read_bytes())
    m.require(final['status']=='native-no-device-complete-numeric-model-pending'and final['native_preflight']is True and final['numeric160']is False,'actual completed native-only producer')
    m.require(final['source_digest']==m.c.package_digest(root)and plan['source_digest']==m.c.package_digest(root)and plan['image']==m.c.IMAGE,'same actual v9 source/image')
    m.require(plan['current_authority']==a.current_authority and plan['stage_aware_mode']=='native-only','same fixed authority actual native-only plan')
    expected=dict(host=m.HOST_SHA,host_dependency=m.OLD_SHA,library=m.c.DECODE_SHA,config=m.c.CONFIG_SHA)
    m.require(plan['source_pins']==expected,'actual original helper/library/config pins')
    proof=m.accept_native_provenance(oldroot/'native',root,a,lane)
    checked(verdict_ref)
    proof.update(native_reused_from_actual_completed_producer=verdict_ref,new_host_adapter=m._adapter_ref)
    return proof
def transform_main(original):
    source=textwrap.dedent(original)
    old='native=run_stage(lane,lane.native,verdict)\n        native_proof=accept_native_provenance(a.run_root/"native",root,a,lane)'
    new='native_proof=_adapter_reuse_native(_adapter_module,_adapter_native_ref,lane,root,a)'
    if source.count(old)!=1:raise ValueError('actual native entry anchor drift')
    result=source.replace(old,new)
    if result.replace(new,old)!=source:raise ValueError('native reuse registered inverse')
    ast.parse(result);return result
def main():
    global _MODULE
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--pipeline-ref',required=True);p.add_argument('--adapter-sha256',required=True)
    p.add_argument('--native-verdict-ref',required=True)
    a,rest=p.parse_known_args()
    if '--stop-after-numerics'not in rest or '--resume-numeric-receipt'in rest or '--stop-after-native'in rest:
        raise ValueError('fresh numeric-only original pipeline, no model/resume route')
    if rest.count('--physical-device')!=1 or rest[rest.index('--physical-device')+1]!='4':raise ValueError('explicit physical4')
    own=Path(__file__).resolve();ownref=dict(path=str(own),bytes=own.stat().st_size,sha256=a.adapter_sha256);checked(ownref)
    pref=json.loads(a.pipeline_ref);pipeline=checked(pref)
    native_ref=json.loads(a.native_verdict_ref);checked(native_ref)
    if pref['sha256']!=PIPE_SHA:raise ValueError('actual sealed v9 original pipeline identity')
    sys.path.insert(0,str(pipeline.parent))
    spec=importlib.util.spec_from_file_location('actual_v9_pipeline',pipeline);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    _MODULE=m
    original=m.Lane.observe
    replacement=transform_observe(inspect.getsource(original))
    m.__dict__.update(_adapter_scope=scoped_cards,_adapter_ref=ownref,_adapter_checked=checked,
        _adapter_reuse_native=reuse_native,_adapter_module=m,_adapter_native_ref=native_ref,
        _adapter_protected=protected_observation,_adapter_nonselected=nonselected_identity)
    namespace={};exec(compile(replacement,str(own)+':registered-observe','exec'),m.__dict__,namespace)
    m.Lane.observe=namespace['observe']
    namespace={};exec(compile(transform_main(inspect.getsource(m.main)),str(own)+':registered-native-reuse','exec'),m.__dict__,namespace)
    m.main=namespace['main']
    # Every original method except observe remains the identical function object.
    # Original source_plan/package digest/native/numeric/create/cleanup are reused.
    sys.argv=[str(pipeline)]+rest
    return m.main()
if __name__=='__main__':raise SystemExit(main())
