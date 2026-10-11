"""Actual failed-parent, successful-capture-child and failed-consumer authority.
No old successful whole is reconstructed. Every old result remains immutable.
"""
import json,re
from pathlib import Path,PurePosixPath
import offline_contract as D
from capture_identity import exact
HOST_REF={"path":str(D.RAW_ROOT/"HOST_RESULT.json"),"bytes":113022,"sha256":"8f1c512544ac46e77912a3ee870b9610d3ae8ba333c89ecdd12b9731ec48687f"}
CAPTURE_CLI_REF={"path":str(D.RAW_ROOT/"capture256-CLI-1791678368942182340.json"),"bytes":2665,"sha256":"557e4d14ed43610e058114d0a4f4722fad43071fc59bea0d36d9648bf83228c4"}
FAILED_CLI_REF={"path":str(D.RAW_ROOT/"consume-full256-preprojection-CLI-1791679925302880550.json"),"bytes":2175,"sha256":"ae53806dc9334f53b635d7409da4165a1e0231efb57d3c14fd7c2a6d8531f87b"}
FAILED_STDERR_REF={"path":str(D.RAW_ROOT/"consume-full256-preprojection.stderr"),"bytes":1210,"sha256":"0124cc4fba65e65f5360367b2eb706fd634fb716446f25b4f08bbb0b809e0f5e"}
PRODUCER_ROOT=D.RAW_ROOT/"run-skvq-capture-projection-001-main"
PY="/usr/local/python3.12.13/bin/python3";DOCKER="/usr/bin/docker"
SHELL=['/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','skvq-owned',PY,'-B']
OLD_ROOT=PurePosixPath(D.CAPTURE['path']).parent
def host_argv():
    return ['/usr/bin/env','MAIN_SKVQ_HOST_ENABLE=1','/usr/bin/prlimit','--cpu=7200:7200','--',
      '/usr/bin/python3','-B',str(OLD_ROOT/'MAIN_HOST.py'),'--execute','--source-manifest-sha256',
      D.CAPTURE['sha256'],'--output',str(D.RAW_ROOT)]
def original(value):
    op=value['operation'];record=op['result']['record']
    D.need(value['schema']=='agentweb.operation/v1'and value['terminal']is True and
      value['status']==value['phase']=='completed'and value['succeeded']is False and
      value['ok']is False and value['error']=='exit code'and value['found']is True and op['ok']is True and
      op['result']['state']==record['state']=='completed'and op['routeDecision']=='peer_direct'and
      op['targetPeerId']=='lgw_a6109c51076a4a2c9d2674ca5a8704a0',
      'actual original failed direct whole; not reconstructed successful terminal')
    D.need(record['id']=='exec-00000000000005a7'and [record['command'],*record['args']]==host_argv()and
      type(record['exitCode'])is int and record['exitCode']==1 and record['timedOut']is False and
      record['cancelled']is False and record['error']=='exit code'and 0<record['durationMs']<=7200000,
      'one exact failed014 original argv/id/exit1/non-timeout/non-cancelled')
    printed=json.loads(record['stdout'])
    D.need(exact(printed,dict(host_result=HOST_REF,status='FAILED')),
      'original actual stdout binds unchanged failed HOST_RESULT')
    return record
def qualify_host(host,href):
    D.need(exact(href,HOST_REF)and host['schema']=='SKVQ_HOST_CAPTURE_RESULT_V1'and
      host['status']=='FAILED'and host['source_lock']==D.CAPTURE and host['result']is None and
      host['primary']=="ValueError('actual child nonzero; raw stdout/stderr retained')"and
      host['secondary']==[]and host['cpu_input_only']is False and host['native_ready']is False and
      host['model_ready']is False and len(host['owned'])==3 and
      [r['phase']for r in host['owned']]==['preflight','tp4-capture','independent-consumer'],
      'only actual failed014 consumer seam; no arbitrary failure or partial old host')
    for row in host['owned']:
        D.need(re.fullmatch('[0-9a-f]{64}',row['cid'])and row['released']is True and
          row['source']==D.CAPTURE['sha256'],'actual old three released source-bound owned CIDs')
    return host
