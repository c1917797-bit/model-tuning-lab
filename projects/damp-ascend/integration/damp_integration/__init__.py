"""Source-bound DAMP packed-cache candidate; disabled unless explicitly enabled."""

def register():
    import os
    if os.environ.get("DAMP_PACKED_ENABLED") != "1":
        return
    from .patch import install
    install()

