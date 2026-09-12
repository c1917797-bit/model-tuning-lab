// Exact-shape BF16 numerical gate for the upstream SwigluGatedMlp candidate.
//
// Candidate: aclnnSwigluGatedMlp from the read-only custom OPP.
// Reference: official CANN aclnnMatmul -> aclnnSwiGlu -> aclnnMatmul.
// This program intentionally does not contain a replacement SwiGLU or matmul.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

#include "acl/acl.h"
#include "aclnnop/aclnn_matmul.h"
#include "aclnnop/aclnn_swi_glu.h"

// The upstream installed header currently includes an unshipped build helper
// (aclnn_util.h). Declare the two already-exported C functions directly so
// this gate tests the installed runtime ABI without copying build-only headers
// into the OPP bundle.
extern "C" {
aclnnStatus aclnnSwigluGatedMlpGetWorkspaceSize(
    const aclTensor* x,
    const aclTensor* gateUpWeight,
    const aclTensor* downWeight,
    int64_t cubeMathType,
    aclTensor* y,
    uint64_t* workspaceSize,
    aclOpExecutor** executor);
aclnnStatus aclnnSwigluGatedMlp(
    void* workspace,
    uint64_t workspaceSize,
    aclOpExecutor* executor,
    aclrtStream stream);
}

namespace {

constexpr int64_t kHidden = 5120;
constexpr int64_t kIntermediate = 4352;
constexpr int64_t kGateUp = 2 * kIntermediate;
constexpr int64_t kOutput = 5120;
constexpr double kMaxAbsLimit = 0.125;
constexpr double kRelativeL2Limit = 0.02;

void Check(int32_t status, const char* expression)
{
    if (status != ACL_SUCCESS) {
        throw std::runtime_error(std::string(expression) + " failed with status " + std::to_string(status));
    }
}

#define ACL_CHECK(expression) Check((expression), #expression)

int64_t Numel(const std::vector<int64_t>& shape)
{
    int64_t result = 1;
    for (const auto dim : shape) {
        result *= dim;
    }
    return result;
}

uint16_t FloatToBf16(float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    const uint32_t round = 0x7fffU + ((bits >> 16U) & 1U);
    return static_cast<uint16_t>((bits + round) >> 16U);
}

float Bf16ToFloat(uint16_t value)
{
    const uint32_t bits = static_cast<uint32_t>(value) << 16U;
    float result = 0.0F;
    std::memcpy(&result, &bits, sizeof(result));
    return result;
}

uint64_t NextRandom(uint64_t& state)
{
    state ^= state >> 12U;
    state ^= state << 25U;
    state ^= state >> 27U;
    return state * 2685821657736338717ULL;
}

std::vector<uint16_t> MakeData(int64_t count, uint64_t seed, float scale)
{
    std::vector<uint16_t> result(static_cast<size_t>(count));
    uint64_t state = seed == 0 ? 0x9e3779b97f4a7c15ULL : seed;
    for (auto& item : result) {
        const uint32_t raw = static_cast<uint32_t>(NextRandom(state) >> 40U);
        const float unit = static_cast<float>(raw) / static_cast<float>(0x00ffffffU);
        item = FloatToBf16((2.0F * unit - 1.0F) * scale);
    }
    return result;
}

struct DeviceTensor {
    std::vector<int64_t> shape;
    std::vector<int64_t> strides;
    void* data = nullptr;
    aclTensor* tensor = nullptr;
    size_t bytes = 0;

    DeviceTensor(const std::vector<int64_t>& tensorShape, const std::vector<uint16_t>* host)
        : shape(tensorShape), strides(tensorShape.size(), 1),
          bytes(static_cast<size_t>(Numel(tensorShape)) * sizeof(uint16_t))
    {
        for (int64_t i = static_cast<int64_t>(shape.size()) - 2; i >= 0; --i) {
            strides[static_cast<size_t>(i)] =
                shape[static_cast<size_t>(i + 1)] * strides[static_cast<size_t>(i + 1)];
        }
        ACL_CHECK(aclrtMalloc(&data, bytes, ACL_MEM_MALLOC_HUGE_FIRST));
        if (host != nullptr) {
            if (host->size() * sizeof(uint16_t) != bytes) {
                throw std::runtime_error("host tensor byte size mismatch");
            }
            ACL_CHECK(aclrtMemcpy(data, bytes, host->data(), bytes, ACL_MEMCPY_HOST_TO_DEVICE));
        } else {
            ACL_CHECK(aclrtMemset(data, bytes, 0, bytes));
        }
        tensor = aclCreateTensor(shape.data(), shape.size(), aclDataType::ACL_BF16,
                                 strides.data(), 0, aclFormat::ACL_FORMAT_ND,
                                 shape.data(), shape.size(), data);
        if (tensor == nullptr) {
            throw std::runtime_error("aclCreateTensor returned null");
        }
    }

