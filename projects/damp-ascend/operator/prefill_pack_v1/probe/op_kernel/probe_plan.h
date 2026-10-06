// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cstdint>
namespace DampPrefillFloatProbe {
constexpr uint32_t ABI_VERSION=1, MAX_COUNT=896, GUARD_INTS=8, OUTPUTS=4;
struct Tiling { uint32_t count; uint32_t abiVersion; uint32_t useCandidate; uint32_t reserved; };
// Full N+16 INT32 buffers: raw quotient bits, valid-input, finite-result, certificate-accepted.
constexpr int32_t GUARDS[OUTPUTS]={0x13579bdf,0x2468ace0,0x10293847,0x31415926};
}
