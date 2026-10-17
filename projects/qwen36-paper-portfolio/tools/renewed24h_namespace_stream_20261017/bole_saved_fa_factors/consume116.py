import argparse,json,os,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C


def consume(t,sr,outer):
    import pipeline118t as K
    return K.consume(t,C,C.source(sr),sr,outer)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'actual Devices[] consumer')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh consumer output')
    try:
        import torch as t
        t.set_num_threads(1);value=consume(t,sr,C.obj(json.loads(a.stage_ref)));C.write(a.output,value)
    except BaseException as e:C.write(a.output.with_name(a.output.name+'.failure.json'),dict(primary=repr(e),traceback=traceback.format_exc(),source=sr,NPU=False));raise
    return 0 if value['diagnostic_complete']and value['qualified']is False else 3

if __name__=='__main__':raise SystemExit(main())
