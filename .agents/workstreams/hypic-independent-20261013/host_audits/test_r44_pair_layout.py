"""Scientific bookkeeping controls; never inference or performance proof."""
import math
import pytest
from host_audits.r44_pair_layout import flow_key,flow_summary,interval_union,finite_span
def event(phase,identifier):return {"ph":phase,"cat":"HostToDevice","name":"f","id":identifier}
def test_exact_ids_above_double_precision_and_type():
 assert flow_key(event("s",2**53+1))!=flow_key(event("s",2**53))
 assert flow_key(event("s",2**53+1))!=flow_key(event("s",str(2**53+1)))
def test_fanout_and_boundary_and_ambiguous_remain():
 rows=[event("s",1),event("f",1),event("f",1),event("f",2),event("s",3),event("s",4),event("s",4),event("f",4)]
 r=flow_summary(rows)["categories"]["HostToDevice"]
 assert r["keys"]==4 and r["fan_out"]==1 and r["missing_start"]==1 and r["missing_end"]==1 and r["ambiguous_multi_start"]==1
 assert r["starts"]==4 and r["ends"]==4
def test_unsupported_id_is_reported():
 r=flow_summary([event("s",True),event("f",None)])
 assert r["unsupported_id_events"]==2
def test_intermediate_only_keeps_both_missing_endpoints():
 r=flow_summary([event("t",9)])["categories"]["HostToDevice"]
 assert r["intermediate"]==1 and r["missing_start"]==1 and r["missing_end"]==1
def test_overlap_union_is_not_sum():
 assert interval_union([(0,4),(2,6),(3,5),(10,12)])==8
 assert interval_union([])==0
@pytest.mark.parametrize("value",[float("nan"),float("inf"),-1])
def test_bad_duration_rejected(value):
 with pytest.raises(ValueError):finite_span({"ts":0,"dur":value})
def test_negative_or_nonfinite_interval_rejected():
 with pytest.raises(ValueError):interval_union([(2,1)])
 with pytest.raises(ValueError):interval_union([(0,math.inf)])

def test_native_cannot_be_relabelled_as_algorithm_arm():
 from host_audits.r44_pair_layout import check_report
 row={"path":"/r","sha256":"s"};accept={"state":"BOTH_COUNT2_ARMS_FULL_DIAGNOSTIC_GUARDS_TRACE_AND_RELEASE_VALID","arms":{"G3":{"report":row}}}
 report={"policy":{"group":"G1","algorithm_on":False,"pdc_on":False},"r44_diagnostic_transport_valid":True,"live_release_verified":True,"profiler":{"four_rank_trace_valid":True},"r44_profiler":{"max_iterations":2}}
 with pytest.raises(ValueError,match="actual arm"):check_report("G3",row,accept,report)
def test_incomplete_or_different_report_not_accepted():
 from host_audits.r44_pair_layout import check_report
 row={"path":"/r","sha256":"s"};accept={"state":"BOTH_COUNT2_ARMS_FULL_DIAGNOSTIC_GUARDS_TRACE_AND_RELEASE_VALID","arms":{"G1":{"report":row}}}
 report={"policy":{"group":"G1","algorithm_on":False,"pdc_on":False},"r44_diagnostic_transport_valid":True,"live_release_verified":True,"profiler":{"four_rank_trace_valid":False},"r44_profiler":{"max_iterations":2}}
 with pytest.raises(ValueError,match="full count2"):check_report("G1",row,accept,report)
 with pytest.raises(ValueError,match="report binding"):check_report("G1",{"path":"/other","sha256":"s"},accept,report)
