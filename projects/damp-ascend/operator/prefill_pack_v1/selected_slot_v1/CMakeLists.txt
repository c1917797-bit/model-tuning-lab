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
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/../exact_float_div_bits.h" FLOAT_FROZEN_SHA)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/../../quantizer/exact_quantizer_bits.h" EXACT_FROZEN_SHA)
if(NOT FLOAT_FROZEN_SHA STREQUAL "bca2ab982ac57ebed71efa4145281b5ee37faa5ec46cc0beccddf9d83eb2ae04" OR
   NOT EXACT_FROZEN_SHA STREQUAL "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169")
    message(FATAL_ERROR "frozen exact-float / integer scalar-helper source mismatch")
endif()

option(DAMP_BUILD_SELECTED_PREFILL_V1 "Build experimental selected-slot prefill pack" OFF)
if(NOT DAMP_BUILD_SELECTED_PREFILL_V1)
    message(FATAL_ERROR "Selected-slot pack is default OFF; explicit opt-in is required")
endif()
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/../../quantizer/fast_integer_certificate/integer_certificate_ascendc.h" CERT_SHA)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/../../production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h" PLAN_SHA)
if(NOT CERT_SHA STREQUAL "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb" OR
   NOT PLAN_SHA STREQUAL "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc")
    message(FATAL_ERROR "frozen quantizer/geometry source mismatch")
endif()
find_package(ASC REQUIRED)

# [MODIFY] 工程名
project(qwen36_damp_selected_prefill_v1 LANGUAGES ASC CXX)
# NEW isolated exact-float prefill SR probe; frozen targets are not linked.

set(CMAKE_CXX_STANDARD 17)

set(ACL_INCLUDE_DIR "$ENV{ASCEND_HOME_PATH}/aarch64-linux/include")
set(ACL_LIB_DIR "$ENV{ASCEND_HOME_PATH}/lib64")

# Build only the independently named TORCH_LIBRARY module.  This experimental
# plugin must never replace the vendor op registry globally.

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c
        "import os, torch; print('DAMP_TORCH_CMAKE_PREFIX_PATH=' + os.path.realpath(torch.utils.cmake_prefix_path), flush=True)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE DAMP_TORCH_METADATA_STDOUT
    ERROR_VARIABLE DAMP_TORCH_METADATA_STDERR
    RESULT_VARIABLE DAMP_TORCH_METADATA_RESULT
    TIMEOUT 60
)
if(NOT DAMP_TORCH_METADATA_RESULT STREQUAL "0")
    message(FATAL_ERROR
        "Torch metadata discovery failed (${DAMP_TORCH_METADATA_RESULT}): "
        "${DAMP_TORCH_METADATA_STDERR}")
endif()
# torch import on this exact image writes an npu-smi warning to stdout. Extract
# only our marked metadata; never interpret the complete stdout as a path.
string(REGEX MATCH "(^|\n)DAMP_TORCH_CMAKE_PREFIX_PATH=([^\r\n]+)"
    DAMP_TORCH_METADATA_LINE "${DAMP_TORCH_METADATA_STDOUT}")
if(NOT DAMP_TORCH_METADATA_LINE)
    message(FATAL_ERROR "Torch metadata marker is missing from Python stdout")
endif()
set(TORCH_CMAKE_PREFIX_PATH "${CMAKE_MATCH_2}")
if(NOT IS_DIRECTORY "${TORCH_CMAKE_PREFIX_PATH}" OR
   NOT EXISTS "${TORCH_CMAKE_PREFIX_PATH}/Torch/TorchConfig.cmake")
    message(FATAL_ERROR
        "Python-selected TorchConfig.cmake does not exist: "
        "${TORCH_CMAKE_PREFIX_PATH}/Torch/TorchConfig.cmake")
endif()
find_package(Torch REQUIRED CONFIG
    PATHS "${TORCH_CMAKE_PREFIX_PATH}/Torch" NO_DEFAULT_PATH)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c
        "import os, torch_npu; print('DAMP_TORCH_NPU_PATH=' + os.path.realpath(os.path.dirname(torch_npu.__file__)), flush=True)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE DAMP_TORCH_NPU_METADATA_STDOUT
    ERROR_VARIABLE DAMP_TORCH_NPU_METADATA_STDERR
    RESULT_VARIABLE DAMP_TORCH_NPU_METADATA_RESULT
    TIMEOUT 60
)
if(NOT DAMP_TORCH_NPU_METADATA_RESULT STREQUAL "0")
    message(FATAL_ERROR
        "torch_npu metadata discovery failed (${DAMP_TORCH_NPU_METADATA_RESULT}): "
        "${DAMP_TORCH_NPU_METADATA_STDERR}")
endif()
string(REGEX MATCH "(^|\n)DAMP_TORCH_NPU_PATH=([^\r\n]+)"
    DAMP_TORCH_NPU_METADATA_LINE "${DAMP_TORCH_NPU_METADATA_STDOUT}")
if(NOT DAMP_TORCH_NPU_METADATA_LINE)
    message(FATAL_ERROR "torch_npu metadata marker is missing from Python stdout")
endif()
set(TORCH_NPU_PATH "${CMAKE_MATCH_2}")
if(NOT IS_DIRECTORY "${TORCH_NPU_PATH}/include" OR
   NOT IS_DIRECTORY "${TORCH_NPU_PATH}/lib" OR
   NOT EXISTS "${TORCH_NPU_PATH}/include/torch_npu/csrc/aten/CustomFunctions.h" OR
   NOT EXISTS "${TORCH_NPU_PATH}/lib/libtorch_npu.so")
    message(FATAL_ERROR "Python-selected torch_npu headers/library are missing: ${TORCH_NPU_PATH}")
endif()
set(TORCH_NPU_INCLUDE_DIRS ${TORCH_NPU_PATH}/include)
set(TORCH_NPU_LIBRARIES ${TORCH_NPU_PATH}/lib)

# [MODIFY] 所有 add_custom → <your_op>（保持 _ops 后缀）
add_library(qwen36_damp_selected_prefill_v1_ops SHARED
    op_extension/selected_prefill_torch.cpp
    op_extension/register.cpp
)

# Compile the wrapper as ASC because it includes the kernel definition and
# launches it with triple-chevron syntax.  Keeping both in one compilation unit
# is what permits RunOpApi to enqueue the launch without stream(true) flushing.
set_source_files_properties(
    op_extension/selected_prefill_torch.cpp
    PROPERTIES LANGUAGE ASC
)

target_include_directories(qwen36_damp_selected_prefill_v1_ops PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/op_kernel
    ${CMAKE_CURRENT_SOURCE_DIR}/op_extension
    ${TORCH_INCLUDE_DIRS}
    ${TORCH_NPU_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
    ${ACL_INCLUDE_DIR}
)

target_link_libraries(qwen36_damp_selected_prefill_v1_ops PRIVATE
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

target_link_directories(qwen36_damp_selected_prefill_v1_ops PRIVATE
    ${ACL_LIB_DIR}
    "$ENV{ASCEND_HOME_PATH}/aarch64-linux/lib64"
    ${TORCH_NPU_LIBRARIES}
)

target_compile_options(qwen36_damp_selected_prefill_v1_ops PRIVATE
    ${TORCH_CXX_FLAGS}
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>
)

message(STATUS "TORCH_LIBRARY module 'libqwen36_damp_selected_prefill_v1_ops.so' will be built")
