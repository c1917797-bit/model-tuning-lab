"""Default-OFF finite readonly source copy; never create, start or exec a container."""
import argparse,hashlib,importlib.util,json,os,resource,stat,struct,subprocess,time
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
ROOT=Path('/opt/host/vnf/austinov/bole-native-ar-elf-bridge-v1')
AGG=dict(path=str(T/'NATIVE_AR_MAP_V3_FULL_AGGREGATION.json'),bytes=136077,sha256='d87061e2e85f8c730ed37701fafe201055fe6cf5a3d8ee5536c13e9a4e36ac8d')
RESULT=dict(path='/opt/host/vnf/austinov/run-bole-native-ar-map-v3/RESULT.json',bytes=375030,sha256='9dd64a67a1c706887a19d07bdbc55a346f35539045bc4d0ae0a9cb68bdc00826')
LM=dict(path='/opt/host/vnf/austinov/bole-native-ar-fia-control-v2/library_maps.py',bytes=5771,sha256='b1a0231cfb11fcd9a18cc0153ad2fb93098d58dd7aba642c20ecf69438bbbc82')
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
S=1267866920
BMAX=280680576
def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    p=Path(p);a=p.stat();h=hashlib.sha256();n=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
    z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)and n==z.st_size,'stable complete stream hash')
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj(r):
    a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'exact complete original Ref2/Ref3');return json.loads(Path(r['path']).read_bytes())
def put(p,v):
    with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(p)
def canonical(i):
    z=dict(i);mounts=i['Mounts'];need(len({x['Destination']for x in mounts})==len(mounts),'unique complete mount destinations')
    z['Mounts']=sorted(mounts,key=lambda x:x['Destination']);return z
def child_unlimited():
    resource.setrlimit(resource.RLIMIT_AS,(resource.RLIM_INFINITY,resource.RLIM_INFINITY))
