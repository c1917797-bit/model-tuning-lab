# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

# Modified 2026-10-06: independently named test-only reference target.
cmake_minimum_required(VERSION 3.16)

find_package(ASC REQUIRED)

project(qwen36_damp_native_reference LANGUAGES ASC CXX)

set(CMAKE_CXX_STANDARD 17)

set(ACL_INCLUDE_DIR "$ENV{ASCEND_HOME_PATH}/aarch64-linux/include")
set(ACL_LIB_DIR "$ENV{ASCEND_HOME_PATH}/lib64")

option(DAMP_BUILD_NATIVE_REFERENCE "Explicit test-only native-derived reference" OFF)
if(NOT DAMP_BUILD_NATIVE_REFERENCE)
    message(FATAL_ERROR "Reference target is test-only; pass -DDAMP_BUILD_NATIVE_REFERENCE=ON explicitly")
endif()
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -c
        "import os, torch; print('DAMP_REFERENCE_TORCH_CMAKE_PREFIX_PATH=' + os.path.realpath(torch.utils.cmake_prefix_path), flush=True)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE DAMP_REFERENCE_TORCH_METADATA_STDOUT
    ERROR_VARIABLE DAMP_REFERENCE_TORCH_METADATA_STDERR
    RESULT_VARIABLE DAMP_REFERENCE_TORCH_METADATA_RESULT
    TIMEOUT 60
)
if(NOT DAMP_REFERENCE_TORCH_METADATA_RESULT STREQUAL "0")
    message(FATAL_ERROR
        "Torch metadata discovery failed (${DAMP_REFERENCE_TORCH_METADATA_RESULT}): "
        "${DAMP_REFERENCE_TORCH_METADATA_STDERR}")
endif()
# torch import on this exact image writes an npu-smi warning to stdout. Extract
# only our marked metadata; never interpret the complete stdout as a path.
string(REGEX MATCH "(^|\n)DAMP_REFERENCE_TORCH_CMAKE_PREFIX_PATH=([^\r\n]+)"
    DAMP_REFERENCE_TORCH_METADATA_LINE "${DAMP_REFERENCE_TORCH_METADATA_STDOUT}")
if(NOT DAMP_REFERENCE_TORCH_METADATA_LINE)
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
        "import os, torch_npu; print('DAMP_REFERENCE_TORCH_NPU_PATH=' + os.path.realpath(os.path.dirname(torch_npu.__file__)), flush=True)"
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE DAMP_REFERENCE_TORCH_NPU_METADATA_STDOUT
    ERROR_VARIABLE DAMP_REFERENCE_TORCH_NPU_METADATA_STDERR
    RESULT_VARIABLE DAMP_REFERENCE_TORCH_NPU_METADATA_RESULT
    TIMEOUT 60
)
if(NOT DAMP_REFERENCE_TORCH_NPU_METADATA_RESULT STREQUAL "0")
    message(FATAL_ERROR
        "torch_npu metadata discovery failed (${DAMP_REFERENCE_TORCH_NPU_METADATA_RESULT}): "
        "${DAMP_REFERENCE_TORCH_NPU_METADATA_STDERR}")
endif()
string(REGEX MATCH "(^|\n)DAMP_REFERENCE_TORCH_NPU_PATH=([^\r\n]+)"
    DAMP_REFERENCE_TORCH_NPU_METADATA_LINE "${DAMP_REFERENCE_TORCH_NPU_METADATA_STDOUT}")
if(NOT DAMP_REFERENCE_TORCH_NPU_METADATA_LINE)
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

add_library(qwen36_damp_native_reference_ops SHARED
    op_kernel/native_sr_reference_kernel.asc
    op_extension/native_sr_reference_torch.cpp
    op_extension/register.cpp
)

# C++ wrapper uses stream(true) direct launch, not ASC queued RunOpApi.
target_include_directories(qwen36_damp_native_reference_ops PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/op_kernel
    ${CMAKE_CURRENT_SOURCE_DIR}/op_extension
    ${TORCH_INCLUDE_DIRS}
    ${TORCH_NPU_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
    ${ACL_INCLUDE_DIR}
)

target_link_libraries(qwen36_damp_native_reference_ops PRIVATE
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

target_link_directories(qwen36_damp_native_reference_ops PRIVATE
    ${ACL_LIB_DIR}
    "$ENV{ASCEND_HOME_PATH}/aarch64-linux/lib64"
    ${TORCH_NPU_LIBRARIES}
)

target_compile_options(qwen36_damp_native_reference_ops PRIVATE
    ${TORCH_CXX_FLAGS}
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>
)

message(STATUS "TORCH_LIBRARY module 'libqwen36_damp_native_reference_ops.so' will be built")
