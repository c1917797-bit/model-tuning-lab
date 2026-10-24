"""Only bounded whole-tree ENOENT retry count/backoff; original tree/resource semantics unchanged."""
def need(v,s):
 if not v:raise ValueError(s)
def adapt(files):
 out=dict(files);before=files['output_scan131r8.py'];text=before.decode()
 for old,new in(
  ('for attempt in range(1,4):','for attempt in range(1,65):'),
  ('if attempt==3 or time.monotonic()>=end:raise','if attempt==64 or time.monotonic()>=end:raise'),
  ('    continue\n   need(root_identity',"""    delay=min(.005,max(0.,end-time.monotonic()))
    if delay:time.sleep(delay)
    continue
   need(root_identity"""),
  ('full_tree_retry_attempts=3,total_seconds=1','full_tree_retry_attempts=64,total_seconds=1')):
  need(text.count(old)==1,'one exact output scan retry seam');text=text.replace(old,new,1)
 out['output_scan131r8.py']=text.encode()
 need(all(out[n]==v for n,v in files.items()if n!='output_scan131r8.py'),'no algorithm/resource threshold/other file mutation')
 return out,dict(before=before,after=out['output_scan131r8.py'])
def inverse(files,delta):
 out=dict(files);need(out['output_scan131r8.py']==delta['after'],'exact output scanner inverse')
 out['output_scan131r8.py']=delta['before'];return out
