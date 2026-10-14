# 架构、递推、三角系统与数值

## A1. 先区分 full attention 与 GDN

**适用**：选题、接入 attention/state 优化、估算混合模型成本。

full attention 是因果 softmax 加权历史 V；decode 要读取随上下文增长的 KV。GQA 共享 K/V heads，不能把 Q head 数等同于 KV 数。FlashAttention 是 IO-aware exact attention 的算法路线，不是删掉历史 tokens；PagedAttention 是 KV 分页/共享管理路线，不是新的注意力数学。[FlashAttention](https://arxiv.org/abs/2205.14135)、[PagedAttention](https://arxiv.org/abs/2309.06180)。论文的 GPU 收益不是本机测量。

GDN 则维护固定形状的矩阵状态。两类层共存时，“KV 少了多少”不等于“整个模型状态少了多少”；仅优化16层FA也不能假定覆盖48层GDN。反过来，GDN 算子加速也不会消除 FA、MLP 和 HCCL 成本。

**实现边界**：可改存储、搬运、kernel 分块和调度；不能仅凭模型名字把FA内核安装到GDN。先绑定 config→模型模块→worker hook→真实 operator。**最小反例**：插件 ON 时调用数为0或全部回退，计时即便更快也没有测到该机制。

## A2. Gated delta 的可审计递推

以下统一用列向量、状态 `S∈R^(Dv×Dk)`；文献或 runtime 转置布局必须显式转换。基于 [Gated Delta Networks，v3 Eq.10](https://arxiv.org/html/2412.06464v3) 的等价改写：

```
Sbar = alpha_t * Sprev
u_t  = beta_t * (v_t - Sbar @ k_t)
Snew = Sbar + u_t @ k_t.T
o_t  = Snew @ q_t
```

这是数学参考，不是直接可部署的 kernel。实际 runtime 的 g 可能是 log-decay，alpha=exp(g)；beta 的激活、Q/K normalization、q scale、conv 状态和输出 gate 必须以真实路径核实，不能重复激活或遗漏。GDN key/value heads 不相等时，每个 value head 的 key 映射也是语义的一部分。

**修改边界**：可重排等价运算、将状态延迟物化、融合中间搬运；不能把“用衰减后的 S 计算残差”换成未衰减的 S，或凭经验换 head 映射。**最小鉴别**：非零初态、alpha≠1、beta≠0、非正交keys、多valuehead、连续多步。零初态单步会隐藏衰减和初态错误。

**本文推导：延迟物化的结构**。设某次物化基态为 S0，a_t=∏alpha，则

`S_t = a_t*S0 + Σ_i (a_t/a_i)*u_i*k_i.T`。

注意 u_i 依赖当时完整逻辑状态，不能只用基态计算。比值形式要求alpha>0且累积乘积未下溢；实际零衰减/下溢时用区间乘积或重基态flush，不能做0/0。实现还要处理日志容量、槽位复用与 prefix 快照；“少写回 state”不是“删除 state”。[DeltaLog](https://arxiv.org/abs/2608.15533) 是对应论文方向；这里的展开式是本库解释，不代表已完整迁移作者实现。

## A3. 三角求逆为何出现在 chunkwise GDN

chunk 内的顺序 delta 更新可重写成三角系统。对严格下三角依赖 L，常见形式是 `M=I+L`，求 `M*X=B`；beta/decay 的左右乘法、packed 行布局和因果 mask 必须从实际 KKT/WY 构造映射，不能仅替换一个名称相近的 solve 函数。[GDN v3 §3.3 gated UT/WY推导](https://arxiv.org/html/2412.06464v3) 提供结构来源；该文Eq.6–9是未加入gate的DeltaNet前置，不能省略decay。 [稳定三角求逆](https://arxiv.org/abs/2605.21325) 提供优化路线。

**本文推导（精确实数算术）**：C阶严格下三角L满足L^C=0，因此

`(I+L)^(-1)=Σ_(j=0..C-1)(-L)^j`。

令P=-L，N项近似 `X_N=Σ_(j=0..N-1)P^j`，定义残差 `R_MX=I-M*X_N=P^N`。修正 `X'=X_N*(I+R_MX)` 满足新残差 `I-M*X'=R_MX²`。但浮点计算和不相容布局下，`I-MX`与`I-XM`对应的修正不能随意交换。

关键反例：严格下三角矩阵的谱半径恒为0，但有限次幂和范数仍可能大（非正规性）；“ρ(L)<1”不能证明低阶截断准确。扩大近似阶数会增加乘法、workspace和roundoff，不能因为精度变好就假定更快。[When Good Enough Is Optimal](https://arxiv.org/abs/2606.06034) 的量化GDN路线与本轮FP32候选有实现/硬件差异，必须单列。

**适配设计**：保留矩阵输入语义、active tile mask、tail有效长度、dtype、head映射；可改乘法树/块大小/UB复用与Ascend实现。partial chunk（如129=64+64+1）不可读取另一请求或padding垃圾。输出逆矩阵正确还需整个chunk输出、最终state、下一chunk/下一decode正确。

## A4. 误差不是一个 tolerance

**本文推导**：对线性系统，小残差表示后向一致性；前向误差还受到条件数和缩放影响。若 `X≈M^-1`，则 `M^-1-X=M^-1*(I-MX)`；因此不能只看 `I-MX` 小就认定输出和任务无损。

递推误差会被后续转移、q投影、层间非线性放大或衰减。保留四类检查：逆/solve残差；完整NPU输出；完整多步state与不活动槽位；最终任务得分。逐rank/逐case判定，均值不能掩盖一个失败rank。报告绝对、归一化RMS/范数、最大误差等预注册指标；近零分母的规则提前固定。

独立参考不要复用候选多项式或关键搬运；可用FP64顺序递推/三角前代。原生NPU也是被检查的对象，不是绝对真理：同时对原生和候选进行独立比较，分别标注原生舍入误差和新增误差。

bitwise重复验证适用于冻结实现的确定性回放要求；不证明它与dense语义相同。反之，数值接近不证明槽位串扰和图回放正确。用户“任务精度≤1%损失”不能改写成tensor tolerance=0.01。

## A5. 选题前的反事实检查

对于压缩/剪枝/近似：量化的是权重、激活、FA KV，还是GDN recurrent state？本机有相应存储及计算支持吗？2-bit打包节省字节不等于2-bit原生算力；解包/转置/重建成本应入账。对于Mamba/SSD论文，代数联系不等于相同ABI和state生命周期。[SSD/Mamba2](https://arxiv.org/abs/2405.21060) 的正确ID不是2406.02528。

把机制匹配和可获收益分开：匹配但不在关键路径，可能正确但无收益；路径匹配、数值失败，先归因当前实现；只有有效配置对照才能关闭该配置，不据此否定所有硬件/论文。
