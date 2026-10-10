"""Actual same660 NumPy-vs-independent-scalar byte parity before ANY writer NPU."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_byte_oracle as O
def self_test(np):
    rows=[]
    for kind in("float16","bfloat16"):
        for bits in(2,4):
            for starts in([0,64,128,192,256],[0,1,17,111,256],[0,1,2,3,256]):
                layout=dict(permutation=list(reversed(range(256))),starts=starts,smooth=[1.]*256,clip=.95)
                for count in(1,17):
                    values=[O.scalar(((i*17+t*31)%113-56)/19,kind)for t in range(count)for i in range(256)]
                    raw=O.scalar_bytes(values,kind)
                    scalar=O.encode_scalar(raw,layout,bits,kind)
                    vector=O.encode_numpy(raw,layout,bits,kind,np)
                    C.need(scalar==vector,"actual NumPy byte parity vs independent scalar: "+repr((kind,bits,starts,count)))
                    rows.append(dict(dtype=kind,bits=bits,starts=starts,tokens=count,all_payload_SS_ZP_bitwise_equal=True))
    C.need(len(rows)==24,"all24 actual vector/scalar configurations")
    return rows
def run(expected,plan_ref,output):
    source=C.source(expected)
    C.need("torch"not in sys.modules and"torch_npu"not in sys.modules and
      not list(Path("/dev").glob("davinci*"))and
      not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),"Devices[] no framework/NPU")
    from writer_inputs import consume_plan
    plan=consume_plan(plan_ref,source)
    from writer_consume import numpy_module
    np,npref=numpy_module(plan);begin=time.monotonic();rows=self_test(np)
    value=dict(schema="skvq.actual-writer.numpy-preflight/v1",status="ACTUAL_NUMPY_SCALAR_BYTES_BITWISE_CHECKED",
      source_ref=source,input_plan_ref=plan_ref,actual_numpy_ref=npref,configurations=rows,
      actual_configurations=24,elapsed_seconds=time.monotonic()-begin,
      no_torch=True,Devices_empty=True,**C.scopes())
    out=Path(output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),"new single CPU preflight sink")
    return C.publish(out,value)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--input-plan-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    plan=json.loads(Path(a.input_plan_ref_json).read_bytes())
    print(json.dumps(run(a.source_manifest_sha256,plan,a.output),sort_keys=True))
if __name__=="__main__":main()
