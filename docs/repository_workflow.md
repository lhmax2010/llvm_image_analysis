# 阶段提交与证据归档规则

用户在本会话明确要求将分析目录初始化为main，并推送到 https://github.com/lhmax2010/llvm_image_analysis.git。后续完成一个阶段即提交并推送一次，不能将中途状态称为阶段完成；任何凭据失败都停止并请用户自行配置，不猜密码、不读取/写入token。

|阶段|提交信息|完成门槛/状态|
|---|---|---|
|1|stage1: log and code forensics|文本证据、源码快照与忽略规则；已完成|
|2a|stage2a: qb console forensics + baseline command fix|QB完整控制台与首次参数修正；已完成|
|2b|stage2b: compressor failure signatures|普通用户真压缩器与原mic打包函数现场签名；已完成|
|2a2|stage2a2: fix -c position|插件加载时序与普通用户启动验证；已完成|
|3|stage3: hq patch review and complementary patches|总部补丁原文评审、稀疏实测、以总部代码为基线的实际补丁/小测试、最终报告；已完成（本轮流式只作方案，补充diff限定archive.py）|

2026-10-08 用户取消原有整镜像 baseline/space/oom，旧计划的三个镜像复现阶段不再执行。当前只使用普通用户文件实验，不再要求 sudo。

首个提交信息按用户原文保持不变。后续阶段序号和内容如发生合理拆分，继续使用stageN前缀并在status.md记录实际阶段，不伪造完成。

提交前先更新docs/status.md，并核验git暂存区：不纳入work/、完整downloads/src/（唯一特例为用户指定的两个总部0001-*.patch原始导出）、缓存、RPM/deb/镜像/源码压缩包、任何超过5,000,000字节的文件或意外二进制。检查凭据只输出命中类别/文件路径，不能输出秘密原文。用户要求每阶段`git add -A`；仅在已检查忽略规则和新增文件范围后执行。

新产生的超过5MB文件追加精确忽略路径，并在docs/downloads.md登记本地路径、大小、sha256、来源URL；本地产物明确写“无下载URL，生成方式为…”。大证据先gzip，若仍超过5MB，纳入头尾各2000行的文本摘要并说明截断，原始与压缩大文件保留本地并忽略。压缩证据是用户指定的特例，其余二进制不纳入。当前没有超过门槛的evidence文件。

分析直接依赖的源码原样复制到evidence/src_snapshot/，保持相对路径，来源记入<仓名>.SOURCE.txt。不能给下载源码包编造Git分支/commit/checkout时刻；注明不适用或未知，并记录可核验的URL与sha256。sandbox到手后新增mic-bootstrap-sandbox/快照与对应SOURCE.txt；保留当前实际snapshot版本。源码快照用于核验，不是完整可构建仓库。

`git push -u origin main`，之后常规`git push`；不force-push、不覆盖远端既有历史。每次推送后核验远端main与本地HEAD一致。后续阶段对话只回一行“commit hash + 改动文件列表”；本次初始化推送另按用户要求给出最多3层的仓库文件树及总大小。

当前stage3全部交付完成，使用指定stage3 commit信息提交推送。总部clone忽略；依最新用户指令，downloads/src/hq_mic/下仅两个0001-*.patch原始导出可入库，其他downloads/src仍禁止。原样依赖快照保存在evidence/src_snapshot。
