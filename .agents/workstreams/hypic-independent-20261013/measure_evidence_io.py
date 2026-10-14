"""Bounded host-only evidence I/O measurement; no runtime policy change."""
import argparse
import json
import os
import statistics
import tempfile
import time
from pathlib import Path

def trial(parent,count,batch):
    payload=(json.dumps({"event":"synthetic-only","rank":0,"step":1,"padding":"x"*280})+"\n").encode()
    with tempfile.TemporaryDirectory(prefix="hypic-evidence-io-",dir=parent) as folder:
        path=Path(folder)/"synthetic.jsonl"
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        start=time.perf_counter_ns()
        try:
            for i in range(count):
                view=memoryview(payload)
                while view:
                    n=os.write(fd,view)
                    if n<=0:raise OSError("short write")
                    view=view[n:]
                if (i+1)%batch==0:os.fsync(fd)
            os.fsync(fd)
        finally:os.close(fd)
        elapsed=(time.perf_counter_ns()-start)/1e6
        if path.stat().st_size!=count*len(payload):raise ValueError("write length mismatch")
        return elapsed

def main():
    p=argparse.ArgumentParser();p.add_argument("--parent",default="/cache/cch");a=p.parse_args()
    parent=Path(a.parent).resolve()
    if str(parent)!="/cache/cch":raise ValueError("fixed scoped temporary parent required")
    result={}
    for batch in (1,64):
        ms=[trial(parent,1000,batch) for _ in range(3)]
        result[str(batch)]={"trials_ms":ms,"median_ms":statistics.median(ms)}
    print(json.dumps({"host_only":True,"synthetic_events_per_trial":1000,
      "fsync_batch_size":result,"scope":"I/O microcost only; no algorithm benchmark, no device work, no permission to weaken durability"}))

if __name__=="__main__":main()

