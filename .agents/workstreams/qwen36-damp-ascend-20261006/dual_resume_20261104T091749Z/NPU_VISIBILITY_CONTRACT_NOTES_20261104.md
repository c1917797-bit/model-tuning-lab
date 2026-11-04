# NPU visibility contract — evidence needed after V9

Public-source review only. This note does not establish any host runtime PASS.

V9 stopped at count==1 but did not record the actual count. Retain the assertion until evidence distinguishes count0 from count>1. Neither CPU reference ABI results nor a phase named NPU_OPERATOR establishes actual NPU arithmetic.

Official torch_npu2.10 device_count prefers HAL drvGetDevNum filtered by ASCEND_RT_VISIBLE_DEVICES, with a C++ aclrtGetDeviceCount fallback and initialized-state caching. Thus a manager-tool total is not sufficient to interpret this failed assertion.
- https://github.com/Ascend/pytorch/blob/v2.10.0/torch_npu/npu/__init__.py
- https://github.com/Ascend/pytorch/blob/v2.10.0/torch_npu/csrc/core/npu/NPUFunctions.cpp

ASCEND_VISIBLE_DEVICES is a Docker Runtime mount parameter; ASCEND_RT_VISIBLE_DEVICES selects logical compute devices and renumbers user indices. DCMI/management-tool enumeration is not proof of its compute visibility semantics.
- https://www.hiascend.com/doc_center/source/en/mindx-dl/300/dluserguide/clusterscheduling/dlug_guide_03_000105.html
- https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/910/maintenref/envvar/envref_07_0028.html

Next minimal diagnostic: record actual count, exact env repr, package/function/module origins, torch.npu versus torch_npu.npu identity, initialization/cache and HAL/fallback statuses before reference bootstrap and at the failed boundary. Use the same scoped container's clean process as a comparison. Import pollution is an unproved hypothesis, not an attribution.
Inspect Privileged, Devices, DeviceCgroupRules, runtime, mounts and actual node major/minor. A successful aclrtGetPhyDevIdByLogicDevId mapping logical0 to physical0 complements exact node/cgroup ownership evidence.
- https://www.hiascend.com/doc_center/source/zh/CANNCommunityEdition/910beta1/API/runtimeapi/aclcppdevg_03_2060.html
- https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities

Preparation lessons confirmed in this scope migration: update all real authority/size/hash/cutoff/device/lock/protection/readset operands together; preserve gamma inputs[4] and RAM constants; distinguish schema Ref descriptions from typed runtime Refs; treat freshly proved removed historical containers honestly instead of inventing inspect states; repeated observation receipts need unique immutable names; each actual retry needs fresh output/control/owner directories. These changes are control adaptation, not paper success.
