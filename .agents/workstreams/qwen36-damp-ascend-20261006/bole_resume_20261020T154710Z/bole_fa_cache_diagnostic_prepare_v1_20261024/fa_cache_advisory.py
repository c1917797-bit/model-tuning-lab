"""Own immutable FA cache advisory only. No global cache, deletion, or RAM waiver."""
import os
import stat
import re
from pathlib import Path

FLAG='BOLE_OWN_FA_CACHE_ADVISE_ENABLE'
CONTRACT=dict(schema='bole.own-immutable-fa-cache-advisory/v1',enabled=True,
              only='B-SHA.bin',advisory='POSIX_FADV_DONTNEED',formal_performance=False)
_AUTH=None

def need(v,s):
    if not v:raise ValueError(s)

def configure(c,root):
    global _AUTH
    flag=os.environ.get(FLAG,'0')
    if flag in('','0'):
        need(c['m'].get('own_fa_cache_advisory')is None,'declared cache advisory needs explicit enable')
        return
    C,m=c['C'],c['m']
    need(flag=='1' and m.get('own_fa_cache_advisory')==CONTRACT,
         'exact qualification-only source opt-in')
    p=m.get('fastpath_numeric_qualification')
    need(type(p)is dict and p.get('enabled')is True and p.get('formal_performance')is False and
         p.get('independent_reference')is True and p.get('input_tokens')==32768 and
         p.get('output_tokens')in(8,160) and
         m.get('performance_profile',{}).get('formal_performance')is not True,'formal prohibited')
    import worker_resource_v2 as R
    import fa_block_store as B
    need(C.ref(__file__)==m['files']['fa_cache_advisory.py'] and
         C.ref(B.__file__)==m['files']['fa_block_store.py'],'actual helper/archive source')
    ident=R.identity(c) # original exact OWNED/CID/cgroup/source/rank proof, no new authority
    need(ident['source']==c['source'] and ident['rank']==c['rank'] and
         c['source']==C.ref(Path(m['root'])/'SOURCE_BOUND.json'),'actual source identity')
    expected=Path(m['model_receipt_root'])/('FASTPATH-NUMERIC-R%d'%c['rank'])/'FA-BLOCKS'
    need(root==expected and root==Path(c['root'])/'FA-BLOCKS' and
         root.is_dir() and not any(p.is_symlink()for p in(root,*root.parents)),
         'only exact current source/rank owned FA root')
    st=root.stat()
    need(stat.S_ISDIR(st.st_mode) and st.st_uid==os.geteuid(),'own ordinary FA root')
    need(hasattr(os,'posix_fadvise') and hasattr(os,'POSIX_FADV_DONTNEED'),
         'native bounded advisory required, unsupported refuses')
    need(_AUTH is None,'one source-owned archive context per worker')
    _AUTH=dict(c=c,source=dict(c['source']),root=root,dev=st.st_dev,ino=st.st_ino,
               pid=ident['pid'],cid=ident['cid'],membership=ident['cgroup_membership'],rank=c['rank'])

def selected(root,path):
    if os.environ.get(FLAG,'0')in('','0'):return False
    need(os.environ.get(FLAG)=='1' and _AUTH is not None,'configured cache advisory required')
    import fastpath_numeric_sink as S
    a=_AUTH;c=a['c']
    need(S._CONTEXT is c and c['source']==a['source'] and c['rank']==a['rank'] and
         os.getpid()==a['pid'] and root==a['root'],'actual source/CID/rank context, no UID-only authorization')
    members=[l.split(':',2)[2]for l in Path('/proc/self/cgroup').read_text().splitlines()
             if len(l.split(':',2))==3 and 'memory'in l.split(':',2)[1].split(',')]
    need(members==[a['membership']] and Path(members[0]).name==a['cid'],'same actual CID membership')
    st=root.stat()
    need(not any(p.is_symlink()for p in(root,*root.parents)) and
         (st.st_dev,st.st_ino)==(a['dev'],a['ino']) and path.parent==root,
         'same exact owned root inode')
    # Metadata paths are read normally, never advised. All other owned archive names reject.
    if re.fullmatch(r'T-[0-9a-f]{64}\.json',path.name):return False
    need(re.fullmatch(r'B-[0-9a-f]{64}\.bin',path.name)is not None,
         'only immutable full-hash FA blob advisory')
    return True

