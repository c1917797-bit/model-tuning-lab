"""Opt-in diagnostic bootstrap; enabled errors must not silently continue."""
import os
if os.environ.get("INDEPENDENT_CACHE_DIAGNOSTIC")=="1":
    try:
        from independent_diagnostic_loader import enable
        enable()
    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(78)
