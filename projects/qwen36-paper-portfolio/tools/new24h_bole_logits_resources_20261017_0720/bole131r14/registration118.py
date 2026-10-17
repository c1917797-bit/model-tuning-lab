"""Actual pinned lazy registration after device/ARM; no synthetic arch or DSO."""
import importlib,importlib.machinery
from pathlib import Path
UTILS=dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/utils.py',bytes=67646,sha256='575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02')
def actual(torch,C,*,arm_verified):
 C.need(arm_verified is True,'actual MAIN_ARM precedes custom extension registration')
 C.checked(UTILS);utils=importlib.import_module('vllm_ascend.utils');C.need(C.ref(utils.__file__)==UTILS,'actual full utils lazy registration source')
 # This exact installed function calls bootstrap_custom_op_env, imports the
 # real extension+meta_registration and owns its libcust_opapi fallback.
 C.need(utils.enable_custom_op()is True,'actual installed custom-op registration must succeed')
 ext=importlib.import_module('vllm_ascend.vllm_ascend_C');p=Path(ext.__file__)
 C.need(isinstance(ext.__spec__.loader,importlib.machinery.ExtensionFileLoader)and p.parent==Path(UTILS['path']).parent and p.name.startswith('vllm_ascend_C')and p.suffix=='.so','actual native extension, not Python replacement')
 er=C.ref(p);C.checked(er);maps=Path('/proc/self/maps').read_text();rows=[s for s in maps.splitlines()if str(p)in s];C.need(bool(rows),'actual extension mapping')
 opapi=sorted({s.split()[-1]for s in maps.splitlines()if 'libcust_opapi.so'in s and s.split()[-1].startswith('/')})
 deps=[]
 for name in opapi:
  r=C.ref(name);C.checked(r);deps.append(dict(ref=r,maps=[s for s in maps.splitlines()if name in s]))
 return dict(registration_source=UTILS,method='enable_custom_op',registration_returned=True,actual_extension_ref=er,actual_extension_maps=rows,actual_opapi_mappings=deps,opapi_execution_proven=False,loaded_libraries=sorted(map(str,torch.ops.loaded_libraries)))
