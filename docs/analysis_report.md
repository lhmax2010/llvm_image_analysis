# tizen-headed-aarch64 mic 打包失败分析

2026-10-08（Asia/Shanghai），**stage3最终版**。QB控制台取证、真压缩器签名、无root稀疏归档、总部真实源码/提交评审与archive补充diff/小测试完成。整镜像baseline/space/oom已取消；全程普通用户，不调用sudo、不改系统。

## 结论与置信度

两次QB最吻合压缩写失败后清理输出，**ENOSPC为最可能资源触发（中等置信）**；mic丢弃子进程返回码/输出，使原始错误变成move缺文件异常，这个代码缺陷已确认（高置信）。真中途SIGKILL的残留坏.gz签名不同于两次QB；没有原始errno、失败时df/配额或内核/cgroup证据，不能把ENOSPC或OOM写成唯一已证实根因。

总部方案的容量部分是**缓解**，不是空间不够仍能成功的修复；但真实前置c446578已经给gzip/pigz、bzip2、lzop、zstd的压缩/解压加rc与合并输出检查，诊断缺陷已有部分修复。需要更正“总部仍无压缩rc/stderr”的假设。我们的补充只在archive._call_external统一原文日志、CreatorError、命令/rc与压缩前同盘剩余空间，保留总部函数和tar回退代码。详情见 [总部逐行评审](hq_patch_review.md) 和 [实际diff](complementary.patch)。

“1189686的pigz几秒就被杀、mic死了”已被真实控制台否定：mic约30秒后抛FileNotFoundError并返回1，QB继续同步日志并正常标记failed。子压缩器受何种外部事件仍需其rc/stderr，-9即使取得也只能证明SIGKILL，OOM需额外内核/cgroup证据。

## 证据链

|证据|直接支持的结论|边界|
|---|---|---|
|1187398full-log.txt L8878–8926、8936、8955|gzip启动到首traceback42.433s；缺.tar.gz；mic返回1；QB普通failed|没有gzip原始rc/stderr|
|1189686full-log.txt同段|pigz启动到首traceback29.828s；同样缺文件/返回1/failed|不是无traceback、不是mic突然消失|
|原mic2.1.3 archive.py L66–110、129、153、180、327–348|捕获后丢弃压缩rc；mktemp；不验产物就move|仅代表两次QB旧实现，HQ新版已有rc检查|
|22组stage2b真压缩器/原mic函数实验|真EFBIG清理.gz→FileNotFoundError；真中途SIGKILL留坏.gz→原mic move成功|真实ENOSPC未运行，EFBIG源码走写错误路径；历史时机不唯一|
|原始打包路径及成功体积|完整中间tar与.gz并存，位置在work tmpdir，不因最终outdir改变|完整峰值模型非历史worker实测|
|stage3未挂载ext4文件实验|tar -S显著减中间tar，提取还原洞且内容一致|随机数据/单次性能，不能量化真实镜像洞图|
|lthor3.4源码+libarchive3.7.2读流API实验|现代API能对本实验GNU稀疏档案补零还原完整内容|未刷写真实设备，不代表旧版本/稀疏pax所有格式|

详细逐行取证见 [qb_console_forensics.md](qb_console_forensics.md)、[log_forensics.md](log_forensics.md)，源码链路见 [code_reading.md](code_reading.md)，原始失败签名及信号源码见 [signature_experiment.md](signature_experiment.md)。三个公开mic.log只记录到压缩启动，与含stdout/stderr的QB控制台不是同一渠道。父1189639传递子1189686失败，并非同一worker的相同mic现场。

## OOM/写失败对照

|情形|真实压缩器rc|输出现场|原mic层结果|与QB两次失败|
|---|---|---|---|---|
|正常gzip/pigz|0|完整.gz|move成功|成功对照|
|EFBIG写失败，忽略SIGXFSZ以得到write errno|gzip1 / pigz27|都主动删除.gz|FileNotFoundError|形状吻合；尚非证明ENOSPC|
|输出约一半后SIGKILL|两者-9（shell137）|都残留坏.gz|move成功，gzip -t失败|典型中途kill不吻合|
|默认文件限额SIGXFSZ|gzip-25 / pigz-25|gzip删输出，pigz残留|gzip缺文件；pigz假成功|信号处理有差异|
|SIGINT/TERM/HUP|gzip重新抛对应信号；pigzINT4/TERM-15/HUP-1|gzip皆清理；pigz仅INT清理|可形成类似缺文件|不能只据缺文件定errno|

