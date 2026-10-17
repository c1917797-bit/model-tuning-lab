import argparse,importlib.machinery,importlib.util,json,os,subprocess,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C


def bootstrap(m):
    h=C.load(m['cann_helper_ref'],'_116realCANN');root='/usr/local/Ascend/cann-9.1.0/python/site-packages'
    C.need(h.ROOT==root,'actual CANN source path');h.cached()
    h.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
    direct=h.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[root]));sys.path.insert(0,root)
    C.need(h.spec_identity(importlib.util.find_spec('acl'))==direct,'actual ACL extension not fake module');return direct


def collect_conv(m,out):
    collector=m['files']['collect_conv_abi.py'];p=C.checked(collector);target=out/'ACTUAL_CONV_ABI.json'
    r=subprocess.run([sys.executable,'-I','-B',str(p),'--execute','--script-sha256',collector['sha256'],'--output',str(target)],capture_output=True,text=True,timeout=120)
    C.write(out/'CONV_ABI_PROCESS.json',dict(script=collector,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,NPU=False))
    C.need(r.returncode==0,'actual conv ABI collector; original receipt/trace preserved')
    v=C.obj(C.ref(target));C.need(v['primary']is None and v['NPU']is False and v['operator_executed']is False and v['no_device_fds']is True and v['script']==collector,'actual same-source CPU conv ABI, not qualification')
    return C.ref(target)

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'actual Devices[] CPU guard')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh CPU ABI output');a.output.mkdir();actual=None;conv=None;primary=None;controls=None
    C.write(a.output/'PROCESS.json',dict(source=sr,actual_argv=sys.argv,backend_autoload=os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD'),ASCEND=os.environ.get('ASCEND_RT_VISIBLE_DEVICES'),NPU=False))
    try:
        r=subprocess.run([sys.executable,'-I','-B',str(C.checked(m['files']['suite116.py']))],capture_output=True,text=True,timeout=180)
        C.write(a.output/'SOFTWARE_CONTROLS.json',dict(source=sr,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,NPU=False));controls=C.ref(a.output/'SOFTWARE_CONTROLS.json');C.need(r.returncode==0,'whole actual source suite')
        C.write(a.output/'CANN.json',dict(source=m['cann_helper_ref'],actual=bootstrap(m),NPU=False))
        import torch as t,torch_npu
        t.set_num_threads(1)
        import abi116
        abi116.record(t,torch_npu,sr,m['header_ref'],a.output/'ACTUAL_FIA_ABI.json');actual=C.ref(a.output/'ACTUAL_FIA_ABI.json')
        import root_pair_stage
        root_pair=root_pair_stage.run(t,C,m,sr,a.output)
        C.write(a.output/'ROOT_PAIR_STAGE.json',root_pair)
        # Actual0d08 proved normal GDN import queries HAL; keep conv pending.
        conv=None
    except BaseException as e:primary=repr(e);C.write(a.output/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc(),source=sr,NPU=False))
    C.write(a.output/'STAGE_RESULT.json',dict(schema='bole.tree-CPU-stage/vFAfactor',source=sr,authority=m['authority_ref'],actual_abi_ref=actual,actual_conv_abi_ref=conv,conv_abi_pending=True,conv_abi_pending_reason='actual116R3-GDN-import-requires-HAL',root_pair_stage_ref=C.ref(a.output/'ROOT_PAIR_STAGE.json')if(a.output/'ROOT_PAIR_STAGE.json').is_file()else None,software_controls=controls,actual_meta=dict(pass_gate=primary is None,kind='actual-installed-FIA-schema-not-Meta-execution',operator_executed=False,NPU=False),primary=primary,NPU=False,qualified=False));return 0 if primary is None else 3

if __name__=='__main__':raise SystemExit(main())
