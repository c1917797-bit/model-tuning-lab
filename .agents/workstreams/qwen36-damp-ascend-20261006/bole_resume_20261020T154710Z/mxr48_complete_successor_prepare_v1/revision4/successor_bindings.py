"""Source-specific MAIN authority consumer only. No approval producer or owner."""
import hashlib,json,time
from pathlib import Path
WORK=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PREP=WORK/'mxr48_complete_successor_prepare_v1'/'revision4'
ROOT=PREP/'prepared-source'
START,CUT=1792740953,1792827353
WINDOW=dict(path=str(WORK/'renew24_20261023T073553Z/BACKUP_PREPARATION_WINDOW_V1.json'),bytes=660,sha256='e5e10cdb3487b3fe2152054b23ccbf1b22b9d2c9a5d70b071d79eb75612fb2ba')
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>0,
  'actual complete nonempty Ref3 required; authority is unbound')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary actual Ref3 path')
 h=hashlib.sha256();before=p.stat()
 with p.open('rb')as f:
  while b:=f.read(2**20):h.update(b)
 after=p.stat();need(before.st_size==r['bytes']and h.hexdigest()==r['sha256']and
  (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
  (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'complete stable actual Ref3')
 return p
def obj(r):return json.loads(checked(r).read_text())
def validate_authority(m,template,authority,*,clock):
 a=obj(authority)
 expected=dict(schema='mxr.MAIN-reviewed-context-successor-authority/v1',approved=True,
  preparation_window_ref=WINDOW,prepared_template_ref=template,source_root=str(ROOT),
  outputs=m['outputs'],physical=[6],protected=[0,1,2,3],start_epoch=START,cutoff_epoch=CUT,
  resources=m['resources'])
 need(type(a)is dict and set(a)==set(expected)|{'MAIN_review_ref'}and
  all(type(a[k])is type(v)and a[k]==v for k,v in expected.items()),'exact distinct source-specific MAIN authority, not old/preparation ticket')
 need(template is not None,'actual immutable reviewed template')
 checked(template)
 review=obj(a['MAIN_review_ref'])
 need(review==dict(schema='mxr.MAIN-context-successor-source-review/v1',decision='approve',
  prepared_template_ref=template,source_file_refs=m['files'],parent_source_ref=m['parent_source_ref'],
  context_repair_ref=m['context_repair_ref'],preparation_window_ref=WINDOW,resources=m['resources'],
  math_thresholds_unchanged=True,original97_tests_retained=True),
  'full actual MAIN source review, not caller PASS or generic window')
 w=obj(WINDOW);need(w['preparation_authorized']is True and w['device_execution_requires_distinct_MAIN_source_review']is True
  and(w['start_epoch'],w['cutoff_epoch'])==(START,CUT),'preparation ancestor only')
 if clock:need(START<=time.time()and time.time()+m['phase_seconds']<=CUT,'full original600+cleanup inside current unchanged window')
 return a
def validate_source(sr,m,root,*,clock,allow_unwritten=False):
 need(Path(root)==ROOT and m['root']==str(ROOT)and m['schema']=='mxr.event-single6-source/v1'
  and m['prepared_only']is False and m['default_enabled']is False and
  m['window']==dict(start=START,cutoff=CUT)and
  (m['phase_seconds'],m['child_seconds'],m['cleanup_seconds'])==(600,300,90),'actual bounded current singleton source')
 for n,r in m['files'].items():need(Path(r['path'])==ROOT/n,'whole own source path');checked(r)
 for r in m['preparation_readset']:checked(r)
 own=m['files']['successor_bindings.py'];need(checked(own).read_bytes()==Path(__file__).read_bytes(),'actual current authority consumer source')
 template=m['prepared_template_ref'];tm=obj(template)
 builder=m['files']['prepare_successor.py'];ns=dict(__file__=builder['path'],__name__='_checked_successor_reconstruction')
 exec(compile(checked(builder).read_bytes(),builder['path'],'exec'),ns)
 bundle=ns['render']();ns['inverse'](bundle)
 need(tm==bundle['manifest'],'whole71 source/template reconstruction, not file-only inventory')
 need(m==dict(tm,prepared_only=False,authority_ref=m['authority_ref'],prepared_template_ref=template),
  'only actual MAIN authority and template binding differ from prepared source')
 validate_authority(m,template,m['authority_ref'],clock=clock)
 if not allow_unwritten:
  need(sr is not None and sr['path']==str(ROOT/'SOURCE_MANIFEST.json')and obj(sr)==m,'actual bound manifest Ref')
 return m
