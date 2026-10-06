# tizen-headed-aarch64 mic 打包失败分析报告

日期：2026-10-06（Asia/Shanghai）。**stage2b阶段报告：在stage2a控制台/基线参数取证基础上，完成真gzip/pigz正常、EFBIG、SIGKILL及默认SIGXFSZ现场签名与原mic打包函数实验。真实镜像复现与源码patch未完成，资源触发原因尚未唯一确定。**

## 结论与置信度

1. **已确认，置信度高：mic 2.1.3 的打包错误处理丢失原始失败原因。** `archive._call_external` 捕获压缩进程 rc 和输出，gzip/pigz 等调用者丢弃；随后直接移动预期压缩文件。尚未创建输出的假gzip返回1（注入ENOSPC文本）与self-SIGKILL返回-9，都会变成相同的 `shutil.move` / `FileNotFoundError`。这是源码与实际探针共同闭合的代码缺陷，不等于已经查明真实worker资源失败原因。证据：[原始代码探针](../evidence/original_archive_probe.json)、[源码](../evidence/src_snapshot/mic/mic/archive.py) L66–110、327–348。
2. **已确认，置信度高：两份QB失败控制台均有FileNotFoundError traceback。** gzip启动到首traceback42.433秒，pigz29.828秒；两者均定位archive.py:346的shutil.move，随后mic返回1。公开mic.log仍只到压缩启动行，两个输出渠道不同。证据：1187398full-log.txt和1189686full-log.txt均L8878–8926、8936；[完整控制台取证](qb_console_forensics.md)。
3. **已确认，置信度高：“pigz几秒就被杀、mic死了”被否定。** mic在约30秒后抛异常并返回1，外层继续同步日志，再由QB标记普通失败；父1189639只传播这个子失败。不能把mic.log停止误判成进程停止；压缩器自身是否受SIGKILL仍无rc支持。证据：1189686full-log.txt L8878–8955、36–45；1189639full-log.txt L22536–22544。
4. **已确认，置信度高：旧流程额外保存完整 `.tar`，改用pigz没有消除这项磁盘压力。** `.tar`位于工作tmpdir的 `build/imgcreate-*/out`，不是最终CLI outdir。成功镜像逻辑量模型：旧约5.46GiB，流式约3.05GiB，差2.40GiB（不含缓存/bootstrap等，非实测）。证据：[磁盘模型](../evidence/disk_model.json)、[成功原始日志](../downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log) L7420–7427、[源码路径追踪](code_reading.md)。
5. **真实外部触发原因尚未闭合，置信度不足。** ENOSPC升为首选资源假设（中等置信）：真EFBIG写失败清理输出并得到QB同形FileNotFoundError；真中途SIGKILL留坏.gz，被mic直接move为成功，与QB不同。可捕获信号/配额/tar先失败等仍可能，打开输出前SIGKILL或外部删文件也未彻底排除。见 [现场签名实验](signature_experiment.md)。mic被直接杀死/步骤突然超时不符合真实控制台的异常与正常收尾。没有直接证据足以唯一判定资源触发，更不能据 `FileNotFoundError` 认定gzip被OOM杀。`rc=-9`即使拿到也只证明SIGKILL，还需内核/cgroup记录确定OOM来源。

## 证据对照表

