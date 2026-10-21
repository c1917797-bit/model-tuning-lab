# 交接：Paper-to-Ascend 0909 NPU 4-7

接收聊天 threadId：01a13944-6558-7f20-b211-f98c3163214b。按用户明确授权交接。
本端已停止新增实验、源码修改、准备任务续派和调度；不停止已准入控制器，不删除容器或证据，不延长窗口，不另发跨聊天消息。队列仅供接收端接手，不是后台调度。
运行状态以同目录 JSON 的 fresh_state 时间戳为准。本文保存前的初次观察是2026-10-21 09:04:50 UTC。

## 位置、提交与边界

主机 chicaihong01/ma；awmcp peer lgw_a6109c51076a4a2c9d2674ca5a8704a0。
规范仓库 /opt/host/vnf/austinov/model-tuning-lab。
分支 work/qwen36-damp-ascend-20261006。
交接前源码/证据提交 0321f257eb534d24b5097dd788947c624479e8cd（V30，285文件）。
本次交接MD/JSON单独提交；用 git log -1 -- 本文件相对路径查交接提交。
工作目录：
/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z

最新工作备份 CURRENT_NEXT_BACKUP_V30.json：11261 bytes，sha256 ba963be5b2188425f15bacf782eb5d4d0439f79346dc63113f744819b355122c。
父级HANDOFF.md和两份既有skill有其他工作区修改，未纳入本端提交；不得覆盖/reset。其他未跟踪文件未动。
已知push阻塞：HTTPS缺username、SSH22 timeout；本次未重试、改认证或保存凭据。代码/证据/交接均保留在主机规范仓库。
4个原准备子代理均completed，没有继续派发。旧awmcp operation可能过期，以保留文件为准。

不可延长的原截止：1792597630 = 2026-10-21 15:47:10 UTC。
原phase3600秒、共享cleanup180秒；新准入必须剩余完整3780秒，不重置入口clock。现unit RuntimeMaxSec3900/TimeoutStopSec180/Restart=no。
仅物理NPU4–7→guest0–3；物理0–3受保护。不reset设备，不改HugeTLB，不停外来进程。
固定CPU集合{0,1,2,3,144,145,166}，宿主元数据CPU166/512MiB。
当前串行GDN模型CPU0,1,2,3/quota4/32GiB，CPU角色CPU0/quota1/8GiB/Devices[]。G2/G3并发流式角色配置不同，不能套用GDN profile。
image sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1。
guest Python3.12 -B并source CANN9.1 set_env.sh，不可加-I；host -I -B。
host AS soft512MiB/hard infinity；Docker/Go子进程AS恢复infinity、实际RSS仍≤512MiB。大型原始rank约604MB，必须完整流式SHA，不能read_bytes。
observer96固定最多96 units、discovery1MiB/总4MiB，完整发现/全量读取/PID0/新鲜≤60秒；超界必须拒绝，不能抽样、截断或自动扩上限。

## 唯一已准入任务及MAIN

unit bole-gdn-candidate-v5-model-20261020t154710z.service，2026-10-21 08:52:06 UTC启动。
09:04:50初次观察：active/running，MainPID764682/ControlPID0；NPU模型容器已停止，Devices[]独立CPU consumer仍运行，最终RESULT尚不存在。JSON保存时再次观察可能已更新。

MAIN锁：工作目录/MAIN_ADMISSION.lock，device64774，inode8405603，/proc/locks key fd:06:8405603。
当时FLOCK ADVISORY WRITE由父PID764682/FD3持有，argv为candidate-v5/host_service.py --execute --source-ref完整Ref3 --output run-bole-gdn-g1-probe-candidate-v5。
不要删除锁文件、加第二把锁、启动第二调度器、reset unit或杀父进程。
父控制器按原预算完成所有owned cleanup并写RESULT后退出，FD/flock自然释放。
RemainAfterExit=yes意味着正常终态为active/exited，MainPID=ControlPID=0；不能把该终态误判为仍运行。
下一准入还需核对RESULT primary/secondary/source相等、所有owned stopped+retained/PID0/noOOM/empty ExecIDs，以及fresh完整observer与MAIN空闲。

| 角色 | CID | 初次观察 |
|---|---|---|
| CPU parser/software | f8c2c721b3087cb5649d863de5bbcb2be18bf0b08ae38103cbff2e4520000d54 | stopped/PID0/noOOM |
| 四卡模型 | bb9367d6fb02d1bed4e402b83757024b66f42f6443941835ebbde57ab760aec2 | stopped/PID0/noOOM |
| CPU independent | 4bdd290bfba672bab7fdb8baa278305ab3df625383ac1d7d7d2848214c247e84 | running/init PID900390 |

当时CPU consumer ExecID b64200594f13e105aa60167bdeaf0766b1a85fea4191fa807b5af9fdc0028d43。
stopped init的137退出码不是OOM结论，须核对实际OOMKilled及cleanup receipt。

