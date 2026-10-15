"""Own Devices[] build-only guest. Reuse original builder, never dlopen outputs."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
    if not v:raise ValueError(m)
def ref(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
    need(ref(r['path'])==r,'exact Ref3');return Path(r['path']).read_bytes()
def load(r):
    data=checked(r);s=importlib.util.spec_from_file_location('_isolated_kdma_build',r['path']);m=importlib.util.module_from_spec(s);exec(compile(data,r['path'],'exec'),m.__dict__);return m
def safety():
    need(not list(Path('/dev').glob('davinci*')),'Devices[] nodes')
    need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0' and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','CPU env')
    need(not any(n.split('.')[0] in ('torch_npu','vllm','vllm_ascend','triton') for n in sys.modules),'guest backend imports forbidden')
    maps=Path('/proc/self/maps').read_text();need(not any(s in maps for s in ('libascendcl','libtorch_npu','libge_runner')),'guest no NPU runtime')
    for fd in Path('/proc/self/fd').iterdir():
        try:target=os.readlink(fd)
        except FileNotFoundError:continue
        need('/dev/davinci' not in target,'no device FD')
    return dict(forbidden_modules=[],no_device_nodes=True,no_device_fds=True,no_npu_runtime_maps=True)
def main():
    if '--execute'not in sys.argv:print('disabled');return 0
    started=time.monotonic();p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute',action='store_true')
    for k in ('source','source-sha256','expected-cid','remaining-seconds','output'):p.add_argument('--'+k,required=True)
    a=p.parse_args();own=ref(a.source);need(own['sha256']==a.source_sha256,'own source');m=json.loads(checked(own))
    need(m['schema']=='deltalog.owned-kdma-build-source/v1' and m['root']==str(P),'build-only owner schema')
    seconds=int(a.remaining_seconds);need(0<seconds<=810 and time.time()+seconds+90<1792135097,'fixed phase and cleanup clock')
    need(a.expected_cid in Path('/proc/self/cgroup').read_text(),'owned CID')
    out=Path(a.output);need(out.is_absolute() and not out.exists(),'new output');out.mkdir()
    snapshots=[safety()];primary=None;result=None
    try:
        for r in m['files'].values():checked(r)
        for r in m['build_host_refs']:checked(r)
        for r in m['image_refs']:checked(r) # guest-only domain, never host mount
        authority=checked(m['authority']);need(hashlib.sha256(authority).hexdigest()=='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99','authority')
        verifier=load(m['mechanical_verifier']);need(len(verifier.verify(Path(m['build_source_manifest']['path']).parent.parent))==16,'source arithmetic inverse16')
        builder=load(m['build_script_ref']);old=sys.argv
        sys.argv=[m['build_script_ref']['path'],'--execute','--source-manifest',m['build_source_manifest']['path'],'--source-manifest-sha256',m['build_source_manifest']['sha256'],'--authority',m['authority']['path'],'--authority-sha256',m['authority']['sha256'],'--cmake',m['cmake_image_ref']['path'],'--cmake-sha256',m['cmake_image_ref']['sha256'],'--output',str(out/'build')]
        try:need(builder.main()==0,'isolated actual build exit')
        finally:sys.argv=old
        rr=ref(out/'build'/'RESULT.json');v=json.loads(checked(rr))
        need(v['schema']=='deltalog-readout-mac-actual-build/v042' and v['primary'] is None and v['source_manifest']==m['build_source_manifest'] and v['authority']==m['authority'] and v['Devices']==[] and v['NPU'] is False and v['numeric_qualified'] is False and v['model_ready'] is False,'actual build narrow verdict')
        need([x['arm'] for x in v['artifacts']]==['readout_mac042','readout_mac042_debug'] and all(x['exit_code']==0 and x['error'] is None for x in v['commands']),'both isolated artifacts')
        for row in v['artifacts']:
            for key in ('library','cache','compile_commands'):
                if row[key] is not None:checked(row[key])
        snapshots.append(safety());result=dict(build_complete=True,build_result_ref=rr,NPU=False,model_ready=False)
        need(time.monotonic()-started<=seconds,'whole child deadline')
    except BaseException as e:primary=repr(e)
    finally:
        snapshots.append(safety())
        with(out/'RESULT.json').open('x')as f:json.dump(dict(schema='deltalog.owned-kdma-build-child/v1',source=own,actual_cid=a.expected_cid,primary=primary,result=result,safety=snapshots,NPU=False,model_ready=False,elapsed_seconds=time.monotonic()-started),f,sort_keys=True)
    need(primary is None,'build failed; logs retained');return 0
if __name__=='__main__':raise SystemExit(main())
