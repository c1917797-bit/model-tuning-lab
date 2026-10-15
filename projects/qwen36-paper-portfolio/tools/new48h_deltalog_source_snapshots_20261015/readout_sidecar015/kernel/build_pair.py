"""Single Devices[] fresh-source baseline/KDMA build; owner wraps this child."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def write(p,v):
    with Path(p).open('x')as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    import sys
    if '--execute' not in sys.argv: print('disabled'); return 0
    p=argparse.ArgumentParser(allow_abbrev=False)
    for key in ('source-manifest','source-manifest-sha256','authority','authority-sha256','cmake','cmake-sha256','output'):p.add_argument('--'+key,required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--include-combination',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
    if sha(a.source_manifest)!=a.source_manifest_sha256 or sha(a.authority)!=a.authority_sha256 or a.authority_sha256!='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99':raise ValueError('source/actual fixed authority')
    authority=json.loads(Path(a.authority).read_bytes())
    if authority['start_epoch']!=1791962297 or authority['cutoff_epoch']!=1792135097 or not 1791962297<=time.time()<1792135097:raise ValueError('fixed current clock')
    if list(Path('/dev').glob('davinci*'))or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0':raise ValueError('Devices[] CPU build only')
    if not Path(a.cmake).is_absolute()or sha(a.cmake)!=a.cmake_sha256:raise ValueError('actual CMake binary Ref')
    source=json.loads(Path(a.source_manifest).read_bytes())
    if source['schema']!='deltalog-readout-sidecar-source/v015':raise ValueError('source manifest schema')
    def validate():
        for item in source['files']:
            file=root/item['path']
            if '..'in Path(item['path']).parts or file.stat().st_size!=item['bytes']or sha(file)!=item['sha256']:raise ValueError('source closure drift')
    validate();out=Path(a.output)
    if not out.is_absolute()or out.exists()or not out.parent.is_dir():raise ValueError('new owned build root')
    out.mkdir();start=time.monotonic();commands=[];artifacts=[];primary=None
    def command(argv,name,limit):
        left=min(810-(time.monotonic()-start),1792135097-time.time()-90)
        if left<=0:raise ValueError('build phase fixed cutoff/90s cleanup reserve')
        stdout=out/(name+'.stdout');stderr=out/(name+'.stderr');code=None;error=None
        try:
            with stdout.open('x')as so,stderr.open('x')as se:code=subprocess.run(argv,stdout=so,stderr=se,timeout=min(limit,left)).returncode
        except BaseException as exc:error=repr(exc)
        record=dict(argv=argv,exit_code=code,error=error,stdout=ref(stdout)if stdout.exists()else None,stderr=ref(stderr)if stderr.exists()else None)
        write(out/(name+'.json'),record);commands.append(record)
        if error or code!=0:raise RuntimeError('actual build failed '+name)
    try:
        command([a.cmake,'--version'],'cmake-version',30)
        for arm in ('readout_sidecar_v015',):
            build=out/(arm+'-build');build.mkdir()
            command([a.cmake,'-S',str(root/arm),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release',
                '-DASCEND_CANN_PACKAGE_PATH=/usr/local/Ascend/cann-9.1.0','-DASCEND_COMPUTE_UNIT=ascend910b',
                '-DENABLE_COPY_KERNEL_SRC_TO_ASCENDC=FALSE','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                '-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3'],arm+'-configure',120)
            command([a.cmake,'--build',str(build),'--parallel','1','--verbose'],arm+'-build',600)
            library=build/('libqwen36_gdn_deltalog_decode_'+arm+'_ops.so')
            artifacts.append(dict(arm=arm,library=ref(library),cache=ref(build/'CMakeCache.txt'),compile_commands=ref(build/'compile_commands.json')if(build/'compile_commands.json').exists()else None))
            validate()
    except BaseException as exc:primary=repr(exc)
    finally:
        write(out/'RESULT.json',dict(schema='deltalog-readout-sidecar-actual-build/v015',source_manifest=ref(a.source_manifest),authority=ref(a.authority),
            commands=commands,artifacts=artifacts,primary=primary,elapsed_seconds=time.monotonic()-start,
            Devices=[],NPU=False,numeric_qualified=False,model_ready=False,original_a369_source_identity_verified=False))
    return 3 if primary else 0
if __name__=='__main__':raise SystemExit(main())
