"""Additional fail-closed conjunction, never a replacement for either original oracle."""
import math
def need(v,m):
 if not v:raise ValueError(m)
def metric(value):
 need(type(value)is dict and value.get('threshold')==.005,'original .005 tensor gate, not task1%')
 x=value.get('relative_rms');need(type(x)in(int,float)and math.isfinite(x)and 0<=x<=.005,'whole-output finite error')
def numeric(graph,active):
 need(graph.get('schema')=='kivi.direct-fp32.graph-independent1536/v1'and graph.get('full_outputs')==1536 and graph.get('candidate_imported')is False and graph.get('writer_full_pool_byte_equal')is True,'independent saved full1536 and complete slot/pool bytes')
 need(graph.get('reference_state')=='actual-captured-pending-after-append-before-AV-before-seal','reference pending state, not post-seal')
 metric(graph['metrics'])
 need(active.get('schema')=='kivi.active128-slot-reuse-independent/v1'and active.get('all6_outputs')==9216 and active.get('active_k_seals')==2 and active.get('value_shifts')==6 and active.get('epochs')==[1,2],'all6 active replays and real slot epochs')
 need(active.get('byte_reference')=='source-exact original author CPU quant+packing'and active.get('attention_reference')=='softmax-fp64-fsum-exp-QK-over16-V-final-A16/v1','independent original references')
 need(len(active.get('metrics',[]))==6,'six whole1536 comparisons')
 for m in active['metrics']:metric(m)
 return dict(saved1536=True,active9216=True,component_domains_only=True,model_ready=False,performance_ready=False,task_ready=False)
def graph_receipt(value,writer):
 need(value.get('actual_graph_captured')is True and value.get('actual_graph_replayed')is True and value.get('writer_full_pool_byte_parity')is True and value.get('actual_r156_writer')==writer and value.get('full_outputs')==1536,'actual new writer capture/replay required')
 return True
def performance_ready(*unused):
 raise ValueError('component tests cannot grant full model/performance permission')
