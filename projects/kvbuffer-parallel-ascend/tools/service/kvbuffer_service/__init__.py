"""Explicit opt-in service evidence entrypoint."""
def register():
    from .evidence import register as install
    install()

