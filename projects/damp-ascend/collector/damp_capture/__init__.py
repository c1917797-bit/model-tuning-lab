"""Opt-in output-preserving DAMP reference collector, never a speed candidate."""
def register():
    import os
    if os.environ.get("DAMP_CAPTURE_ENABLE") == "1":
        from .patch import register as install
        install()