|事实|构建机/cgroup OOM假设|工作目录ENOSPC假设|目前能否区分|
|---|---|---|---|
|两份QB控制台均traceback、mic返回1、QB普通failed链|不支持mic自己被直接杀死；子压缩器OOM仍未知|相容但没有资源实证|已区分mic异常退出与整步骤突然死亡；压缩器原因仍未知|
|真中途SIGKILL vs 真EFBIG写失败|两种真压缩器SIGKILL留坏.gz，被mic直接move|两种写失败都删除.gz并报FileNotFoundError|典型现场现在可区分；QB更吻合主动cleanup，ENOSPC中等置信，仍无直接errno|
|gzip通常数MiB RSS；本机探针1,804KiB|gzip自身占GiB的解释弱；cgroup页缓存/其他进程仍可能触发|先tar后gzip需要额外完整tar和gz空间|ENOSPC值得优先试验，未定性|
|0917、0930镜像体积相近，0930稍小|不足以说明worker内存充足|不足以说明当时工作盘剩余空间充足|须实际df/cgroup记录|
|0917、0930bootstrap源RPM完全相同|不支持bootstrap代码变化必然致OOM|也不支持bootstrap变化必然致ENOSPC|worker和包/宿主环境仍有差别|
|1003新增pigz2.8，日志确实用pigz|默认更多线程，量级可增加十几/几十MiB|仍落完整tar，磁盘峰值未消除|不是资源根因证据|
|没有worker dmesg/memory.events/df|缺直接OOM证据|缺直接磁盘满证据|必须补取|

原始事实范围：0930与1003日志L7360–7367；成功日志L7420–7441。更完整对照见 [日志取证](log_forensics.md)，新增QB完整打包尾段和逐关键词行号见 [控制台取证](qb_console_forensics.md)。

## 已取得材料及限制

- 三个日志：成功 [0917](../downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log)，失败 [0930 gzip](../downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log)、[1003 pigz](../downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log)。成功小文件和两份失败builddata ks都已取得，无需用成功ks替代失败ks；三份repomd.xml均HTTP200。URL、大小、sha256见 [下载清单](downloads.md)。未下载成功tar.gz实体。
- 成功gzip启动19:11:52 UTC，下一条manifest记录19:13:05，相隔73秒（包含返回/改名等间隙）；tar段15秒。目录列示tar.gz大小696,473,433字节（696.47MB，664.21MiB），见 [目录快照](../downloads/indexes/20260917.132101-images.html) L14。没有用日志间隔伪称精确压缩CPU时间。
- 四个QB页面只各请求一次，都跳转登录，返回的是登录HTML，不能当成image步骤日志：[请求与最终URL记录](../evidence/download_records.json)。这是stage1匿名访问的历史记录；stage2a用户新增五份控制台后，完整命令与两次真实traceback/状态已取得，worker内核日志仍没有。
- **成功ks的MD5不匹配发布MD5SUMS。** 期望`d6525a80cb6c07fc27554f093874d864`，当前下载得到`ba215c35a7b10975c6f69956528f81cc`；目录ks修改时间23:20晚于校验清单19:13。其余已下载且在MD5SUMS中可核验的packages、files、xml、manifest均匹配。因此不能认定当前ks是原构建输入的逐字节副本；原因可能是发布后修改，但没有修订记录，不能确定。证据：[MD5核验](../evidence/published_md5_check.json)、[目录快照](../downloads/indexes/20260917.132101-images.html) L5、10、[原始MD5SUMS](../downloads/logs/MD5SUMS)。未修改原文件来“配平”校验。
- 匿名Tizen Git访问失败。官方Ubuntu 24.04的mic2.1.3源码包解压于 `downloads/src/mic/`，对应.deb已下载并仅在目录内展开；两者archive.py的sha256相同。版本与日志相符，但现代Tizen Git commit和worker是否存在同版本本地修改未验证。旧Intel/Tizenorg Git镜像保留作来源说明，未拿旧版冒充2.1.3。
- 额外取得三个snapshot的bootstrap源码RPM。0917/0930相同commit且RPM字节相同；1003加入pigz2.8。spec只写无版本约束的`BuildRequires: mic`，不能仅据spec确认内嵌mic版本。三次日志L16都写复制宿主mic，L19均打印2.1.3。详见 [源码阅读](code_reading.md) 和 [三个bootstrap下载摘要](../evidence/more_downloads.json)。
- `sandbox/dkson95/clang`匿名未取得；GitHub旧镜像fetch返回missing remote ref。[尝试记录](../evidence/prepare_sources.json)。没有得到`packaging/patch_archive.py`，无法完成逐项实际评审。

