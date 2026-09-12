// Public-API PyTorch bridge for the pinned upstream SwigluGatedMlp operator.
//
// This file intentionally avoids vLLM-Ascend private adapter helpers. Tensor
// descriptors are built with the public ACL metadata API and execution is
// submitted to torch-npu's public current-stream API. The bridge contains no
// replacement matmul or activation implementation.

#include <ATen/ATen.h>
#include <c10/util/Exception.h>
#include <torch/extension.h>

#include <dlfcn.h>

#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "aclnn/acl_meta.h"
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "torch_npu/csrc/framework/OpCommand.h"

namespace {

using GetWorkspaceFn = aclnnStatus (*)(
    const aclTensor*, const aclTensor*, const aclTensor*, int64_t,
    aclTensor*, uint64_t*, aclOpExecutor**);
using ExecuteFn = aclnnStatus (*)(
    void*, uint64_t, aclOpExecutor*, aclrtStream);

struct OperatorApi {
    void* handle = nullptr;
    GetWorkspaceFn get_workspace = nullptr;
    ExecuteFn execute = nullptr;
};

OperatorApi& GetOperatorApi()
{
    static OperatorApi api;
    static std::once_flag once;
    std::call_once(once, [&]() {
        const char* configured = std::getenv("QWEN35_T21_OPAPI_LIBRARY");
        const char* library =
            configured == nullptr || configured[0] == '\0'
            ? "libcust_opapi.so"
            : configured;
        api.handle = dlopen(library, RTLD_NOW | RTLD_LOCAL);
        TORCH_CHECK(api.handle != nullptr,
                    "failed to load T21 upstream operator library ", library,
                    ": ", dlerror());
        api.get_workspace = reinterpret_cast<GetWorkspaceFn>(
            dlsym(api.handle, "aclnnSwigluGatedMlpGetWorkspaceSize"));
        api.execute = reinterpret_cast<ExecuteFn>(
            dlsym(api.handle, "aclnnSwigluGatedMlp"));
        TORCH_CHECK(api.get_workspace != nullptr && api.execute != nullptr,
                    "T21 upstream operator ABI symbols are missing from ",
                    library);
    });
    return api;
}

std::vector<int64_t> CopySizes(const at::Tensor& tensor)
{
    return {tensor.sizes().begin(), tensor.sizes().end()};
}

std::vector<int64_t> CopyStrides(const at::Tensor& tensor)
{
    return {tensor.strides().begin(), tensor.strides().end()};
}

bool IsZeroOffsetContiguous(const at::Tensor& tensor)
{
    return tensor.storage_offset() == 0 && tensor.is_contiguous();
}

bool IsZeroOffsetDenseTranspose2d(const at::Tensor& tensor)
{
    return tensor.dim() == 2 && tensor.storage_offset() == 0 &&
           tensor.stride(0) == 1 &&
           tensor.stride(1) == tensor.size(0);
}

std::vector<int64_t> StorageDims(const at::Tensor& tensor)
{
    if (IsZeroOffsetContiguous(tensor)) {
        return CopySizes(tensor);
    }
    if (IsZeroOffsetDenseTranspose2d(tensor)) {
        return {tensor.size(1), tensor.size(0)};
    }
    TORCH_CHECK(false,
                "T21 bridge accepts only zero-offset contiguous tensors or ",
                "zero-copy 2-D transposes of contiguous storage; sizes=",
                tensor.sizes(), " strides=", tensor.strides(),
                " storage_offset=", tensor.storage_offset());
}

class PublicAclTensor {
public:
    explicit PublicAclTensor(const at::Tensor& tensor)
        : sizes_(CopySizes(tensor)), strides_(CopyStrides(tensor)),
          storage_dims_(StorageDims(tensor))
    {
        TORCH_CHECK(tensor.scalar_type() == at::ScalarType::BFloat16,
                    "T21 bridge requires BF16 tensors");
        TORCH_CHECK(tensor.device().type() == c10::DeviceType::PrivateUse1,
                    "T21 bridge requires NPU tensors");
        tensor_ = aclCreateTensor(
            sizes_.data(), sizes_.size(), ACL_BF16, strides_.data(),
            tensor.storage_offset(), ACL_FORMAT_ND, storage_dims_.data(),
            storage_dims_.size(), const_cast<void*>(tensor.const_data_ptr()));
        TORCH_CHECK(tensor_ != nullptr, "aclCreateTensor returned null");
    }

    PublicAclTensor(const PublicAclTensor&) = delete;
    PublicAclTensor& operator=(const PublicAclTensor&) = delete;

    ~PublicAclTensor()
    {
        if (tensor_ != nullptr) {
            aclDestroyTensor(tensor_);
        }
    }

