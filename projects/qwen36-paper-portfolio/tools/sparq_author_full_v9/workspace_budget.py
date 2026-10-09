"""Exact guarded payload accounting from frozen GraphTokenWorkspace; no Torch import.
Long-context capacity and cumulative all16FA/batch/max_pages state are admitted
BEFORE allocation. These bounds are not proof of installed allocation/kernel support.
"""
import common as c
BLOCK,DIM,HEADS=128,256,6
SCREEN_MAX_LENGTH=c.SCREEN_LENGTH
def guarded_bytes(batch,max_pages,budget=128):
 c.require(type(batch) is int and batch in range(1,17) and type(max_pages) is int and 0<max_pages<=320 and budget==128,
  "actual full model batch/max_pages/budget, never numeric18page assumption")
 capacity=max_pages*BLOCK;scratch_pages=(budget+BLOCK-1)//BLOCK
 shapes=((batch*max_pages,8),(batch,4),(capacity,8),(batch*capacity,8),(capacity,8),(batch,8),
  (batch*scratch_pages,4),(batch,4),((batch*scratch_pages+1)*BLOCK*DIM,2),
  ((batch*scratch_pages+1)*BLOCK*DIM,2),(batch*HEADS*DIM,2),(batch*HEADS*DIM,2))
 return sum((n+128)*size for n,size in shapes)
def transient_ceiling(batch,max_pages):
 # Simultaneously-live physical maps, BF16+FP32 short keys, Q casts/channels,
 # logits/divide/mask/softmax variants, stable argsort/ranking, selected K/V,
 # alpha and conservative implementation workspace. Not projected allocator PASS.
 n=max_pages*BLOCK
 return (batch*n*(8*5+32*(2+4)+HEADS*4*5+8*3)+batch*HEADS*DIM*4*4+
  batch*128*DIM*2*2+batch*128*HEADS*8+256*1024**2)
def admission(existing,batch,pages,actual_current,baseline_current,actual_peak):
 c.require(all(type(v) is int and v>=0 for v in (existing,actual_current,baseline_current,actual_peak)) and
  actual_peak>=actual_current,"actual allocator CPU observation fields, never projected PASS")
 addition=guarded_bytes(batch,pages)
 transient=transient_ceiling(batch,pages)
 c.require(existing+addition+transient<=c.AUX_CEILING,"all capture buckets guarded+new+transient admission before allocation")
 c.require(actual_current-baseline_current<=c.AUX_CEILING and actual_peak-baseline_current<=c.AUX_CEILING,
  "actual all-process allocator peak delta ceiling, conservative common growth included; no memory saving claim")
 return dict(projected_guarded_bytes=existing+addition,transient_ceiling_bytes=transient,
  actual_current_delta_bytes=actual_current-baseline_current,actual_peak_upper_delta_bytes=actual_peak-baseline_current,
  measured_not_numerical_pass=True)
