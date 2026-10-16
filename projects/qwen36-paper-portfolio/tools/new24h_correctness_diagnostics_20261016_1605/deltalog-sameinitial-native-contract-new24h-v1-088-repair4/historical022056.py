"""Exact old022 receipt as archive evidence, never new-library or hardware authority."""
import ast,hashlib,importlib.util,json
from pathlib import Path
OLD_API_SHA='bed0ba7fd4b74455c3e28ffdb074195ce43823932043c8f02da805c03f508fc7'
OLD_AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json',bytes=3591,sha256='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99')
OLD=" need(m['window']==dict(start=1791962297,cutoff=1792135097)and 1791962297<=time.time()<1792135097,'same immutable runtime window')"
NEW=' historical_window(m,read)'
def historical_window(m,read):
 if m['window']!=dict(start=1791962297,cutoff=1792135097)or m['authority_ref']!=OLD_AUTH:raise ValueError('exact old022 window/oldauthority archive identity')
 a=read(OLD_AUTH)
 if a['start_epoch']!=1791962297 or a['cutoff_epoch']!=1792135097:raise ValueError('actual old authority content, not a moved deadline')
 return True
def derive(raw,globals_):
 if len(raw)!=21204 or hashlib.sha256(raw).hexdigest()!=OLD_API_SHA:raise ValueError('exact reviewed immutable022 API source')
 text=raw.decode();tree=ast.parse(text);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='admit_receipt');body=''.join(text.splitlines(True)[fn.lineno-1:fn.end_lineno])
 if body.count(OLD)!=1:raise ValueError('one original expired current-clock predicate')
 changed=body.replace(OLD,NEW)
 if changed.replace(NEW,OLD)!=body:raise ValueError('whole original receipt function inverse')
 ns=dict(globals_,historical_window=historical_window)
 exec(compile(changed,str(Path(__file__).resolve())+'::source-derived-old022-receipt','exec'),ns)
 return ns['admit_receipt']
def admit(api_ref,source_ref,owner_ref):
 p=Path(api_ref['path']);raw=p.read_bytes()
 if set(api_ref)!={'path','bytes','sha256'}or api_ref['bytes']!=21204 or api_ref['sha256']!=OLD_API_SHA or p.is_symlink():raise ValueError('exact old022 API Ref')
 s=importlib.util.spec_from_file_location('_056_historical_original022',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 result=derive(raw,vars(v))(source_ref,owner_ref)
 return dict(result,historical_022_only=True,new_library_numeric_qualified=False,current_hardware_authority=False)
