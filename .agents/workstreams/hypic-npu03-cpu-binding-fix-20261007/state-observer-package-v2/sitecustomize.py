"""Opt-in loader adapted from the repository runtime-monkeypatch template."""
import os
if os.environ.get("HYPIC_STATE_OBSERVER_ENABLE") == "1":
    try:
        from hypic_diagnostic_patch import activate
        activate()
    except BaseException:
        # Python otherwise swallows ordinary sitecustomize exceptions.
        import traceback
        traceback.print_exc()
        os._exit(78)
