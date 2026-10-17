"""131/C1 diagnostic command; genuine114/025 ownership stays in its donor."""
import hashlib,importlib.util,json,sys,time
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent
START=1792134133;CUT=1792220533
OUTPUT_POSIX='/opt/host/vnf/austinov/run-bole-model131repair9-MAIN-NEW24H_001'
CPU_OUTPUT_POSIX='/opt/host/vnf/austinov/run-bole-model131repair9-CPU-MAIN-NEW24H_001'
OUT=Path(OUTPUT_POSIX);CPU_OUT=Path(CPU_OUTPUT_POSIX)
from sourceio import need,ref,checked,obj,write


def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m


def output_argument(raw):
 need(type(raw)is str and '\\'not in raw and PurePosixPath(raw).is_absolute()and raw in(OUTPUT_POSIX,CPU_OUTPUT_POSIX),'exact unique Linux owned output')
 return Path(raw)


def source(sr,clock=True):
 import bind_model
 m=obj(sr);need(m['root']==str(P)and m['prepared_only']is False and m['default_enabled']is False,
  'actual bound defaultOFF model source')
 bind_model.readset(sr)
 for r in m['dependencies']:checked(r)
 need(m['native_speculative_config']==dict(method='mtp',num_speculative_tokens=8)and
  m['profile']==dict(input_tokens=131,tree_nodes=3,HTTP_output_tokens=10,retirement_barrier_output_tokens=1,concurrency=1,
  max_model_len=4096,max_num_batched_tokens=4096,max_num_seqs=1,prefix_cache=False,async_scheduling=False,enforce_eager=True,mamba_cache_mode='none'), 'one preregistered C1 diagnostic command, no workload promotion')
 if clock:need(START<=time.time()and time.time()+3600<CUT,'whole3600 must fit unchanged actual window')
 return m


def server_command():
 from cap48_provider import explicit_lazy_argv
 r=P/'dependencies/original005_server_entry.py';need(ref(r)['sha256']=='ac0931cb9f17a93ae923c7cbfd1a92e757d376a417c1ed910b134f984216d080','exact actual005 command source')
 args=load(ref(r),'_131_actual005_command').original_command(8230)
 args.remove('--async-scheduling')
 for key,value in(('--max-model-len','4096'),('--max-num-batched-tokens','4096'),('--max-num-seqs','1')):args[args.index(key)+1]=value
 args+=['--no-async-scheduling','--mamba-cache-mode','none','--speculative-config','{"method":"mtp","num_speculative_tokens":8}']
 need('--enforce-eager'in args and '--no-enable-prefix-caching'in args,'same frozen native eager/prefixOFF protocol')
 return explicit_lazy_argv(args)
