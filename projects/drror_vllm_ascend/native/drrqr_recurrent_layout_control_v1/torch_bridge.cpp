/*
 * Plugin-owned, explicitly loaded PyTorch bridge for the DRRQR recurrent
 * layout control operator.  This file intentionally does not replace or
 * register anything in the upstream _C_ascend namespace.
 */
#include <limits.h>
#include <stdlib.h>

#include <dlfcn.h>
#include <mutex>
#include <string>

#include <torch/extension.h>

#include "aclnn_torch_adapter/op_api_common.h"

namespace drrqr_ascend_ext {
namespace {

std::mutex g_exact_opapi_mutex;
void* g_exact_opapi_handle = nullptr;
std::string g_exact_opapi_path;

std::string canonical_path(const std::string& path) {
    TORCH_CHECK(!path.empty() && path.front() == '/',
                "DRRQR op-api library path must be absolute");
    char resolved[PATH_MAX] = {};
    TORCH_CHECK(realpath(path.c_str(), resolved) != nullptr,
                "cannot resolve DRRQR op-api library: ", path);
    return std::string(resolved);
}

void* checked_symbol(void* handle, const char* name,
                     const std::string& expected_path) {
    dlerror();
    void* address = dlsym(handle, name);
    const char* error = dlerror();
    TORCH_CHECK(address != nullptr && error == nullptr,
                "missing symbol ", name, " in ", expected_path,
                error == nullptr ? "" : std::string(": ") + error);
    Dl_info info = {};
    TORCH_CHECK(dladdr(address, &info) != 0 && info.dli_fname != nullptr,
                "dladdr failed for ", name);
    TORCH_CHECK(canonical_path(info.dli_fname) == expected_path,
                "symbol ", name, " resolved outside configured library: ",
                info.dli_fname);
    return address;
}

void configure_exact_opapi(const std::string& path) {
    const std::string resolved = canonical_path(path);
    std::lock_guard<std::mutex> lock(g_exact_opapi_mutex);
    if (g_exact_opapi_handle != nullptr) {
        TORCH_CHECK(g_exact_opapi_path == resolved,
                    "DRRQR op-api library is already fixed to ",
                    g_exact_opapi_path);
        return;
    }
    void* handle = dlopen(resolved.c_str(), RTLD_NOW | RTLD_LOCAL);
    TORCH_CHECK(handle != nullptr, "dlopen failed for ", resolved, ": ",
                dlerror());
    checked_symbol(handle,
                   "aclnnDrrqrRecurrentLayoutControlV1GetWorkspaceSize",
                   resolved);
    checked_symbol(handle, "aclnnDrrqrRecurrentLayoutControlV1", resolved);
    g_exact_opapi_handle = handle;
    g_exact_opapi_path = resolved;
}

void* exact_symbol(const char* name) {
    std::lock_guard<std::mutex> lock(g_exact_opapi_mutex);
    TORCH_CHECK(g_exact_opapi_handle != nullptr,
                "configure_exact_opapi must be called before the DRRQR op");
    return checked_symbol(g_exact_opapi_handle, name, g_exact_opapi_path);
}

std::string configured_opapi_path() {
    std::lock_guard<std::mutex> lock(g_exact_opapi_mutex);
    return g_exact_opapi_path;
}

}  // namespace

#define DRRQR_EXEC_EXACT_NPU_CMD(aclnn_api, ...)                              \
  do {                                                                        \
    static const auto getWorkspaceSizeFuncAddr =                              \
        exact_symbol(#aclnn_api "GetWorkspaceSize");                           \
    static const auto opApiFuncAddr = exact_symbol(#aclnn_api);               \
    static const auto initMemAddr = GetOpApiFuncAddr("InitHugeMemThreadLocal");\
    static const auto unInitMemAddr =                                         \
        GetOpApiFuncAddr("UnInitHugeMemThreadLocal");                          \
    static const auto releaseMemAddr = GetOpApiFuncAddr("ReleaseHugeMem");    \
    auto acl_stream = c10_npu::getCurrentNPUStream().stream(false);           \
    uint64_t workspace_size = 0;                                              \
    uint64_t* workspace_size_addr = &workspace_size;                          \
    aclOpExecutor* executor = nullptr;                                        \
    aclOpExecutor** executor_addr = &executor;                                \
    InitHugeMemThreadLocal initMemFunc =                                      \
        reinterpret_cast<InitHugeMemThreadLocal>(initMemAddr);                \
    UnInitHugeMemThreadLocal unInitMemFunc =                                  \
        reinterpret_cast<UnInitHugeMemThreadLocal>(unInitMemAddr);            \
    if (initMemFunc) { initMemFunc(nullptr, false); }                         \
    auto converted_params =                                                   \
        ConvertTypes(__VA_ARGS__, workspace_size_addr, executor_addr);        \
    auto getWorkspaceSizeFunc =                                               \
        ConvertToOpApiFunc(converted_params, getWorkspaceSizeFuncAddr);       \
    auto workspace_status = call(getWorkspaceSizeFunc, converted_params);     \
    TORCH_CHECK(workspace_status == 0, "call " #aclnn_api                    \
                " GetWorkspaceSize failed, detail:", aclGetRecentErrMsg());   \
    void* workspace_addr = nullptr;                                           \
    at::Tensor workspace_tensor;                                              \
    if (workspace_size != 0) {                                                \
      at::TensorOptions options =                                             \
          at::TensorOptions(torch_npu::utils::get_npu_device_type());         \
      workspace_tensor = at::empty({static_cast<int64_t>(workspace_size)},    \
                                   options.dtype(at::kByte));                 \
      workspace_addr = const_cast<void*>(workspace_tensor.storage().data()); \
    }                                                                         \
    auto acl_call = [converted_params, workspace_tensor, workspace_addr,      \
                     workspace_size, acl_stream, executor]() mutable -> int { \
      typedef int (*OpApiFunc)(void*, uint64_t, aclOpExecutor*,               \
                               const aclrtStream);                            \
      OpApiFunc opApiFunc = reinterpret_cast<OpApiFunc>(opApiFuncAddr);       \
      auto api_ret = opApiFunc(workspace_addr, workspace_size, executor,      \
                               acl_stream);                                   \
      TORCH_CHECK(api_ret == 0, "call " #aclnn_api                           \
                  " failed, detail:", aclGetRecentErrMsg());                  \
      ReleaseConvertTypes(converted_params);                                  \
      ReleaseHugeMem releaseMemFunc =                                         \
          reinterpret_cast<ReleaseHugeMem>(releaseMemAddr);                   \
      if (releaseMemFunc) { releaseMemFunc(nullptr, false); }                 \
      return api_ret;                                                         \
    };                                                                        \
    at_npu::native::OpCommand cmd;                                            \
    cmd.Name(#aclnn_api);                                                     \
    cmd.SetCustomHandler(acl_call);                                           \
    cmd.Run();                                                                \
    if (unInitMemFunc) { unInitMemFunc(nullptr, false); }                     \
  } while (false)

at::Tensor recurrent_layout_control_v1(
    const at::Tensor& query,
    const at::Tensor& key,
    const at::Tensor& value,
    at::Tensor& state,
    const c10::optional<at::Tensor>& beta,
    const c10::optional<double> scale,
    const c10::optional<at::Tensor>& actual_seq_lengths,
    const c10::optional<at::Tensor>& ssm_state_indices,
    const c10::optional<at::Tensor>& num_accepted_tokens,
    const c10::optional<at::Tensor>& g,
    const c10::optional<at::Tensor>& gk) {
    TORCH_CHECK(scale.has_value(), "scale cannot be empty");
    auto output = at::empty(value.sizes(),
                            value.options().dtype(at::ScalarType::BFloat16));
    float scale_real = static_cast<float>(scale.value());
    DRRQR_EXEC_EXACT_NPU_CMD(aclnnDrrqrRecurrentLayoutControlV1,
                            query, key, value, beta, state,
                            actual_seq_lengths, ssm_state_indices, g, gk,
                            num_accepted_tokens, scale_real, output);
    return output;
}

}  // namespace drrqr_ascend_ext

TORCH_LIBRARY(drrqr_ascend, m) {
    m.def(
        "recurrent_layout_control_v1(Tensor query, Tensor key, Tensor value, "
        "Tensor(a!) state, *, Tensor? beta=None, float? scale=None, "
        "Tensor? actual_seq_lengths=None, Tensor? ssm_state_indices=None, "
        "Tensor? num_accepted_tokens=None, Tensor? g=None, Tensor? gk=None) "
        "-> Tensor");
}

TORCH_LIBRARY_IMPL(drrqr_ascend, PrivateUse1, m) {
    m.impl("recurrent_layout_control_v1",
           &drrqr_ascend_ext::recurrent_layout_control_v1);
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("configure_exact_opapi",
          &drrqr_ascend_ext::configure_exact_opapi);
    m.def("configured_opapi_path",
          &drrqr_ascend_ext::configured_opapi_path);
}