结果根 /opt/host/vnf/austinov/run-bole-gdn-g1-probe-candidate-v5。
最终 RESULT.json，消费结果 cpu-consumer/gdn/GDN-INDEPENDENT.json，四rank数值报告由其完整Ref定位。
提交operation exec-000000000000040b已经completed0，不是活实验句柄；真正实验由systemd承载。
其他已完成句柄：0414 matched metadata v4、0415 G3 v2 OFF/help准备、0417 AR174只读复制、041a只读源码、041b V30提交、041d有界交接观察。完整exec前缀为exec-000000000000。
041c全仓status导致工具stdout截断，041d已完整替代；两者只读。无本端第二资源owner或后台调度。

## 已验证与未验证

G2 source13：
- 实际两请求各4token+barrier、四rank ACK/HTTP/retirement/native MTP load通过，4088源前后相等。
- G2_V13_MODEL_METADATA_READBACK.json独立读取4556保留引用，1240436 bytes，sha989edb4d558c0006327ee3b1e432263a7090a80cda8e196147966f102481c7a0。
- 只证明该短流，不是1024/EOS/任务/性能。

GDN matched-v5：
- 实际384帧=4rank×2request×48层，O/P/U/selected原门限通过，732源相等，三个owned停止保留。
- GDN_MATCHED_V5_MODEL_METADATA_READBACK.json：170750 bytes，sha0c9425eed0337253bc33616f575198f422c7231eb97bb5219cb0dabcffd6aebc；独立reader v4重跑原源码/软件/组件/MTP load门、核对全部384及840引用通过。
- RESULT /opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v5/RESULT.json：238251 bytes，sha8bad263436d441dd1e84d0147788bd9ff2d04ccf77cb86f55c8335e41d0b5bd0。
- 两份image-only chunk.py/solve_tril.py共31121 bytes，从同一停止模型容器只读复制，完整SHA与四snapshot+四host_binding一致。这是事后复核证据，未追改原732输入。
- gdn_matched_v5_installed_sources_v2/PROJECTIONS.json：6136 bytes，sha24c624cbdf9b9fc859ad766a514c56aa63a9bf359ae000fed75e2659ab57f2be。
- reader v1猜错串行CPU数、v2缺宿主image源码、v3 CLI被数值循环变量覆盖，失败全部保留；v4实际通过。

GDN candidate-v5：
- 实际240同镜像软件+native parser通过，独立732源/738引用通过，CPU helper停止。
- SOURCE /opt/host/vnf/austinov/bole-gdn-g1-probe-candidate-v5/SOURCE_BOUND.json：118267 bytes，shaf4dca1e9a13efbe7921a2e6157e950d00727e634cc2b341e63eacbc1f3ded3f6。
- COMMANDS3868 bytes，sha5af4a0133bdb930c76a7faa398c476c65f42f56d06978573aec6147db4e157af。
- CPU RESULT /opt/host/vnf/austinov/run-bole-gdn-g1-probe-candidate-v5-CPU/RESULT.json：236687 bytes，shaca7658ba5d342670ef36b98d08d359fe7a3b67ddaf10b545ead764335c0ab6c6。
- GDN_CANDIDATE_V5_CPU_METADATA_READBACK.json：147317 bytes，shab388170cca91234305d881b02703c7bcf906c72a50ea1310261ca4c25aeedc2f。
- 当前MODEL结果及独立复核须接手端继续读取，不能以matched384替代candidate资格。

G3 v2：
- source gate全量current5017/required4647/parent4559通过，6项Parent/Prepare纯控件通过，host audit5118通过。
- SOURCE /opt/host/vnf/austinov/bole-g3-fixed1024-20261020T154710Z-v2/SOURCE_BOUND.json：1223544 bytes，shaca87c8547a449f71994866e191ee40816a1e52f395e68f752c092f8c58637a85。
- COMMANDS3575 bytes，shaaef7f66a2cccab96eea85de256808621a5e9f859e753cfb4ddfdd174069857b4。
- G3_SOURCE13_ACTUAL_SOURCE_PREPARATION_EXECUTION_V2.json、G3_ACTUAL13_PARENT_PREPARE_FIXTURE_CONTROLS_V2.json、G3_V2_HOST_SOURCE_AUDIT.json全部保留。
- submit_g3_v2_cpu_v1.py仅AST/OFF/help通过，unit not-found；实际381和1024均未准入/通过。
- v1 CPU在测试前因17个旧L4 actor未进入guest RO readset失败，原5000源相等、停止保留。v2仅把确切17 Ref加入builder deps及V.required，未放宽任何数学/资源门。

