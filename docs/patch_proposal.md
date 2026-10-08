# 总部后态的实际补充补丁（2026-10-08，stage3）

交付 [complementary.patch](complementary.patch)，只改mic/archive.py imports和_call_external。总部真实c446578已加四压缩/解压函数rc检查，不重复改它们；eadc8fd5的开关与tar回退代码也保留。完整逐行评审及真实diff/hunk见 [hq_patch_review.md](hq_patch_review.md)。流式只作可选方案，未实现。

## 基线及叠加

两份Git导出patch对干净2.1.3单独dry-run都缺一个archive上下文hunk，不能假称“两份直接叠加”成功。先在work副本补齐真实3cc580e诊断依赖，再依次原样apply c446578、eadc8fd5；不编辑总部patch。我们的候选diff dry-run成功后才写正式docs文件，并apply到work副本，真实Gerrit HEAD同样dry-run成功。见 [验证JSON](../evidence/hq/complementary-validation.json)、[HQ HEAD dry-run](../evidence/hq/complementary-gerrit-dryrun.log)。downloads/src/mic及总部clone未修改。

## 实际改变

1. _call_external保留返回tuple接口。stdout/stderr分别communicate，兼容字段outdata返回stdout+stderr；非零先warning记录rc和安全引用完整命令，raw记录未截断stderr与stdout，再抛CreatorError，异常包含输出末20行。启动失败同样抛CreatorError，不调用会直接sys.exit(2)的msger.error。
2. 压缩前对gzip/pigz/bzip2/pbzip2/lzop/zstd取得实际输入文件大小和其输出目录shutil.disk_usage.free，写入日志。输入为中间.tar时就是用户要求的.tar大小。解压不误记该日志；查询失败warning，仍允许原命令报告实际失败。不是容量保证，不因未压缩输入大于free而提前拒绝。
3. 唯一非零返回例外是tar -S初次尝试，供总部旧代码回退普通tar；stderr仍记录。若这里统一先抛错会破坏HQ兼容性，因此保留例外。普通tar最终非零、四种压缩及解压非零均抛CreatorError。总部四函数已有rc检查保留，可在JSON核验函数块完全未改。

## 普通用户小测试

[test_archive.py](../evidence/complementary/test_archive.py) 的26例全部通过：gzip、pigz、bzip2、zstd、lzop各压缩/解压exit1及SIGKILL（20例），真实gzip roundtrip、成功tuple、拒-S后总部fallback、真实稀疏gztar roundtrip、完整_make_tarball两个失败保留既有最终文件。使用真实子进程，只有msger消息记录和HQ递归/var/tmp诊断stub；CreatorError使用真实基线模块。见 [results.json](../evidence/complementary/results.json)、[test.log](../evidence/complementary/test.log)。此外独立真实包导入/真实msger文件日志验证，stderr空白未截断保留，见 [真实日志](../evidence/complementary/real-mic.log)；另有未修改Gerrit代码两组gzip失败测试，确认总部自身已报告rc和输出。所有测试无root、挂载、整镜像。

原stage2b真EFBIG/SIGKILL签名证明旧mic诊断缺陷，但不是新补丁测试；本次新测试单独记录。假stderr写入ENOSPC文本只验证日志通道，不能冒充真实ENOSPC复现。

## 副作用与残留风险

- 分离stdout/stderr后按stdout+stderr合并，失去跨流时间交织；日志保留全部stderr，异常只取20行。非UTF8用replace转文本，不声称保留原始字节；communicate仍无界缓冲，未扩大为新的I/O架构。
- CreatorError替代大多数OSError会被mic正式错误处理分支捕获，改进控制台/mic.log可读性；-9只写rc，不自动定OOM。
- 总部任意-S失败后回退普通tar的策略未改，可能在ENOSPC时扩大再次写盘；初次失败已新增原文日志帮助识别。
- 依本轮限定范围，mktemp、无独立move前存在/完整性检查、config字符串布尔正规化、fallocate缺失/rc处理、失败后df/free/cgroup采样均未实施。它们不再作为stage3未完成项，部署风险/后续项已在最终报告列明。
- 容量耗尽仍可发生；总部稀疏容量方案是缓解，c446已部分修复错误处理，我们补齐日志渠道与领域异常，不宣称消除ENOSPC。

## 流式作为后续独立选项

tar | gzip/pigz可默认关闭、独立于-S，并与-S叠加去掉整个中间tar。须分别检查两端rc、关闭管道并回收进程，兼顾SIGPIPE优先级、输出原子发布、并发RSS与gzip头部变化；稀疏格式消费端兼容性不因流式消失。本轮不生成流式diff。容量模型见 [sparse_experiment.md](sparse_experiment.md)。
