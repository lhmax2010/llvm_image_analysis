# mic 日志取证（2026-10-06）

## 材料与证据边界

本报告只据实际下载内容判断，不将任务中提及的 traceback 当成已经拿到的证据。原始文件未改动；下载 URL、字节数和 sha256 见 `docs/downloads.md`。完整逐行 diff：`evidence/20260917.132101-vs-20260930.105301.diff`、`evidence/20260930.105301-vs-20261003.102419.diff`。文件尾字节与关键词扫描见 `evidence/log_metadata.json`。所有时间沿用日志的 UTC。

## 开头、选项与目录

### 20260917.132101

- mic 宿主与 bootstrap 都打印 2.1.3：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L1、19；机器分别为 `.202`、`.91`、`.168`，不是同一 worker。
- runtime=bootstrap 的实际行为由创建 bootstrap、复制宿主 mic、启动 chroot 证实：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L11–19。不是仅依据默认配置。
- ks 路径见 `downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L2、20，构建工作目录由打包命令得到：`downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L7426。
- 完整 mic 启动命令、显式 `--tmpdir/--cachedir/--outdir/--compress-image` 没有出现在公开日志；不能声称掌握同一整条命令。无 tmpfs 挂载输出也不能排除环境本身将 `/var/tmp` 放在 tmpfs。

### 20260930.105301

- mic 宿主与 bootstrap 都打印 2.1.3：`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L1、19；机器分别为 `.202`、`.91`、`.168`，不是同一 worker。
- runtime=bootstrap 的实际行为由创建 bootstrap、复制宿主 mic、启动 chroot 证实：`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L11–19。不是仅依据默认配置。
- ks 路径见 `downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L2、20，构建工作目录由打包命令得到：`downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L7366。
- 完整 mic 启动命令、显式 `--tmpdir/--cachedir/--outdir/--compress-image` 没有出现在公开日志；不能声称掌握同一整条命令。无 tmpfs 挂载输出也不能排除环境本身将 `/var/tmp` 放在 tmpfs。

### 20261003.102419

- mic 宿主与 bootstrap 都打印 2.1.3：`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L1、19；机器分别为 `.202`、`.91`、`.168`，不是同一 worker。
- runtime=bootstrap 的实际行为由创建 bootstrap、复制宿主 mic、启动 chroot 证实：`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L11–19。不是仅依据默认配置。
- ks 路径见 `downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L2、20，构建工作目录由打包命令得到：`downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L7366。
- 完整 mic 启动命令、显式 `--tmpdir/--cachedir/--outdir/--compress-image` 没有出现在公开日志；不能声称掌握同一整条命令。无 tmpfs 挂载输出也不能排除环境本身将 `/var/tmp` 放在 tmpfs。

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

## 三个具体问题

1. 成功 gzip 启动在 `downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log` L7427 的 19:11:52；下一条创建 manifest 在 L7428 的 19:13:05，相隔 **73 秒**。这是 gzip 加返回/改名等开销的日志区间，不能精确拆成纯 CPU 压缩时间。tar 段为 15 秒（L7426–7427），打包至 manifest 共 88 秒（L7425–7428）。公开目录 `downloads/indexes/20260917.132101-images.html` L14 列出输出 **696,473,433 字节（696.47 MB / 664.21 MiB）**，未下载 tar.gz 实体，因此是服务端目录宣称大小。
2. 0930 的最后一行是 `downloads/logs/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log` L7367，16:54:24 gzip 启动。**公开日志没有 traceback**，无法计算“gzip 启动到 traceback”的秒数，也无法确认后续 mic 是否仍活着。不存在 gzip 的 ENOSPC stderr、`Killed` 或进程终止 signal 记录。全文出现的 `signal` 都是 `org.tizen.system-signal-sender` 包名/路径，不能算被杀证据（行号详见 `evidence/log_metadata.json`）。
3. 1003 同样在 `downloads/logs/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log` L7367，16:22:01 pigz 启动行结束；最后一行与启动是同一条记录，故时间差 **0 秒**，不能当作 pigz 运行 0 秒就死亡。最后有完整换行，命令与文件名完整，无半行/半个字符截断；存在语义上的未完成，但没有字节级截断证据（`evidence/log_metadata.json`）。没有后续时间戳，未知实际终止时间。