Native AR：
- 实际map诊断全176：174 overlay mapdev8:8/stat0:77且inode相等；1既有driver相等，1原允许vdso。诊断成功不是mapped identity pass。
- 已从停止的原CPU诊断容器whole-copy全部174 ELF，1267866920 bytes，最大280680576。原fingerprint/wholeSHA/ELF/buildID相等。
- 原Python实际PT_INTERP解析为/lib/ld-linux-aarch64.so.1，复制后完整SHA唯一join canonical /usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1。
- 实体 /opt/host/vnf/austinov/bole-native-ar-elf-bridge-v1，174 *.elf+PT_INTERP_exact_copy.elf，文件/目录0555；不要再修改。
- native_ar_elf_bridge_v1/CATALOG.json：320726 bytes，sha78e8a06c7e6e97b8565cef7f850d0fe17a91aad2aa98a95ab3aa24a484a2ece2。
- NATIVE_AR_EXACT174_ELF_COPY_EXECUTION_V1.json实际0，固定600秒内101.17秒完成复制/重开核对；没有create/start/exec容器或改镜像。文件系统对象已变化，不可声称inode不变。
- 174 canonical guest RO bind适配器、原CPU严格maps门、256 native调用都尚未准备/执行。本端收到交接后停止。

## 接收端队列与准确命令

以下需接收端确认接手后顺序执行，本端不代跑。

A. 只读等待当前控制器自然完成清理：

    /usr/bin/systemctl show bole-gdn-candidate-v5-model-20261020t154710z.service --property=Id,ActiveState,SubState,Result,ExecMainStatus,MainPID,ControlPID

完整结果/summary的有界读取命令在JSON next_commands.result_summary，避免把完整大JSON经小工具输出截断。RESULT不存在或MainPID不为0时不准入下一项。须核对真实GDN-INDEPENDENT及全部384指标、owner释放。

B. candidate MODEL通过后需一个新版本独立只读reader，当前尚无该文件。以已通过read_gdn_matched_v5_model_metadata_v4.py为模板，绑定candidate自己的SOURCE/RESULT/CID及两份精确installed-source投影，不能冒用matched的model_result/CID，不能取消未知Ref拒绝门。

C. A/B及全部原门通过后，可运行现成G3 v2 CPU提交控制器；它自行重读冻结输入/fixture/audit、fresh observer96、检查cutoff和单一MAIN外层flock：

    /usr/bin/python3 -I -B /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/submit_g3_v2_cpu_v1.py --execute --controller-ref '{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/submit_g3_v2_cpu_v1.py","bytes":8152,"sha256":"3827569bc92320c2175c0b75c14c7a4d858d1bd0bfb9e01e6fe7923ec9bc595c"}'

预期unit bole-g3-v2-cpu-20261020t154710z.service；
结果 /opt/host/vnf/austinov/run-bole-g3-fixed1024-20261020T154710Z-v2-CPU/RESULT.json。
全381、原parser和saved-v7 cold门真实通过后才准备一个有限1024 MODEL的新提交控制器；目前没有该提交器。不要直接运行缺外层锁的COMMANDS.CPU/model，不重用v1失败unit，不与本端并发调度。

D. Native AR后续需新版本显式声明174宿主源及canonical guest只读alias，原owned_create基线+174精确delta+完整argv inverse/实际Mounts闭包。解释器和loader要create前挂好，不能在活容器里替换。
保留原library_maps.py5771 bytes/sha b1a0231cfb11fcd9a18cc0153ad2fb93098d58dd7aba642c20ecf69438bbbc82的dev/inode/hash/ELF门。先Devices[]CPU原metadata实际通过，后physical4 singleton原128帧×two fillers=256调用。未知lazy dlopen继续拒绝、保留后新版本修复；不加cap/prefix豁免。

## 阻塞与最终成功条件

当前运行阻塞为candidate CPU独立消费/cleanup及父MAIN锁，fresh JSON可显示其是否已结束。
G3的381/1024实际验证尚未做。Native AR原16帧/32坐标失败未解，原 .001+.01*absTruth阈值不可改；fsum CPU对照不是native通过。
GDN v4曾因sourceio多末尾LF失败；v5恢复qualified1037字节后对照模型通过。G3/G2原sourceio1038属于另一谱系，不能统一去空白；frozen whole SHA必须保留，git diff例外已有精确审计。
正式任务15525行（1319/164/14042），Think OFF/正常EOS/max2048，百分比点及相对退化均≤1%；尚无全任务实际分数。
HE官方164题必须新remote版本严格sandbox：UID65534/env-i/dropALL/no-new-priv/Devices[]/netnone/privateIPC/ROroot/tmpfs256M/pids64/nofile128/fsize8MiB/runc/CPU145 quota1/memswap2GiB/exact3 public RO mounts；禁止宿主执行生成代码。旧本地版本不可达，不得发明hash。
正式性能：相同production/Capture OFF，3 paired固定1024 E2E，每对10*OFF>=11*ON；TTFT=首个非空token ID完整−POST，TPOT=(第1024−第1)/1023；同recv同时间，不插值。尚无正式三对结果。
formal_success/task_ready/performance_ready/native_AR_qualified/normal_EOS_qualified全部false。不得把源码、CPU、短流或诊断晋级为论文成功。

保存交接后本端不再做实验性写入；接收端以真实结果与规范仓库继续，截止和NPU保护边界不变。