    DeviceTensor(const DeviceTensor&) = delete;
    DeviceTensor& operator=(const DeviceTensor&) = delete;

    ~DeviceTensor()
    {
        if (tensor != nullptr) {
            aclDestroyTensor(tensor);
        }
        if (data != nullptr) {
            aclrtFree(data);
        }
    }

    std::vector<uint16_t> CopyToHost() const
    {
        std::vector<uint16_t> result(static_cast<size_t>(Numel(shape)));
        ACL_CHECK(aclrtMemcpy(result.data(), bytes, data, bytes, ACL_MEMCPY_DEVICE_TO_HOST));
        return result;
    }
};

template <typename GetWorkspace, typename Execute>
void RunAclnn(GetWorkspace getWorkspace, Execute execute, aclrtStream stream)
{
    uint64_t workspaceSize = 0;
    aclOpExecutor* executor = nullptr;
    ACL_CHECK(getWorkspace(&workspaceSize, &executor));
    void* workspace = nullptr;
    if (workspaceSize != 0) {
        ACL_CHECK(aclrtMalloc(&workspace, workspaceSize, ACL_MEM_MALLOC_HUGE_FIRST));
    }
    try {
        ACL_CHECK(execute(workspace, workspaceSize, executor, stream));
        ACL_CHECK(aclrtSynchronizeStream(stream));
    } catch (...) {
        if (workspace != nullptr) {
            aclrtFree(workspace);
        }
        throw;
    }
    if (workspace != nullptr) {
        ACL_CHECK(aclrtFree(workspace));
    }
}

void RunCandidate(
    const DeviceTensor& x,
    const DeviceTensor& gateUpWeight,
    const DeviceTensor& downWeight,
    DeviceTensor& output,
    aclrtStream stream)
{
    RunAclnn(
        [&](uint64_t* workspaceSize, aclOpExecutor** executor) {
            return aclnnSwigluGatedMlpGetWorkspaceSize(
                x.tensor, gateUpWeight.tensor, downWeight.tensor, 1,
                output.tensor, workspaceSize, executor);
        },
        [&](void* workspace, uint64_t workspaceSize, aclOpExecutor* executor, aclrtStream callStream) {
            return aclnnSwigluGatedMlp(workspace, workspaceSize, executor, callStream);
        },
        stream);
}

void RunReference(
    const DeviceTensor& x,
    const DeviceTensor& gateUpWeight,
    const DeviceTensor& downWeight,
    DeviceTensor& gateUp,
    DeviceTensor& activated,
    DeviceTensor& output,
    aclrtStream stream)
{
    RunAclnn(
        [&](uint64_t* workspaceSize, aclOpExecutor** executor) {
            return aclnnMatmulGetWorkspaceSize(
                x.tensor, gateUpWeight.tensor, gateUp.tensor, 1, workspaceSize, executor);
        },
        [&](void* workspace, uint64_t workspaceSize, aclOpExecutor* executor, aclrtStream callStream) {
            return aclnnMatmul(workspace, workspaceSize, executor, callStream);
        },
        stream);
    RunAclnn(
        [&](uint64_t* workspaceSize, aclOpExecutor** executor) {
            return aclnnSwiGluGetWorkspaceSize(
                gateUp.tensor, -1, activated.tensor, workspaceSize, executor);
        },
        [&](void* workspace, uint64_t workspaceSize, aclOpExecutor* executor, aclrtStream callStream) {
            return aclnnSwiGlu(workspace, workspaceSize, executor, callStream);
        },
        stream);
    RunAclnn(
        [&](uint64_t* workspaceSize, aclOpExecutor** executor) {
            return aclnnMatmulGetWorkspaceSize(
                activated.tensor, downWeight.tensor, output.tensor, 1, workspaceSize, executor);
        },
        [&](void* workspace, uint64_t workspaceSize, aclOpExecutor* executor, aclrtStream callStream) {
            return aclnnMatmul(workspace, workspaceSize, executor, callStream);
        },
        stream);
}

int64_t ParseInteger(const char* value, const char* name)
{
    size_t consumed = 0;
    const std::string text(value);
    const auto result = std::stoll(text, &consumed);
    if (consumed != text.size() || result <= 0) {
        throw std::runtime_error(std::string(name) + " must be a positive integer");
    }
    return result;
}

}  // namespace

