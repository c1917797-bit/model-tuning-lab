"""Readout-only inverse plus verbatim015 debug inverse recovers original B010."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sidecar_inverse015 as S
EARLY='        Muls(qUb_, qUb_, scale_, HEAD_DIM);\n        PipeBarrier<PIPE_V>();\n'
SIG='    __aicore__ inline void StoreOutput(uint64_t offset, uint32_t rows)\n    {\n'
SPLIT='        Muls(qUb_, qUb_, scale_ == 0.088388346135616302490234375f ? 0.0625f : scale_, HEAD_DIM);\n        PipeBarrier<PIPE_V>();\n'
LATE='        if (scale_ == 0.088388346135616302490234375f) {\n            PipeBarrier<PIPE_V>();\n            Muls(attnUb_, attnUb_, scale_ * 16.0f, rows);\n            PipeBarrier<PIPE_V>();\n        }\n'
def reverse(text):
 if text.count(SIG+LATE)!=1 or text.count(SPLIT)!=1 or EARLY in text:raise ValueError('exact split output/query seams')
 text=text.replace(SIG+LATE,SIG)
 return text.replace(SPLIT,EARLY)
def verify(root):
 old=json.loads((root/'B010_ORIGINAL_SOURCE.json').read_bytes());rows=[]
 for arm in('split_scale_v051','split_scale_sidecar_v051'):
  for r in old['files']:
   if r['path']=='build_pair.py':continue
   relative=r['path'].replace('key_projection',arm);text=(root/'kernel'/relative).read_text(encoding='utf8')
   if arm=='split_scale_v051':text=text.replace('split_scale_v051','key_projection').replace('SplitScaleV050','KeyProjection').replace('SPLIT_SCALE_V050','KEY_PROJECTION')
   else:text=text.replace('split_scale_sidecar_v051','readout_sidecar_v015').replace('SplitScaleSidecarV050','ReadoutSidecarV015').replace('SPLIT_SCALE_SIDECAR_V050','READOUT_SIDECAR_V015')
   if r['path'].endswith('key_projection.h'):text=reverse(text)
   if arm.endswith('sidecar_v051'):text=S.normalized(r['path'],text)
   b=text.encode()
   if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('original source inverse '+relative)
   rows.append(dict(arm=arm,original=r,recovered=True))
 if len(rows)!=14:raise ValueError('all14 compile sources')
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 print(json.dumps(dict(rows=verify(P),compiled=False,NPU=False)))
if __name__=='__main__':main()
