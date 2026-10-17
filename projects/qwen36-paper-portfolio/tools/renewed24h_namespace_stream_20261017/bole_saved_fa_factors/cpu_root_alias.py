"""Exact existing CPU sole-RW namespace binding, never generic string replace."""
from pathlib import Path,PurePosixPath
ALLOWED={'ROOT_PAIR_STAGE.json',*('ROOT-PAIR-RANK-%d.json'%i for i in range(4))}
def resolve(C,ref,*,cpu_owner_ref,owner,final_inspect_ref):
 C.need(type(ref)is dict and set(ref)=={'path','bytes','sha256'},'exact original guest root-repeat Ref3')
 path=PurePosixPath(ref['path']);C.need(path.parent==PurePosixPath('/adakv-results/preflight')and path.name in ALLOWED,
      'exact guest preflight root-repeat filename, no traversal or arbitrary alias')
 inspected=C.obj(final_inspect_ref);parent=Path(cpu_owner_ref['path']).parent
 C.need(inspected['Id']==owner['cid']and inspected['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and inspected['State']['Running']is False and inspected['State']['Pid']==0 and
        inspected['State']['ExitCode']==0 and not inspected.get('ExecIDs')and not inspected['State'].get('OOMKilled')and
        inspected['HostConfig']['ReadonlyRootfs']is True and not inspected['HostConfig'].get('Devices')and not inspected['HostConfig'].get('DeviceRequests'),
        'same exact released Devices[] CPU CID and readonly root')
 rw=[x for x in inspected['Mounts']if x['RW']]
 C.need(len(rw)==1 and rw[0]['Source']==str(parent)and rw[0]['Destination']=='/adakv-results','sole actual owner-local RW binding')
 full=dict(ref,path=str(parent/'preflight'/path.name));C.checked(full);return full
