"""Exact four-role dynamic metadata transport into the existing shared leaf.

The original owned live inspection/namespace guards run before publication.
Saved stopped snapshots may test transport; they grant no current live authority.
"""
import hashlib
import json
import os
from pathlib import Path
import re

ROLES=('consumer_owner_ref','model_owner_ref','consumer_inspect','model_inspect')
NAMES={role:'CHANNEL-METADATA-'+role+'.json'for role in ROLES}
LEDGER='CHANNEL-METADATA-HANDOFF.json'
MAX_COPY_BYTES=8*2**20
LEDGER_CAP=16*1024


def host_stat(path):
    st=Path(path).stat();return dict(device=st.st_dev,inode=st.st_ino,bytes=st.st_size,mtime_ns=st.st_mtime_ns)


def ledger_bytes(C,value):
    data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
    C.need(len(data)<=LEDGER_CAP,'complete metadata provenance ledger within16KiB, never truncate')
    return data


def normalized(C,reference):
    C.need(type(reference)is dict and set(reference)in({'path','sha256'},{'path','bytes','sha256'}),'only original exact Ref2 or Ref3, no path-prefix exemption')
    path=Path(reference['path'])
    C.need(path.is_absolute()and path.is_file()and not any(p.is_symlink()for p in(path,*path.parents)),'ordinary original metadata before normalization')
    actual=C.ref(path)
    C.need(actual['sha256']==reference['sha256']and('bytes'not in reference or actual['bytes']==reference['bytes']),'actual full-byte normalization of original inspected Ref2/3')
    C.checked(actual)
    return actual


def expected_original(C,m,role,reference):
    root=Path(m['output_root'])/('cpu-consumer'if role.startswith('consumer')else'dense')
    path=Path(reference['path'])
    C.need(path.parent==root and(path.name=='OWNED.json'if role.endswith('owner_ref')else re.fullmatch(r'inspect-[0-9]+\.json',path.name)is not None),'one explicit current role/path from the exact source, no arbitrary transported Ref')


