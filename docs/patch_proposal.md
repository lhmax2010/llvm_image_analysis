# 补丁方案（阶段稿，未实施）

2026-10-06 的 `sudo -n true` 返回“需要密码”（`evidence/sudo_check.txt`）。依用户明确要求，本轮停止在复现前；以下为根据已确认代码缺陷整理的设计，**不是已交付/已验证 patch**。`patches/` 暂不放伪完成补丁。真实ENOSPC/OOM和完整mic基线尚未完成。stage2a新增两份真实QB缺文件traceback并修正首次baseline的parser错误；只读参数验证通过，未新增实际源码patch。

## 已确认需要修复的部分

`evidence/src_snapshot/mic/mic/archive.py` L66–83 捕获 rc 和输出，L102、129、153、180、289 丢弃它们；L346 未验证结果直接 move。已用原始源码和 fake gzip 验证 rc=1 与 -9 被折叠成相同缺文件异常，见 `evidence/original_archive_probe.json`。

拟直接修改 mic 源码，而不是使用 bootstrap 的字符串替换脚本：

1. 统一所有外部压缩、解压和 tar 调用的返回码检查。保留命令参数列表、不经 shell；出错信息包含子进程 rc、完整安全转义命令、stderr 最后20行（设置总字节上限）。`rc=-9` 标注 SIGKILL，不能直接写成 OOM；其他负 rc 同样标注对应 signal。错误派生自 `CreatorError` 并在发生处写入 msger，确保 QB 的 mic.log 也看得到。stdout/stderr 独立捕获并解码，修正 `_do_untar` 的 bytes/None join。长输出使用有界读取/环形缓冲，避免 `communicate()` 对未知大输出造成额外内存。
2. `_make_tarball` 对内置 gz/bz2/lzo/zstd 压缩器使用流式管道：GNU `tar -C ... -cf - -- <files>` → `gzip/pigz -c` 等 → 同一目标目录的安全临时压缩文件。不落完整中间 `.tar`。不使用 shell，不加 `--sparse`，保留普通 tar 可刷写语义。
3. 必须等待并分别检查 tar 与压缩器的 rc。压缩器出错导致 tar SIGPIPE 时，优先报告下游原始写失败/SIGKILL，并附 tar rc，避免误判根因。启动第二个进程失败时关闭管道、终止并回收已经启动的 tar；中途异常也回收两端，避免孤儿进程。
4. 用 mkstemp 取代 mktemp；最终发布前检查产物存在，只有完整成功才原子 replace。失败清理半成品，保留已有最终文件。tar 不存在的 Python tarfile fallback 与未知自定义 compressor 回调维持兼容但同样做输出存在检查、失败清理；单文件 compress/decompress 不强制流式，但统一 rc 检查。
5. 在共享 make_archive 层打包前和 finally 中各记录 `df -B1 <输入/暂存目录>` 与 `free -m`，两者 rc/输出都注明；资源诊断失败不能覆盖原始打包异常。如需最终 CLI outdir 的 df，可在 package 调用层另加。`free -m` 是宿主视角，cgroup memory.current/events 仍应由 QB worker 收集。
6. 共享 archive 层被 loop、raw、fs 等 imager 使用，需要回归 tar/gztar/bztar/lzotar/zsttar 及单文件压缩/解压。现版本 `_do_zstd` 用于 zsttar，`_COMPRESS_FORMATS` 没有 zstd 注册，不顺便扩大 CLI 功能。

## 磁盘收益的当前模型

来自成功日志的 I（五个镜像逻辑大小）=2,580,786,618 字节，估计 GNU tar T=2,580,797,440 字节，目录列示压缩包 C=696,473,433 字节：旧打包约 `I+T+C=5,858,057,491` 字节，新打包约 `I+C=3,277,260,051` 字节，减少约 **2.40 GiB，44%**。计算见 `evidence/disk_model.json`，原始证据见 `docs/log_forensics.md`。

这不是完整基线实测，实际应将 I 换为分配块 I_alloc，并加缓存/bootstrap/安装目录等 O；如最终输出跨文件系统还需计入双份 C。不能在未复现的情况下声称已测得峰值或补丁已修复 QB。

## sandbox 各项的采用边界

|可见/待确认项|处理|理由与证据|
|---|---|---|
|bootstrap 强制 GNU tar|采用/保留|0917/0930 spec L95–99，1003 spec L104–108；保护 lthor 兼容性|
|bootstrap 提供 pigz 2.8|采用/保留可选压缩器|1003 spec L20、60–65、102–103；提速，未降低中间 tar 的磁盘占用|
|pigz `-p 2`|待拿到 sandbox 后评审；倾向改为可配置上限|只是任务举例，未知原补丁是否有该改动；本机20CPU探针默认17,392KiB、p2 3,800KiB，差13,592KiB，gzip1,804KiB，见 `evidence/compressor_probe.json`；不足以证明修复GiB级压力|
|失败后只检查文件存在|采用为末端防御，不能代替 rc/stderr|否则仍不能区分ENOSPC、信号和tar失败|
|bootstrap 中 patch_archive.py 文本替换|不能逐项评价；倾向迁至 mic 源码|没有取得脚本；三次运行还复制宿主mic，必须核实补丁在复制前后何时应用|
|对 bzip2/zstd/lzop 一致处理|采用|原函数均存在同样丢弃rc的问题，不能只修gzip|

## 待实施测试

- fake gzip 输出 ENOSPC 并 exit1：新错误必须有 rc=1、命令、stderr原文，最终文件不得发布。
- fake gzip 自杀 SIGKILL：新错误必须有 rc=-9/SIGKILL，不能叫作已证明OOM。
- fake tar 非零、gzip成功退出：必须仍失败，不发布不完整包；同时检查管道回收。
- 大于管道缓冲的输入、早退下游，验证不挂死及两个rc的优先级。
- gzip/pigz/bzip2/zstd 可用路径的真实小文件 roundtrip（缺少可选工具时明确skip），确认tar内容完整且没有稀疏pax特征。
- 无tar的Python fallback、目标文件已存在、含空格/以横线开头名称、假压缩器rc0却不产物等边界。

现有 `evidence/probe_scripts/original_archive_probe.py`（原执行位置work/） 是旧行为取证脚本，不能冒充上述新行为回归测试。
