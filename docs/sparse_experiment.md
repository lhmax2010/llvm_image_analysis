# 稀疏归档现场实验（2026-10-08）

普通用户 UID 1000，GNU tar 1.35、gzip 1.12；没有 sudo、挂载、整镜像构建或刷写。驱动为 [run_experiment.py](../evidence/sparse/run_experiment.py)，逐命令参数、返回码、单次墙钟时间及 stat 分配块见 [summary.json](../evidence/sparse/summary.json)；原文输出在 evidence/sparse/。这是打包收益实验，真实压缩器失败现场签名已在 [signature_experiment.md](signature_experiment.md) 完成。

## 输入与方法

在 work/sparse/ 下执行 truncate -s 2147483648 filesystem.img；2 GB 采用 2 GiB（2,147,483,648 B）。mkfs.ext4 -F -E lazy_itable_init=0,lazy_journal_init=0 直接格式化文件，随后 debugfs -w 的 write 将 600 MiB（629,145,600 B）不可压缩随机文件写入 /random-payload。输入文件实际占用 697,483,264 B，另含 ext4 元数据/日志等分配块。没有在任意偏移破坏文件系统的回退写法。见 [mkfs](../evidence/sparse/mkfs.log)、[debugfs write](../evidence/sparse/debugfs-write.log)、[inode stat](../evidence/sparse/debugfs-stat.log)、[只读 e2fsck](../evidence/sparse/e2fsck-readonly.log)。

归档分别为 tar -C work/sparse -cf normal.tar -- filesystem.img 和 tar -S -C work/sparse -cf sparse.tar -- filesystem.img；实际驱动使用绝对路径。gzip -c 将结果写入各自 .tar.gz，保留中间 tar 供核验。所有生成大文件留在 work/sparse/，不推送。time.monotonic() 计时，不是 CPU 时间；每项单次、缓存/磁盘负载未标准化，不能当稳定性能基准。

## 实测

|项目|普通 tar|tar -S|
|---|---:|---:|
|tar 文件大小 B|2,147,491,840|697,487,360|
|tar du 实际占用 B|2,147,491,840|697,491,456|
|tar 用时 s|3.123|13.417|
|gzip 输出 B|630,732,468|629,320,754|
|gzip 用时 s|17.293|11.512|
|提取后逻辑大小 B|2,147,483,648|2,147,483,648|
|提取后实际占用 B|2,147,487,744|697,479,168|
|GNU header typeflag|0|S|

中间 tar 减少 1,450,004,480 B（67.52%）；压缩包只减少 1,411,714 B（0.22%）。这验证了核心收益是跳过空洞的中间 tar 写盘；零字节原本就容易压缩。当前机器 tar -S 较慢，gzip 较快，合计 tar+gzip 为 20.416s vs 24.928s；不能声称整体提速。

GNU tar -xf sparse.tar 不需要再带 -S；提取文件仍有空洞。两个提取物与输入 SHA256 全相同：470f71672d4236200a452921708ab681b5f92bf5270c74218c4f4f43e4f3410c。普通提取物分配量较逻辑量多 4096 B，以 stat.st_blocks*512 原值记录，不能用逻辑大小替代实际占用。

## tar -tvf 的差异

[普通列表](../evidence/sparse/normal-list.log) 和 [稀疏列表](../evidence/sparse/sparse-list.log) **完全相同**，都显示成员逻辑大小 2,147,483,648 B；-tvf 不直观显示节约的归档物理量。因此列表相同不证明 tar 未使用稀疏格式。驱动读取首部 typeflag 分别为 0 和 S，header size 字段也不同；档案 stat/du 才显示容量差异。该 GNU 格式取自本机默认，不能由本机格式断言所有部署都选择此格式；已取得总部代码并未显式指定tar --format。

GNU 手册解释存储洞位置/真实内容并在提取时恢复洞：[Archiving Sparse Files](https://www.gnu.org/s/tar/manual/html_node/sparse.html)。GNU 稀疏成员属于扩展格式；第三方解码者需理解洞映射：[Tar Internals](https://www.gnu.org/software/tar/manual/html_chapter/Tar-Internals.html)。上述外部文档只用于格式背景，具体容量/哈希由本地实验直接验证。

## 与 0917 对照及条件估算

0917 五个成员逻辑量合计 2,580,786,618 B，目录列示 .tar.gz 696,473,433 B；旧 GNU tar 中间量模型 2,580,797,440 B，见 [log_forensics.md](log_forensics.md)、[disk_model.json](../evidence/disk_model.json)。成功档案本身未下载，真实分配块/洞图未知。

一种外推：若真实镜像分配比例与本实验相同（约 32.48%），中间 tar 从 **2.581 GB 降到约 0.838 GB**，减少约 1.743 GB。另一种外推：若真实数据与本实验的稀疏 tar/gzip 比率相同，则约 0.772 GB。这两种估算的 0.77–0.84 GB 只是条件场景，**不是可信区间，也不是实测 worker 剩余空间或真实 tar 上界**；真实软件数据可压缩，gzip 696 MB 不能等同分配块 696 MB。计算见 [extrapolation.json](../evidence/sparse/extrapolation.json)。要收紧估算，QB 需记录每个源镜像 stat.st_blocks、文件系统洞图/du 与实际 sparse.tar 大小。

以实际磁盘分配量 A、稀疏 tar 量 S、压缩结果 C、其他工作量 O 表示，同盘非流式峰值模型从 A+T+C+O 变为 A+S+C+O。独立流式 tar | gzip/pigz 则去掉整个中间 T/S，仅剩 A+C+O 加管道缓冲；与 -S 可叠加，并不会自动改变稀疏格式的解码兼容性。

## 顺序读流兼容性补充

旧 bootstrap spec 声称 bsdtar 稀疏 pax 档案不能被 lthor 刷写（0917 spec L95–99）。这个历史注释不能推出所有 GNU 稀疏档案或所有版本 lthor 都失败。

官方 Tizen tools lthor 3.4 [thor_tar.c](../evidence/src_snapshot/lthor-3.4/libthor/thor_tar.c) L42–64 取成员逻辑大小并调用 archive_read_data；L127–134 启用 tar/gzip/bzip2，L186–197 计算逻辑量。其顺序 API 有机会由库补零，不能把“顺序读”本身当成不兼容证明。用本机 **libarchive 3.7.2** 原样 API 读取普通 tar、GNU sparse.tar、sparse.tar.gz，三者都输出完整 2,147,483,648 B 且 SHA256 与输入一致；见 [probe](../evidence/sparse/libarchive_stream_probe.py)、[结果](../evidence/sparse/libarchive-stream-results.json)。这是 API 读流验证，未运行 lthor USB/协议或目标刷写，不能替代历史 worker/发布端版本与真实设备验证。

因此 -S 应 opt-in：已确认用支持洞映射的 GNU tar 提取、或完整补零且内容校验过的消费者可开；直接刷写且只支持普通成员/未知库版本的消费者暂不开。loop/raw/fs 是生产端名称，**不能仅据名称决定能否开**；稀疏成员最终消费者决定格式许可。无洞的文件收益有限；Android sparse 镜像编码与宿主文件系统空洞、GNU tar 稀疏编码是三件不同的事。
