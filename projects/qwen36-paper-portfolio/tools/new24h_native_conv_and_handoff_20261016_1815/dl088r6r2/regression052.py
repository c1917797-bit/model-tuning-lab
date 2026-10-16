"""Original real035 step80 is a frozen regression, never an unseen holdout."""
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
def inputs(torch,m,C,case):
 if case=='original-B16-step80':
  r=m['firstfault_ref'];raw=torch.load(C.checked(r),map_location='cpu',weights_only=False)
  cap=raw['captures']['decode'][0];i=cap['inputs'];b=cap['before']
  args=[i[k]for k in('query','key','value','g','beta')]+[b[k]for k in FIELDS]+[i[k]for k in('actual_seq_lengths','ssm_state_indices')]
 elif case=='original-B16-step137':
  r=m['regression137_raw_ref'];raw=torch.load(C.checked(r),map_location='cpu',weights_only=False)
  if raw['event']['step']!=137:raise ValueError('actual original137 event')
  i=raw['inputs'];b={k:torch.load(C.checked(raw['before'][k]),map_location='cpu',weights_only=False)for k in FIELDS}
  args=[i[k]for k in('query','key','value','g','beta')]+[b[k]for k in FIELDS]+[raw['sequence'],i['indices']]
 else:raise ValueError('exact frozen regression case')
 if tuple(args[0].shape)!=(16,4,128):raise ValueError('actual frozen B16 regression geometry')
 return r,args
def run(torch,capture,m,C):
 rows=[]
 for case in('original-B16-step80','original-B16-step137'):
  r,args=inputs(torch,m,C,case);capture(*[x.to('npu:0').clone()for x in args])
  rows.append(dict(case=case,raw=capture.take(),expect='finite-empirical-pass',original_raw=r,old_failure_preserved=True))
 return rows
def audit(torch,m,C,control,side):
 from precast import bits
 r,args=inputs(torch,m,C,control['case'])
 if control['original_raw']!=r or control['old_failure_preserved']is not True or len(side['before'])!=13 or not all(bits(torch,a,b)for a,b in zip(args,side['before'])):raise ValueError('actual regression raw/source/all13 before byte join')
 return True
