"""Run frozen030 auditor with exact container-source to actual host-Ref mapping."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def configure(D,m):
 host=m['native_chunk_host_ref'];image=m['native_chunk_container_path'];C.checked(host)
 C.need(host['sha256']=='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'and host['bytes']==16312,'actual native chunk host identity')
 original=D.checked
 def mapped(r):
  if r.get('path')==image:
   C.need(r==dict(host,path=image),'actual runtime source exact byte/hash join, no path alias guessing')
   return C.checked(host)
  return original(r)
 D.checked=mapped
 return dict(host=host,container_path=image,source_only=True,native_DSO_qualification=False)
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('source-ref','producer-ref','strict-consumer-ref','output'):p.add_argument('--'+n,required=True)
 a=p.parse_args();sr,pr,cr=map(json.loads,(a.source_ref,a.producer_ref,a.strict_consumer_ref));m=C.source(sr)
 D=C.load(m['files']['domain_consumer.py'],'_031_frozen030_domain');configure(D,m)
 D.run(sr,pr,cr,a.output);return 0
if __name__=='__main__':raise SystemExit(main())
