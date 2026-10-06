# 压缩器失败的现场签名实验（stage2b，2026-10-06）

**真 gzip / pigz 在写输出时遭遇 EFBIG 都删除半成品并产生 mic 的 FileNotFoundError；已经写到一半再被 SIGKILL 都留下坏 `.gz`，mic._make_tarball 则 move 成功并返回 True。QB 两次更支持主动清理输出的失败路径，相比“压缩中途被 SIGKILL”更符合写失败；ENOSPC 是中等置信的首选资源假设，仍非已证实根因。** QB依据：`1187398full-log.txt`、`1189686full-log.txt` 均L8878–8926、8936、8951–8955；实验依据：[summary.csv](../evidence/signature/summary.csv)、[全部结果](../evidence/signature/results.json)。

## 一、源码与版本核对

### gzip 1.12：写错误和信号都会清理，但 SIGKILL 不会

本机 `/usr/bin/gzip` 为 `gzip 1.12-1ubuntu3.2`；Ubuntu 24.04 Noble 的上游版本亦为1.12，见 [Ubuntu源包页面](https://packages.ubuntu.com/source/noble/gzip) 与 [环境记录](../evidence/signature/environment.json)。下载官方1.12 release，GNU主站90秒超时后通过 GNU镜像 `mirrors.kernel.org/gnu/gzip/gzip-1.12.tar.xz` 与 Ubuntu `gzip_1.12.orig.tar.xz` 分别取得，两份原档字节相同，sha256 `ce5e03e519f637e1f814011ace35c4f87b33c0bbabeec35baf5fbd3479e91956`。这不是取master最新源码。来源/字节数/哈希见 [source_provenance.json](../evidence/signature/source_provenance.json)，原样快照见 [gzip-1.12.SOURCE.txt](../evidence/src_snapshot/gzip-1.12.SOURCE.txt)。

Ubuntu补丁 series 及每份补丁也原样归档在 `evidence/src_snapshot/gzip-ubuntu-1.12-1ubuntu3.2/debian/`，所改文件不涉及本文的gzip.c/util.c写错误和信号清理路径；s390缓冲补丁作用于dfltcc.c，而本机x86_64。QB宿主显示Ubuntu24.04，但压缩命令在Tizen bootstrap内运行，**没有取得QB内实际gzip包版本/hash**，不能据宿主系统就证明其gzip与本机字节一致。

- [util.c](../evidence/src_snapshot/gzip-1.12/util.c) L239–247 调用 `write()`；L278–296 的 `write_buf` 在返回-1时调用 `write_error()`。L465–472 的 `write_error` 保留errno、`perror(ofname)` 后调用 `abort_gzip()`；ENOSPC和EFBIG均走这条通用写错误路径，没有按errno区分清理方式。
- [gzip.c](../evidence/src_snapshot/gzip-1.12/gzip.c) L2103–2121 的 `remove_output_file` 在已打开命名输出、`remove_ofname_fd>=0` 时close并`xunlink`；L2127–2131 的 `abort_gzip` 调用它后 `do_exit(ERROR)`。`ERROR=1` 见 [gzip.h](../evidence/src_snapshot/gzip-1.12/gzip.h) L51–53；退出1。这里讨论的是QB的 `gzip -f input.tar` 命名输出；若用 `gzip -c >file`，外层shell持有重定向文件，清理现场会不同，本实验不使用这种形式。
- [gzip.c](../evidence/src_snapshot/gzip-1.12/gzip.c) L235–255 的 handled_sig 包含SIGINT、SIGHUP、SIGTERM以及SIGXFSZ；L2038–2064 的 `install_signal_handlers` 仅处理未继承SIG_IGN的信号。L2137–2144 的 `abort_gzip_signal` 删除输出，恢复默认处理再raise，所以SIGINT/TERM/HUP可以表现为负信号返回码，同时没有输出。若信号原来被忽略，gzip保持忽略；不能无条件说所有环境下都捕获。
- SIGKILL不可捕获，不能执行上述cleanup。对**已经创建并写入的输出**，中途SIGKILL应留半成品；本机SIGKILL实测验证这一点。若在打开输出之前就被杀，或随后有其他进程删除文件，则可没有残留，这不在本实验的中途kill条件内。

### pigz 2.8：通用错误清理，实际只安装 SIGINT handler

该版本不是名为 `bail()` 的错误路径，实际是 `throw` → `catch` / `THREADABORT` → `cut_short`，不能按别的版本函数名套结论。原始 [pigz.c](../evidence/src_snapshot/pigz-2.8/pigz.c)：

- L1018–1030 的 `writen()` 检查 `write()` 返回值，失败时 `throw(errno,"write error ...")`；L4164–4165是打开输出失败，L4211–4212是关闭输出失败，也保留errno。
- L940–946 的 `THREADABORT` 打印 `abort: ...`，调用 `cut_short(-err.code)`；主catch见L4736–4738，压缩线程也用同一宏。L926–937 的 `cut_short` 在 `g.outd!=-1 && g.outd!=1` 时unlink(g.outf)，最后 `_exit(sig<0 ? -sig : EINTR)`。因此真实EFBIG（errno27）返回 **27** 并删除输出；ENOSPC（errno28）在同一路径会返回 **28**，后者为源码推断，未做真实ENOSPC试验。
- L4627只有 `signal(SIGINT, cut_short)`，全文无安装SIGTERM/SIGHUP/SIGXFSZ handler。SIGINT清理输出并退出EINTR=4；SIGTERM、SIGHUP、默认SIGXFSZ或SIGKILL在中途终止则不走cleanup（本机各有实测）。同样限于命名输出且已创建，不泛化到stdout重定向/未打开输出的场景。

### mic._make_tarball：只 move + exists，不校验完整性

[archive.py](../evidence/src_snapshot/mic/mic/archive.py) L66–85 `_call_external` 合并捕获stdout/stderr并返回tuple；L87–110 `_do_gzip` 忽略tuple，不管rc就返回 `input_name+'.gz'`。L327–348 的 `_make_tarball`：先tar，再compressor，直接 `shutil.move(tarball_name,archive_name)`，返回 `os.path.exists(archive_name)`；没有大小、CRC、gzip trailer、gzip -t或tar内容校验。所以：缺 `.gz` → move抛FileNotFoundError；半份 `.gz` 存在 → move成功，返回True，即使解压测试明确失败。

## 二、真实实验方法和边界

普通用户UID/EUID=1000；没有sudo、没有整镜像、没有修改mic源码，也不制造内核OOM。脚本为 [run_experiment.py](../evidence/signature/run_experiment.py) 和 [real_compressor_wrapper.py](../evidence/signature/real_compressor_wrapper.py)，原始命令/时间/rc/stderr/存在性及gzip -t结果逐项写入json；输出进度见 [driver.log](../evidence/signature/driver.log)。只对当前实验自己启动的压缩器PID发送信号。

准备 `work/signature/input/payload.bin`，300,000,000字节 `os.urandom`；GNU tar生成 `work/signature/random.tar`，300,011,520字节。输入SHA256与真二进制SHA256见 [input.json](../evidence/signature/input.json)。每次直接实验复制同一tar，调用真实 `gzip -f input.tar` 或 `pigz -f input.tar`；pigz不设-p，保持默认线程策略。mic实验调用原始 `_make_tarball(final.tar.gz,input_dir,archive._do_gzip)`，在PATH中只暴露选中的真压缩器包装入口和GNU tar，避免gzip组被其他pigz抢选。包装器最终exec真实二进制，其PID不变。

`_call_external` 被观察钩子包裹：照常调用原函数，只记录返回tuple和move前输出是否存在，然后原样返回，**没有修正错误处理**。它捕获的压缩器错误另存结果json；原mic.log中仍看不到它。实验驱动为保存异常而catch，所以驱动退出0不是完整mic程序成功；表中的True仅指 `_make_tarball` 函数返回值。

### ulimit -f 必须分开解释两条路径

Bash非POSIX模式 `ulimit -f 100000` 对应 RLIMIT_FSIZE=**102,400,000字节**，已用Bash子进程查询内核limit值确认（input.json）。压缩器包装器设置同一内核资源限制，只限压缩器，不限制先行tar或驱动；结果并不是伪造exit。

1. **EFBIG组**：额外忽略SIGXFSZ，使内核超限的write返回EFBIG，真正进入程序写错误路径。gzip和pigz均打印 `File too large` 并删除输出。
2. **fsize-signal组**：保留默认SIGXFSZ，作为普通ulimit行为对照。gzip捕获SIGXFSZ，删除输出后重新抛信号（-25/153）；pigz未捕获，直接终止（-25/153），留102,400,000字节坏文件。不能把这个pigz结果说成“EFBIG错误处理不删除输出”。
3. **SIGKILL组**：独立watcher按输出文件达到该压缩器正常大小约50%时发SIGKILL；不是在程序未创建输出前自杀。阈值、信号发送和发送前实测大小见各 `*-sigkill.watch.json`。每0.5ms采样，因此有少量超调；gzip直测残留150,208,512字节，pigz直测150,732,800字节。
4. 额外以32MB输出阈值测SIGINT/TERM/HUP，核对源代码的信号差异（各direct json/原始stderr）。

### 真实 ENOSPC 补充尝试

`udisksctl`存在且不交互loop-setup成功，但普通用户在工作目录的ext4 mount失败：`must be superuser to use mount`（rc32）。`udisksctl mount --help`没有指定挂载点选项，其默认挂载在工作目录之外；为遵守所有产物在本目录的边界，不在外部挂载点写实验文件。创建的loop已用udisksctl成功删除，没有残留挂载或sudo调用。完整记录见 [udisks-enospc-attempt.json](../evidence/signature/udisks-enospc-attempt.json)。因此本阶段是**真实EFBIG + 真实进程信号**，ENOSPC处理相同是源码结论，不能宣称真实磁盘满已经复现。

## 三、现场签名对照表

下表输出大小是直接压缩器结束后的现场；mic结果来自另一次独立的真实 `_make_tarball` 运行。“吻合”只比较QB L8926的缺 `.tar.gz` / FileNotFoundError签名，不能据签名认定QB errno。所有8组mic都记录move前存在性与实际子进程rc（[summary.csv](../evidence/signature/summary.csv)）。

|情形|压缩器返回码（Python / shell等价）|输出文件现场|mic层现象|与QB缺文件异常是否吻合|
|---|---|---|---|---|
|gzip正常|0|完整300,048,490 B；gzip -t=0|move成功，True；gzip -t=0|成功对照；与失败不吻合|
|pigz正常|0|完整300,091,807 B；gzip -t=0|move成功，True；gzip -t=0|成功对照；与失败不吻合|
|gzip真实EFBIG，忽略SIGXFSZ|1|输出被删除；stderr: File too large|FileNotFoundError|吻合1187398|
|pigz真实EFBIG，忽略SIGXFSZ|27|输出被删除；stderr: abort: write error ... (File too large)|FileNotFoundError|吻合1189686|
|gzip约一半SIGKILL|-9 / 137|残留150,208,512 B；gzip -t=1|move成功，True，得到坏.gz；gzip -t=1|不吻合1187398|
|pigz约一半SIGKILL|-9 / 137|残留150,732,800 B；gzip -t=1|move成功，True，得到坏.gz；gzip -t=1|不吻合1189686|
|gzip普通ulimit触发SIGXFSZ|-25 / 153|被handler删除；无stderr|FileNotFoundError|形状吻合1187398；说明信号也能删除输出|
|pigz普通ulimit触发SIGXFSZ|-25 / 153|残留102,400,000 B；gzip -t=1|move成功，True，得到坏.gz；gzip -t=1|不吻合1189686|

另测信号：gzip SIGINT=-2、SIGTERM=-15、SIGHUP=-1均删除输出；pigz SIGINT=4且删除，SIGTERM=-15/SIGHUP=-1留下坏输出（不进行完整mic信号补充组，mic文件存在分支已由SIGKILL/SIGXFSZ实测）。这证明“没有输出”不能唯一等于写失败，也不能把所有信号一概当作SIGKILL。

## 四、逐次时间、原始错误与mic现象

直接正常gzip为5.381秒，pigz为0.537秒；不可压缩数据的输出约300MB。本机多线程pigz吞吐明显高于gzip，因此下面QB pigz的gzip吞吐投影误差很大。mic正常gzip为6.715秒、pigz为4.217秒，含tar创建、Python/包装器开销，不直接作为压缩速度。完整毫秒精度原始数据在summary.csv/results.json，未使用`time`或wrapper的shell返回码替代子进程实际rc。

直接gzip EFBIG stderr原文（[文件](../evidence/signature/direct-gzip-efbig.stderr.txt)，开头有空行）：

```text

gzip: /home/linhao/Toolchain/development/llvm_image_analysis/work/signature/direct-gzip-efbig/input.tar.gz: File too large
```

直接pigz EFBIG stderr原文（[文件](../evidence/signature/direct-pigz-efbig.stderr.txt)）：

```text
pigz: abort: write error on /home/linhao/Toolchain/development/llvm_image_analysis/work/signature/direct-pigz-efbig/input.tar.gz (File too large)
```

SIGKILL两组stderr均为空；残留的 `.gz` 经真实 `/usr/bin/gzip -t` 返回1、报 `unexpected end of file`。mic gzip SIGKILL最终文件150,208,512字节，pigz SIGKILL最终文件150,122,883字节；与直测pigz不同是独立运行的轮询超调。mic正常gzip输出比直测多6字节，pigz也多6字节，来源为gzip header中临时输入文件名字不同，输入tar正文一致；不是数据压缩可重复性的假定。

EFBIG的mic trace见 [gzip控制台](../evidence/signature/mic-gzip-efbig.console.log)、[pigz控制台](../evidence/signature/mic-pigz-efbig.console.log)，均定位archive.py:346的shutil.move；分别见 [结果](../evidence/signature/mic-gzip-efbig.json)、[结果](../evidence/signature/mic-pigz-efbig.json)，其中保存了被原始mic代码丢弃的真实子进程错误。SIGKILL的 [gzip结果](../evidence/signature/mic-gzip-sigkill.json)、[pigz结果](../evidence/signature/mic-pigz-sigkill.json)明确为True、输出存在、完整性失败，未出现FileNotFoundError。

## 五、QB写出量与剩余空间的条件估算

按用户指定成功吞吐：`2,580,797,440 B / 73 s = 35,353,389.589 B/s`。这首先是**输入tar吞吐**，不是压缩输出字节率，不能直接用它算剩余磁盘空间。成功输出目录列示696,473,433 B（`downloads/indexes/20260917.132101-images.html` L14）；若以同一平均压缩比，则：

```text
压缩比 r = 696,473,433 / 2,580,797,440 ≈ 0.269868
平均输出速率 = 35,353,389.589 × r ≈ 9,540,731.959 B/s
```

|失败构建|启动→首traceback|按成功速率处理的输入等效量|按成功压缩比估算已写输出|假设ENOSPC时，压缩开始前工作盘剩余空间粗估|
|---|---:|---:|---:|---:|
|1187398 gzip（L8878–8879）|42.433 s|约1.500 GB|约404.842 MB / 386.087 MiB|约0.405 GB，条件估算|
|1189686 pigz（L8878–8879）|29.828 s|约1.055 GB|约284.581 MB / 271.398 MiB|约0.285 GB，只是gzip速率投影|

公式与数字在 [qb_space_estimate.json](../evidence/signature/qb_space_estimate.json)。此处“剩余”指**tar已形成、开始写.gz时该工作盘可供新增输出的空间**；不是mic起始可用空间，也不是失败后df，后者可能因删除.gz而回升。若gzip的输出和中间tar在同一工作文件系统，理想条件下这可以解释能生成tar却写不完gz。

假设很强：各块压缩比相同、平均输入速度稳定、异常处理延迟可忽略、没有别的任务并发写盘/配额/元数据影响、确实在写.gz时ENOSPC。gzip最后输入速度未必等于成功平均；pigz线程速度尤其未经QB校准，本机正常速度已相差约10倍，**不能把0.285GB当作可靠的pigz worker可用空间测量**。没有历史df就没有测量值或可证明置信区间；这些数字只提供调查量级，不能反向证明ENOSPC。

## 六、成因更新与证据边界

- **高置信的机制区分**：在已写输出的真实中途SIGKILL场景，输出留存、mic move返回True并发布坏文件；不是QB的缺输出异常。两次QB缺文件更贴近写错误/主动cleanup，而不是晚期SIGKILL。真正OOM通常通过SIGKILL执行，但本实验没有OOM，仅测SIGKILL文件现场。
- **当前最可能资源触发：ENOSPC，中等置信。** 共同缺文件形状、程序写错误cleanup、先tar后压缩的额外工作盘需求共同支持该优先级；不是有ENOSPC stderr/df直接证据。EFBIG/配额、tar/input先失败、pigz的其他throw（含用户态ENOMEM）、可捕获信号等仍可形成缺文件。没有worker ulimit/磁盘/rc，不能唯一归因。
- 对gzip，SIGINT/TERM/HUP/SIGXFSZ主动cleanup也能缺文件；对pigz，源码明确捕获SIGINT且可cleanup。QB正常失败链没有取消/超时实证，但这不能排除压缩器单独收到信号。
- stage1的fake gzip SIGKILL探针在**输出尚未创建**时自杀，因此其FileNotFoundError只证明mic丢弃负rc；不能代表真gzip已压缩一段后被杀的文件现场。stage2b已用真压缩器和输出进度阈值补上这个缺口，没有推翻stage1的诊断丢失事实。
- gzip 1.12/pigz2.8 source、二进制、named-output条件都有边界；QB bootstrap的精确二进制hash和外部清理动作仍未核验，不能绝对排除“打开输出前SIGKILL”或“中途SIGKILL后别人删文件”。

下一步最有区分力的是保留tar与.gz现场、压缩器rc/stderr、worker RLIMIT_FSIZE/quota/df和内核/cgroup事件。完整基线、真实ENOSPC/OOM、源码修复仍留给后续阶段，不把这组签名实验当作整镜像复现。
