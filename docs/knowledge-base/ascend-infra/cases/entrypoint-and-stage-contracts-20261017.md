# 真实入口与阶段契约

范围：2026-10-17，image660/vLLM-Ascend0.23/CANN9.1。这些是适配及验证程序的经验，不是论文或整模型验收通过。

## 导入与异常清理必须真实执行

BOLE factor repair1 实际1304在 Torch→dill→tempfile 导入时失败：根文件系统只读，未声明可写TMPDIR/HOME；算子调用数0。清理另遇inspect包装不接受cleanup=True。独立检查确认原CID已退出/Pid0/noExec/noOOM；原owner FAIL和secondary保留，不改为PASS。

证据：[故障与独立释放记录](../../../../.agents/workstreams/qwen36-damp-ascend-20261006/evidence/BOLE_FACTOR_AUTHORITY_REPAIR_20261017.json)。这是已证实的环境/回调适配缺陷，不是论文数值失败。

修复只在原唯一RW输出根下创建独占.tmp/.home，实际验证tempfile选址及写读，然后在相同镜像/只读根下导入Torch/dill；清理包装保留原参数及检查语义。实际131f已验证新repair2的正常启动退出0、故意异常退出3且secondary为空并释放、后续CPU阶段退出0。故意异常必须保留FAIL；这些不等于NPU或模型资格，超时路径也不能借用其PASS。

## 提前测试不能依赖未来绑定产物

后继真实1320/1322：256次物理NPU4调用及独立消费者完成。四个FIA选项各64行均复现原保存BF16结果bitwise64/64，也均有相同21行/52元素超原CPU64门。只改innerPrecise、sparse mode或paged/contiguous存储没有修复这些差异；停止无新证据重复这三开关。该结果不能解释首个FA之前的root-repeat输入差异，也不能宣称BOLE整模型通过或论文无效。

DeltaLog原R22实际1310：174项中171通过/3错误/noSkip。两项读取尚不存在的SOURCE_MANIFEST，一项要求/adakv-results临时目录但启动器给宿主长路径；另外owner的32MiB输出预算不足以容纳固定135520行、34,988,664字节的合成索引。保留原3错误及独立owner预算失败，不混为算法失败。

新R22repair1实际1319退出0，131a独立复核：提前阶段执行172项/noSkip，精确列出两个绑定依赖test ID；原模型CPU完整174项仍须在NPU前通过，未执行部分不能算PASS。提前阶段20.845566秒，精确CID d101cae59877c8c0d198e4a0afcb41f46b6146d18af384bd3dd7ca31da49150c 已确认停止/noExec/noOOM/Devices[]。

SOFTWARE.json：26492字节/SHA256 c88a907ee7dcc95bcc1be572a7675bec3d56dea71794ed82a394469bb017535d；位于/opt/host/vnf/austinov/run-dl-R22repair1-early-software-MAIN-RENEW24H_001/software/consumer/。不伪造绑定、不跳过最终门禁；唯一RW使用/adakv-results，消费者通过实际停止容器的CID/source与唯一RW映射解析精确别名，不全局替换。新128MiB输出预算不是原128MiB压力测试内存限制，数值和内存门未变。

## 源码反证：两个请求不自动覆盖物理槽位复用

实际image660 block_pool从空闲队列头分配、普通释放追加队尾；本模型FullAttention/Mamba释放没有使用sliding-window的prepend=True特例。pool32的两个短串行请求不能保证重分配首批物理块。旧双请求包已明确禁止启动；新自然压力协议须从真实容量、各角色块数及分配释放顺序推导，并检查实际映射，不修改分配器制造覆盖、不偷偷加请求、不放宽旧门。

来源为MAIN从本任务已停止image660容器只读取得的block_pool.py（SHA84755b84c36ed6460ceefe2690c9484a9c31488c5da6daa6c918f497d8837dee）、single_type_kv_cache_manager.py（SHAdc425e1e87b6157f3e5c46be2bfee54076ccb020b86c5a8aaa3d9901c75e46ef）。源码复制不是实际worker装载证明；运行仍须核对真实函数来源/hash。

## 下一次适配的最小闭环

1. 明确阶段生成/消费产物，DAG不得依赖未来文件。
2. 同镜像、解释器参数、权限、挂载及环境运行真实启用入口，不只测helper。
3. 核实生产者→消费者的Ref/值、宿主/容器路径、schema/参数类型，负向输入真实拒绝。
4. 分别验证成功、故意异常、超时释放；旧故障保留，修复新增精确回归。
5. 从真实分配器推导生命周期覆盖，再核实实际请求/物理槽位，测试数量不等于覆盖。
6. 部署前检查补丁头为root内相对路径、allowedPaths精确覆盖；MAIN本轮曾误传绝对头或错root，被拒且未编辑，属于控制端错误而非候选失败。只修补丁头，禁止全正文路径替换。
7. 软件通过仅推进到相关NPU门，NPU组件通过仅推进到整模型配对，不能跳到性能/精度结论。

知识库有效性看同类故障是否在昂贵阶段前被拦截，以及到整模型验收的有效进展，不看条目数和审计次数。

## 方法复制不是继承；源码编译上下文也是测试输入

触发：适配 monkeypatch 的类/方法身份，或以 CodeType 对比实际装载函数。

实际 BOLE1341 四个 worker 在 root witness 构造时拒绝，尚未进入新观测边界；原模型加载、health、原始保存并不构成数学通过。actual patch_qwen3_5 将 AscendGatedDeltaNetAttention.forward 复制给 QwenGatedDeltaNetAttention；两类直接继承同一个基类，并非彼此继承。原 isinstance(receiver, AscendClass) 是诊断代码适配缺陷，不能归为论文失效。修复须核对确切 target/receiver、四模块来源、赋值链、globals、原函数体及无 wrapper，不以泛 unwrap 或删身份门代替；逐谓词证据须在聚合拒绝之前持久化。

后继 repair1 已实际同镜像执行119项：118通过、1错误、无跳过；失败为 test_gdn_copy_identity 的 underlying_body。原来源未变，secondary为空，未进入NPU。独立本地 bundled Python3.12.14 再现，而3.9不再现：从整模块抽取部分 ClassDef 后编译，可能丢失 import 参与的编译器优化上下文，生成不同 LOAD_GLOBAL/LOAD_ATTR；不能据此判断真实装载函数被篡改。该本地反证尚不是目标3.12.13修复验收。

下一次不同做法：使用完整冻结源码编译得到的函数 CodeType，再配原 globals 构造软件 fixture；保留生产函数体身份检查。分别覆盖实际赋值链、错误 receiver/source/globals/body/wrapper 和不完整编译上下文反例；在目标解释器及同镜像执行真实 aggregate 入口。测试夹具通过不授予 worker/NPU/整模型资格，原失败结果必须保留。

具体证据、来源与未完成项见工作流 evidence/ROOT_WITNESS_AND_DL_PAYLOAD_20261017.json。验证本条知识看修复是否保留生产身份门且相同反例能在昂贵模型加载前拦截；修复与真实worker验证仍是待完成项。
