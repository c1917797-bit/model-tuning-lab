"""Device-level native logical-slot adapter diagnostic, not live vLLM slots."""
import torch,torch_npu,json
from independent_native_slots import install_linear_material
from independent_kv_slots import install_private_kv
from independent_hybrid_material import MaterialIdentity
from independent_c1_reference import SegmentAffine
def main():
    torch.npu.set_device(0)
    identity=MaterialIdentity('config69db4eb7','independent','linear-test',0,'a'*64,12,8)
    incoming=torch.arange(12*128*128,dtype=torch.float32,device='npu').reshape(12,128,128)*1e-5
    affine=SegmentAffine(torch.eye(128,device='npu')[None].expand(12,128,128).clone(),torch.zeros_like(incoming))
    ssm=torch.zeros(2,12,128,128,device='npu')
    conv=torch.zeros(2,3,2560,device='npu',dtype=torch.bfloat16)
    install_linear_material(identity,identity,affine,incoming,torch.ones(3,2560,device='npu',dtype=torch.bfloat16),ssm,conv,1)
    cache=torch.zeros(2,2,128,1,256,device='npu',dtype=torch.bfloat16)
    original_format=int(torch_npu.get_npu_format(cache))
    cache=torch_npu.npu_format_cast(cache,2)
    print(json.dumps({'scope':'synthetic ND adapter target','original_format':original_format,
        'target_format':int(torch_npu.get_npu_format(cache))}),flush=True)
    keys=torch.ones(2,1,256,device='npu',dtype=torch.bfloat16);values=keys*2
    install_private_kv(cache,keys,values,[1,129],{1,129})
    torch.npu.synchronize()
    linear_error=float((ssm[1]-incoming.transpose(-1,-2)).abs().max().cpu())
    assert linear_error<1e-5
    assert float(ssm[0].sum().cpu())==0 and float(conv[0].sum().cpu())==0
    assert float(cache[0].sum().cpu())==512 and float(cache[1].sum().cpu())==1024
    print(json.dumps({'scope':'logical-slot-NPU-adapter only; not live serving cache','linear_layout_max_error':linear_error,
        'linear_neighbor_unchanged':True,'kv_owned_rows_only':True,'conv_neighbor_unchanged':True}),flush=True)
if __name__=='__main__':main()