详见 [summary.csv](../evidence/signature/summary.csv)。捕获信号、EFBIG/配额、tar先失败、打开输出前被杀或外部删除仍可形成缺文件。当前最强结论是错误处理丢失诊断和写错误cleanup更吻合，资源层保留中等置信。

用成功吞吐的用户指定2,580,797,440 B/73s及输出696,473,433 B粗投影：gzip42.433s约写404.8 MB，pigz29.828s若假设同样gzip输出速度约284.6 MB。实际pigz吞吐未知、输入内容/缓存/负载不同，不能将此当实际剩余空间；见 [估算](../evidence/signature/qb_space_estimate.json) 与log_forensics说明。

## 稀疏实测与峰值模型

普通用户在2GiB ext4文件内用debugfs写600MiB随机文件，未挂载、未提权、未建整镜像。输入实际占用697,483,264 B；结果如下（单次墙钟）：

|项目|普通tar|tar -S|
|---|---:|---:|
|tar大小B|2,147,491,840|697,487,360|
|tar时间s|3.123|13.417|
|gzip大小B|630,732,468|629,320,754|
|gzip时间s|17.293|11.512|
|提取后逻辑大小B|2,147,483,648|2,147,483,648|
|提取后分配字节B|2,147,487,744|697,479,168|

所有提取内容SHA256一致。中间tar少67.52%，gzip只少0.22%；不能声称本机合计时间加速。tar -tvf两份完全相同，显示逻辑大小；实际header typeflag分别0/S。完整命令、du、提取/读流哈希和条件估算见 [sparse_experiment.md](sparse_experiment.md)、[原始结果](../evidence/sparse/summary.json)。

0917逻辑量2,580,786,618 B、gzip696,473,433 B；旧tar模型2,580,797,440 B。若真实分配比例与本实验相同，-S后中间tar约0.838GB、减少1.743GB；按另一“相同sparse tar/gzip比率”假设约0.772GB。这两个条件场景不是可信区间，真实软件数据可压缩，不能把gzip大小当已分配块。需实际源镜像du/洞图收紧估计。

令A为源镜像实际分配量、T普通tar、S稀疏tar、C压缩结果、O其他工作量，同盘峰值模型由A+T+C+O降为A+S+C+O。独立流式tar | gzip/pigz进一步去掉中间T/S，两项可叠加；流式并不改变-S的消费端格式兼容性。跨盘最终copy还可能叠加另一份C。旧使用逻辑I代替A的5.46GiB模型不可冒充实际物理峰值。

## 总部真实提交评审

git://review.tizen.org/git/platform/upstream/mic成功取得sandbox/jaehoon80/devel，HEAD eadc8fd5c1288206601485c1dbff0ecdb1425bcd。c446578d87b055984e5eeca04e2f485436f55759先默认-S、fallocate -d、统计适配并增加四种压缩/解压rc检查；eadc8fd5随后把-S改为KS/CLI opt-in，默认False。show_tar_diagnostics实际来自更早3cc580ebf07677610d58bd8f4b2c3b9ba0a7c15d。两个指定提交作者/日期/subject、原样导出、每文件每hunk dry-run及完整逻辑都在 [hq_patch_review.md](hq_patch_review.md)。

不开--sparse-tar时loop/raw保留普通tar→gzip/pigz→move结构；整体行为并非与2.1.3完全一致，已有rc检查、诊断、无条件fallocate依赖和copy_function变化。开启后loop/raw执行tar -S -C DIR -cf TMP.tar MEMBERS，仍落中间tar；任意-S失败会回退普通tar。fs路径直接tar -czf/-cjf，不经过archive._make_tarball。原样 [HQ archive](../evidence/src_snapshot/hq-mic/mic/archive.py) L303–317、358–378；[fs](../evidence/src_snapshot/hq-mic/mic/imager/fs.py) L68–104。

总部四函数rc检查证据：[archive.py](../evidence/src_snapshot/hq-mic/mic/archive.py) L102–105、132–135、159–162、189–192。它们捕获的是原_call_external合并后的stdout+stderr；没有直接统一logger写入，OSError通道也不同于CreatorError。mktemp、move前独立存在/完整性检查尚未修。show_tar_diagnostics在tar前打印硬编码/var/tmp容量、du和部分进程limits（misc.py L1094–1134），不等于失败瞬间真正工作盘/配额/cgroup证据。

