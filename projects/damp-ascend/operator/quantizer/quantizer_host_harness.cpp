// SPDX-License-Identifier: Apache-2.0
// Parent may compile this in a NEW external output directory; no device needed.
#include <iostream>
#include <iomanip>
#include "exact_quantizer_bits.h"
int main()
{
    uint32_t x, scale;
    while (std::cin >> std::hex >> x >> scale) {
        const auto result = Qwen36DampQuantizer::ExactCode(x, scale);
        std::cout << std::dec << (result.valid ? 1 : 0) << ' '
                  << result.code << '\n';
    }
    return std::cin.eof() ? 0 : 2;
}

