import argparse,ast,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-audit',action='store_true');a=p.parse_args()
 if not a.source_audit:print('{"enabled":false,"NPU":false}');return 0
 m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
 for name,r in m['files'].items():
  path=P/name;assert r['path']==m['root']+'/'+name and path.is_file()and not path.is_symlink();b=path.read_bytes();assert(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256'])
  if name.endswith('.py'):ast.parse(b,str(path))
 print(json.dumps(dict(prepared_own_files_checked=len(m['files']),bound_source_checked=False,physical_preparation_alias=str(P)!=m['root'],NPU=False,qualified=False)));return 0
if __name__=='__main__':raise SystemExit(main())
