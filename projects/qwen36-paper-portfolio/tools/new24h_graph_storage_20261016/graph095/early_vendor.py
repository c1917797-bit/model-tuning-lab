"""Installed-source-derived OPP path before ANY Python Torch/RT initialization."""
import hashlib,json,os,sys
from pathlib import Path
BASE=Path('/vllm-workspace/vllm-ascend/vllm_ascend')
VENDOR=BASE/'_cann_ops_custom/vendors/custom_transformer'
UTILS=dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/utils.py',bytes=67646,sha256='575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02')
def need(v,s):
 if not v:raise ValueError(s)
def environment(value):
 value=dict(value);parts=[x for x in value.get('ASCEND_CUSTOM_OPP_PATH','').split(':')if x]
 # Same prepend-if-absent semantics as actual pinned utils._prepend_env_path.
 if str(VENDOR)not in parts:parts.insert(0,str(VENDOR))
 value['ASCEND_CUSTOM_OPP_PATH']=':'.join(parts);return value
def checked(r):
 p=Path(r['path']);b=p.read_bytes();need(not p.is_symlink()and(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual installed vendor source/config full pin');return b
def before_device():
 need(not any(n=='torch'or n.startswith(('torch.','torch_npu','vllm'))for n in sys.modules),'early check before backend/platform Python imports')
 proof=json.loads((Path(__file__).parent/'ACTUAL_VENDOR_CONFIG_PROOF.json').read_bytes());checked(UTILS)
 maps=Path('/proc/self/maps').read_text();need(not any(x in maps for x in('libascendcl','libtorch_npu','libge_runner')),'before CANN/torch runtime shared libraries')
 need(str(VENDOR)in os.environ.get('ASCEND_CUSTOM_OPP_PATH','').split(':'),'host container env precedes child Python/RT startup')
 rows=[];b=checked(proof['binary_info']);target=json.loads(b)['ChunkGatedDeltaRuleFwdH'];need(target==proof['target'],'actual target binary config list unchanged')
 kernel=VENDOR/'op_impl/ai_core/tbe/kernel'
 for row,expected in zip(target['binaryList'],proof['kernel_jsons']):
  need(expected['path']==str(kernel/row['jsonPath']),'exact actual config path, no invented SoC')
  b=checked({k:expected[k]for k in('path','bytes','sha256')});cfg=json.loads(b)
  binary=kernel/row['binPath'];need(binary.is_file()and not binary.is_symlink()and binary.stat().st_size>0,'actual referenced kernel binary present (not executed or hash proven)')
  rows.append(dict(config={k:expected[k]for k in('path','bytes','sha256')},binary_path=str(binary),binary_bytes=binary.stat().st_size,binary_content_hash_not_read=True,mode=cfg['supportInfo']['opMode']))
 need(len(rows)==8,'all actual target configs; source proof not successful dispatch')
 return dict(schema='ge.early-vendor-before-device/v064',utils=UTILS,vendor=str(VENDOR),actual_env=os.environ['ASCEND_CUSTOM_OPP_PATH'],before_backend_import=True,maps_before=maps,package_configs=rows,root_cause_proven=False,NPU_dispatch_pass=False)
def after_enable(u):
 need(Path(u.__file__).resolve()==BASE/'utils.py','actual utils module path');checked(UTILS)
 need(str(VENDOR)in os.environ.get('ASCEND_CUSTOM_OPP_PATH','').split(':'),'actual bootstrap kept vendor env')
 maps=Path('/proc/self/maps').read_text();wanted=[x for x in maps.splitlines()if any(y in x for y in('vllm_ascend_C','libcust_opapi','libascendcl','libtorch_npu'))]
 return dict(schema='ge.actual-native-vendor-after-enable/v064',utils=UTILS,actual_env=os.environ['ASCEND_CUSTOM_OPP_PATH'],mapped_native_lines=wanted,actual_enable_custom_op_returned_true=True,kernel_dispatch_proven=False)
