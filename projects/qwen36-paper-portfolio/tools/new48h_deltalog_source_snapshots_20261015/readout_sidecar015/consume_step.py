"""CPU raw oracle only. Conditioned actual-before is NOT ideal full-history truth."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
def checked(r):
 p=Path(r['path']);b=p.read_bytes()
 if set(r)!={'path','bytes','sha256'}or len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('exactRef3')
 return p
def module(r,name):
 p=checked(r);s=importlib.util.spec_from_file_location(name,p);M=importlib.util.module_from_spec(s);s.loader.exec_module(M);return M
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
 for k in('raw-ref','oracle-ref','direct-round-ref','output'):p.add_argument('--'+k)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 import torch
 torch.set_num_threads(1);raw=torch.load(checked(json.loads(a.raw_ref)),map_location='cpu',weights_only=True);R=module(json.loads(a.oracle_ref),'_independent013');D=module(json.loads(a.direct_round_ref),'_direct_integer_RNE')
 same=lambda x,y:torch.equal(x.contiguous().view(torch.uint8),y.contiguous().view(torch.uint8))
 output_same=same(raw['outputs']['production'],raw['outputs']['debug']);state_same=all(same(raw['after']['production'][k],raw['after']['debug'][k])for k in raw['before'])
 casts=D.round_bf16(torch,raw['actual_precast_FP32'].double());cast_exact=same(casts,raw['outputs']['debug']);s=raw['sidecar_redzones'];guards=bool((s[:128]==13).all()and(s[-128:]==13).all())
 expected=[]
 for i,slot in enumerate(raw['inputs']['indices'].tolist()):
  _,o=R.advance(torch,R.restore(torch,raw['before'],slot),raw['inputs'],i);expected.append(o)
 expected=torch.stack(expected);error,diag=D.peer_error(torch,raw['outputs']['production'],expected);coords=(raw['outputs']['production'].view(torch.int16)!=D.round_bf16(torch,expected).view(torch.int16)).nonzero().tolist()
 result=dict(schema='deltalog.readout-sidecar-independent/v015',production_debug_output_bitwise=output_same,production_debug_all_state_log_bitwise=state_same,actual_FP32_to_BF16_RNE_exact=cast_exact,sidecar_redzones=guards,conditioned_actual_before_CPU64_peer_error=error,conditioned_diagnostic=diag,mismatch_coordinates=coords,ideal_full_history_truth_available=False,phase='merge'if bool((raw['before']['length'][:,:,0]==7).any())else'append',diagnostic_only=True,qualification=False,original_failures_unchanged=True,NPU=False)
 with Path(a.output).open('x')as f:json.dump(result,f,sort_keys=True);f.write('\n')
 if not(output_same and state_same and cast_exact and guards):raise ValueError('debug transparency or actualcast failed; saved original result')
 return 0
if __name__=='__main__':raise SystemExit(main())
