"""Devices[] actual NumPy vs independent scalar, and current complete writer inputs."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import contract as C
import reference as O
from reader_consume import qualified_numpy
def fixtures(length,bits,kind):
    l=dict(permutation=list(reversed(range(256))),starts=[0,1,64,129,256],smooth=[1.]*256,clip=.95)
    n=8//bits;packed=bytearray();ss=[];zz=[]
    for token in range(length):
        for group,(a,b)in enumerate(zip(l["starts"],l["starts"][1:])):
            codes=[(token+j+group)%((1<<bits))for j in range(b-a)]
            codes += [0]*((-len(codes))%n)
            for offset in range(0,len(codes),n):
                packed.append(sum(codes[offset+j]<<(bits*(n-1-j))for j in range(n)))
            ss.append(.125*(group+1));zz.append(-.25*(group+1))
    dense=O.bytes_a16([((t+c)%17-8)*.0625 for t in range(length)for c in range(256)],kind)
    return bytes(packed),O.bytes_a16(ss,kind),O.bytes_a16(zz,kind),dense,l
def run(expected,whole_ref,output):
    C.need("torch"not in sys.modules and "torch_npu"not in sys.modules and
      not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",n).exists()for n in("devmm_svm","hisi_hdc")),
      "actual no-device reference prerequisite")
    source=C.source(expected);whole=C.writer_whole(whole_ref);items=C.input_rows(whole)
    np,nref=qualified_numpy(whole);checked=[];began=time.monotonic()
    for kind in("float16","bfloat16"):
        for bits in(2,4):
            for length in(5,133,134):
                p,s,z,d,l=fixtures(length,bits,kind)
                scalar=O.decode_axis(p,s,z,d,l,bits,kind,length)
                vector=O.decode_numpy(p,s,z,d,l,bits,kind,length,np)
                C.need(vector.tolist()==scalar,"complete scalar/vector original bytes")
                query=[[((h+c)%7-3)*.015625 for c in range(256)]for h in range(6)]
                want=O.attention(query,scalar,scalar,kind)
                got=O.attention_numpy(query,vector,vector,kind,np)
                C.need(got==want,"every score/probability/all1536 output bitwise scalar/vector")
                checked.append(dict(dtype=kind,bits=bits,length=length,all_outputs_bitwise=True))
    C.need(len(items)==128 and len(checked)==12,"actual complete input/12 independent configurations")
    value=dict(schema="skvq.compiled-reader.cpu/v1",status="ACTUAL_WRITER128_AND_NUMPY12_CHECKED",
      source_ref=source,writer_whole_ref=whole_ref,actual_numpy_ref=nref,actual_cases=128,
      configurations=checked,no_torch=True,Devices_empty=True,elapsed_seconds=time.monotonic()-began,**C.scopes())
    return C.atomic(output,value)
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--writer-whole-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.writer_whole_ref_json and a.output,"actual input descriptor/new CPU sink")
    print(json.dumps(run(a.source_manifest_sha256,json.loads(Path(a.writer_whole_ref_json).read_bytes()),a.output),sort_keys=True))
if __name__=="__main__":main()
