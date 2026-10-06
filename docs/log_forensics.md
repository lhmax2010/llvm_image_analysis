# mic 日志取证（2026-10-06）

## 材料与证据边界

stage1 部分据三份公开 mic.log；stage2a 新增用户提供的五份QB控制台，完整分析见 [qb_console_forensics.md](qb_console_forensics.md)。两类日志保留独立证据边界；下面打包原文仍是旧 mic.log，具体判定已按控制台更新。原始文件未改动；下载 URL、字节数和 sha256 见 `docs/downloads.md`。完整逐行 diff：`evidence/20260917.132101-vs-20260930.105301.diff`、`evidence/20260930.105301-vs-20261003.102419.diff`。文件尾字节与关键词扫描见 `evidence/log_metadata.json`。公开mic.log时间带UTC；QB控制台只有时分秒，重叠段可与mic.log对应，但不补造未打印的时区。

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

## OOM 与 ENOSPC 证据对照（更新）

|证据|构建机 / cgroup OOM|工作目录 ENOSPC|现在的区分能力|
|---|---|---|---|
|两份控制台均move traceback、mic返回1、QB正常failed链（两份L8879–8955）|排除mic自己被直接杀死作为此次终止方式；不能排除压缩子进程被杀|相容：外部失败之后缺文件|此前“mic死了或异常只写控制台”现在确定为后者|
|两份没有压缩器stderr/rc，只有mic rc1（两份L8936；archive.py L66–110）|看不到-9，不能确认子进程OOM|看不到1+ENOSPC，不能确认磁盘满|压缩器SIGKILL与写失败仍不可区分|
|gzip单线程，镜像逻辑大小约2.40GiB；tar全量暂存（两份L8877；磁盘模型）|gzip本体消耗1GiB的解释弱；cgroup页缓存/其他进程仍未知|tar和gz额外空间机制成立|ENOSPC仍是优先资源假设，非直接证据|
|1003使用默认线程pigz（1189686 L8878）|线程/缓冲可能增内存；没有实际RSS/限额|中间tar没有消除|更换压缩器未解决缺输出形状，不证明同一资源触发|
|父任务failed/cancelled/timed out模板（1189639 L22536）|不代表OOM/worker lost|不代表磁盘满|子日志已证明普通失败传播，不是超时/取消实证|
|五份全文无ENOSPC/Killed/OOM事件，df/free子串全为包名/hash/路径等（QB报告第四节）|没有内核或memory.events|没有工作盘空闲块/ENOSPC|无法唯一判定真实资源原因|
|原始代码fake exit1和SIGKILL探针（original_archive_probe.json）|rc=-9也折叠成缺文件异常|模拟ENOSPC exit1同样折叠|与两次QB真实traceback形状相符，但不是资源实验|

### 不可照单接受的推理起点

- `rc=-9` 只表示直接子进程被 SIGKILL，**不证明 OOM**；必须配合内核或 cgroup 证据。其他负返回码也代表信号。若通过 shell 运行，可能变成 137，而本路径传列表、无 shell。
- gzip 常驻内存很小使全机 OOM 直接选 gzip 的解释较弱，但 OOM 的选择还受 cgroup 范围、oom_score_adj、其他存活进程影响，不能说“绝不会选它”；文件页缓存和 tmpfs 也可能计入 cgroup。
- gzip 写失败可能删除半成品 `.gz`，仅文件缺失并不能区分写失败和终止；SIGKILL 的真实 gzip 也可能留下半成品，不能把文件缺失当作 SIGKILL 的必要特征。
- **公开 mic 日志戛然而止不证明 mic 自己或整个步骤死了。** `archive._call_external` 捕获 stderr 后丢弃，未捕获 Python traceback 可只写控制台。已运行原始代码探针，fake exit1 和 sigkill 都得到 `FileNotFoundError` 控制台 traceback，而 mic.log 只保留启动行：`evidence/original_archive_probe.json`、`evidence/original-exit1-console.log`、`evidence/original-sigkill-console.log`、`evidence/original-exit1-mic.log`、`evidence/original-sigkill-mic.log`。

结论：对“外部打包/压缩失败诊断被丢弃，最终由缺压缩输出触发move异常”的判断置信度高；两次mic返回1和QB正常失败均已确认。“mic自己被杀/步骤突然终止”不符合控制台证据。外部资源原因仍未闭合，ENOSPC是优先假设（低至中置信），压缩器子进程OOM/SIGKILL或tar先失败仍待直接rc/stderr、磁盘/cgroup/内核证据。仅有FileNotFoundError不足以证明哪种触发。

## 发布校验补充

成功ks当前下载MD5与MD5SUMS不一致（expected d6525a80cb6c07fc27554f093874d864 / actual ba215c35a7b10975c6f69956528f81cc）；目录L10修改时间23:20晚于校验清单L5的19:13。其余已下载且可核验的packages/files/xml/manifest均匹配，见 `evidence/published_md5_check.json`。不能把当前ks当作成功构建输入逐字节副本；日志与原文件均保留。
