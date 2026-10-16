# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

# ============================================================================
# CMake 构建配置 - Ascend C Kernel 直调
# ============================================================================
#
# 目录结构:
#   op_kernel/     - NPU 计算层（tiling.h + kernel.asc）
#   op_host/       - Host 直调层（.asc 入口 + data_utils.h）
#   op_extension/  - PyTorch 接入层（torch.cpp + register.cpp + ops.h）
#   scripts/       - 测试脚本
#
# [MODIFY] 创建新算子时修改:
# 1. 所有 add_custom → <your_op>（add_custom 是整体算子名，_kernel/_host/_ops 是固定后缀）
# 2. target_compile_options 中的 --npu-arch
# ============================================================================

cmake_minimum_required(VERSION 3.16)

find_package(ASC REQUIRED)

# [MODIFY] 工程名
project(qwen36_gdn_deltalog_decode_split_scale_sidecar_v051 LANGUAGES ASC CXX)

set(CMAKE_CXX_STANDARD 17)

set(ACL_INCLUDE_DIR "$ENV{ASCEND_HOME_PATH}/aarch64-linux/include")
set(ACL_LIB_DIR "$ENV{ASCEND_HOME_PATH}/lib64")

# Build only the independently named TORCH_LIBRARY module.  This experimental
# plugin must never replace the vendor op registry globally.

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import torch; print(torch.utils.cmake_prefix_path)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE TORCH_CMAKE_PREFIX_PATH
)
find_package(Torch REQUIRED HINTS ${TORCH_CMAKE_PREFIX_PATH})

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import importlib.util, pathlib; s=importlib.util.find_spec('torch_npu'); assert s is not None and s.submodule_search_locations, 'torch_npu package missing'; p=pathlib.Path(list(s.submodule_search_locations)[0]).resolve(); assert (p/'include/torch_npu/csrc/core/npu/NPUStream.h').is_file(), 'NPUStream.h missing'; assert (p/'lib').is_dir(), 'torch_npu lib directory missing'; print(p)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE TORCH_NPU_PATH
    RESULT_VARIABLE TORCH_NPU_DISCOVERY_RESULT
    ERROR_VARIABLE TORCH_NPU_DISCOVERY_ERROR
)
if(NOT TORCH_NPU_DISCOVERY_RESULT EQUAL 0 OR TORCH_NPU_PATH STREQUAL "")
    message(FATAL_ERROR "torch_npu package-path discovery failed: ${TORCH_NPU_DISCOVERY_ERROR}")
endif()
if(NOT EXISTS "${TORCH_NPU_PATH}/include/torch_npu/csrc/core/npu/NPUStream.h" OR NOT IS_DIRECTORY "${TORCH_NPU_PATH}/lib")
    message(FATAL_ERROR "Invalid torch_npu include/lib closure at ${TORCH_NPU_PATH}")
endif()
set(TORCH_NPU_INCLUDE_DIRS ${TORCH_NPU_PATH}/include)
set(TORCH_NPU_LIBRARIES ${TORCH_NPU_PATH}/lib)

# [MODIFY] 所有 add_custom → <your_op>（保持 _ops 后缀）
add_library(qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_ops SHARED
    op_extension/qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_torch.cpp
    op_extension/register.cpp
)

# Compile the wrapper as ASC because it includes the kernel definition and
# launches it with triple-chevron syntax.  Keeping both in one compilation unit
# is what permits RunOpApi to enqueue the launch without stream(true) flushing.
set_source_files_properties(
    op_extension/qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_torch.cpp
    PROPERTIES LANGUAGE ASC
)

target_include_directories(qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_ops PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/op_kernel
    ${CMAKE_CURRENT_SOURCE_DIR}/op_extension
    ${TORCH_INCLUDE_DIRS}
    ${TORCH_NPU_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
    ${ACL_INCLUDE_DIR}
)

target_link_libraries(qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_ops PRIVATE
    torch_npu
    tiling_api
    register
    platform
    unified_dlog
    dl
    m
    graph_base
    ascendcl
    ascendc_runtime
)

target_link_directories(qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_ops PRIVATE
    ${ACL_LIB_DIR}
    "$ENV{ASCEND_HOME_PATH}/aarch64-linux/lib64"
    ${TORCH_NPU_LIBRARIES}
)

target_compile_options(qwen36_gdn_deltalog_decode_split_scale_sidecar_v051_ops PRIVATE
    ${TORCH_CXX_FLAGS}
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>
)

message(STATUS "TORCH_LIBRARY module 'libqwen36_gdn_deltalog_decode_split_scale_sidecar_v051_ops.so' will be built")
