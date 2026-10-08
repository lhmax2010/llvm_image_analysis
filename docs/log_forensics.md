# mic 日志取证（2026-10-06）

## 材料与证据边界

stage1 部分据三份公开 mic.log；stage2a 新增用户提供的五份QB控制台，stage2b新增真gzip/pigz失败签名实验，完整分析见 [qb_console_forensics.md](qb_console_forensics.md)。两类日志保留独立证据边界；下面打包原文仍是旧 mic.log，具体判定已按控制台更新。原始文件未改动；下载 URL、字节数和 sha256 见 `docs/downloads.md`。完整逐行 diff：`evidence/20260917.132101-vs-20260930.105301.diff`、`evidence/20260930.105301-vs-20261003.102419.diff`。文件尾字节与关键词扫描见 `evidence/log_metadata.json`。公开mic.log时间带UTC；QB控制台只有时分秒，重叠段可与mic.log对应，但不补造未打印的时区。

## 开头、选项与目录

### 20260917.132101

- mic 宿主与 bootstrap 都打印 2.1.3：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L1、19；机器分别为 `.202`、`.91`、`.168`，不是同一 worker。
- runtime=bootstrap 的实际行为由创建 bootstrap、复制宿主 mic、启动 chroot 证实：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L11–19。不是仅依据默认配置。
- ks 路径见 `downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L2、20，构建工作目录由打包命令得到：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L7426。
- stage1公开mic.log没有完整启动命令；stage2a控制台已取得实际 `cr auto ... --release ... -o ... -k ... --logfile=...`，详见QB报告逐日志章节。该命令没有显式runtime、pack-to、tmpdir或-c。无tmpfs挂载输出仍不能排除/确认环境将 `/var/tmp` 放在tmpfs。

### 20260930.105301

- mic 宿主与 bootstrap 都打印 2.1.3：`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L1、19；机器分别为 `.202`、`.91`、`.168`，不是同一 worker。
- runtime=bootstrap 的实际行为由创建 bootstrap、复制宿主 mic、启动 chroot 证实：`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L11–19。不是仅依据默认配置。
- ks 路径见 `downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L2、20，构建工作目录由打包命令得到：`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L7366。
- stage1公开mic.log没有完整启动命令；stage2a控制台已取得实际 `cr auto ... --release ... -o ... -k ... --logfile=...`，详见QB报告逐日志章节。该命令没有显式runtime、pack-to、tmpdir或-c。无tmpfs挂载输出仍不能排除/确认环境将 `/var/tmp` 放在tmpfs。

### 20261003.102419

- mic 宿主与 bootstrap 都打印 2.1.3：`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L1、19；机器分别为 `.202`、`.91`、`.168`，不是同一 worker。
- runtime=bootstrap 的实际行为由创建 bootstrap、复制宿主 mic、启动 chroot 证实：`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L11–19。不是仅依据默认配置。
- ks 路径见 `downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L2、20，构建工作目录由打包命令得到：`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L7366。
- stage1公开mic.log没有完整启动命令；stage2a控制台已取得实际 `cr auto ... --release ... -o ... -k ... --logfile=...`，详见QB报告逐日志章节。该命令没有显式runtime、pack-to、tmpdir或-c。无tmpfs挂载输出仍不能排除/确认环境将 `/var/tmp` 放在tmpfs。

三份 ks 第一行都包含 `-A aarch64 -f loop --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license`：成功 ks `downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks` L1；失败 ks `downloads/ks/20260930.105301-tizen-headed-aarch64.ks` L1、`downloads/ks/20261003.102419-tizen-headed-aarch64.ks` L1。成功 ks 的两个固定 repo URL 在 L26–27；两份失败 builddata ks 的 L26–27 仍是模板 URL，不能直接当成失败运行时的固定 repo。两份失败 ks sha256 完全相同。

## 分区与磁盘检查

|分区|0917 成功（字节）|0930 gzip（字节）|1003 pigz（字节）|
|---|---:|---:|---:|
|rootfs.img|1960599552|1959587840|1959567360|
|system-data.img|70049792|69959680|69959680|
|user.img|524288000|524288000|524288000|
|ramdisk.img|9457298|9459376|9461272|
|ramdisk-recovery.img|16391976|16420489|16420898|
|合计|2580786618|2579715385|2579697210|

来源：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L7420–7424；`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L7360–7364；`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L7360–7364。失败总逻辑大小比成功稍小，未见镜像突然膨胀。逻辑大小不等于实际分配块数。

三份日志中都没有建 loop 镜像前的工作文件系统可用空间检查输出（全文检索记录见 `evidence/log_metadata.json`）。源码中最终交付文件的空间检查位于打包后，详见 `docs/code_reading.md`；不能从日志缺失得出“磁盘充足”。

## 打包段逐行原文

### tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log

```text
7425: [09/17 19:11:37 UTC] Pack all loop images together to tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.tar.gz
7426: [09/17 19:11:37 UTC] Running command: tar -C /var/tmp/mic/build/imgcreate-eyu_1uwy/tmp-k4mpfzpk -cf /var/tmp/mic/build/imgcreate-eyu_1uwy/out/tmpq8ca4l2r.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
7427: [09/17 19:11:52 UTC] Running command: gzip -f /var/tmp/mic/build/imgcreate-eyu_1uwy/out/tmpq8ca4l2r.tar
7428: [09/17 19:13:05 UTC] Creating manifest file...
7429: [09/17 19:13:07 UTC] The new image can be found here:
7430:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/MD5SUMS
7431:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/SHA1SUMS
7432:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/SHA256SUMS
7433:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/manifest.json
7434:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.files
7435:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks
7436:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.license
7437:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.packages
7438:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.tar.gz
7439:   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.xml
7440: 
7441: [09/17 19:13:07 UTC] Finished.
```

### tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log

```text
7365: [09/30 16:54:10 UTC] Pack all loop images together to tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.tar.gz
7366: [09/30 16:54:10 UTC] Running command: tar -C /var/tmp/mic/build/imgcreate-b62wua5u/tmp-7zn1w9sc -cf /var/tmp/mic/build/imgcreate-b62wua5u/out/tmplxoqzh3o.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
7367: [09/30 16:54:24 UTC] Running command: gzip -f /var/tmp/mic/build/imgcreate-b62wua5u/out/tmplxoqzh3o.tar
```

### tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log

```text
7365: [10/03 16:21:46 UTC] Pack all loop images together to tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.tar.gz
7366: [10/03 16:21:46 UTC] Running command: tar -C /var/tmp/mic/build/imgcreate-q3ebnnd3/tmp-oi7izcgd -cf /var/tmp/mic/build/imgcreate-q3ebnnd3/out/tmpvupuwmim.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
7367: [10/03 16:22:01 UTC] Running command: pigz -f /var/tmp/mic/build/imgcreate-q3ebnnd3/out/tmpvupuwmim.tar
```

## 三个具体问题（按QB控制台更新）

1. **成功对照可以精确到毫秒。** 1178308 gzip启动19:11:52,103 → manifest19:13:05,317 = **73.214秒**，Pack→manifest **88.008秒**；GCC成功1182527 gzip09:48:58,938 → manifest09:50:17,856 = **78.918秒**，Pack→manifest **93.993秒**。这些包含返回/move等开销；两份打包尾段均无警告/traceback，全文较早有其他警告。证据：`1178308full-log.txt` L8933–8936、8949、8974；`1182527full-log.txt` L8903–8906、8919、8944。0917发布输出大小仍为696,473,433字节（公开目录images.html L14，未下载tar.gz实体）。
2. **0930 gzip确有shutil.move traceback。** `1187398full-log.txt` L8878 16:54:24,928 → L8879 16:55:07,361 = **42.433秒**；L8914–8915定位archive.py:346的move，最终FileNotFoundError L8926。未见gzip自身ENOSPC/Killed或其他stderr；L8936明确mic返回1，随后同步log、外层LocalError、QB标记Image_Create/IMAGE/master failed（L8927–8955）。因此此前只凭mic.log“不可知道mic后续是否存活”的项已解决；压缩器rc仍未知。
3. **1003 pigz也有同一traceback。** `1189686full-log.txt` L8878 16:22:01,450 → L8879 16:22:31,278 = **29.828秒**；L8936 mic返回1，EOF在L8955的16:22:32,955，距离pigz启动 **31.505秒**。后面有QB正常failed链，不是只有启动行结束。**“pigz几秒就被杀、mic死了”被否定**；mic活到抛异常并返回1，但pigz子进程是否受SIGKILL仍无证据。父1189639关系由子L36–37明确，父L22536仅传播子失败；其中failed/cancelled/timed out是通用模板，不能称超时事实。

以上QB原文件均在downloads/logs/；每条完整命令、全部打包尾段、所有关键词命中行见 [QB控制台取证](qb_console_forensics.md)。原mic.log末条与启动相差0秒的历史观察仍正确，但它只表示mic.log没记录后续，不再代表控制台/进程运行时长未知。

## OOM 与 ENOSPC 证据对照（stage2b更新）

完整实验、源码行号、原始rc/stderr、输出存在性及gzip -t见 [signature_experiment.md](signature_experiment.md) 和 [summary.csv](../evidence/signature/summary.csv)。实验UID1000，无sudo、无整镜像；EFBIG由真实内核文件大小限制触发，并非伪造错误。ENOSPC未真实复现，只有同一源码处理路径的依据。

|证据|SIGKILL / 构建机或cgroup OOM|写失败 / 工作盘ENOSPC|现在的区分能力|
|---|---|---|---|
|QB均FileNotFoundError、mic返回1、普通failed链（两份full-log L8879–8955）|不支持mic自己被直接杀死|相容于外部失败后缺输出|已确认mic异常退出，原始压缩器rc仍未知|
|真gzip在约50%输出时SIGKILL（direct/mic-gzip-sigkill.json）|rc=-9/137，留150,208,512B坏.gz；mic move True、gzip -t=1|与主动删除输出不同|不吻合1187398的缺文件签名|
|真pigz2.8在约50%输出时SIGKILL（direct/mic-pigz-sigkill.json）|rc=-9/137，直测留150,732,800B，mic留150,122,883B；move True、gzip -t=1|与主动删除输出不同|不吻合1189686的缺文件签名|
|真gzip EFBIG，忽略SIGXFSZ（direct/mic-gzip-efbig.json）|不是信号杀死，rc=1|输出被unlink，真实File too large；mic FileNotFoundError；ENOSPC同cleanup路径|缺文件形状吻合1187398，但不能证明QB errno|
|真pigz EFBIG，忽略SIGXFSZ（direct/mic-pigz-efbig.json）|不是信号杀死，rc=27|throw(errno)→cut_short→unlink；mic FileNotFoundError；ENOSPC按源码应rc28|缺文件形状吻合1189686，但不能证明QB errno|
|普通ulimit -f默认SIGXFSZ（两份fsize-signal.json）|gzip handler删除后rc=-25；pigz默认终止留102,400,000B|并非同一EFBIG错误分支|gzip仍可缺文件；pigz会被mic错误地move为成功，不能把所有ulimit现象说成写失败|
|其他可捕获信号（direct-*-sigint/sigterm/sighup.json）|gzip INT/TERM/HUP清理；pigz只INT清理，TERM/HUP留半成品|可能形成同样缺文件，不唯一等于ENOSPC|主动cleanup机制高置信，特定errno仍需rc/stderr|
|完整中间tar与额外.gz写盘（两份QB L8877；磁盘模型）|gzip本体GiB内存假说弱；其他内存因素未知|工作盘额外空间需求未被pigz消除|结合缺文件形状，ENOSPC升为中等置信首选资源假设|
|没有历史df/quota/ulimit/cgroup/kernel和压缩器rc|不能彻底排除打开输出前SIGKILL或后续外部清理|没有直接ENOSPC证据，也可EFBIG/配额/tar失败等|已区分典型中途SIGKILL与写错误，仍不能唯一锁定真实触发|
|stage1 fake self-SIGKILL（original_archive_probe.json）|包装程序在尚无输出时自杀才形成缺文件|假exit1也没创建输出|仅证明mic忽略rc；不等价于本阶段真压缩器已写一半的SIGKILL|

### 由成功吞吐估算失败时的写出量

用户指定的2,580,797,440B/73s是**输入tar速率**35,353,389.589B/s；用成功目录输出696,473,433B（images.html L14）换算平均压缩比0.269868，得到输出速率约9,540,731.959B/s。1187398的42.433秒对应约**404.842MB / 386.087MiB**输出，1189686的29.828秒对应约**284.581MB / 271.398MiB**输出。这些仅是同速度/同压缩比且确实ENOSPC时，tar已形成后的工作盘可用空间粗估；pigz速度未经QB校准，第二个数只是假用gzip速率的投影，不是测量。条件、公式与不确定性见签名报告第五节及 [估算JSON](../evidence/signature/qb_space_estimate.json)。

### 不可照单接受的推理起点

- `rc=-9` 只表示直接子进程被 SIGKILL，**不证明 OOM**；必须配合内核或 cgroup 证据。其他负返回码也代表信号。若通过 shell 运行，可能变成 137，而本路径传列表、无 shell。
- gzip 常驻内存很小使全机 OOM 直接选 gzip 的解释较弱，但 OOM 的选择还受 cgroup 范围、oom_score_adj、其他存活进程影响，不能说“绝不会选它”；文件页缓存和 tmpfs 也可能计入 cgroup。
- 真gzip/pigz中途SIGKILL在本实验都留下坏半成品，mic直接move；真EFBIG都删除输出并触发缺文件。可捕获信号也可cleanup、打开输出前被杀也可能无文件，所以签名提升相对优先级，不唯一证明ENOSPC。
- **公开 mic 日志戛然而止不证明 mic 自己或整个步骤死了。** `archive._call_external` 捕获 stderr 后丢弃，未捕获 Python traceback 可只写控制台。已运行原始代码探针，stage1 fake exit1和尚未创建输出就self-SIGKILL均得到FileNotFoundError（仅证诊断丢失）；stage2b真中途SIGKILL留半成品而move成功，见签名报告。历史fake探针：`evidence/original_archive_probe.json`、`evidence/original-exit1-console.log`、`evidence/original-sigkill-console.log`、`evidence/original-exit1-mic.log`、`evidence/original-sigkill-mic.log`。

结论：对“外部打包/压缩失败诊断被丢弃，最终由缺压缩输出触发move异常”的判断置信度高；两次mic返回1和QB正常失败均已确认。“mic自己被杀/步骤突然终止”不符合控制台证据。真压缩器签名使“写失败后主动cleanup”比“已压缩一段后SIGKILL”更吻合两次QB；ENOSPC提高为首选资源假设（中等置信），而非已证实根因。典型中途SIGKILL与QB签名不吻合；可捕获信号、EFBIG/配额、tar先失败、打开输出前被杀/别人清理等仍需原始rc/stderr及资源证据排查。

## 发布校验补充

成功ks当前下载MD5与MD5SUMS不一致（expected d6525a80cb6c07fc27554f093874d864 / actual ba215c35a7b10975c6f69956528f81cc）；目录L10修改时间23:20晚于校验清单L5的19:13。其余已下载且可核验的packages/files/xml/manifest均匹配，见 `evidence/published_md5_check.json`。不能把当前ks当作成功构建输入逐字节副本；日志与原文件均保留。

## stage3 稀疏归档收益与证据边界（2026-10-08）

普通用户未挂载ext4文件实验中，中间tar从2,147,491,840 B缩到697,487,360 B（减少67.52%），gzip体积基本相同；普通提取变稠密，稀疏提取还原洞且内容哈希一致。见 [稀疏实验](sparse_experiment.md) 与 [原始结果](../evidence/sparse/summary.json)。这进一步支持原完整中间tar造成磁盘压力的机制，**不能证明历史worker确实ENOSPC**。真实0917按相同分配比例外推2.581 GB→约0.838 GB，属于条件估算，真实洞图仍未知。

最终日志/现场签名判定保持：两次QB更吻合压缩写失败后主动清理输出，ENOSPC为最可能资源触发（中等置信）；mic忽略压缩器rc和输出导致FileNotFoundError掩盖原始原因（高置信）。真实中途SIGKILL留下坏.gz、旧mic直接move，和两次QB缺文件不同；不是所有SIGKILL时机都已排除。EFBIG/配额、可捕获信号、tar先失败等仍需原始rc/stderr和worker资源记录。用户已取消整镜像baseline/space/oom，不再将sudo实验列为下一步。总部真实源码现已取得：c446578已修四种压缩/解压rc检查，eadc8fd5使稀疏归档opt-in；容量触发仍为缓解。新方案不能倒推旧QB errno，见hq_patch_review.md。
