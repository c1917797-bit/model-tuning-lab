"""Pure reversible consumer owning-layer derivation. Never binds or approves."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent
TRANSPORT=W/'accuracy_smoke_ready_prepare_v1/transport_candidate_v2'
ORIGINAL_SHA='bffd5f6cd195ca2af835cde6f37b011c1afa2c6887947882c086b217d4339708'
OLD_IMPORT='import http_common as C'
NEW_IMPORT='import transport_decoder_bridge as B\nC=B.COMMON_PROXY'
OLD_SCORE="""    tm=C.obj(plan['source_ref']);sys.path.insert(0,tm['root'])
    S=C.load(tm['files']['score_tokens.py'],'_task_http_exact_frozen_component_scorer')
    grades=S.replay(plan['source_ref'],client['raw_ref'],full_provenance=False)"""
NEW_SCORE="    grades=B.decode_grades(plan,client)"
def need(v,s):
 if not v:raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def render(root,*,decoder_source_ref=None,HTTP_source_ref=None):
 root=Path(root);need(root.is_absolute()and '..'not in root.parts,'explicit future ordinary root')
 original=(TRANSPORT/'consume_lifecycle.py').read_bytes()
 need(hashlib.sha256(original).hexdigest()==ORIGINAL_SHA,'exact unchanged original transport consumer')
 text=original.decode()
 for old,new in((OLD_IMPORT,NEW_IMPORT),(OLD_SCORE,NEW_SCORE)):
  need(text.count(old)==1,'exact one actual owning seam');text=text.replace(old,new,1)
 files={'consume_lifecycle_replay.py':text.encode(),**{n:(P/n).read_bytes()for n in('transport_decoder_bridge.py','transport_decoder_entry.py')}}
 for n,b in files.items():compile(b,n,'exec')
 bundle=dict(manifest=dict(schema='bole.transport-current-decoder-source/v1',root=str(root),files={n:ref(root/n,b)for n,b in files.items()},
    original_consumer_ref=ref(TRANSPORT/'consume_lifecycle.py',original),decoder_source_ref=decoder_source_ref,HTTP_source_ref=HTTP_source_ref,
    prepared_only=True,default_enabled=False,source_bound=False,formal_task_accuracy_accepted=False,HTTP=False,NPU=False),
    files=files,original=original,pending=['MAIN exact current CPU binding/host inspect/read-only bridge mount',
      'actual historical generation operation/owner/source provenance','source materialization/review and same-image no-device validation'])
 inverse(bundle);return bundle
def inverse(b):
 t=b['files']['consume_lifecycle_replay.py'].decode()
 for old,new in reversed(((OLD_IMPORT,NEW_IMPORT),(OLD_SCORE,NEW_SCORE))):
  need(t.count(new)==1,'one complete inverse seam');t=t.replace(new,old,1)
 need(t.encode()==b['original'],'whole original consumer exactly restored, no dropped native/worker/owner/math gate')
 return t.encode()
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--review',action='store_true');a=p.parse_args()
 if not a.review:print('{"enabled":false,"HTTP":false,"NPU":false}')
 else:
  b=render(P/'reserved-future-source')
  print(json.dumps(dict(files=len(b['files']),whole_inverse=True,source_bound=False,HTTP=False,NPU=False,pending=b['pending'])))
