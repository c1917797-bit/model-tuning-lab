"""Explicit opt-in entry point. Disabled by default."""
def register():
    from .patch import register as install
    install()
