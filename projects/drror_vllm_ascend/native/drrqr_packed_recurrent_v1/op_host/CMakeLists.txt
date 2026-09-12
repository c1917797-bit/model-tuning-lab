add_op_to_compiled_list()

if (BUILD_OPEN_PROJECT)
    target_sources(op_host_aclnnExc PRIVATE
        drrqr_packed_recurrent_v1_def.cpp
    )
endif()

add_ops_compile_options(
    OP_NAME DrrqrPackedRecurrentV1
    OPTIONS
        --cce-auto-sync=on
        -Wno-deprecated-declarations
)

if (NOT BUILD_OPS_RTY_KERNEL)
    add_modules_sources(OPTYPE drrqr_packed_recurrent_v1 ACLNNTYPE aclnn_exclude)
    target_include_directories(${OPHOST_NAME}_tiling_obj PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
    )
endif()