def children_fields(host,capture,failed):
    qualify_host(host,HOST_REF);ncid=host['owned'][1]['cid'];ccid=host['owned'][2]['cid']
    capargv=[DOCKER,'exec','--env','MAIN_OWNED_CID='+ncid,ncid,*SHELL,
      str(OLD_ROOT/'capture_current.py'),'--execute','--source-manifest-sha256',D.CAPTURE['sha256'],
      '--inputs',str(D.RAW_ROOT/'cpu/run-skvq-train-inputs-001-main/INPUTS.json'),
      '--output',str(PRODUCER_ROOT),'--admission',str(D.RAW_ROOT/'CAPTURE_ADMISSION.json'),'--max-total-seconds','4200']
    failargv=[DOCKER,'exec',ccid,*SHELL,str(OLD_ROOT/'consume_stage.py'),'--execute',
      '--source-manifest-sha256',D.CAPTURE['sha256'],'--root',str(PRODUCER_ROOT),
      '--output',str(D.RAW_ROOT/'CAPTURE_CONSUMED.json')]
    for row,argv,code in ((capture,capargv,0),(failed,failargv,1)):
        D.need(row['argv']==argv and row['actual_wrapped_argv']==['/usr/bin/prlimit','--as=unlimited','--',*argv]and
          type(row['exit_code'])is int and row['exit_code']==code and row['terminated']is True and
          type(row['host_pid'])is int and row['host_pid']>1,'actual exact original child argv/CID/source/output/exit')
    D.need(capture['primary']is None and failed['primary']==host['primary']and
      failed['stderr']==FAILED_STDERR_REF and failed['stdout']['bytes']==0 and
      failed['stdout']['sha256']=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      'capture child0, exact old consumer1 and no fabricated old raw-consumer receipt')
    for row,label in ((capture,'capture256'),(failed,'consume-full256-preprojection')):
        for key in ('stdout','stderr'):
            D.need(row[key]['path']==str(D.RAW_ROOT/(label+'.'+key)),'exact original child log path')
    return True
def log_bytes(row):
    D.need(type(row)is dict and set(row)=={'path','bytes','sha256'}and type(row['bytes'])is int and
      row['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',row['sha256'])and D.ref(row['path'])==row,
      'entire actual original log Ref, explicit zero-byte stdout permitted only as a log')
    return Path(row['path']).read_bytes()
def inspect():
    original_ref=D.FAILED_ORIGINAL;original(D.obj(original_ref));host=qualify_host(D.obj(HOST_REF),HOST_REF)
    capture=D.obj(CAPTURE_CLI_REF);failed=D.obj(FAILED_CLI_REF);children_fields(host,capture,failed)
    for row in(capture,failed):
        for key in('stdout','stderr'):log_bytes(row[key])
    text=log_bytes(FAILED_STDERR_REF).decode('utf-8')
    D.need(text.endswith('ValueError: same real captured rank process\n')and
      str(OLD_ROOT/'consume_loader_current.py')in text and 'line 22, in consume'in text and
      'v["identity"]==item["identity"]'in text,'actual original firstfault at the exact full-identity comparison')
    return dict(schema='skvq.capture014.actual-failure-authority/v1',original_ref=original_ref,
      host_result_ref=HOST_REF,capture_child_ref=CAPTURE_CLI_REF,failed_consumer_child_ref=FAILED_CLI_REF,
      failed_consumer_stderr_ref=FAILED_STDERR_REF,original_whole_exit=1,capture_child_exit=0,
      old_consumer_child_exit=1,original_failed_whole_preserved=True,not_old_success=True,
      independent_new_raw_consumption_pending=True,native_ready=False,model_ready=False)