stage2a2补充：第二次baseline的插件路径失败已通过本地入口早读全局-c修正，普通用户完整命令到root guard，另行确认loop导入和全部CONF键值，见 [基线修正](baseline.md)。官方mic入口/打包源码未修改，完整root基线仍未完成。

## 复现结果

|实验|状态|结果/限制|证据|
|---|---|---|---|
|磁盘预算|已记录|工作盘可用118,592,036,864字节，约110.45GiB；总内存31,540MiB，满足15GB预算|[本机环境](../evidence/environment.txt)|
|本地mic版本|已验证|官方源码直接运行显示2.1.3；系统尚未安装mic，官方.deb仅本地解包；未配置系统apt源以遵守目录限制|[版本输出](../evidence/mic-source-version.log)、[Ubuntu Packages](../downloads/tools-Packages) L506–517|
|旧archive fake gzip exit1|已执行，无需root|tuple含rc1和模拟ENOSPC文本，packing仍报FileNotFoundError，mic.log未记录原错误|[结果](../evidence/original_archive_probe.json)、[控制台](../evidence/original-exit1-console.log)|
|旧archive fake gzip SIGKILL|已执行，无需root|tuple rc=-9；同样缺文件异常与mic.log启动行结束；**没有复现OOM**|[结果](../evidence/original_archive_probe.json)、[控制台](../evidence/original-sigkill-console.log)|
|gzip/pigz2.8资源量级|已执行，无需root|64MiB随机数据，20CPU；gzip1,804KiB，pigz默认17,392KiB，p2为3,800KiB；p2节省13,592KiB；不是mic峰值|[量级探针](../evidence/compressor_probe.json)、[编译记录](../evidence/pigz-build.log)、[gzip time](../evidence/compressor-gzip.time.txt)、[默认pigz time](../evidence/compressor-pigz-default.time.txt)、[p2 time](../evidence/compressor-pigz-p2.time.txt)|
|sudo前置检查|失败，按指令停止|`sudo -n true`输出“sudo: a password is required”；没有尝试密码|[sudo输出](../evidence/sudo_check.txt)|
|首次aarch64基线|parser退出2；已修命令|此前-c与--non-interactive位置错误；新增release、对齐-o/-k；仅只读parser和help验证，未重跑镜像|[基线修正](baseline.md)、[验证](../evidence/baseline-command-validation.json)|
|真EFBIG/SIGKILL签名|已完成，无root|两种真压缩器22组含8组原mic函数；写失败删除输出，SIGKILL留坏输出且move True|[签名报告](signature_experiment.md)、[结果](../evidence/signature/results.json)|
|loop文件系统ENOSPC|未执行压缩|udisks免交互loop成功，但普通用户mount到工作目录失败；loop已删除；未用sudo/外部挂载目录|[尝试](../evidence/signature/udisks-enospc-attempt.json)|
|MemoryMax=1G/512M OOM|未执行|需要root；尚无谁被杀、kernel日志或形状匹配结论|—|
|新补丁fake gzip测试|未执行|新补丁尚未实施，不能把旧行为探针当作新补丁验证|—|

原始探针命令/输出/耗时保存在 [完整探针输出](../evidence/original_archive_probe.log) 及JSON，压缩器探针JSON内记录每条命令和耗时。最初两次探针测试驱动对mic日志handler重复设置失败，原输出分别保留在`evidence/original_archive_probe-first-attempt.log`、`evidence/original_archive_probe-second-attempt.log`；最终改为每种模式独立进程，最终探针成功。它们不属于真实mic失败证据。

由于没有真实ENOSPC/OOM试验，仍不能判定资源触发。stage2b已用真EFBIG重现缺文件形状，真中途SIGKILL反而留坏.gz并move成功；stage1 fake未创建输出便被杀，不能冒充真实中途SIGKILL签名。ENOSPC/OOM整镜像资源复现尚未成立。

## 代码问题与补丁方案