int main(int argc, char** argv)
{
    int64_t rows = 1;
    uint64_t seed = 1;
    for (int index = 1; index < argc; ++index) {
        const std::string argument(argv[index]);
        if (argument == "--m" && index + 1 < argc) {
            rows = ParseInteger(argv[++index], "--m");
        } else if (argument == "--seed" && index + 1 < argc) {
            seed = static_cast<uint64_t>(ParseInteger(argv[++index], "--seed"));
        } else {
            std::fprintf(stderr, "usage: %s [--m positive-int] [--seed positive-int]\n", argv[0]);
            return 64;
        }
    }
    if (rows != 1 && rows != 5 && rows != 8 && rows != 16) {
        std::fprintf(stderr, "--m must be one of 1, 5, 8, 16\n");
        return 64;
    }

    aclrtStream stream = nullptr;
    bool initialized = false;
    bool deviceSet = false;
    try {
        ACL_CHECK(aclInit(nullptr));
        initialized = true;
        ACL_CHECK(aclrtSetDevice(0));
        deviceSet = true;
        ACL_CHECK(aclrtCreateStream(&stream));

        int exitCode = 0;
        {
            const auto xHost = MakeData(rows * kHidden, seed ^ 0x11111111ULL, 0.10F);
            const auto gateUpHost = MakeData(kHidden * kGateUp, seed ^ 0x22222222ULL, 0.02F);
            const auto downHost = MakeData(kIntermediate * kOutput, seed ^ 0x33333333ULL, 0.02F);

            DeviceTensor x({rows, kHidden}, &xHost);
            DeviceTensor gateUpWeight({kHidden, kGateUp}, &gateUpHost);
            DeviceTensor downWeight({kIntermediate, kOutput}, &downHost);
            DeviceTensor candidate({rows, kOutput}, nullptr);
            DeviceTensor reference({rows, kOutput}, nullptr);
            DeviceTensor gateUp({rows, kGateUp}, nullptr);
            DeviceTensor activated({rows, kIntermediate}, nullptr);

            RunCandidate(x, gateUpWeight, downWeight, candidate, stream);
            RunReference(x, gateUpWeight, downWeight, gateUp, activated, reference, stream);

            const auto candidateHost = candidate.CopyToHost();
            const auto referenceHost = reference.CopyToHost();
            double maxAbs = 0.0;
            double squaredDifference = 0.0;
            double squaredReference = 0.0;
            int64_t nonFinite = 0;
            int64_t exact = 0;
            for (size_t index = 0; index < referenceHost.size(); ++index) {
                const double actual = Bf16ToFloat(candidateHost[index]);
                const double expected = Bf16ToFloat(referenceHost[index]);
                if (!std::isfinite(actual) || !std::isfinite(expected)) {
                    ++nonFinite;
                    continue;
                }
                const double difference = actual - expected;
                maxAbs = std::max(maxAbs, std::abs(difference));
                squaredDifference += difference * difference;
                squaredReference += expected * expected;
                exact += candidateHost[index] == referenceHost[index] ? 1 : 0;
            }
            const double relativeL2 =
                std::sqrt(squaredDifference) / std::max(std::sqrt(squaredReference), 1.0e-12);
            const bool passed =
                nonFinite == 0 && maxAbs <= kMaxAbsLimit && relativeL2 <= kRelativeL2Limit;
            std::printf(
                "{\"schema\":\"qwen35-t21-bf16-numerical/v1\",\"m\":%lld,"
                "\"seed\":%llu,\"hidden\":%lld,\"intermediate\":%lld,"
                "\"gate_up\":%lld,\"output\":%lld,\"non_finite\":%lld,"
                "\"max_abs\":%.10g,\"relative_l2\":%.10g,\"exact_fraction\":%.10g,"
                "\"max_abs_limit\":%.10g,\"relative_l2_limit\":%.10g,\"passed\":%s}\n",
                static_cast<long long>(rows), static_cast<unsigned long long>(seed),
                static_cast<long long>(kHidden), static_cast<long long>(kIntermediate),
                static_cast<long long>(kGateUp), static_cast<long long>(kOutput),
                static_cast<long long>(nonFinite), maxAbs, relativeL2,
                static_cast<double>(exact) / static_cast<double>(referenceHost.size()),
                kMaxAbsLimit, kRelativeL2Limit, passed ? "true" : "false");
            exitCode = passed ? 0 : 2;
        }

        ACL_CHECK(aclrtDestroyStream(stream));
        stream = nullptr;
        ACL_CHECK(aclrtResetDevice(0));
        deviceSet = false;
        ACL_CHECK(aclFinalize());
        initialized = false;
        return exitCode;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "ERROR: %s\n", error.what());
        if (stream != nullptr) {
            aclrtDestroyStream(stream);
        }
        if (deviceSet) {
            aclrtResetDevice(0);
        }
        if (initialized) {
            aclFinalize();
        }
        return 1;
    }
}
