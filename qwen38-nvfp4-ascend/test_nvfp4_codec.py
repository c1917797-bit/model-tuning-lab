from nvfp4_codec import (
    decode_e4m3fn,
    dequantize_nvfp4,
    unpack_e2m1,
)


def test_low_nibble_is_first() -> None:
    assert unpack_e2m1(bytes([0x21])) == [0.5, 1.0]
    assert unpack_e2m1(bytes([0x9F])) == [-6.0, -0.5]


def test_e4m3fn_boundaries() -> None:
    assert decode_e4m3fn(0x00) == 0.0
    assert decode_e4m3fn(0x38) == 1.0
    assert decode_e4m3fn(0x7E) == 448.0
    assert decode_e4m3fn(0xB8) == -1.0


def test_group16_scale_application() -> None:
    packed = bytes([0x22] * 16)  # 32 values, all +1.0
    actual = dequantize_nvfp4(packed, [0.5, 2.0], 4.0)
    assert actual == [2.0] * 16 + [8.0] * 16


def test_rejects_group32_substitution() -> None:
    try:
        dequantize_nvfp4(bytes([0]), [1.0], 1.0, group_size=32)
    except ValueError as error:
        assert "group_size=16" in str(error)
    else:
        raise AssertionError("group32 must not be accepted as NVFP4")


if __name__ == "__main__":
    test_low_nibble_is_first()
    test_e4m3fn_boundaries()
    test_group16_scale_application()
    test_rejects_group32_substitution()
    print("PASS: NVFP4 reference codec")