def verified_read(path,ref,root,cap,digest):
    # Caller has already performed original strict Ref/ordinary/size checks.
    need(selected(root,path),'same current source/CID/rank blob before descriptor open')
    directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    fd=None
    try:
        ds=os.fstat(directory);a=_AUTH
        need((ds.st_dev,ds.st_ino)==(a['dev'],a['ino']),'same authorized directory descriptor')
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory)
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and
             before.st_uid==os.geteuid() and before.st_size==ref['bytes']<=cap<=65536,
             'single-link own regular bounded immutable blob')
        parts=bytearray()
        while len(parts)<=ref['bytes']:
            chunk=os.read(fd,ref['bytes']+1-len(parts))
            if not chunk:break
            need(len(chunk)<=ref['bytes']+1-len(parts),'bounded actual descriptor read')
            parts.extend(chunk)
        data=bytes(parts);del parts
        after=os.fstat(fd)
        stable=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        need(stable(before)==stable(after) and len(data)==ref['bytes'] and
             digest(data)==ref['sha256'] and path.name=='B-'+ref['sha256']+'.bin',
             'same descriptor full bytes/hash and content-address name before advice')
        named=os.stat(path.name,dir_fd=directory,follow_symlinks=False)
        need(stable(named)==stable(before),'same named inode before advisory')
        os.fsync(fd) # never advise dirty/partially verified file; syscall failure is fatal
        result=os.posix_fadvise(fd,0,ref['bytes'],os.POSIX_FADV_DONTNEED)
        need(result is None,'native advisory success required; no false/errno acceptance')
        final=os.fstat(fd);named=os.stat(path.name,dir_fd=directory,follow_symlinks=False)
        need(stable(final)==stable(before) and stable(named)==stable(before),
             'same immutable descriptor/path after advisory')
        return data
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)

STAT_KEYS=('cache','rss','rss_huge','mapped_file','dirty','writeback',
           'total_cache','total_rss','total_rss_huge','total_mapped_file',
           'total_dirty','total_writeback','hierarchical_memory_limit')
def memory_stat(cgroup):
    p=Path(cgroup)/'memory.stat'
    with p.open('r')as f:text=f.read(65537)
    need(len(text.encode())<=65536,'bounded actual memory.stat')
    values={}
    for line in text.splitlines():
        parts=line.split()
        if parts and parts[0]in STAT_KEYS:
            need(len(parts)==2 and parts[0]not in values,'unique typed selected memory.stat')
            value=int(parts[1]);need(value>=0,'nonnegative actual memory stat');values[parts[0]]=value
    need('cache'in values and 'rss'in values,'actual cache/rss categories required')
    return values

def sample_memory_stat(cgroup):
    try:return dict(available=True,values=memory_stat(cgroup))
    except Exception as error:return dict(available=False,error_type=type(error).__name__)

def preflight(C,m,sr):
    """Same-image Devices[] import/bootstrap contract only, never a reclaim permission."""
    import fa_block_store as B
    import worker_resource_v2 as R
    import server090 as S
    import bole_performance_profile as PERF
    need(_AUTH is None and os.environ.get(FLAG,'0')in('','0'),'CPU import default OFF')
    for n,mod in [('fa_cache_advisory.py',__import__(__name__)),
                  ('fa_block_store.py',B),('worker_resource_v2.py',R),('server090.py',S)]:
        need(C.ref(mod.__file__)==m['files'][n],'actual loaded source '+n)
    need(m.get('own_fa_cache_advisory')==CONTRACT and
         R.LIMIT==48*2**30 and R.PER_RANK==8455716864,'unchanged original RAM limits')
    p=m['fastpath_numeric_qualification']
    need(p['enabled']is True and p['independent_reference']is True and
         p['formal_performance']is False and p['input_tokens']==32768 and
         p['output_tokens']in(8,160),'actual original qualification profile')
    resolved=S.environment({PERF.FLAG:'1'},sr,Path(m['model_receipt_root']))
    need(resolved.get(FLAG)=='1' and m['performance_arm']=='bole','actual service worker opt-in bootstrap')
    need(hasattr(os,'posix_fadvise') and hasattr(os,'POSIX_FADV_DONTNEED'),'image API available')
    return dict(schema='bole.own-fa-cache-cpu-contract/v1',source=sr,Devices=[],
                import_defaultOFF=True,worker_bootstrap_verified=True,reclaim_executed=False,
                cgroup_identity_verified=False,filecache_cause_proven=False,numerical_qualified=False)

def validate_memory_stat(value):
    need(type(value)is dict and type(value.get('available'))is bool,'explicit memory-stat status')
    if value['available']:
        need(set(value)=={'available','values'} and type(value['values'])is dict and
             {'cache','rss'}<=set(value['values'])<=set(STAT_KEYS) and
             all(type(x)is int and x>=0 for x in value['values'].values()),
             'bounded selected nonnegative kernel memory-stat fields')
    else:
        need(set(value)=={'available','error_type'} and type(value['error_type'])is str and
             value['error_type'].isidentifier() and len(value['error_type'])<=128,
             'unavailable is diagnostic only, never fabricated cache values')
    return value
