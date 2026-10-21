"""Pure Docker argv/actual-inspect reader. Never starts/stops a container."""
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C

TMPFS='rw,nosuid,nodev,noexec,size=268435456,mode=1777'
ENV=['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','HOME=/tmp','LANG=C.UTF-8',
     'ASCEND_RT_VISIBLE_DEVICES=','ASCEND_VISIBLE_DEVICES=','TORCH_DEVICE_BACKEND_AUTOLOAD=0',
     'PYTHONDONTWRITEBYTECODE=1','HF_HUB_OFFLINE=1','OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1',
     'MKL_NUM_THREADS=1','NUMEXPR_NUM_THREADS=1']


def path(value):
    p=Path(value);C.need(p.is_absolute()and '..'not in p.parts and ','not in str(p)and ':'not in str(p),
        'explicit public-only stage path');return str(p)


def argv(name,image,source_root,suite_root,input_root,capsule_sha,mode):
    C.need(name.startswith('bole-he-')and len(name)<=80 and all(c in'abcdefghijklmnopqrstuvwxyz0123456789-'for c in name),
           'unique MAIN-owned sandbox name')
    C.need(type(image)is str and image.startswith('sha256:')and len(image)==71
           and all(c in'0123456789abcdef'for c in image[7:]),'actual immutable same-image ID')
    C.need(mode in('preflight','controls','tasks')and len(capsule_sha)==64,'explicit bounded sandbox mode/source')
    return ['/usr/bin/docker','create','--name',name,'--runtime','runc','--network','none','--ipc','private',
        '--read-only','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--memory',str(2*2**30),'--memory-swap',str(2*2**30),'--cpus','1','--pids-limit','64',
        '--ulimit','nofile=128:128','--ulimit','fsize=8388608:8388608','--tmpfs','/tmp:'+TMPFS,
        '--workdir','/tmp','--mount','type=bind,src='+path(source_root)+',dst=/source,readonly',
        '--mount','type=bind,src='+path(suite_root)+',dst=/suite,readonly',
        '--mount','type=bind,src='+path(input_root)+',dst=/inputs,readonly',
        '--entrypoint','/usr/bin/env',image,'-i',*ENV,'python3','-I','-B','/source/he_worker.py',
        '--'+mode,'--capsule-sha256',capsule_sha]


def inspect_actual(value,*,expected_id,expected_image,expected_argv,source_root,suite_root,input_root):
    C.need(type(value)is list and len(value)==1,'one actual exact owned Docker inspect object')
    v=value[0];h=v['HostConfig'];config=v['Config'];state=v['State']
    C.need(v['Id']==expected_id and len(expected_id)==64 and v['Image']==expected_image,
           'exact actual sandbox ID/image, no name-only ownership')
    C.need(v['Path']=='/usr/bin/env'and v['Args']==expected_argv[expected_argv.index(expected_image)+1:]
           and config['User']=='65534:65534'and config['WorkingDir']=='/tmp',
           'actual exact env-i entrypoint/arguments/nonprivileged user')
    C.need(h['Runtime']=='runc'and h['NetworkMode']=='none'and h['IpcMode']=='private'
           and h['PidMode']==''and h['UTSMode']==''and not h['Privileged']and h['ReadonlyRootfs']is True,
           'actual isolated read-only namespaces without accelerator runtime')
    C.need(not h.get('Devices')and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')
           and not h.get('VolumesFrom')and not h.get('Links')and not h.get('PortBindings')
           and not h.get('ExtraHosts')and not h.get('CapAdd')and h['CapDrop']==['ALL']
           and h['SecurityOpt']==['no-new-privileges'],'no device/network/privilege injection')
    C.need(h['Memory']==h['MemorySwap']==2*2**30 and h['NanoCpus']==10**9
           and h['PidsLimit']==64 and h['Tmpfs']=={'/tmp':TMPFS},'actual bounded memory/CPU/PIDs/private scratch')
    limits={r['Name']:(r['Soft'],r['Hard'])for r in h['Ulimits']}
    C.need(limits=={'nofile':(128,128),'fsize':(8388608,8388608)},'actual FD/file-size limits')
    wanted={'/source':path(source_root),'/suite':path(suite_root),'/inputs':path(input_root)}
    mounts=v['Mounts'];C.need(len(mounts)==3,'only three public read-only mounts')
    C.need({r['Destination']:r['Source']for r in mounts}==wanted
           and all(r['Type']=='bind'and r['RW']is False and r.get('Propagation')=='rprivate'for r in mounts),
           'actual exact public-only immutable mounts')
    C.need(state['Running']is False and state['ExitCode']==0 and state['OOMKilled']is False
           and state['Error']==''and state['StartedAt']!=state['FinishedAt'],
           'actual completed sandbox, exit0, no OOM/error')
    return dict(actual_sandbox_identity_and_limits_verified=True,container_id=expected_id,
                image=expected_image,read_only_mounts=wanted,generated_code_scope='external isolated official evaluator')
