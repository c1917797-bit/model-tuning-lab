"""Default-OFF independently named fresh DeltaLog provider."""
def register():
 from .provider import register as enable
 return enable()