已确认问题：丢弃rc/stderr、末端move掩盖原因、完整中间tar放大磁盘需求、打包前缺工作文件系统预算/日志、mktemp名称竞争；解tar失败分支还有bytes/None join问题。空间检查在打包后向最终destdir交付阶段，无法保障工作盘压缩峰值。具体文件和行号见 [源码阅读](code_reading.md)。

拟直接修改mic源码的共享archive层：统一rc/命令/stderr末尾错误；流式GNU tar→压缩器；两个子进程均检查rc并回收，优先保留压缩器写失败证据；安全临时文件、成功才发布、move前存在检查；所有压缩/解压分支一致；打包前后记录工作盘df和free。预计减少约2.40GiB中间tar，但须用实际基线验证。详细实现边界、失败处理和测试列表见 [补丁方案](patch_proposal.md)。**目前只是设计，patches目录没有实施的patch。**

可见bootstrap中强制GNU tar的措施有价值，应保留刷机兼容性；提供pigz可提速。`-p 2`可降低多线程缓冲内存，但本机仅降低约13.27MiB，无法单独证明修复GiB级worker压力。sandbox文本替换脚本尚不可见，不对其具体行为作无证据判断；应检查是否会被复制宿主mic覆盖，以及bzip2/zstd和其他imager是否一致。

## 继续所需材料与命令

按用户明确规定，sudo非免密时停止。已整理 [需sudo的脚本](need_sudo.sh) 和 [5秒采样器](sampler.py)；本轮没有运行该脚本，它不是已验证复现配方。脚本使用目录内展开的官方mic和本地配置，不修改系统apt源/安装系统包；如果后续发现依赖不足会停止，不能把本地解包称为完整安装。

用户自行在终端认证后，可依次运行：

```bash
cd /home/linhao/Toolchain/development/llvm_image_analysis
sudo -- bash docs/need_sudo.sh baseline
# 依据采样的工作目录实际峰值计算字节数：
sudo -- bash docs/need_sudo.sh space <峰值字节数乘0.8>
sudo -- bash docs/need_sudo.sh oom 1G
sudo -- bash docs/need_sudo.sh oom 512M
```

这些是待执行命令，**并非声称必须由用户一次跑完**；也可用户提供可用sudo会话后由后续协作继续。小盘实验明确需要基线测量值，不默认填入理论量。MemoryMax实验应允许mic启动并记录选中的牺牲进程；如果在安装/初始化就失败，不能当作打包阶段等价复现。脚本会保存time、完整控制台、mic日志、5秒df/free/RSS/du采样及OOM日志，目录均在本工作目录。不能保证通用内核/插件环境一次即成功；现场失败应继续调查。

请提供有权限取得的`tools/mic-bootstrap` sandbox分支clone路径或`packaging/patch_archive.py`原文，后续需把相关取证副本保存在本工作目录。还有：

- QB五份控制台、命令与mic/步骤状态现已取得；仍需压缩器原始rc和stdout/stderr、tar rc，不把mic的1当作压缩器的1。
- 失败worker当时工作盘`df -B1 /var/tmp/mic`、`findmnt -T /var/tmp/mic`（含tmpfs/quota/inode），bootstrap和输出所在设备，以及占用/剩余量；不能拿本机df代替历史worker。
- kernel journal/dmesg中的OOM记录、cgroup路径与memory.max/peak/events、`oom_score_adj`；若确有压缩子进程被杀，确认其选择与资源来源；此次mic已知以异常返回1，不再将其直接被杀列为同等解释。
- 实际worker宿主和bootstrap的archive.py sha256、mic包版本/来源、pigz版本/CPU数；现代Git准确commit及sandbox补丁应用时机。
- 成功ks发布后为何与MD5SUMS不符，是否能从QB取得原始输入副本。

状态为“stage2b真压缩器与原mic函数的现场签名实验完成；完整镜像/ENOSPC/OOM/补丁待后续阶段”。当前已确认的代码缺陷足以解释诊断丢失；真实触发原因待上述材料或真实资源实验闭合。
