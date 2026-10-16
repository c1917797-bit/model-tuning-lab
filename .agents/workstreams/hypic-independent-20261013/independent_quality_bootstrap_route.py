"""Pure explicit startup selection; no runtime imports or device allocation."""
def select_bootstrap(contract):
    quality=contract.get("formal_quality",False)
    performance=contract.get("formal_performance",False)
    if type(quality)is not bool or type(performance)is not bool or quality and performance:
        raise ValueError("explicit nonambiguous quality/performance mode required")
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
