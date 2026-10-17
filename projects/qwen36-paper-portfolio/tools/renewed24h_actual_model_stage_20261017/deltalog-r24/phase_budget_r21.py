"""New R21 registration only; never changes a historical run or UTC cutoff."""
WHOLE=3600
CLEANUP=270
POSTVERIFY=900
MARGIN=90
WORK=WHOLE-CLEANUP-POSTVERIFY-MARGIN
CUT=1792313000

def need(v,m):
 if not v:raise ValueError(m)

def registration():return dict(schema='deltalog.r21-new-experiment-clock/v1',whole_seconds=WHOLE,cleanup_seconds=CLEANUP,postverify_seconds=POSTVERIFY,margin_seconds=MARGIN,work_seconds=WORK,cutoff_epoch=CUT,not_retroactive=True)

def manifest(m):
 need(m['budgets']['phase_seconds']==WHOLE and m['budgets']['cleanup_seconds']==CLEANUP and m['cutoff_epoch']==CUT,'exact new R21 experiment clock with unchanged cleanup/cut')
 need(m['phase_budget_registration']==registration(),'exact full R21 phase registration')

def work_remaining(now,started,wall,cut):
 need(cut==CUT,'original fixed new-authority UTC cut')
 value=min(WHOLE-(now-started),cut-wall)-CLEANUP-POSTVERIFY-MARGIN
 need(value>0,'no work time after cleanup270/postverify900/margin90 within new3600/cut')
 return value

def post_remaining(now,started,wall,cut):
 need(cut==CUT,'original fixed new-authority UTC cut')
 value=min(POSTVERIFY,WHOLE-(now-started)-MARGIN,cut-wall-MARGIN)
 need(value>0,'no positive postverify900 within new3600/cut/margin90')
 return value
