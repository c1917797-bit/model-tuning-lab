"""DefaultOFF software facade, NOT the whole-original MAIN runtime command.
Use host_run.py directly for ON so MCP command, actual argv and consumer agree.
"""
import json,sys
def main():
 if len(sys.argv)==1:
  print(json.dumps(dict(status="disabled",remote_exec=False,npu_executed=False,model_ready=False,ready=False)));return
 if "--packet-audit-only" in sys.argv or "--source-audit-only" in sys.argv:
  import source_gate;source_gate.main();return
 if "--execute" not in sys.argv:
  print(json.dumps(dict(status="disabled",npu_executed=False,model_ready=False,ready=False)));return
 raise ValueError("MAIN runtime entry is exact host_run.py; facade execve changes whole-original argv")
if __name__=="__main__":main()
