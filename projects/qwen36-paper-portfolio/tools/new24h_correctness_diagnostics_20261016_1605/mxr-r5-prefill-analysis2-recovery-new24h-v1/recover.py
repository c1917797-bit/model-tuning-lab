"""Read-only alias recovery, NOT a rerun or a successful old-parent verdict."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path

P=Path(__file__).resolve().parent
FAILURE="ValueError('actual separate analysis and software receipt exact byte/source join')"
NAMES=dict(analysis='ANALYSIS120A1.json',receipt='ANALYSIS_RECEIPT.json',software='SOFTWARE_CONTROLS.json',parent='RESULT.json',inspect='FINAL_INSPECT.json',create='CREATE_ARGV.json',cid='CID.json')


def need(v,why):
    if not v:raise ValueError(why)


def ref(p):
    p=Path(p);h=hashlib.sha256();n=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())


def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3')
    p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary immutable file')
    before=p.stat();need(ref(p)==r,'exact preserved input bytes/SHA');after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'quiescent immutable input')
    return p


def obj(r):return json.loads(checked(r).read_bytes())


def load(r,name):
    spec=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def parse_create(argv,O,root):
    need(type(argv)is list and argv[:2]==[O.DOCKER,'create']and argv.count(O.IMAGE)==1,'actual original Docker create argv')
    index=argv.index(O.IMAGE);prefix=argv[:index];child=argv[index+1:]
    mounts={};env={}
    for i,value in enumerate(prefix):
        if value=='--mount':
            text=prefix[i+1];fields=text.split(',')
            need(fields[0]=='type=bind'and len(fields)in(3,4)and fields[1].startswith('src=')and fields[2].startswith('dst=')and (len(fields)==3 or fields[3]=='readonly'),'exact ordinary bind encoding')
            src,dst=fields[1][4:],fields[2][4:];need(src not in mounts and dst not in[v[0]for v in mounts.values()],'unique bind endpoints')
            mounts[src]=(dst,len(fields)==3)
        if value=='-e':
            k,v=prefix[i+1].split('=',1);need(k not in env,'unique explicit environment');env[k]=v
    need([src for src,(_,rw)in mounts.items()if rw]==[str(root)]and mounts[str(root)]==('/adakv-results',True),'ONE exact owned RW host-root to /adakv-results alias')
    expected=dict(ASCEND_RT_VISIBLE_DEVICES='',ASCEND_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR='/adakv-results',HOME='/adakv-results')
    need(env==expected,'unchanged Devices[] CPU environment')
    name=prefix[prefix.index('--name')+1];guest=int(prefix[prefix.index('--cpuset-cpus')+1])
    need(argv==O.create_argv(guest,mounts,env,name,child),'all original create resources/security/flags preserved')
    return mounts,env,name,guest,child


def validate(O,own,owner_ref,analysis_ref,evidence,data,root):
    need(set(evidence)==set(NAMES)and set(data)==set(NAMES),'complete exact seven preserved input records')
    for key,name in NAMES.items():
        need(Path(evidence[key]['path'])==root/name,'exact frozen parent output leaf/file')
    parent,inspect,receipt,software,d,argv=(data[k]for k in('parent','inspect','receipt','software','analysis','create'))
    need(parent['schema']=='mxr.prefill-analysis-owned-CPU/v120-analysis1'and parent['source']==owner_ref and parent['guest_source']==own['guest_source']and parent['stage_ref']==own['actual_stage_ref'],'actual failed parent exact source/stage')
    need(parent['primary']==FAILURE and parent['secondary']==[]and parent['resource_release_verified']is True and parent['stopped_retained']is True and parent['Devices']==[]and parent['NPU']is False and parent['qualified']is False,'ONLY exact alias predicate failed; old parent remains FAILED')
    need(type(inspect)is dict and inspect['Id']==parent['cid']and inspect['State']['Status']=='exited'and inspect['State']['Running']is False and inspect['State']['Pid']==0 and inspect['State']['ExitCode']==0 and inspect['State']['OOMKilled']is False and not inspect.get('ExecIDs'),'original child stopped exit0/noexec/noOOM')
    mounts,env,name,guest,child=parse_create(argv,O,root)
    need(data['cid']==dict(cid=parent['cid'],name=name),'actual original CID/name receipt joins CREATE and terminal inspect')
    need(len(child)==10 and child[:2]==['-I','-B']and child[2]==own['files']['analysis_entry.py']['path']and child[3:5]==['--execute','--source-ref']and json.loads(child[5])==owner_ref and child[6]=='--stage-ref'and json.loads(child[7])==own['actual_stage_ref']and child[8:]==['--output','/adakv-results/ANALYSIS120A1.json'],'actual exact source-bound analysis entry argv')
    O.inspect_owned(inspect,parent['cid'],mounts,env,guest,name,child)
    required=[owner_ref,*own['files'].values(),analysis_ref,own['guest_source'],own['actual_stage_ref'],own['actual_attribution_ref'],own['actual_CPU_owner_ref']]
    for r in required:need(mounts.get(r['path'])==(r['path'],False),'required source/evidence file exact RO mount')
    guest_ref=receipt['analysis_ref'];host_ref=evidence['analysis']
    need(type(guest_ref)is dict and set(guest_ref)=={'path','bytes','sha256'}and guest_ref['path']=='/adakv-results/ANALYSIS120A1.json'and guest_ref['bytes']==host_ref['bytes']and guest_ref['sha256']==host_ref['sha256'],'ONE validated guest alias with exact host bytes/SHA; no Ref rewrite')
    need(receipt['schema']=='mxr.prefill-analysis-owned-child/v120-analysis1'and receipt['source']==owner_ref and receipt['analysis_source']==analysis_ref and receipt['stage_ref']==own['actual_stage_ref']and receipt['software']==software and receipt['NPU']is False and receipt['qualified']is False,'original child receipt exact source/stage/software')
    need(software['source']==owner_ref and software['tests']==O.SOFTWARE_CASES==22 and software['passed']is True and software['NPU']is False and software['actual_data_consumed']is False,'original22 successful software controls, not fake numerical pass')
    # This does not mutate d or replace its source/path. The original numerical
    # predicate accepts extra transport metadata from its original receipt.
    O.receive_report(dict(d,owned_software=software),own,owner_ref)
    return dict(schema='mxr.analysis-alias-recovery/v120-analysis2',transport_recovery_valid=True,original_parent_pass=False,original_parent_primary=parent['primary'],original_parent_ref=evidence['parent'],original_analysis_ref=host_ref,original_guest_analysis_ref=guest_ref,original_receipt_ref=evidence['receipt'],original_software_ref=evidence['software'],original_inspect_ref=evidence['inspect'],original_create_ref=evidence['create'],original_CID=parent['cid'],actual_software_controls=22,cases=3,tileheads_per_case=384,qualification=False,model=False,performance=False,task=False,reference_validity_resolved=False,NPU=False,no_original_file_changed=True,no_numeric_report_copy=True)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--evidence-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"qualification":false}');return 0
    sr=json.loads(a.source_ref);m=obj(sr)
    need(m['schema']=='mxr.analysis-recovery-source/v120-analysis2'and m['root']==str(P)and m['files']['recover.py']==ref(__file__)and m['default_enabled']is False,'exact readonly recovery source')
    [checked(r)for r in m['files'].values()]
    owner_ref=m['original_owner_source_ref'];own=obj(owner_ref)
    need(own['analysis_source_ref']==m['original_analysis_source_ref']and own['root']==m['original_owner_root'],'exact old source chain')
    [checked(r)for r in own['files'].values()]
    O=load(own['files']['owned_analysis.py'],'_recovery120_frozen_owner')
    plan_ref=json.loads(a.evidence_ref);evidence=obj(plan_ref)
    need(evidence['schema']=='mxr.analysis-recovery-evidence/v120-analysis2'and evidence['source']==sr,'explicit source-bound actual seven-Ref evidence plan')
    refs=evidence['records'];need(set(refs)==set(NAMES)and refs==m['actual_record_refs'],'complete exactly frozen actual evidence readset')
    need(sum(r['bytes']for r in refs.values())<=m['budgets']['input_bytes_max'],'bounded existing JSON only, never rerun tensor analysis')
    [checked(r)for r in refs.values()]
    if a.source_audit:print(json.dumps(dict(source=sr,plan_ref=plan_ref,records=refs,NPU=False,qualification=False)));return 0
    need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','readonly CPU recovery autoloadOFF')
    data={key:obj(r)for key,r in refs.items()}
    need(data['cid']['cid']==m['actual_CID'],'fixed actual original container, no future identity')
    result=validate(O,own,owner_ref,m['original_analysis_source_ref'],refs,data,Path(m['actual_parent_output_root']))
    result.update(source=sr,evidence_plan_ref=plan_ref)
    root=Path(m['recovery_output_root'])
    need(a.output==root/'RECOVERY.json'and root.parent.is_dir()and not root.exists()and not any(q.is_symlink()for q in(root.parent,*root.parents)),'one fresh authorized recovery leaf; no original RW alias')
    payload=(json.dumps(result,sort_keys=True,allow_nan=False)+'\n').encode();need(len(payload)<=65536,'bounded verdict only, no numeric laundering')
    root.mkdir()
    with a.output.open('xb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
    return 0


if __name__=='__main__':raise SystemExit(main())
