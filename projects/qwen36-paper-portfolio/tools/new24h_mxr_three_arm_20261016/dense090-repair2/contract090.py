"""Dense-only opportunity measurement, never candidate/model qualification."""
import hashlib,importlib.util,json,time
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent
START=1792134133;CUT=1792220533
OUTPUT_POSIX='/opt/host/vnf/austinov/run-dense-e2e090repair2-MAIN-NEW24H_001'
OUT=Path(OUTPUT_POSIX)
DRIVER=dict(path='/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py',bytes=49810,sha256='cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822')
PROFILES=(2048,16384);MEASURED=1;WARMUPS=1
def need(v,m):
 if not v:raise ValueError(m)
def output_argument(raw):
 need(type(raw)is str and '\\'not in raw and PurePosixPath(raw).is_absolute()and raw==OUTPUT_POSIX,'exact registered Linux absolute output, never Windows serialization')
 return Path(raw)
def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and all(not x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'ordinary stable exact Ref3');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 import sys
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def source(sr,clock=True):
 m=obj(sr);need(m['schema']=='dense.e2e-opportunity-source/v090'and m['root']==str(P)and m['default_enabled']is False,'exact090 source/defaultOFF')
 for r in[*m['files'].values(),*m['dependencies']]:checked(r)
 need(m['profiles']==list(PROFILES)and m['measured_requests']==MEASURED and m['warmup_requests']==WARMUPS and m['output_tokens']==1024,'frozen both profiles')
 a=obj(m['authority_ref']);need(a['start_epoch']==START and a['cutoff_epoch']==CUT,'actual fixed24h')
 if clock:need(START<=time.time()and time.time()+3600<CUT,'whole3600 must fit unchanged cutoff')
 return m
def server_command():
 from cap48_provider import explicit_lazy_argv
 r=Path(__file__).parent/'dependencies/original005_server_entry.py';need(ref(r)['sha256']=='ac0931cb9f17a93ae923c7cbfd1a92e757d376a417c1ed910b134f984216d080','exact005 command builder')
 v=load(ref(r),'_090_actual005_command');args=v.original_command(8230);args.remove('--async-scheduling');args[args.index('--max-model-len')+1]='17408';args[args.index('--max-num-batched-tokens')+1]='16384';args[args.index('--max-num-seqs')+1]='1';args+=['--no-async-scheduling','--mamba-cache-mode','none']
 return explicit_lazy_argv(args)
def client_command(tokens,leaf,sr):
 need(tokens in PROFILES,'only frozen2K/16K');return [str(P/'client090.py'),'--execute','--source-ref',json.dumps(sr),'--input-tokens',str(tokens),'--barrier-root',str(leaf/('barriers-'+str(tokens))),'--output',str(leaf/('profile-%d.json'%tokens))]
