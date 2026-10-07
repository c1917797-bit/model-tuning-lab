"""Default OFF. Explicit model opt-in must fail worker startup closed."""
import os
if os.environ.get("QWEN36_SPARQ_TOKEN_ENABLED")=="1":
 try:
  from model_bridge import install_from_env
  install_from_env()
 except BaseException:
  # Python swallows ordinary sitecustomize exceptions and would run dense.
  # Retain exact original traceback, then prevent a silent candidate fallback.
  import sys,traceback
  traceback.print_exc(file=sys.stderr);sys.stderr.flush()
  os._exit(78)
