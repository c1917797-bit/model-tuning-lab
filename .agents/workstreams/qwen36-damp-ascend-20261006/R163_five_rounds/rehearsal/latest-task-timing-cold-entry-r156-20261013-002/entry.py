"""Source-pinned cold import seam for original timing001. No formula changes."""
import argparse,hashlib,importlib.util,json,math,os,sys
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(r,manifest):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>0,'exact Ref3')
 actual=manifest['local_source_map'][r['path']]if os.name=='nt'else r
 p=Path(actual['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink()and ref(p)==actual and(actual['bytes'],actual['sha256'])==(r['bytes'],r['sha256']),'complete real relocated source bytes')
 return p,p.read_bytes()
def validate_args(argv):
 values={'--source-sha256','--dense-ref-json','--candidate-ref-json','--inputs-ref-json','--overhead-seconds','--safety-factor','--output'}
 flags={'--estimate'};seen=set();i=0
 while i<len(argv):
  name=argv[i];need(name in values|flags and name not in seen,'unknown/duplicate original timing flag');seen.add(name);i+=1
  if name in values:need(i<len(argv)and not argv[i].startswith('--'),'missing original timing flag value');i+=1
 if '--estimate'in seen:need({'--source-sha256','--dense-ref-json','--candidate-ref-json','--inputs-ref-json','--overhead-seconds','--output'}<=seen,'complete actual paired-smoke timing args')
 return argv
def boot(sha):
 r=ref(P/'SOURCE_MANIFEST.json');need(r['sha256']==sha,'new cold-entry source pin');m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());need(m['schema']=='r156.task-timing-cold-seam/v1'and m['default_enabled']is False and m['cutoff']==1792002456,'immutable R156 entry scope')
 for n,row in m['files'].items():need(ref(P/n)['bytes']==row['bytes']and ref(P/n)['sha256']==row['sha256'],'new leaf drift')
 donor,_=read(m['task_source_ref'],m);dm=json.loads(donor.read_bytes())
 for name,row in dm['files'].items():
  need(type(row)is dict and set(row)=={'bytes','sha256'},'actual donor ownfile size/SHA schema')
  read(dict(path=str(PurePosixPath(m['task_source_ref']['path']).parent/name),**row),m)
 path,raw=read(m['original_timing_ref'],m);need(not {'core','consume','client'}.intersection(sys.modules),'foreign preloaded task modules rejected')
 # Actual source directory and real unchanged modules, not fake __file__/stub.
 sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location('_actual_original_task_timing',path);T=importlib.util.module_from_spec(spec);sys.modules[spec.name]=T
 try:exec(compile(raw,str(path),'exec',dont_inherit=True),T.__dict__)
 except BaseException:sys.modules.pop(spec.name,None);raise
 for name in('core','consume','client'):
  value=sys.modules[name];expected=dict(path=str(PurePosixPath(m['task_source_ref']['path']).parent/(name+'.py')),**dm['files'][name+'.py']);p,_=read(expected,m);need(ref(value.__file__)==ref(p),'actual imported module provenance: '+name)
 need(T.C.CUT==m['cutoff']and T.C.START==m['start_epoch'],'original R156 clock untouched')
 return T,m
def main(argv=None):
 argv=list(sys.argv[1:]if argv is None else argv)
 if not argv:print(json.dumps(dict(enabled=False,actual_ETA='unmeasured')));return 0
 for flag in('--entry-source-sha256','--cold-source-only'):need(argv.count(flag)<=1,'duplicate new entry flag')
 parser=argparse.ArgumentParser();parser.add_argument('--entry-source-sha256',required=True);parser.add_argument('--cold-source-only',action='store_true');a,rest=parser.parse_known_args(argv);validate_args(rest)
 need(not a.cold_source_only or not rest,'cold source is not an estimate')
 if not a.cold_source_only:need(os.name=='posix','actual ETA requires Linux original window/reports; no CPU fixture promotion')
 T,m=boot(a.entry_source_sha256)
 if a.cold_source_only:
  T.C.source(m['task_source_ref']['sha256']);need(not {'torch','torch_npu','triton'}.intersection(sys.modules),'cold source no backend');print(json.dumps(dict(status='ACTUAL_ORIGINAL_TIMING_COLD_LOADED',source=m['original_timing_ref'],task_source=m['task_source_ref'],NPU=False,actual_ETA='unmeasured',full_start_admitted=False)));return 0
 need(rest and rest[rest.index('--source-sha256')+1]==m['task_source_ref']['sha256'],'original task source SHA, not wrapper SHA')
 old=sys.argv;sys.argv=[m['original_timing_ref']['path'],*rest]
 try:T.main()
 finally:sys.argv=old
 return 0
if __name__=='__main__':raise SystemExit(main())
