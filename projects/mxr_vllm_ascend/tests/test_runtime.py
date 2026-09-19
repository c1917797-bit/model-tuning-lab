from __future__ import annotations

import pytest

from mxr_vllm_ascend.runtime import adapter_for_version


@pytest.mark.parametrize("version", ["0.23.0", "v0.23.0", "0.23.1rc1"])
def test_v023_adapter(version):
    assert adapter_for_version(version) == "v023"


@pytest.mark.parametrize("version", ["0.27.0", "v0.27.0", "0.27.1rc1"])
def test_v027_adapter(version):
    assert adapter_for_version(version) == "v027"


@pytest.mark.parametrize("version", ["0.22.0", "0.24.0", "0.28.0", "main", "1.0.0"])
def test_unknown_version_fails(version):
    with pytest.raises(RuntimeError):
        adapter_for_version(version)
