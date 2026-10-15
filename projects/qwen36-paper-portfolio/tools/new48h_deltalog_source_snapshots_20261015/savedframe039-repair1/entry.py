"""Owned Devices[] only; selected saved frame, no NPU or changed gate."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def main():
 if '--execute'not in sys.argv:print('disabled');return
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=('cpu-preflight',),required=True)
 for n in('source-ref','authority-ref','lifecycle-ref','output'):p.add_argument('--'+n,required=True)
 p.add_argument('--steps',type=int,choices=(16,),default=16);a=p.parse_args();sr,ar=map(json.loads,(a.source_ref,a.authority_ref));m=C.source(sr);C.window(ar)
 C.need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','actual Devices[] CPU environment')
 owner=C.obj(m['original_failed_owner_ref']);prod=C.obj(m['original_producer_ref'])
 C.need(owner['schema']=='deltalog.diagnostic-owned-host/v035'and owner['target_source']==m['original_source_ref']and owner['primary']is not None and owner['stopped_retained']is True and owner['secondary']==[]and owner['steps']==160,'actual failed released original160 remains failed')
 C.need(prod['source']==m['original_source_ref']and prod['primary']is None and prod['steps']==160 and prod['NPU']is True,'actual producer160 source, not qualified owner')
 C.need([r['raw']for r in prod['records']if r['kind']=='mixed'and r['batch']==16 and r['step']==80]==[m['selected_raw_ref']],'fixed first-failure raw from actual producer')
 out=Path(a.output);C.need(out.parent.is_dir()and not out.exists(),'fresh CPU output');out.mkdir()
 import torch
 torch.set_num_threads(1);C.need('torch_npu'not in sys.modules,'no backend autoimport')
 D=C.load(m['files']['diagnose.py'],'_actual039_singleframe');rr=D.run(torch,C,m,out)
 C.write(out/'STAGE_RESULT.json',dict(schema='deltalog035.saved-frame-CPU/v039',source=sr,authority=ar,lifecycle=json.loads(a.lifecycle_ref),diagnostic=rr,pass_gate=True,diagnostic_complete=True,NPU=False,model_ready=False,qualification=False,original_failed160_unchanged=True))
if __name__=='__main__':main()
