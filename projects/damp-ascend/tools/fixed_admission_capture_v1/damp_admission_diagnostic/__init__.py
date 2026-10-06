"""Explicit diagnostic opt-in; importing this package is stdlib-only."""
def register():
    import os
    if os.environ.get("DAMP_ADMISSION_TRACE_ENABLE") != "1":
        return
    from .observer import register as install
    return install()
