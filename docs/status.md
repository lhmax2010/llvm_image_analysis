# 阶段状态（2026-10-08，stage3完成）

stage3完成总部真实源码/提交评审、逐hunk兼容性dry-run、普通用户稀疏归档实测、仅archive.py的实际补充diff、28组小测试和真实mic日志验证、最终报告。未安装或部署系统/worker；整镜像baseline/space/oom已取消，need_sudo.sh停用，不再要求sudo。流式仅作可选方案，未实现。

## 本阶段交付

- docs/analysis_report.md：最终结论、置信度、证据链、总部方案与补充建议、部署前提和仍需QB确认项。
- docs/hq_patch_review.md：两个真实提交身份、逐文件/链路/默认/风险评审、诊断真实来源、所有文件/hunk原文结果。
- downloads/src/hq_mic/0001-Improve-toybox-compatibility-and-sparse-file-handlin.patch：c446578原样Git导出。
- downloads/src/hq_mic/0001-Support-optional-sparse-tar-archiving-via-kickstart-.patch：eadc8fd5原样Git导出。
- evidence/hq/3cc580e-diagnostics.patch：额外实际诊断依赖。两份直接对2.1.3各失败一个archive hunk；补齐该原始依赖后顺序叠加通过，raw.py offset+17，无fuzz，没有编辑总部patch。
- docs/complementary.patch：只改archive.py imports/_call_external，保留总部四函数rc检查及tar fallback。候选先dry-run再正式写入，work组合基线及Gerrit HEAD均可叠加。
- evidence/complementary/：28组普通用户exit1/SIGKILL/实际roundtrip/fallback/目标保护测试，以及真实包import、实际CreatorError与真实msger日志验证。没有整镜像/root。
- docs/sparse_experiment.md与evidence/sparse/：2GiB未挂载ext4文件写600MiB随机数据；中间tar少67.52%、gzip体积少0.22%、提取稀疏/hash验证、条件外推及现代libarchive读流核验。
- evidence/src_snapshot/hq-mic/及SOURCE：Git HEAD分析依赖原样快照；完整clone只留downloads/src/hq_mic/mic，不推。

## 读过的文件和范围

完整读取两个format-patch及额外3cc580e诊断diff、HEAD mic/archive.py，以及对应所有修改hunk。总部源码读取/审查修改段与关键调用段：

- mic/archive.py；mic/cmd_create.py；mic/conf.py；mic/kickstart/custom_commands/micboot.py；tools/mic。
- mic/imager/loop.py、raw.py、fs.py、baseimager.py的打包及createopts赋值段。
- mic/rt_util.py的prepare_create、bootstrap宿主复制与sync_mic段。
- mic/utils/misc.py的get_file_size/show_tar_diagnostics；utils/fs_related.py的find_binary_path；utils/runner.py的quiet；utils/errors.py的CreatorError。
- mic/msger.py的info/warning/raw与stdout/stderr/文件handler关键段；mic/__init__.py；plugins/imager/loop_plugin.py、raw_plugin.py、fs_plugin.py的creatoropts入口。
- 本地旧mic2.1.3对应段、五份QB控制台已有逐行取证、stage2b实验/原始gzip/pigz相关源码签名、稀疏实验全部结果。官方lthor3.4 thor_tar.c与thor.c读流接口关键段。

这是指定修改/链路评审，不声称逐行审计整个仓库。CLI create_parser与vendored pykickstart的Mic_Bootloader实际只读执行（8+2例），没有运行mic main或imager do_create。

## 未读/未取得/未验证

- 未逐行阅读HEAD其余无关文件、全部vendored pykickstart/requests/urlgrabber及整仓历史；最近15个commit只查看列表，对3cc/c446/eadc读实际diff，其余不声称审过。
- 手工eadc8fd5.patch不存在，无可比较对象；以真实Git导出为准，不再追索该手工版。
- sandbox/dkson95/clang及其patch_archive.py仍未取得，本轮分支是sandbox/jaehoon80/devel，不能混为同一源码。
- 未验证真实lthor USB/目标设备刷写或worker部署，libarchive3.7.2读流正确不推广到历史所有版本/格式。
- 未取得历史QB压缩器rc/stderr、失败时df/inode/quota及内核/cgroup事件；真实ENOSPC未执行，EFBIG写错误路径与签名不能当实际worker errno。
- 0917公开KS MD5仍与发布MD5SUMS不符，待QB原始输入hash；没有下载成功大tar.gz。

## 最终判定与推送

两次QB最吻合写失败后主动清理输出，ENOSPC为最可能资源触发（中等置信）；旧mic丢弃rc/输出并move缺文件的缺陷高置信。典型中途SIGKILL签名不同。“pigz几秒被杀、mic死了”被QB traceback/返回1/普通failed否定。总部-S容量方案是缓解，c446已经部分修错误诊断；补充diff加强统一日志/CreatorError和同盘容量观察。

阶段提交信息stage3: hq patch review and complementary patches；提交后推origin main并核验本地HEAD/远端main一致。此前最新已推stage2a2为ae6ba089b127ed24872ebb7ef85f9cf110a5a5a0，历史stage1/2a/2b证据保留。最终commit hash在对话返回，不向报告写入无法稳定自引用的hash。