## OOM 与 ENOSPC 证据对照

|证据|构建机 / cgroup OOM|工作目录 ENOSPC|区分能力|
|---|---|---|---|
|两次公开日志都止于压缩启动行|相容：mic/步骤被杀可如此|也相容：stderr/traceback 未进入 mic 日志|弱；须取完整控制台|
|gzip 没有 stderr 和 rc|无法看到 -9|无法看到 1 + ENOSPC|不能据缺失排除 ENOSPC|
|gzip 单线程，镜像总逻辑大小约 2.40 GiB|gzip 本体通常仅几 MiB；“gzip 自己耗尽 1 GiB”缺乏依据|先 tar 再 gzip 有明显额外磁盘需求|机制上 ENOSPC 值得优先验证|
|1003 从 gzip 改为默认线程 pigz|会增加线程和缓冲；是否越限未知|中间完整 tar 仍然存在，未减少磁盘峰值|不能说明已修复 ENOSPC|
|两次失败大小略低于成功|不能直接说明内存足够|同样不能说明剩余磁盘足够|须看 worker 实际资源|
|未获得 dmesg / memory.events / df|没有 OOM 直接证据|没有 ENOSPC 直接证据|真实环境根因未闭合|
|原始代码 fake gzip exit 1 与 SIGKILL 探针|SIGKILL 子进程 rc=-9 后仍转为缺文件异常|模拟 rc=1 + ENOSPC 文字也转为同样异常|证实原始诊断丢失，并非真实 OOM/ENOSPC 复现|

### 不可照单接受的推理起点

- `rc=-9` 只表示直接子进程被 SIGKILL，**不证明 OOM**；必须配合内核或 cgroup 证据。其他负返回码也代表信号。若通过 shell 运行，可能变成 137，而本路径传列表、无 shell。
- gzip 常驻内存很小使全机 OOM 直接选 gzip 的解释较弱，但 OOM 的选择还受 cgroup 范围、oom_score_adj、其他存活进程影响，不能说“绝不会选它”；文件页缓存和 tmpfs 也可能计入 cgroup。
- gzip 写失败可能删除半成品 `.gz`，仅文件缺失并不能区分写失败和终止；SIGKILL 的真实 gzip 也可能留下半成品，不能把文件缺失当作 SIGKILL 的必要特征。
- **公开 mic 日志戛然而止不证明 mic 自己或整个步骤死了。** `archive._call_external` 捕获 stderr 后丢弃，未捕获 Python traceback 可只写控制台。已运行原始代码探针，fake exit1 和 sigkill 都得到 `FileNotFoundError` 控制台 traceback，而 mic.log 只保留启动行：`evidence/original_archive_probe.json`、`evidence/original-exit1-console.log`、`evidence/original-sigkill-console.log`、`evidence/original-exit1-mic.log`、`evidence/original-sigkill-mic.log`。

结论：对“压缩失败信息被丢弃”的判断置信度高；对两次真实失败的外部触发原因，公开材料不足以定性。暂将 ENOSPC 作为优先验证假设，OOM 和 worker/步骤外部终止仍待查。

## 发布校验补充

成功ks当前下载MD5与MD5SUMS不一致（expected d6525a80cb6c07fc27554f093874d864 / actual ba215c35a7b10975c6f69956528f81cc）；目录L10修改时间23:20晚于校验清单L5的19:13。其余已下载且可核验的packages/files/xml/manifest均匹配，见 `evidence/published_md5_check.json`。不能把当前ks当作成功构建输入逐字节副本；日志与原文件均保留。
