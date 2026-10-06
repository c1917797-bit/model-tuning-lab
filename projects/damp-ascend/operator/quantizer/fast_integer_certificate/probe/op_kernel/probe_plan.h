// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <array>
#include <cstdint>
namespace DampIntegerProbe {
constexpr uint32_t ABI_VERSION=1, MAX_COUNT=896, GUARD_INTS=8, OUTPUTS=7;
struct Tiling { uint32_t count; uint32_t abiVersion; };
constexpr int32_t floor_log2(int32_t k) {
    int32_t f=0; while (k>1) { k>>=1; ++f; } return f;
}
constexpr std::array<int32_t,128> make_c() {
    std::array<int32_t,128> a{};
    for (int32_t j=0;j<127;++j) {
        const int32_t k=2*j+1, f=floor_log2(k)-1;
        a[j]=(k<<(23-f))+((j&1)?-1:1);
    }
    a[127]=a[126]; return a;
}
constexpr std::array<int32_t,128> make_f() {
    std::array<int32_t,128> a{};
    for (int32_t j=0;j<127;++j) a[j]=floor_log2(2*j+1)-1;
    a[127]=a[126]; return a;
}
constexpr auto C_TABLE=make_c();
constexpr auto F_TABLE=make_f();
constexpr const char* C_SHA256="7c6e8dbfe3ea2a3dcaf62ab2ef14936d2d9252a36738eb6b78ba4b1d37c7c708";
constexpr const char* F_SHA256="2df58f09be50ce6051418c229acf641a37c9596f1826884ee02d7a02b1581a83";
constexpr const char* CF_SHA256="c58fdd435e302b9209203dcbdd38b7e456bed8f0d425d9f7339ca5b46e3582c8";
// Outputs: accepted, lowerFloor, upperFloor, lowerDomain, upperDomain,
// finalSignedCode, finalValid. Whole N+16 backing buffers, distinct sentinels.
constexpr int32_t GUARDS[OUTPUTS] = {
    0x13579bdf,0x2468ace0,0x10293847,0x31415926,
    0x27182818,0x456789ab,0x56789abc};
}

