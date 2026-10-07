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
project(qwen36_native_recurrent_copy_trace_v2 LANGUAGES ASC CXX)

set(CMAKE_CXX_STANDARD 17)

set(ACL_INCLUDE_DIR "$ENV{ASCEND_HOME_PATH}/aarch64-linux/include")
set(ACL_LIB_DIR "$ENV{ASCEND_HOME_PATH}/lib64")

# Build only the independently named TORCH_LIBRARY module.  This experimental
# plugin must never replace the vendor op registry globally.

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import torch; print('KVBP_PATH='+torch.utils.cmake_prefix_path)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE TORCH_CMAKE_RAW
    RESULT_VARIABLE TORCH_CMAKE_RESULT
)
if(NOT TORCH_CMAKE_RESULT EQUAL 0)
    message(FATAL_ERROR "Torch metadata process failed")
endif()
string(REGEX MATCH "KVBP_PATH=([^\r\n]+)" _ "${TORCH_CMAKE_RAW}")
set(TORCH_CMAKE_PREFIX_PATH "${CMAKE_MATCH_1}")
if(NOT IS_DIRECTORY "${TORCH_CMAKE_PREFIX_PATH}")
    message(FATAL_ERROR "Torch metadata marker path missing")
endif()
find_package(Torch REQUIRED HINTS ${TORCH_CMAKE_PREFIX_PATH})

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import os, torch_npu; print('KVBP_PATH='+os.path.dirname(torch_npu.__file__))"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE TORCH_NPU_RAW
    RESULT_VARIABLE TORCH_NPU_RESULT
)
if(NOT TORCH_NPU_RESULT EQUAL 0)
    message(FATAL_ERROR "Torch NPU metadata process failed")
endif()
string(REGEX MATCH "KVBP_PATH=([^\r\n]+)" _ "${TORCH_NPU_RAW}")
set(TORCH_NPU_PATH "${CMAKE_MATCH_1}")
if(NOT IS_DIRECTORY "${TORCH_NPU_PATH}")
    message(FATAL_ERROR "Torch NPU metadata marker path missing")
endif()
set(TORCH_NPU_INCLUDE_DIRS ${TORCH_NPU_PATH}/include)
set(TORCH_NPU_LIBRARIES ${TORCH_NPU_PATH}/lib)

# [MODIFY] 所有 add_custom → <your_op>（保持 _ops 后缀）
add_library(qwen36_native_recurrent_copy_trace_v2_ops SHARED
    op_extension/qwen36_native_recurrent_copy_trace_v2_torch.cpp
    op_extension/register.cpp
)

# Compile the wrapper as ASC because it includes the kernel definition and
# launches it with triple-chevron syntax.  Keeping both in one compilation unit
# is what permits RunOpApi to enqueue the launch without stream(true) flushing.
set_source_files_properties(
    op_extension/qwen36_native_recurrent_copy_trace_v2_torch.cpp
    PROPERTIES LANGUAGE ASC
)

target_include_directories(qwen36_native_recurrent_copy_trace_v2_ops PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/op_kernel
    ${CMAKE_CURRENT_SOURCE_DIR}/op_extension
    ${TORCH_INCLUDE_DIRS}
    ${TORCH_NPU_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
    ${ACL_INCLUDE_DIR}
)

target_link_libraries(qwen36_native_recurrent_copy_trace_v2_ops PRIVATE
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

target_link_directories(qwen36_native_recurrent_copy_trace_v2_ops PRIVATE
    ${ACL_LIB_DIR}
    "$ENV{ASCEND_HOME_PATH}/aarch64-linux/lib64"
    ${TORCH_NPU_LIBRARIES}
)

target_compile_options(qwen36_native_recurrent_copy_trace_v2_ops PRIVATE
    ${TORCH_CXX_FLAGS}
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>
)

message(STATUS "TORCH_LIBRARY module 'libqwen36_native_recurrent_copy_trace_v2_ops.so' will be built")
