"""Adds only the new callback opt-in to existing physical4/Devices[] policy."""
def install(C):
 previous=C.environment
 def environment(service,leaf):
  value=previous(service,leaf);value.update(MXR_BLOCK_REFINEMENT044_ENABLE='1');return value
 C.environment=environment;C.inspect_owned.__globals__['environment']=environment