def durable_bytes(C,path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    result=C.ref(path)
    C.need(result['bytes']==len(data)and result['sha256']==hashlib.sha256(data).hexdigest(),'complete durable ordinary byteequal metadata copy')
    C.checked(result)
    return result


def source_guard(C,source_ref):
    m=C.obj(source_ref)
    C.need(C.ref(__file__)==m['files']['g2_handoff.py']and m['default_enabled']is False,'source-bound reviewed metadata transport, default OFF')
    return m


class ChannelWriter:
    """Delegate every original check; transport only the one terminal write."""
    def __init__(self,C,source_ref):
        self.C=C;self.source=source_ref;self.m=source_guard(C,source_ref);self.used=False;self.result=None
        pin=self.m['files']['g2_stream_owner.py']
        C.need((pin['bytes'],pin['sha256'])==(5917,'3d7d61e06e2de7e0680f4503530267bbb0cd87402b287d037cf89dd1562db8af'),'whole original v7 bind and exact argv guards unchanged before transport')
        C.checked(pin)
    def __getattr__(self,name):return getattr(self.C,name)
    def write(self,path,value):
        C=self.C
        C.need(not self.used and Path(path)==Path(self.m['stream_channel_contract_path'])and value['schema']=='bole.owned-independent-stream-channel/v2'and value['source']==self.source and value['root']==self.m['stream_channel_root']and'metadata_handoff'not in value,'only original bind single terminal exact-source CHANNEL publication')
        self.used=True;copied,ledger=publish(C,self.source,{role:value[role]for role in ROLES})
        transported=dict(value,**copied,metadata_handoff=ledger)
        verify(C,self.source,transported)
        # Consumer BOOT polls existence. Publish the complete capability only
        # after all four copies and ledger are durable, through the unchanged
        # qualified channel pending/rename/fsync primitive.
        import g2_channel as channel_io
        C.need(C.ref(channel_io.__file__)==self.m['files']['g2_channel.py'],'exact source-owned existing atomic channel writer')
        self.result=channel_io.write(Path(path),transported)
        return self.result
    def complete(self,result):
        self.C.need(self.used and self.result==result,'original bind completed exactly one transported publication')
        channel=self.C.obj(result);proof=verify(self.C,self.source,channel)
        for row in proof['roles'].values():self.C.need(normalized(self.C,row['original_declared_ref'])==row['original_actual_ref']and host_stat(row['original_actual_ref']['path'])==row['original_host_stat'],'actual host originals remain byteexact/same inode after publication')
        return channel['metadata_handoff']


def publish(C,source_ref,originals):
    m=source_guard(C,source_ref);C.need(set(originals)==set(ROLES),'exact four dynamic metadata roles, no omitted owner/inspection')
    root=Path(m['stream_channel_root'])
    C.need(root.is_absolute()and root.is_dir()and not any(p.is_symlink()for p in(root,*root.parents)),'existing source-owned shared leaf; never another output')
    rows={};total=0
    # Validate all four original inputs before creating any copy. A missing input
    # never produces a partial success ledger or a channel capability.
    for role in ROLES:
        declared=originals[role];actual=normalized(C,declared);expected_original(C,m,role,actual)
        total+=actual['bytes'];C.need(total<=MAX_COPY_BYTES,'bounded complete metadata transport, also charged to original64MiB budget')
        rows[role]=dict(original_declared_ref=declared,original_actual_ref=actual,original_host_stat=host_stat(actual['path']))
    for role in ROLES:
        row=rows[role];data=C.checked(row['original_actual_ref']).read_bytes()
        copy=durable_bytes(C,root/NAMES[role],data);C.checked(row['original_actual_ref'])
        C.need((copy['bytes'],copy['sha256'])==(row['original_actual_ref']['bytes'],row['original_actual_ref']['sha256']),'whole original and transported metadata bytes remain equal')
        C.need(host_stat(row['original_actual_ref']['path'])==row['original_host_stat'],'same actual original file identity throughout transport')
        row.update(copy_ref=copy,copy_host_stat=host_stat(copy['path']))
    value=dict(schema='bole.actual-four-role-channel-metadata-handoff/v1',source=source_ref,transport_source=m['files']['g2_handoff.py'],root=str(root),roles=rows,total_copy_bytes=total,all_original_bytes_verified_on_host=True,Ref2_inspect_bytes_normalized=True,original_live_guards_required_before_call=True,metadata_in_original64MiB_charge=True,live_identity_inferred_from_stopped_capture=False,model_ready=False,formal_success=False)
    ledger=durable_bytes(C,root/LEDGER,ledger_bytes(C,value))
    directory=os.open(root,os.O_RDONLY)
    try:os.fsync(directory)
    finally:os.close(directory)
    return {role:rows[role]['copy_ref']for role in ROLES},ledger


def verify(C,source_ref,channel):
    m=source_guard(C,source_ref);ledger_ref=channel['metadata_handoff'];ledger=C.obj(ledger_ref)
    root=Path(m['stream_channel_root'])
    C.need(ledger_ref['path']==str(root/LEDGER)and ledger_ref['bytes']<=LEDGER_CAP and ledger['schema']=='bole.actual-four-role-channel-metadata-handoff/v1'and ledger['source']==source_ref and ledger['transport_source']==m['files']['g2_handoff.py']and ledger['root']==str(root)and set(ledger['roles'])==set(ROLES),'exact source/leaf/roles metadata provenance')
    C.need(ledger['all_original_bytes_verified_on_host']is True and ledger['Ref2_inspect_bytes_normalized']is True and ledger['original_live_guards_required_before_call']is True and ledger['metadata_in_original64MiB_charge']is True and ledger['live_identity_inferred_from_stopped_capture']is False and ledger['model_ready']is False and ledger['formal_success']is False,'transport only, original live authority/numerical/resource gates unchanged')
    total=0
    for role in ROLES:
        row=ledger['roles'][role];original=row['original_actual_ref'];declared=row['original_declared_ref'];copy=row['copy_ref']
        C.need(type(original)is dict and set(original)=={'path','bytes','sha256'}and type(declared)is dict and set(declared)in({'path','sha256'},{'path','bytes','sha256'}),'normalized exact original provenance Ref3, original Ref2 retained')
        expected_original(C,m,role,original)
        C.need(original['path']==declared['path']and original['sha256']==declared['sha256']and('bytes'not in declared or original['bytes']==declared['bytes']),'original declared and full-byte normalized metadata agree')
        C.need(channel[role]==copy and copy['path']==str(root/NAMES[role])and(copy['bytes'],copy['sha256'])==(original['bytes'],original['sha256']),'only exact whole-file four-role copies, no unknown Ref redirection')
        C.checked(copy)
        C.need(set(row['original_host_stat'])==set(row['copy_host_stat'])=={'device','inode','bytes','mtime_ns'}and all(type(x)is int and x>=0 for st in(row['original_host_stat'],row['copy_host_stat'])for x in st.values())and row['original_host_stat']['bytes']==original['bytes']and row['copy_host_stat']==host_stat(copy['path']),'actual whole original size and current exact bound-copy device/inode/mtime')
        total+=copy['bytes']
    C.need(total==ledger['total_copy_bytes']and total<=MAX_COPY_BYTES,'all complete metadata charged, no hidden/truncated files')
    return ledger


def stage_saved_probe(C,source_ref,stage_root):
    """Host-only staging of exact stopped v7 snapshots, never live authority."""
    m=source_guard(C,source_ref);proof=m['g2_metadata_handoff_v8'];old=C.obj(proof['failed_source']);channel=C.obj(proof['failed_channel']);root=Path(stage_root)
    C.need(root.is_dir()and root in[Path(m['output_root'])/'handoff-preflight',Path(m['output_root']+'-CPU')/'handoff-preflight'],'fresh sole-owned CPU test output, no write to failed source/output')
    C.need(channel['source']==proof['failed_source']and channel['root']==old['stream_channel_root'],'actual retained source-bound failed channel')
    rows={};total=0
    for role in ROLES:
        declared=channel[role];original=normalized(C,declared);expected_original(C,old,role,original)
        C.need(original==proof['failed_four_full_refs'][role],'only four exact independently observed actual stopped snapshots')
        copy=durable_bytes(C,root/NAMES[role],C.checked(original).read_bytes());C.checked(original)
        C.need((copy['bytes'],copy['sha256'])==(original['bytes'],original['sha256']),'whole actual stopped snapshot transported without metadata rewrite')
        rows[role]=dict(original_declared_ref=declared,original_actual_ref=original,copy_ref=copy,original_host_stat=host_stat(original['path']),copy_host_stat=host_stat(copy['path']));total+=copy['bytes']
    C.need(total<=MAX_COPY_BYTES,'complete saved transport remains bounded')
    saved=dict(channel,**{role:rows[role]['copy_ref']for role in ROLES})
    channel_ref=durable_bytes(C,root/'COLD-SAVED-CHANNEL.json',(json.dumps(saved,sort_keys=True,allow_nan=False)+'\n').encode())
    ledger=dict(schema='bole.actual-stopped-snapshot-channel-handoff-probe/v1',source=source_ref,transport_source=m['files']['g2_handoff.py'],evidence_source=proof['failed_source'],original_channel=proof['failed_channel'],guest_channel_root_alias=old['stream_channel_root'],actual_probe_root=str(root),roles=rows,channel=channel_ref,total_copy_bytes=total,original_snapshots_are_stopped=True,actual_live_identity_qualified=False,model_ready=False,NPU=False)
    return durable_bytes(C,root/'COLD-SAVED-HANDOFF.json',ledger_bytes(C,ledger))


def verify_saved_probe(C,source_ref,stage_ref,*,guest):
    m=source_guard(C,source_ref);proof=m['g2_metadata_handoff_v8'];v=C.obj(stage_ref);root=Path(v['actual_probe_root']);old=C.obj(proof['failed_source'])
    C.need(stage_ref['bytes']<=LEDGER_CAP and v['schema']=='bole.actual-stopped-snapshot-channel-handoff-probe/v1'and v['source']==source_ref and v['transport_source']==m['files']['g2_handoff.py']and v['evidence_source']==proof['failed_source']and v['original_channel']==proof['failed_channel']and v['guest_channel_root_alias']==old['stream_channel_root']and set(v['roles'])==set(ROLES),'exact reviewed source and stopped-snapshot diagnostic lineage')
    C.need(root in[Path(m['output_root'])/'handoff-preflight',Path(m['output_root']+'-CPU')/'handoff-preflight']and stage_ref['path']==str(root/'COLD-SAVED-HANDOFF.json')and v['channel']['path']==str(root/'COLD-SAVED-CHANNEL.json')and v['original_snapshots_are_stopped']is True and v['actual_live_identity_qualified']is False and v['model_ready']is False and v['NPU']is False,'saved diagnostics never qualify new live identities or a model')
    saved=C.obj(v['channel']);original_channel=C.obj(proof['failed_channel']);total=0
    for role in ROLES:
        row=v['roles'][role];original=row['original_actual_ref'];copy=row['copy_ref']
        C.need(original==proof['failed_four_full_refs'][role]and row['original_declared_ref']==original_channel[role]and copy['path']==str(root/NAMES[role])and(copy['bytes'],copy['sha256'])==(original['bytes'],original['sha256'])and saved[role]==copy,'exact original Ref2/3, normalized bytes and complete copy for each role')
        C.checked(copy);C.need(row['copy_host_stat']==host_stat(copy['path'])and row['original_host_stat']['bytes']==original['bytes'],'actual saved copy binding/inode/complete original size');total+=copy['bytes']
        if guest:C.need(not Path(original['path']).exists(),'cold guest must actually lack every original dynamic metadata file; transport cannot be masked by an accidental mount')
        else:C.need(normalized(C,row['original_declared_ref'])==original and host_stat(original['path'])==row['original_host_stat'],'original host snapshot still unchanged/same inode')
    restored=dict(saved,**{role:original_channel[role]for role in ROLES})
    C.need(restored==original_channel and total==v['total_copy_bytes']and total<=MAX_COPY_BYTES,'only four metadata Ref operands change; complete original saved channel preserved')
    if guest:C.need(Path(v['guest_channel_root_alias']).samefile(root),'actual declared guest alias and current owned test leaf share device/inode')
    return v
