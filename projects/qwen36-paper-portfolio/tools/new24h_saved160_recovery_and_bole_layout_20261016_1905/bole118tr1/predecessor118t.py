"""Exact completed 118c chain, not an old layout-certificate alias."""

def need(C,v,text):C.need(v,'actual118c '+text)

def join(C,m):
 p=m['actual_118c'];sr=p['source'];s=C.obj(sr)
 need(C,s['schema']=='bole.tree-fa-owned-source/v118c'and s['prepared_only']is False,'bound source')
 no=C.obj(p['numeric_owner']);co=C.obj(p['consumer_owner']);outer=C.obj(p['stage']);cap=C.obj(p['capture']);v=C.obj(p['consumer'])
 need(C,no['schema']=='bole.tree-owned/v118c'and no['source']==sr and no['primary']is None and no['secondary']==[]and no['stopped_retained']is True and no['physical']==[4]and no['logical']==0 and no['result']==p['stage'],'released numeric owner')
 need(C,outer['schema']=='bole.tree-stage/v118c'and outer['source']==sr and outer['primary']is None and outer['NPU']is True and outer['qualified']is False and outer['result']==p['capture'],'outer/capture')
 need(C,cap['schema']=='bole.actual-native-conv-capture/v118c'and cap['source']==sr and cap['operator_executed']is True and len(cap['records'])==len(cap['before_records'])==12,'actual12 capture')
 need(C,co['schema']=='bole.tree-owned-CPU/v118c'and co['source']==sr and co['primary']is None and co['secondary']==[]and co['resource_release_verified']is True and co['stopped_retained']is True and co['numeric_owner']==p['numeric_owner']and co['stage_ref']==p['stage']and co['stage_result']==p['consumer'],'released independent consumer')
 need(C,v['schema']=='bole.native-conv-independent/v118c'and v['source']==sr and v['actual_capture']==p['capture']and v['pass_gate']is True and v['native_SD_chronology_pass']is True and len(v['rows'])==12 and v['qualified']is False and v['model_ready']is False and v['BOLE_model_ready']is False,'independent complete12 no scope promotion')
 need(C,v['records']==cap['records']and v['before_records']==cap['before_records'],'actual same twelve frames')
 return dict(schema='bole.actual118c-prerequisite/v118t',source=sr,numeric_owner=p['numeric_owner'],consumer=p['consumer'],native_chronology_pass=True,tree_TND_supported=None,model_ready=False)