def interpreter(p):
    size=p.stat().st_size
    with p.open('rb')as f:
        h=f.read(64);need(len(h)==64 and h[:4]==b'\x7fELF'and h[4]==2 and h[5]in(1,2),'actual bounded ELF64 interpreter header')
        order='<'if h[5]==1 else'>'
        _,machine,_,_,phoff,_,_,_,phsize,phcount,_,_,_=struct.unpack(order+'HHIQQQIHHHHHH',h[16:])
        need(machine==183 and phsize>=56 and phcount<=4096 and phoff+phcount*phsize<=size,'complete actual aarch64 program table')
        paths=[]
        for k in range(phcount):
            f.seek(phoff+k*phsize);kind,_,offset,_,_,length,_,_=struct.unpack(order+'IIQQQQQQ',f.read(56))
            if kind==3:
                need(1<length<=4096 and offset+length<=size,'bounded whole PT_INTERP');f.seek(offset);b=f.read(length)
                need(b[-1:]==b'\0'and b.count(b'\0')==1,'one complete PT_INTERP path');paths.append(b[:-1].decode('ascii'))
        need(len(paths)==1 and paths[0].startswith('/')and str(Path(paths[0]))==paths[0]and'..'not in Path(paths[0]).parts,'one exact ordinary absolute PT_INTERP')
        return paths[0]
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--controller-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"container_admitted":false}');return 0
    need(a.controller_ref and json.loads(a.controller_ref)==ref(__file__),'exact reviewed source copier')
    os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'original Docker/Go hard AS infinity');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
    start=time.monotonic();agg=obj(AGG);result=obj(RESULT);need(result['primary']is None and result['secondary']==[]and result['diagnostic_completed']is True and result['source_before']==result['source_after']and len(result['source_before'])==1094,'complete actual source-equal map diagnostic')
    for path,sha in result['source_before'].items():need(ref(path)['sha256']==sha,'every original 1094 source input unchanged')
    need(agg['source']==ref('/opt/host/vnf/austinov/run-bole-native-ar-map-v3/cpu-preflight/map-identity/EXECUTABLE-MAPPINGS.jsonl')and agg['count']==176 and agg['counts']==dict(match=1,mismatch=174,special_skip=1),'all original176 rows, no sampling')
    candidates=[r for r in agg['rows']if r['status']=='mismatch'];need(len(candidates)==174 and len({r['canonical']for r in candidates})==174,'all174 exact unique mismatches')
    for row in candidates:
        f=row['fingerprint'];need(row['path']==row['canonical']==f['ref']['path']and Path(row['path']).is_absolute()and str(Path(row['path']))==row['path']and'..'not in Path(row['path']).parts,'all canonical literal ordinary guest paths')
        need(row['map_dev']==[8,8]and row['stat_dev']==[0,77]and row['map_inode']==row['stat_inode']==f['stat']['inode']and row['fingerprint_error']is None and f['ELF']['ELF']is True and f['ELF']['machine']==183,'only exact observed overlay identity mismatch')
    need(sum(r['fingerprint']['ref']['bytes']for r in candidates)==S and max(r['fingerprint']['ref']['bytes']for r in candidates)==BMAX,'original complete byte and largest-file caps')
    ordinary=[r for r in agg['rows']if r['status']=='match'];special=[r for r in agg['rows']if r['status']=='special_skip']
    need(len(ordinary)==len(special)==1 and ordinary[0]['map_dev']==ordinary[0]['stat_dev']==[8,3]and special[0]['path']=='[vdso]','driver existing backing and original explicit kernel-only skip')
    ownref=result['summary']['diagnostic_owned'];own=obj(ownref);relref=result['summary']['diagnostic_release'];rel=obj(relref);cid=own['cid'];need(cid=='6fa1b850a63380d37cbab2f2aa5f3bc2e620827bd1ba8423f98df01304156be9'and own['image']==IMAGE and own['guest_cpus']==[0]and rel['container']==cid and rel['stopped']is True and rel['retained']is True and rel['deleted']is False and rel['errors']==[],'only actual original stopped-retained Devices[] CPU owner')
    afterref=ref(rel['after_inspect']['path']);saved=obj(afterref);need(saved['exit_code']==0,'successful original saved inspect');original=json.loads(saved['stdout'])[0]
    need(original['HostConfig']['Devices']==[]and original['HostConfig']['CpusetCpus']=='0'and original['HostConfig']['Memory']==8*2**30,'original CPU role resource profile')
    def run(argv):
        remaining=600-(time.monotonic()-start);need(remaining>0,'one unrenewed600 whole copy clock')
        q=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=min(90,remaining),preexec_fn=child_unlimited)
        need(q.returncode==0 and resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss<=512*1024,'complete bounded readonly Docker operation and actual RSS '+q.stderr)
        return q
    def inspect():
        q=run(['/usr/bin/docker','inspect',cid]);need(len(q.stdout.encode())<=4*2**20,'complete bounded inspect no truncation');items=json.loads(q.stdout);need(len(items)==1,'one actual original container');i=items[0];s=i['State']
        need(i['Id']==cid and i['Image']==IMAGE and s['Running']is False and s['Pid']==0 and s['OOMKilled']is False and not i.get('ExecIDs'),'current stopped PID0/noOOM/emptyExecIDs')
        for k in('Id','Image','State','Mounts','HostConfig','Config'):need(canonical(i)[k]==canonical(original)[k],'all original stopped metadata exact '+k)
        return i,dict(bytes=len(q.stdout.encode()),sha256=hashlib.sha256(q.stdout.encode()).hexdigest())
    before,before_wire=inspect();need(not ROOT.exists()and ROOT.parent==Path('/opt/host/vnf/austinov'),'exclusive new approved host copy leaf')
    fs=os.statvfs(ROOT.parent);free=fs.f_bavail*fs.f_frsize;need(not(fs.f_flag&getattr(os,'ST_NOEXEC',8))and free>=2*S+4*2**30,'actual executable backing and explicit copy/disk reserve')
    need(ref(LM['path'])==LM,'whole original unchanged ELF fingerprint implementation');spec=importlib.util.spec_from_file_location('_original_ar_library_maps',LM['path']);L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
    ROOT.mkdir(mode=0o700);rows=[];copied=0
    for index,row in enumerate(candidates):
        wanted=row['fingerprint'];guest=wanted['ref'];tmp=ROOT/('%03d.partial'%index);final=ROOT/('%03d.elf'%index)
        argv=['/usr/bin/docker','cp',cid+':'+guest['path'],str(tmp)];q=run(argv)
        need(tmp.is_file()and not tmp.is_symlink()and tmp.stat().st_size==guest['bytes'],'one exact ordinary copied ELF file')
        host=L.fingerprint(tmp);need(host['ref']['bytes']==guest['bytes']and host['ref']['sha256']==guest['sha256']and host['ELF']==wanted['ELF'],'whole original SHA and original ELF/buildIDs, no alternate identity rule')
        source_mode=stat.S_IMODE(tmp.stat().st_mode);os.chmod(tmp,0o555);tmp.rename(final)
        frozen=L.fingerprint(final);need(frozen['ref']['bytes']==guest['bytes']and frozen['ref']['sha256']==guest['sha256']and frozen['ELF']==wanted['ELF'],'frozen full original hash and ELF after final mode/rename')
        st=final.stat();rows.append(dict(ordinal=index,guest_ref=guest,guest_ELF=wanted['ELF'],original_diagnostic_row=row,host_ref=frozen['ref'],host_ELF=frozen['ELF'],host_stat=frozen['stat'],host_ctime_ns=st.st_ctime_ns,host_mode=stat.S_IMODE(st.st_mode),copy_received_mode=source_mode,copy_argv=argv,copy_exit=q.returncode))
        copied+=guest['bytes'];need(copied<=S,'complete one-copy byte bound, no growth')
    need(copied==S and len(rows)==174,'all exact174 files copied')
    python=[r for r in rows if r['guest_ref']['path']=='/usr/local/python3.12.13/bin/python3.12'];need(len(python)==1,'exact observed actual Python ELF')
    interp=interpreter(Path(python[0]['host_ref']['path']));tmp=ROOT/'PT_INTERP.partial'
    q=run(['/usr/bin/docker','cp','-L',cid+':'+interp,str(tmp)]);need(tmp.is_file()and not tmp.is_symlink()and tmp.stat().st_size<=BMAX,'ordinary bounded literal actual loader target')
    loader=L.fingerprint(tmp);matches=[r for r in rows if r['guest_ref']['bytes']==loader['ref']['bytes']and r['guest_ref']['sha256']==loader['ref']['sha256']and r['guest_ELF']==loader['ELF']]
    need(len(matches)==1,'actual literal PT_INTERP whole bytes uniquely join one observed canonical loader')
    os.chmod(tmp,0o555);loaderpath=ROOT/'PT_INTERP_exact_copy.elf';tmp.rename(loaderpath);loader_ref=ref(loaderpath)
    for r in rows:
        current=L.fingerprint(r['host_ref']['path']);st=Path(r['host_ref']['path']).stat();need(current==dict(ref=r['host_ref'],ELF=r['host_ELF'],stat=r['host_stat'])and st.st_ctime_ns==r['host_ctime_ns']and stat.S_IMODE(st.st_mode)==r['host_mode']==0o555,'all174 exact immutable final source backing files independently reopened')
    need(sum(p.stat().st_size for p in ROOT.iterdir())==S+loader_ref['bytes'],'whole exact disk materialization without partials')
    after,after_wire=inspect();need(canonical(after)==canonical(before),'all complete original stopped inspect metadata unchanged')
    os.chmod(ROOT,0o555)
    need(time.monotonic()-start<=600,'same finite source copy clock complete')
    output=dict(schema='bole.exact-observed174-ELF-readonly-copy-catalog/v1',controller_ref=ref(__file__),aggregation_ref=AGG,diagnostic_result_ref=RESULT,original_library_maps_ref=LM,original_owned_ref=ownref,original_release_ref=relref,original_after_inspect_ref=afterref,original_cid=cid,image=IMAGE,rows=rows,source_ELF_count=174,source_ELF_bytes=S,max_ELF_bytes=BMAX,PT_INTERP=dict(literal=interp,exact_copy=loader_ref,canonical_guest_ref=matches[0]['guest_ref'],canonical_host_ref=matches[0]['host_ref']),existing_driver_row=ordinary[0],original_kernel_skip=special[0],host_backing_device=ROOT.stat().st_dev,host_mount_noexec=False,free_bytes_at_entry=free,full_inspect_before=before_wire,full_inspect_after=after_wire,all_original_stopped_metadata_unchanged=True,actual_child_maxrss_KiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,phase_seconds=600,elapsed=time.monotonic()-start,container_created=False,container_started=False,container_exec_performed=False,container_admitted=False,original_container_or_image_modified=False,original_ELF_bytes_equal=True,filesystem_objects_unchanged=False,mapped_identity_qualified=False,native_FA_math_qualified=False,all256_native_calls_completed=False,formal_success=False,NPU=False)
    rr=put(Path(__file__).parent/'CATALOG.json',output);print(json.dumps(dict(catalog_ref=rr,source_ELF_count=174,source_ELF_bytes=S,PT_INTERP=output['PT_INTERP'],mapped_identity_qualified=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
