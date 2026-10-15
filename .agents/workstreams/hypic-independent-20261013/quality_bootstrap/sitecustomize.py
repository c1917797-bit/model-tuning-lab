import os
if os.environ.get('INDEPENDENT_COMPACT_HYPIC')=='1':
    try:
        from independent_quality_compact_loader import enable
        enable()
    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(78)
