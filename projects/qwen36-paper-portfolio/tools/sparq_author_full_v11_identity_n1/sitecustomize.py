"""Default OFF; candidate explicitly opted in and actual full kernel authority required."""
import os
if os.environ.get("QWEN36_SPARQ_STOCK_FULL_ENABLED")=="1":
 try:
  import identity_bridge
  identity_bridge.install_frontend() # Real assignment source tap before first request.
  import bridge
  bridge.install_from_env()
 except BaseException:
  import sys,traceback
  traceback.print_exc(file=sys.stderr);sys.stderr.flush();os._exit(78)
