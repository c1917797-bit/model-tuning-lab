"""Source identity and reviewed boundary locators, NOT compiled-binary provenance."""
import hashlib
from pathlib import Path
def check(refs):
 rows=[]
 for r in refs:
  b=Path(r['path']).read_bytes()
  if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('native boundary source drift')
  rows.append(r)
 required={'6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5','83a07e6602e81822f8da2f47d4a25fce8beb5ffb5646f402ea6fd3c9d642463e','267d7815021d812421fec3851897ee06dd6680cce4a13f27279ed72ac8b3f63b','8d59d19537be6c998d2fdc7957ffbebd9a35091f2c92ab5a495018ced4c9bcef'}
 if not required <= {r['sha256']for r in rows}:raise ValueError('complete reviewed source boundary closure')
 return dict(schema='mxr.native-working-DAG-source-proof/v042',refs=rows,source_reviewed=True,compiled_DSO_matches_Cpp_source_proven=False,locators={'chunk.py':'solve output_dtype=k.dtype; W/U to BF16; _C_ascend native h/o; PCP1','gdn_fwd_h_kernel.hpp':'105-113 HType INPUT_TYPE/FinalState STATE_TYPE;342 initial CAST_RINT','block_epilogue_gdn_fwdh_vnew.hpp':'216-226 delta FP32 -> BF16 vnew and separately decayed BF16 update','block_epilogue_gdn_fwdh_update.hpp':'146-159 final FP32/intermediate BF16 state'},scope='CPU canonical FP32 operational DAG, not instruction-exact Ascend/CANN-exp theorem; actual native initial witness remains required')
