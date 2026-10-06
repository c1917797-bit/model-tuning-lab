"""Safe template entrypoint for a removable runtime patch."""


def activate() -> None:
    raise RuntimeError(
        "Implement the one declared treatment before enabling this template"
    )
