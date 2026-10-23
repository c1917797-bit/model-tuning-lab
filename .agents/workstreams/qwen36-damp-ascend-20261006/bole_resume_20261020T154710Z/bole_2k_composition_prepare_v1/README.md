# BOLE2k 六组件实际组合（纯 host、未准入）

本节点只验证代码适配能否在同一实际全文件映射上顺序组合，并完整还原原始字节。不是整源构建器，不产生 SOURCE_BOUND、MAIN review、authority、命令或设备操作。

## 固定实际来源与结果

入口 `python3 -I -B /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_2k_composition_prepare_v1/compose_components.py --check`。无参数默认 OFF；其他参数拒绝。

实际基线是 `formal_pair_ready_prepare_v1/strict-source-proposal-v3/PREPARED_PAIR.json` 中 BOLE 的完整402文件/306 Python文件，不是手工14文件子集。每个实际 Ref 均完整重读验证 path/bytes/SHA256；非Python文件保留不变。加入4个明确的资格observer/consumer依赖，然后依次运行原资格tap、geometry、snapshot、native-input、numeric2k、statecodec。最终409文件/313 Python文件均实际编译；每级保持独立renderer字典名字空间且不插入sys.path。

实际操作 `exec-0000000000000b28` 终态 exit0、12.860秒、stderr空：六级全部通过，逆序逐级调用实际 inverse/undo（没有inverse的tap/依赖只用完整前后字节delta），最终全部402父文件与键逐字节还原。实际负控：native-input缺geometry/snapshot前驱拒绝；逆向前字节漂移拒绝；错误真实rendererSHA拒绝；实际codec重复应用拒绝。污染/None renderer aliases及全sys.modules/sys.path恢复均核对。没有运行旧整套测试。

## 旧codec范围，不能自动追随新源码

本次固定提交 `6f8461ee834089fd57f945097eae22d58ae2b646` 的renderer 5444B SHA`1b0b923bf117dde24ad62910718a02836ff74fa3c83c16fe4c39a31072a90641`（通过git show读入内存），helper15394B SHA`b7bc24128b2ba3561a03a7f5cf5694258ab77c6d4d09b02f9b07eabd9a349e86`。其他组件均固定实际磁盘SHA，漂移即拒。

MAIN后来完成的CPU raw释放renderer5745B SHA`bc1fa64b1c792496a140f8a2e3ac9f139784cc288b87200db6f2881aeb20c7fa`不属于本次组合控制。其单独0b25证据不被本节点借用。将来整源必须显式使用新版本并绑定新的组合来源，不能把本次旧版PASS冒充新版证据。

## 最短整源路径与未覆盖项

当前只证明上述六个实际API没有exact-once或Python语法冲突，**whole2k_ready/source_bound/numerical_qualified/NPU/HTTP均false**。仍未接入：

1. Q.short8、render160真实whole2k producer/manifest/command；2048输入identity/profile/client需显式整源接线（此处基线manifest仍131，未改标签冒充2k）。
2. whole2k source-validator、有限clock/authority和MAIN实际source review；不替换source_validated、不自签任何票。
3. native2k prefill-first强request/完整token ID/实际页表geometry取证，以及同镜像Torch/ABI测试。
4. runtime_joint的host/HBM/磁盘/原始证据联合预留；raw_reservation目前仅helper存在，尚未接入真实sink。这里没有证明实际内存峰值或容量够用。
5. 新版CPU raw释放精确delta的最终整源组合绑定。
6. 独立真实2k NPU数值/多步状态、原生AR配对、预先冻结的多样负载、正式性能、GSM8K/HumanEval/MMLU smoke/full精度。

建议下一整源节点复用已有owner和validator：先在内存接Q的短8来源+已审输入delta/新版codec，完整反向还原并保留每级Ref；然后只补whole2k validator/clock与predevice调用链。实际前缀geometry与runtime_joint未满足必须硬拒，不能因本次组件组合通过而上卡。131历史资格不借给2k。

## 原始响应

初次六级探查0b24及最终实际控制0b28完整工具原始响应保存在外部证据JSON（见交接Ref），不是自写的PASS替代物。代码不复制完整source树、没有输出源码文件、没有device执行。外部大证据不进入源码提交。
