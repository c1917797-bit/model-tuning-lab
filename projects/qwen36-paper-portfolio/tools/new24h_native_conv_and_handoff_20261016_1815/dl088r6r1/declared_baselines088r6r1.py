"""Exact declared fixture reads; Windows fallback is local software-only."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def fingerprint(p):
 b=Path(p).read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def manifest():return json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
def checked_fixture(key,local):
 r=manifest()['files'][key];q=Path(r['path'])if sys.platform=='linux'else local
 if not q.is_file()or any(x.is_symlink()for x in(q,*q.parents))or fingerprint(q)!={k:r[k]for k in('bytes','sha256')}:raise ValueError('declared exact fixture bytes/hash required: '+key)
 return q
def historical_R1():
 p=checked_fixture('HISTORICAL_R1_FINGERPRINTS.json',P/'HISTORICAL_R1_FINGERPRINTS.json');v=json.loads(p.read_bytes())
 if v['schema']!='deltalog.historical-not-deployed-R1-content-fingerprints/v088-repair6-repair1'or v['actual_R1_remote_directory_exists']is not False or v['current_file_dependency']is not False:raise ValueError('historical R1 fingerprint schema; never fake deployment')
 return v
def actual_R2_template():
 p=checked_fixture('baseline_R2/SOURCE_TEMPLATE.json',P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair2'/'SOURCE_TEMPLATE.json');v=json.loads(p.read_bytes())
 if v['root']!='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair2':raise ValueError('actual canonical v1 R2 root')
 return v
def actual_R5_file(name):return checked_fixture('baseline_R5/'+name,P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair5'/name)
