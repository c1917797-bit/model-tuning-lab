"""Read the whole original AWMCP envelope without rewriting success/origin fields."""
import json,re
def require(ok,why):
 if not ok:raise ValueError(why)
def original_terminal(envelope,peer):
 require(type(envelope) is dict,"whole original JSON object")
 outer=envelope.get("structuredContent",envelope)
 require(type(outer) is dict,"original structuredContent")
 if "structuredContent" in envelope:
  blocks=[b for b in envelope.get("content",[]) if b.get("type")=="text"]
  if blocks:
   require(len(blocks)==1,"one complete original textual envelope")
   require(json.loads(blocks[0]["text"])==outer,"original text/structured envelope disagreement or truncation")
 if outer.get("schema")=="agentweb.operation/v1":
  require(outer.get("kind")=="exec" and outer.get("ok") is True and outer.get("found") is True and
   outer.get("terminal") is True and outer.get("succeeded") is True and outer.get("status")=="completed" and
   outer.get("phase")=="completed" and outer.get("error") is None,"actual original completed successful operation_get, never failed/notfound")
  operation=outer.get("operation");oid=outer.get("operationId");shape="operation_get"
  require(type(operation) is dict,"original operation object required")
  for key in ("routeDecision","targetPeerId"):
   if key in outer:require(outer[key]==operation.get(key),"duplicate original route/target disagreement")
  if isinstance(outer.get("result"),dict) and "record" in outer["result"]:
   require(outer["result"]==operation.get("result"),"duplicate original result disagreement")
 else:
  require(outer.get("operationKind")=="exec" and "operationId" in outer and "operation" not in outer,
   "actual whole original direct a_exec, not extracted/flattened operation_get")
  operation=outer;oid=outer["operationId"];shape="direct_exec"
 require(re.fullmatch(r"exec-[0-9a-f]{16}",oid or ""),"original stable exec operationId")
 require(operation.get("routeDecision") in ("peer_direct","upstream_local_peer") and operation.get("targetPeerId")==peer and
  operation.get("ok") is True,"original actual intended target and route")
 result=operation.get("result")
 require(type(result) is dict and result.get("state")=="completed" and result.get("ok") is True and type(result.get("record")) is dict,
  "original operation result.record, not unrelated top result")
 record=result["record"]
 require(record.get("id")==oid and record.get("state")=="completed" and record.get("exitCode")==0 and record.get("cancelled") is False and
  record.get("timedOut") is False and record.get("error") is None and type(record.get("command")) is str and
  type(record.get("args")) is list and all(type(a) is str for a in record["args"]) and
  type(record.get("stdout")) is str and type(record.get("stderr")) is str,
  "complete successful original foreground command/args/stdout/stderr and matching record ID")
 for obj in (envelope,outer,operation,result,record):
  require(not any("truncat" in str(k).lower() and v not in (False,None,0,"") for k,v in obj.items()),"truncated original receipt forbidden")
 return dict(operation_id=oid,record=record,route_decision=operation["routeDecision"],target_peer_id=operation["targetPeerId"],
  origin_shape=shape,operation_id_origin="structuredContent.operationId" if "structuredContent" in envelope else "operationId",
  record_origin=("structuredContent." if "structuredContent" in envelope else "")+("operation.result.record" if shape=="operation_get" else "result.record"))
