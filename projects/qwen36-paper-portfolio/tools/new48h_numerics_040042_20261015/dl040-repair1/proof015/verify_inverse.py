"""Mechanically erase sidecar-only additions and recover every B010 source hash."""
import argparse,hashlib,json,re
from pathlib import Path
SIDECAR_BLOCK="        // DEBUG_SIDECAR_V015_BEGIN: read-only actual FP32 before BF16 Cast.\n        event_t sidecarVToMte3 = static_cast<event_t>(pipe_->FetchEventID(HardEvent::V_MTE3));\n        SetFlag<HardEvent::V_MTE3>(sidecarVToMte3);\n        WaitFlag<HardEvent::V_MTE3>(sidecarVToMte3);\n        DataCopy(precastGm_[offset], attnUb_, rows);\n        event_t sidecarMte3ToV = static_cast<event_t>(pipe_->FetchEventID(HardEvent::MTE3_V));\n        SetFlag<HardEvent::MTE3_V>(sidecarMte3ToV);\n        WaitFlag<HardEvent::MTE3_V>(sidecarMte3ToV);\n        // DEBUG_SIDECAR_V015_END\n"
def normalized(name,text):
 text=text.replace('readout_sidecar_v015','key_projection').replace('ReadoutSidecarV015','KeyProjection').replace('READOUT_SIDECAR_V015','KEY_PROJECTION').replace('deltalog-readout-sidecar','deltalog-key-projection').replace('/v015','/v010')
 if name.endswith('key_projection.h'):
  text=text.replace('    GM_ADDR precastFP32;\n','').replace('        precastGm_.SetGlobalBuffer(reinterpret_cast<__gm__ float *>(p.precastFP32));\n','').replace('    GlobalTensor<float> precastGm_;\n','')
  text=re.sub(r'        // DEBUG_SIDECAR_V015_BEGIN:.*?        // DEBUG_SIDECAR_V015_END\n','',text,flags=re.S)
 if name.endswith('_kernel.asc'):text=text.replace('    GM_ADDR precastFP32,\n','').replace('stateIndices, out, precastFP32};','stateIndices, out};')
 if name.endswith('ops.h')or name.endswith('_torch.cpp'):text=text.replace('    const at::Tensor& stateIndices,\n    const at::Tensor& precastFP32)','    const at::Tensor& stateIndices)')
 if name.endswith('_torch.cpp'):
  text=text.replace('    check_npu_contiguous(precastFP32, "precast_fp32");\n','').replace('            (GM_ADDR)precastFP32.mutable_data_ptr(),\n','')
  text=re.sub(r'    // DEBUG_SIDECAR_V015_CHECK_BEGIN.*?    // DEBUG_SIDECAR_V015_CHECK_END\n\n','',text,flags=re.S)
 if name.endswith('register.cpp'):
  text=text.replace('Tensor state_indices, Tensor(g!) precast_fp32) -> Tensor','Tensor state_indices) -> Tensor').replace('    const at::Tensor&,\n    const at::Tensor&)\n{','    const at::Tensor&)\n{')
 return text
def verify(root):
 old=json.loads((root/'B010_ORIGINAL_SOURCE.json').read_bytes());rows=[]
 for r in old['files']:
  new=r['path'].replace('key_projection','readout_sidecar_v015');text=(root/'kernel'/new).read_text(encoding='utf8')
  if r['path'].endswith('key_projection.h')and(text.count(SIDECAR_BLOCK)!=1 or text.count('DEBUG_SIDECAR_V015_BEGIN')!=1):raise ValueError('exact read-only sidecar block required')
  base=normalized(r['path'],text).encode()
  if len(base)!=r['bytes']or hashlib.sha256(base).hexdigest()!=r['sha256']:raise ValueError('arithmetic/source inverse mismatch '+r['path'])
  rows.append(dict(original=r,debug_path=new,recovered=True))
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 print(json.dumps(dict(schema='deltalog.sidecar-mechanical-inverse/v015',rows=verify(Path(__file__).resolve().parent),NPU=False,compiled=False)))
if __name__=='__main__':main()
