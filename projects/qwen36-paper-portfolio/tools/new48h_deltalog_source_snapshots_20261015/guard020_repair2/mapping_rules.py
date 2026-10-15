"""Exact allowlisted physical-resource/identity edits; no mathematical edits."""
RULES={
 'host.py':[("physical5","physical4"),("external4/6/7","external5/6/7"),("MAIN-020'","MAIN-020-physical4'"),("choices=(5,),default=5","choices=(4,),default=4")],
 'producer.py':[("plan['physical']==5","plan['physical']==4"),("physical5","physical4"),("physical=5","physical=4")],
 'scope_adapter.py':[("physical!=5","physical!=4"),("return (5,)","return (4,)"),("physical5","physical4"),("rest[rest.index('--physical-device')+1]!='5'","rest[rest.index('--physical-device')+1]!='4'")],
 'run_stage.py':[("'--physical-device','5'","'--physical-device','4'")]}
def adapt(name,text):
 for old,new in RULES.get(name,[]):
  if old not in text:raise ValueError('missing exact mapping anchor '+name+':'+old)
  text=text.replace(old,new)
 return text
def restore(name,text):
 for old,new in reversed(RULES.get(name,[])):
  if new not in text:raise ValueError('missing inverse mapping anchor '+name+':'+new)
  text=text.replace(new,old)
 return text
