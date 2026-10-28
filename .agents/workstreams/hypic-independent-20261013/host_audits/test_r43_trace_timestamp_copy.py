"""Precision and fail-closed controls for official timestamp-format adaptation."""
from decimal import Decimal
import copy,math,pytest
from host_audits.r43_trace_timestamp_copy import decimal_time,adapt_events,verify_events,inspect_events
def event(ts="1793216209616773.580",dur=0.001):
 return {"ph":"X","ts":ts,"dur":dur,"pid":60,"tid":60,"name":"op","args":{"id":1793216209616773580}}
def test_epoch_precision_and_shared_origin():
 a=[event(),event("1793216209616773.581"),{"ph":"s","id":5,"ts":"1793216209616773.581"}]
 origin=Decimal("1793216209616773")
 b=adapt_events(a,origin);assert b[1]["ts"]-b[0]["ts"]!=0
 assert Decimal(str(b[1]["ts"]))-Decimal(str(b[0]["ts"]))==Decimal(".001")
 assert b[2]["id"]==5 and b[0]["args"]==a[0]["args"]
 assert verify_events(a,b,origin)["timestamps"]==3
 assert float(a[0]["ts"])==float(a[1]["ts"])
@pytest.mark.parametrize("v",["NaN","Infinity","1e9","1;import os",True,None,"0.1234567890",float("nan"),float("inf")])
def test_timestamp_bad_input_rejected(v):
 with pytest.raises(ValueError):decimal_time(v)
@pytest.mark.parametrize("d",[-.001,float("nan"),float("inf"),"1",True,None])
def test_bad_duration_rejected(d):
 with pytest.raises(ValueError):inspect_events([event(dur=d)])
def test_roundtrip_loss_rejected():
 with pytest.raises(ValueError,match="roundtrip"):adapt_events([event("999999999999999999.001")],Decimal(0))
@pytest.mark.parametrize("mode",["drop","duration","flowid","offset","reorder"])
def test_all_records_and_fields_guard(mode):
 a=[event(),dict(event("1793216209616773.581"),id=9)]
 b=adapt_events(a,Decimal("1793216209616773"))
 if mode=="drop":b.pop()
 if mode=="duration":b[0]["dur"]=2
 if mode=="flowid":b[1]["id"]=10
 if mode=="offset":b[0]["ts"]+=.001
 if mode=="reorder":b.reverse()
 with pytest.raises(ValueError):verify_events(a,b,Decimal("1793216209616773"))
