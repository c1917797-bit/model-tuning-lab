"""One source-bound diagonal16 defect correction; no runtime or file writes."""
import hashlib
import importlib.util
from pathlib import Path
BASE={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/R118/mxr-y16-compensated-v1-028/derive.py','bytes':5999,'sha256':'33be9c5ee33dc2cea27c85b965d3a34e9fafc6b7d85bb2aa9cf94a6ed4a28ee6'}
NEWTON=r'''
  // MXR_DIAG16_DEFECT_BEGIN: one correction of observed inverse-trick error.
  // X is the original half diagonal16 inverse. R=I-X-A16*X, Xnew=X+X*R.
  // Only the existing half Cube / FP32 accumulator and scratch L1 are used.
  if constexpr (RefineDiag16 && MatrixSize == 64) {
    TMOV(a_l0_tile[0], I_l1_tile);
    TMOV(b_l0_tile[0], I_l1_tile);
    set_flag(PIPE_MTE1, PIPE_M, event_0);
    wait_flag(PIPE_MTE1, PIPE_M, event_0);
    TMATMUL(c_l0_tile[0], a_l0_tile[0], b_l0_tile[0]);

    set_flag(PIPE_M, PIPE_MTE1, event_0);
    wait_flag(PIPE_M, PIPE_MTE1, event_0);
    TMOV(a_l0_tile[0], I_neg_l1_tile);
    TMOV(b_l0_tile[0], X_l1_tile);
    set_flag(PIPE_MTE1, PIPE_M, event_0);
    wait_flag(PIPE_MTE1, PIPE_M, event_0);
    TMATMUL_ACC(c_l0_tile[0], c_l0_tile[0], a_l0_tile[0], b_l0_tile[0]);

    set_flag(PIPE_M, PIPE_MTE1, event_0);
    wait_flag(PIPE_M, PIPE_MTE1, event_0);
    TMOV(a_l0_tile[0], Zero_l1_tile);
    CopyDiagonalFractalsL1ToL0<InputT, FractalSize, MatrixSize>(
        M_neg_l1_tile, a_l0_tile[0]);
    set_flag(PIPE_MTE1, PIPE_M, event_0);
    wait_flag(PIPE_MTE1, PIPE_M, event_0);
    TMATMUL_ACC(c_l0_tile[0], c_l0_tile[0], a_l0_tile[0], b_l0_tile[0]);
    set_flag(PIPE_M, PIPE_FIX, event_0);
    wait_flag(PIPE_M, PIPE_FIX, event_0);
    TMOV(R_l1_tile, c_l0_tile[0]);
    set_flag(PIPE_FIX, PIPE_MTE1, event_0);
    wait_flag(PIPE_FIX, PIPE_MTE1, event_0);

    TMOV(a_l0_tile[1], X_l1_tile);
    TMOV(b_l0_tile[1], I_l1_tile);
    set_flag(PIPE_MTE1, PIPE_M, event_0);
    wait_flag(PIPE_MTE1, PIPE_M, event_0);
    TMATMUL(c_l0_tile[1], a_l0_tile[1], b_l0_tile[1]);
    set_flag(PIPE_M, PIPE_MTE1, event_0);
    wait_flag(PIPE_M, PIPE_MTE1, event_0);
    TMOV(b_l0_tile[1], R_l1_tile);
    set_flag(PIPE_MTE1, PIPE_M, event_0);
    wait_flag(PIPE_MTE1, PIPE_M, event_0);
    TMATMUL_ACC(c_l0_tile[1], c_l0_tile[1], a_l0_tile[1], b_l0_tile[1]);
    set_flag(PIPE_M, PIPE_FIX, event_0);
    wait_flag(PIPE_M, PIPE_FIX, event_0);
    TMOV(X_l1_tile, c_l0_tile[1]);
    set_flag(PIPE_FIX, PIPE_MTE1, event_0);
    wait_flag(PIPE_FIX, PIPE_MTE1, event_0);
    set_flag(PIPE_M, PIPE_MTE1, event_0);
    wait_flag(PIPE_M, PIPE_MTE1, event_0);
  }
  // MXR_DIAG16_DEFECT_END
'''
def need(v,m):
 if not v:raise ValueError(m)
def base(ref=None):
 ref=BASE if ref is None else ref;p=Path(ref['path']);raw=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and len(raw)==BASE['bytes']and hashlib.sha256(raw).hexdigest()==BASE['sha256'],'whole source-bound028 derivation, not caller math');spec=importlib.util.spec_from_file_location('_mxr034_frozen028_derivation',p);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
def sources(impl,entry,base_ref=None):
 D=base(base_ref);rows,old_edits=D.sources(impl,entry);s=rows['tri_inverse_y16_impl.cpp'].decode();changes=[]
 def change(old,new,count=1):
  nonlocal s
  need(s.count(old)==count,'exact new source seam');s=s.replace(old,new);changes.append((old,new,count))
 change(D.RESIDUAL+'\n','')
 change(D.ADD_LOW,'')
 change('mxr_y16_v1','mxr_diag16_defect_v1',s.count('mxr_y16_v1'))
 change('CompensateY16','RefineDiag16',s.count('CompensateY16'))
 change('Y_lo_l1_tile','R_l1_tile',s.count('Y_lo_l1_tile'))
 marker='  /*\n   * Unrolled recursion part:'
 change(marker,NEWTON+'\n'+marker)
 restored=s
 for old,new,count in reversed(changes):
  if new:need(restored.count(new)==count,'new inverse seam');restored=restored.replace(new,old)
  elif old==D.ADD_LOW:
   m='    TMATMUL_ACC(c_l0_tile[1], c_l0_tile[1], a_l0_tile[1], b_l0_tile[0]);\n';need(restored.count(m)==1,'restore frozenY16 add point');restored=restored.replace(m,m+old)
  else:
   m='    /* Load complementary blocks of X in L0B.';need(restored.count(m)==1,'restore frozenY16 residual point');restored=restored.replace(m,old+m)
 need(restored.encode()==rows['tri_inverse_y16_impl.cpp'],'whole034 inverse equals frozen028 source')
 for old,new,count in reversed(old_edits):
  need(restored.count(new)==count,'original author inverse seam');restored=restored.replace(new,old)
 need(restored.encode()==impl,'whole false-control math/layout inverse original40303 author bytes')
 return {'tri_inverse_y16_impl.cpp':s.encode(),'tri_inverse_y16.cpp':rows['tri_inverse_y16.cpp']},changes
if __name__=='__main__':
 import json
 print(json.dumps(dict(enabled=False,build=False,NPU=False)))
