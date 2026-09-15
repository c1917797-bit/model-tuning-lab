from verify_device_ownership import (
    parse_container_pids,
    parse_device_pids,
    verify,
)


def test_accepts_only_container_owned_device_processes():
    owned = parse_container_pids(" 101\n102\n103\n")
    observed = parse_device_pids(
        {
            4: "Process id:101 Process name:worker",
            5: "Process id:102 Process name:worker",
        }
    )
    result = verify(owned, observed)
    assert result["ok"] is True
    assert result["foreign_pids"] == []


def test_rejects_foreign_device_process():
    result = verify({101, 102}, {101, 999})
    assert result["ok"] is False
    assert result["foreign_pids"] == [999]


def test_rejects_missing_container_process_set():
    result = verify(set(), set())
    assert result["ok"] is False