两份真实patch对原2.1.3分别dry-run各有一个archive hunk失败；缺的是3cc580e诊断及c446的tar上下文，不修改总部补丁。work副本补齐真实3cc580e后顺序c446→eadc均通过，只有raw.py +17行offset，无fuzz。缺依赖的“2.1.3+两份直接patch”不能假称成功；部署应取包含祖先的正式mic包。额外依赖导出保存在evidence/hq/，完整clone不推。

## 我们的补充建议与实际交付

[complementary.patch](complementary.patch)只修改mic/archive.py imports及_call_external；总部已修改的四压缩函数、tar开关/回退、make_tarball/config/imager均保留。压缩前shutil.disk_usage记录输入.tar字节数与产物所在目录free；失败记录rc/安全引用命令、stderr不截断原文，并抛真实CreatorError，异常附末20行。四个函数已有HQ rc检查，经共享层获得统一日志；顺带覆盖lzop/pbzip2和所有解压方向。

仅首个tar -S非零保留返回tuple供总部fallback；同样先记日志，避免在共享层无条件抛错破坏HQ回退。没有实现流式压缩、额外mktemp替换或move防御，遵守本轮限定范围；这些作为后续独立风险列出，不声称已修。stdout/stderr由分别捕获到合并返回，时间交织会变化；非UTF8替换解码、communicate无界缓冲仍需注意。容量日志只观察，不以tar_size>free武断阻止可压缩输入。

候选diff先在2.1.3+3cc580e+c446578+eadc8fd5上dry-run，再写正式文件并apply；真实Gerrit HEAD dry-run也通过。28组普通用户小测试包含各压缩/解压exit1/SIGKILL、完整打包失败保留旧目标、真实gzip/稀疏tar roundtrip与-S fallback；另验证实际包import、实际CreatorError和真实msger文件日志。见 [测试结果](../evidence/complementary/results.json)、[真实日志验证](../evidence/complementary/real-import-logging.log)、[补充说明](patch_proposal.md)。没有将旧行为签名实验冒充新补丁验证。

可选流式tar | gzip/pigz仅作为后续方案说明，不生成代码：可独立开关并与-S叠加，去掉中间tar；须分别检查两端rc/回收管道，并接受并发资源/压缩头部hash变化，消费端兼容性仍需验证。

## 总部方案部署前提清单

- [ ] QB worker实际宿主mic更新到包含3cc580e诊断依赖、c446578和eadc8fd5的版本；核验路径/commit/文件hash，branch内__version__=2.1.0不能单独证明部署。
- [ ] 实际发布KS的bootloader加入--sparse-tar，记录原始KS hash及解析值；CLI是另一opt-in入口。通常KS部署方式中“新worker mic + KS启用”缺一不可。
- [ ] 默认bootstrap复制更新后的宿主mic（HQ rt_util.py L165–175），只更新bootstrap RPM不够；use_mic_in_bootstrap/py2例外则核验bootstrap实际mic。
- [ ] bootstrap内GNU tar支持-S/所选格式，fallocate存在且支持工作文件系统-d；日志证明实际-S而非普通tar回退。
- [ ] 消费端/库/设备能正确展开洞和刷写内容；仅普通成员或未知版本链路不开-S。现代libarchive读流结果不能代表历史全部lthor。
- [ ] 工作盘为源分配块、稀疏tar、压缩输出、缓存/bootstrap及其他负载保留空间；仍收集失败瞬间df/inode/quota与内核/cgroup证据。
- [ ] 采用补充diff时核验上述真实依赖与rootless测试，保留HQ回退例外；我们只交付源码patch，没有安装到worker或系统。

## 仍需QB侧确认

压缩器原始rc/完整输出与失败瞬间工作文件系统df/inode/quota；worker内核/cgroup memory.events、并行任务及退出信号；实际worker mic/包/KS hash、bootstrap覆盖顺序与GNU tar版本；真正的lthor/库/目标设备版本及稀疏格式验证；成功源镜像分配块与稀疏tar实量。0917公开KS当前MD5不匹配发布MD5SUMS，不能认定与QB原始输入逐字节相同；sandbox/dkson95/clang仍未取得。

## 取消的工作与最终交付状态

整镜像baseline/space/oom取消，need_sudo.sh停用；历史parser/plugin/root guard证据保留在 [baseline.md](baseline.md)。stage3已完成总部真实评审、普通用户稀疏/读流实验、实际单文件补充diff与小测试；遗留的是历史QB资源证据和部署验证，不再以sudo实验为交付门槛。读过/未读过的文件范围见 [status.md](status.md)。提交推送使用stage3: hq patch review and complementary patches，并核验远端main与本地HEAD一致。
