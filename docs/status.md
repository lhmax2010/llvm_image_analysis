# 阶段状态（2026-10-06，stage2a2 fix -c position）

## 计划
1. 下载材料和逐行取证。
2. 对应源码/补丁调查。
3. sudo 与预算检查；真实 mic 基线、loop ENOSPC、cgroup OOM 复现。
4. 源码补丁与回归测试，最终报告。

## 进度
- 阶段一完成：所有要求的成功小文件、两次失败日志/ks、三个 repomd.xml 已下载；未下载成功 tar.gz。
- stage1四个QB匿名请求各一次均重定向登录；stage2a用户提供五份完整控制台，现在已取得实际mic命令、traceback与mic返回状态。见docs/qb_console_forensics.md。
- 阶段二完成到可匿名获取边界：官方 mic 2.1.3 release 与三个 snapshot bootstrap SRPM 已取得；两个 Git 镜像是旧版本，sandbox 分支匿名未取得。
- 阶段三日志/代码取证完成：见 docs/log_forensics.md、docs/code_reading.md。
- 已运行原始 archive 的无需 root 假压缩器探针，以及 pigz 2.8/gzip 64 MiB 数据的资源量级探针；不能冒充完整镜像复现。
- sudo -n true 检查失败，输出需要密码；已按用户要求停止复现及补丁实施，未猜测/读取密码。证据 evidence/sudo_check.txt。
- 用户首次执行baseline在parser层退出2，原始evidence/baseline-20261006-211839-*完整保留。stage2a修正need_sudo.sh：-c移入cr auto参数，--non-interactive移至全局位置，补--release并对齐QB的-o/-k；只读完整参数解析与--help通过。未调用sudo、未重新建镜像。见docs/baseline.md。
- docs/sampler.py保留；docs/patch_proposal.md仍为未实施设计稿，源码补丁未生成。
- 按用户新要求整理Git归档：.gitignore排除大文件/二进制/完整源码；直接依赖源码原样快照到evidence/src_snapshot，报告证据链接指向快照。
- 仓库目标：https://github.com/lhmax2010/llvm_image_analysis.git；本地main已初始化；stage1已提交推送；stage2b已提交推送；本阶段提交信息为stage2a2: fix -c position。暂存区大小/文本/快照/链接校验通过（evidence/git_stage1_validation.json）；推送状态以本地HEAD与远端main实际引用核验，后续阶段规则见docs/repository_workflow.md。

- stage2b完成：真gzip1.12/pigz2.8共22组实验，含正常/EFBIG/SIGKILL/默认SIGXFSZ及原mic打包函数8组；只用普通用户，无sudo/整镜像。详见docs/signature_experiment.md、evidence/signature/summary.csv。
- GNUgzip1.12官方release与Ubuntu1.12原档字节相同，源码/Ubuntu补丁原样追加快照；大文件均留work/signature且find扫描显式忽略，哈希/来源已登记。

- stage2a2完成：本地mic_local.py接受全局-c并在PluginMgr导入前加载配置，原始mic源码/入口未修改。完整普通用户试跑已到Root permission is required，实际loop插件导入另行验证；CONF各键名/值与真实ConfigMgr一致。见docs/baseline.md和evidence/baseline-dryrun-nonroot-result.json。

## 已闭合结论
- 两份公开mic.log仍止于压缩启动行，但新增1187398/1189686控制台都含shutil.move的FileNotFoundError、mic returned 1、QB正常failed链；gzip到首traceback42.433秒，pigz29.828秒。“pigz几秒就被杀、mic死了”被否定，子压缩器是否受SIGKILL仍未知（两份full-log L8878–8955）。
- archive丢弃压缩子进程rc/输出；stage1尚未创建输出的fake exit1/self-SIGKILL都报FileNotFoundError。stage2b真写错误也报FileNotFoundError，但真中途SIGKILL留坏.gz、move True，证明旧fake探针不能代替真实现场签名。
- 成功压缩日志区间 73 秒、目录列示输出 696,473,433 字节：evidence/20260917.132101-packing.txt、downloads/indexes/20260917.132101-images.html。
- 0917/0930 的 bootstrap 源 RPM 完全相同；1003 加入 pigz 2.8；三次运行都复制宿主 mic：evidence/more_downloads.json、evidence/src_snapshot/mic-bootstrap-20261003.102419/packaging/mic-bootstrap.spec、三个原始 log L16。
- .tar 暂存在工作 tmpdir 的 build/imgcreate-*/out；最终 outdir 不改变这部分磁盘需求：evidence/src_snapshot/mic/mic/archive.py、evidence/src_snapshot/mic/mic/imager/baseimager.py。

## 需要我拍板的事项
- 请用户自行在终端认证sudo或运行 docs/need_sudo.sh；这是用户任务文本的显式停止条件，不是工具自动审批拒绝。
- 请提供用本人权限取得的 sandbox/dkson95/clang clone 路径（仍须将分析产物放本工作目录）或 packaging/patch_archive.py 原文；旧 GitHub mirror 缺该 ref，Tizen 服务不可匿名取得。
- 完整QB控制台与mic状态已补齐；仍缺压缩器rc/stderr、worker工作盘及内核/cgroup资源证据。

## 挂账
- 成功ks当前MD5不匹配发布MD5SUMS，需取QB原始输入，不能认定逐字节等同：evidence/published_md5_check.json、downloads/indexes/20260917.132101-images.html。
- 外部打包/压缩失败后的缺文件move异常已确认；资源触发未定性，ENOSPC优先（中等置信）；真中途SIGKILL现场不吻合QB，写错误cleanup形状吻合，特定errno仍需直接证据。mic被直接杀死/步骤突然超时不符合本次控制台收尾。
- 首次基线只到参数错误；完整镜像基线、loop磁盘满、MemoryMax限额、内核OOM记录尚未完成。
- 源码补丁及其新行为测试待复现阶段；未知 sandbox 脚本无法逐项评审。patches/README.md注明未生成patch，未将方案稿冒充已完成补丁。

## 独立出现的基线记录补充

本轮签名实验期间，evidence/中新增baseline-20261006-214442-*文本。它们不是本轮signature驱动生成，本轮未运行sudo/基线。仅原样归档：console.log显示参数已解析，随后Plugin dir不存在、Can't support subcommand loop，返回2；没有完成整镜像。stage2a2已修本地入口及need_sudo.sh的配置加载时序；普通用户试跑和实际插件导入验证通过，完整root基线仍待后续。
