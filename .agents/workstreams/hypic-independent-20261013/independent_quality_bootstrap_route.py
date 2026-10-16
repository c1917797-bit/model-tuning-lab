"""Pure explicit startup selection; no runtime imports or device allocation."""
def quality_mode(contract):
    keys=("formal_quality","formal_performance","formal_quality_canary")
    flags=[contract.get(k,False) for k in keys]
    if any(type(x)is not bool for x in flags) or sum(flags)>1:
        raise ValueError("explicit exclusive quality/performance/Canary mode required")
    if flags[2]:
        diagnostic=contract.get("cache_diagnostic")
        if type(diagnostic)is not dict or not isinstance(diagnostic.get("compact_manifest"),str) or not diagnostic["compact_manifest"].strip():
            raise ValueError("catalog Canary requires explicit treatment manifest before admission")
    return "canary" if flags[2] else "full" if flags[0] else None

def select_bootstrap(contract):
    quality=quality_mode(contract)
    diagnostic=contract.get("cache_diagnostic")
    if diagnostic is None or diagnostic=={}:return None
    if type(diagnostic)is not dict:raise ValueError("explicit diagnostic configuration required")
    manifest=diagnostic.get("compact_manifest")
    if manifest is not None and (not isinstance(manifest,str) or not manifest.strip()):
        raise ValueError("valid explicit compact manifest required")
    if quality:
        if not manifest:raise ValueError("quality treatment requires catalog compact manifest")
        return "quality_bootstrap"
    return "compact_bootstrap" if manifest else "diagnostic_bootstrap"