    aclTensor* get() const { return tensor_; }

private:
    std::vector<int64_t> sizes_;
    std::vector<int64_t> strides_;
    std::vector<int64_t> storage_dims_;
    aclTensor* tensor_ = nullptr;
};

void CheckInputs(const at::Tensor& x,
                 const at::Tensor& gate_up_weight,
                 const at::Tensor& down_weight)
{
    TORCH_CHECK(x.dim() == 2 && gate_up_weight.dim() == 2 &&
                    down_weight.dim() == 2,
                "T21 bridge requires three rank-2 tensors");
    TORCH_CHECK(x.device() == gate_up_weight.device() &&
                    x.device() == down_weight.device(),
                "T21 bridge tensors must be on the same NPU");
    TORCH_CHECK(x.scalar_type() == at::ScalarType::BFloat16 &&
                    gate_up_weight.scalar_type() == at::ScalarType::BFloat16 &&
                    down_weight.scalar_type() == at::ScalarType::BFloat16,
                "T21 bridge requires BF16 tensors");
    TORCH_CHECK(x.size(0) >= 1 && x.size(0) <= 16,
                "T21 bridge is gated to decode/small-batch M in [1,16]");
    TORCH_CHECK(x.size(1) == 5120 &&
                    gate_up_weight.sizes() == at::IntArrayRef({5120, 8704}) &&
                    down_weight.sizes() == at::IntArrayRef({4352, 5120}),
                "T21 bridge shape contract is Qwen3.5-27B BF16 TP4 only");
    TORCH_CHECK(gate_up_weight.size(1) == 2 * down_weight.size(0),
                "gate/up width must be twice the local intermediate width");
}

at::Tensor SwigluGatedMlp(const at::Tensor& x,
                          const at::Tensor& gate_up_weight,
                          const at::Tensor& down_weight)
{
    CheckInputs(x, gate_up_weight, down_weight);
    auto output = at::empty({x.size(0), down_weight.size(1)}, x.options());
    auto acl_x = std::make_shared<PublicAclTensor>(x);
    auto acl_gate_up = std::make_shared<PublicAclTensor>(gate_up_weight);
    auto acl_down = std::make_shared<PublicAclTensor>(down_weight);
    auto acl_output = std::make_shared<PublicAclTensor>(output);

    auto& api = GetOperatorApi();
    uint64_t workspace_size = 0;
    aclOpExecutor* executor = nullptr;
    const auto prepare_status = api.get_workspace(
        acl_x->get(), acl_gate_up->get(), acl_down->get(), 1,
        acl_output->get(),
        &workspace_size, &executor);
    TORCH_CHECK(prepare_status == 0,
                "aclnnSwigluGatedMlpGetWorkspaceSize failed: ",
                prepare_status);

    at::Tensor workspace;
    void* workspace_address = nullptr;
    if (workspace_size != 0) {
        workspace = at::empty(
            {static_cast<int64_t>(workspace_size)},
            x.options().dtype(at::ScalarType::Byte));
        workspace_address = workspace.mutable_data_ptr();
    }
    const auto stream =
        c10_npu::getCurrentNPUStream(x.get_device()).stream(false);
    auto execute = api.execute;
    auto acl_call = [execute, workspace_address, workspace_size, executor,
                     stream, workspace, x, gate_up_weight, down_weight, output,
                     acl_x, acl_gate_up, acl_down, acl_output]() -> int {
        return execute(workspace_address, workspace_size, executor, stream);
    };
    // Match torch-npu's official ACLNN scheduling seam so the custom call is
    // ordered with the host task queue. Captures keep tensors, workspace, and
    // public ACL descriptors alive until the queued callable is consumed.
    at_npu::native::OpCommand::RunOpApiV2(
        "aclnnSwigluGatedMlp", acl_call);
    return output;
}

bool SupportsLayout(const at::Tensor& tensor)
{
    return IsZeroOffsetContiguous(tensor) ||
           IsZeroOffsetDenseTranspose2d(tensor);
}

at::Tensor SwigluGatedMlpMeta(const at::Tensor& x,
                              const at::Tensor& gate_up_weight,
                              const at::Tensor& down_weight)
{
    TORCH_CHECK(x.dim() == 2 && gate_up_weight.dim() == 2 &&
                    down_weight.dim() == 2,
                "T21 bridge meta kernel requires rank-2 tensors");
    TORCH_CHECK(gate_up_weight.size(0) == x.size(1),
                "T21 bridge meta gate/up K mismatch");
    TORCH_CHECK(gate_up_weight.size(1) == 2 * down_weight.size(0),
                "T21 bridge meta intermediate-width mismatch");
    return at::empty({x.size(0), down_weight.size(1)}, x.options());
}

}  // namespace

TORCH_LIBRARY(qwen35_t21, module)
{
    module.def(
        "swiglu_gated_mlp(Tensor x, Tensor gate_up_weight, "
        "Tensor down_weight) -> Tensor");
}

TORCH_LIBRARY_IMPL(qwen35_t21, PrivateUse1, module)
{
    module.impl("swiglu_gated_mlp", &SwigluGatedMlp);
}

TORCH_LIBRARY_IMPL(qwen35_t21, Meta, module)
{
    module.impl("swiglu_gated_mlp", &SwigluGatedMlpMeta);
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module)
{
    module.def("swiglu_gated_mlp", &SwigluGatedMlp,
               "Qwen3.5 TP4 upstream SwigluGatedMlp through public ACL APIs");
    module.def("supports_layout", &SupportsLayout,
               "Return whether the public ACL descriptor bridge supports a layout");
}
