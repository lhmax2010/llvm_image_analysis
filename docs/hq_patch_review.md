# 总部mic真实提交评审（2026-10-08，stage3）

源码通过用户指定的 git://review.tizen.org/git/platform/upstream/mic 成功clone，分支sandbox/jaehoon80/devel，HEAD eadc8fd5。没有使用SSH、sudo、系统安装或整镜像；认证账号/密码没有写入脚本、日志或回复。[clone来源](../evidence/hq/clone-provenance.json)、[最近15个提交](../evidence/hq/branch-log.txt)、[原样源码来源](../evidence/src_snapshot/hq-mic.SOURCE.txt)。旧HTTP403只说明此前HTTP入口不可用，不代表本次git协议失败。

## 提交身份与真实导出

|commit|作者|作者日期|subject|
|---|---|---|---|
|c446578d87b055984e5eeca04e2f485436f55759|Jaehoon Chung|2026-10-07T17:45:16+09:00|Improve toybox compatibility and sparse file handling during packaging|
|eadc8fd5c1288206601485c1dbff0ecdb1425bcd|Jaehoon Chung|2026-10-07T19:31:54+09:00|Support optional sparse tar archiving via kickstart and CLI|
|3cc580ebf07677610d58bd8f4b2c3b9ba0a7c15d|Jaehoon Chung|2026-10-07T11:39:10+09:00|Add diagnostics for /var/tmp usage and ulimit before tar operations|

两份用户指定提交原样导出，文件名保留git默认（都从0001开始）：

- [0001-Improve-toybox-compatibility-and-sparse-file-handlin.patch](../downloads/src/hq_mic/0001-Improve-toybox-compatibility-and-sparse-file-handlin.patch)：c446578。
- [0001-Support-optional-sparse-tar-archiving-via-kickstart-.patch](../downloads/src/hq_mic/0001-Support-optional-sparse-tar-archiving-via-kickstart-.patch)：eadc8fd5。

重要修正：**c446578已经检查gzip/pigz、bzip2、lzop、zstd压缩与解压rc，异常带命令、rc和合并输出；“gzip/pigz路径仍无rc/stderr”的判断不成立。** show_tar_diagnostics来自更早3cc580e，不是c446578新增；本次也取得并读取其真实diff，作为必要依赖附在 [3cc580e-diagnostics.patch](../evidence/hq/3cc580e-diagnostics.patch)，不是擅自改写两份总部补丁。

手工downloads/src/hq_mic/eadc8fd5.patch当前不存在，故没有可比对象，见 [比较记录](../evidence/hq/manual-comparison.log)。若存在时按要求应忽略index行和空白比较；本次不能声称已比较不存在的文件。后续一律以以上Git导出及commit内容为准。

## 逐文件逻辑：c446578（对照3cc580e后态）

以下源码行号引用HEAD的原样快照，变化本身另由真实patch核验；没有把HQ源码与旧2.1.3快照混用。

|文件|改动与含义|证据行号|
|---|---|---|
|mic/archive.py|四种压缩函数捕获tuple，非零抛OSError，包含命令/exit code/解码合并stdout+stderr；适用于压缩和解压。pigz/pbzip2仍按which自动选。c446单独时tar先默认-S，失败重跑普通tar并检查rc；eadc随后改为opt-in。|[archive.py](../evidence/src_snapshot/hq-mic/mic/archive.py) L85–113、115–143、145–170、172–200；c446 patch四个函数hunk和tar hunk|
|mic/imager/loop.py|打包前无条件find_binary_path(fallocate)，逐普通文件执行fallocate -d以回收零块/恢复洞；只对file记录大小，quiet的rc未检查。此处不受sparse_tar开关控制。|[loop.py](../evidence/src_snapshot/hq-mic/mic/imager/loop.py) L520–527；[fs_related.py](../evidence/src_snapshot/hq-mic/mic/utils/fs_related.py) L48–61；[runner.py](../evidence/src_snapshot/hq-mic/mic/utils/runner.py) L105–106|
|mic/utils/misc.py|普通文件用os.stat取逻辑/分配MB向上取整并取max；目录先试两种GNU du，失败退du -s -k。适配toybox/busybox，返回仍不是只按实际分配块估空间。|[misc.py](../evidence/src_snapshot/hq-mic/mic/utils/misc.py) L407–437|

兼容性风险：fallocate缺失时find_binary_path会抛CreatorError，并不是返回None后跳过；不支持-d时quiet rc被忽略。因此即使没有--sparse-tar，完整流程也新增依赖/物理打洞动作，不可宣称与2.1.3完全一致。对很大文件的零块扫描可能增加耗时；需核验bootstrap里的fallocate及所用文件系统。rc/stdout.decode没有errors策略，非UTF8诊断可能另抛UnicodeDecodeError；OSError没有设置真实errno，不能由异常类型本身确定ENOSPC。

## 逐文件逻辑：eadc8fd5与开关链路

|文件|改动/传递路径|源码行号|
|---|---|---|
|tools/mic|create公共parent_parser新增--sparse-tar，store_true，default=False；属于cr auto/loop/raw/fs子命令选项，而非全局入口前。|[tools/mic](../evidence/src_snapshot/hq-mic/tools/mic) L102–103|
|mic/cmd_create.py|CLI值为True才写configmgr.create['sparse_tar']，False不覆盖已有KS/config启用值。|[cmd_create.py](../evidence/src_snapshot/hq-mic/mic/cmd_create.py) L168–169|
|mic/kickstart/custom_commands/micboot.py|bootloader.sparse_tar初值False；解析--sparse-tar store_true/defaultFalse，序列化只有True时输出该旗标。|[micboot.py](../evidence/src_snapshot/hq-mic/mic/kickstart/custom_commands/micboot.py) L34、43–44、51–52|
|mic/conf.py|create.DEFAULTS加入False；KS读取bootloader.sparse_tar，True时写create['sparse_tar']=True。|[conf.py](../evidence/src_snapshot/hq-mic/mic/conf.py) L85、220–222|
|mic/imager/loop.py|packing(dstfile,imgdir,sparse=getattr(self,'sparse_tar',False))。|[loop.py](../evidence/src_snapshot/hq-mic/mic/imager/loop.py) L535–537|
|mic/imager/raw.py|同样将sparse值传到packing；不启用则False。|[raw.py](../evidence/src_snapshot/hq-mic/mic/imager/raw.py) L477–480|
|mic/imager/fs.py|单独tar命令插-S；不通过archive._make_tarball。压缩后缀由-czf/-cjf直接交给tar。|[fs.py](../evidence/src_snapshot/hq-mic/mic/imager/fs.py) L68–104|
|mic/archive.py|make_archive复制kwargs避免污染格式表，只给tar系加入sparse；_make_tarball传入_do_tar，_do_tar默认False，True先-S，非零回退普通tar，最后检查普通tar rc。|[archive.py](../evidence/src_snapshot/hq-mic/mic/archive.py) L282、303–317、358–378、456、486–490|

中间桥梁未在eadc修改但实际存在：rt_util.prepare_create取configmgr.create（[rt_util.py](../evidence/src_snapshot/hq-mic/mic/rt_util.py) L342–370），插件将creatoropts交各creator（plugins/imager/loop_plugin.py L37–40、raw_plugin.py L40–43、fs_plugin.py L33–35）；BaseImageCreator按createopts各键setattr（[baseimager.py](../evidence/src_snapshot/hq-mic/mic/imager/baseimager.py) L108–114），因此sparse_tar能成为imager属性，不需要额外白名单。

只读实际parser验证auto/loop/raw/fs各开/关共8例、bootloader开/关及序列化2例均通过，见 [parser驱动](../evidence/hq/parser_probe.py)、[结果](../evidence/hq/parser-results.json)。未执行mic main/do_create，也未绕过UID检查。

### (a) 默认是否完全等同2.1.3

**默认普通tar命令/loop-raw的先tar再gzip/pigz结构一致，整体错误行为和依赖不完全一致。** 新进程、未使用CLI/KS/config开启时False，_do_tar走tar -C DIR -cf TMP.tar MEMBERS；_make_tarball仍会压缩、move。总部已新增rc检查、诊断、fallocate及copy_function=shutil.copy，所以不能采纳commit message的“100% backward compatibility”作为完整证明。

CLI/KS在“开启=True，省略默认关闭”的语义一致，都只会启用，没有--no-sparse-tar关闭入口。siteconf则有额外风险：_parse_siteconf把值作为字符串update（conf.py L167–172），没有为sparse_tar正规化；配置写sparse_tar=False可能变成真值字符串。ConfigMgr.reset还复用DEFAULTS字典（L121–127），同进程多次KS解析的粘性需另验。本次新补丁范围只archive.py，不擅自修conf。

### (b) 开启后的完整命令与落盘

loop/raw GNU tar路径：`tar -S -C <target_dir> -cf <archive_dir>/tmpXXXX.tar <os.listdir成员...>`；单文件成员为basename。任何-S失败都会警告并重跑`tar -C <target_dir> -cf <tmp.tar> <members...>`，**不是只识别“不支持-S”才回退**；ENOSPC、读失败等也会触发，可能掩盖首个错误和重新增大临时tar。此时第二次stdout决定最终OSError（archive.py L303–317）。

仍先写一个完整的**稀疏编码tar档案文件**，再运行`pigz -f TMP.tar`（可用时）或`gzip -f TMP.tar`；不是写完整逻辑镜像的稠密tar，也不是流式tar|gzip。_make_tarball L368–378未改mktemp，压缩后直接move，无独立存在/完整性检查。没有GNU tar时Python tarfile fallback不接受/实现sparse参数（L372–373、335–356），会失去-S收益。

fs路径完整形态：`tar -S --numeric-owner --preserve-permissions --one-file-system --directory <instroot> <excludes...> -czf <dst> .`（gzip）；bzip2为-cjf，普通tar为-cf。fs原本就是tar内压缩，不经过archive._do_gzip，且不含-S不支持时的回退。不能把loop/raw的临时.tar模型套到fs。

### (d) tar rc与show_tar_diagnostics究竟做什么

诊断实现来自3cc580e：[misc.py](../evidence/src_snapshot/hq-mic/mic/utils/misc.py) L1094–1134，调用在archive._do_tar L300–301、_imp_tarfile L344–345、fs.py L82。内容为：shutil.disk_usage('/var/tmp')的total/used/free和百分比；du -sh /var/tmp与/var/tmp/mic；/proc/self/limits中Limit/file size/open files/address space/data size行。单位代码按1024**3却标GB，实际为GiB；只在tar前记录。

所有正常诊断经msger.info，失败经warning，到QB控制台及配置--logfile的mic文件日志（[msger.py](../evidence/src_snapshot/hq-mic/mic/msger.py) L353–377，文件格式L264–266）。du stderr被DEVNULL，rc未检查，异常吞掉；没有free/RSS/cgroup、inode/配额，也没有compress前或失败后的同盘快照。目标硬编码/var/tmp，若--tmpdir/临时tar在另一文件系统可能测错盘；递归du成本可能较高。这有助定位容量/文件限额，但不足以独立确定ENOSPC。

c446 tar检查两次调用rc，压缩函数也检查rc/合并输出；_call_external本体仍为旧实现，stderr合入stdout且未主动msger输出（archive.py L66–85）。总部OSError可能在tools/mic L332–336重抛而非CreatorError的L341–346正常日志路径。因此我们的补充是统一日志渠道和领域异常，不是重新发明总部已经存在的四函数rc检查。

### (e) 根因：缓解与修复分别是什么

**空间耗尽触发是缓解；错误诊断缺陷已有部分修复。** -S不提供空间保证，本机中间tar实测少67.52%（不是所有真实镜像都必然同样比例）；loop/raw仍需S+C及其他工作量。c446新增压缩rc/输出检查已防止多数坏.gz假成功和把写失败折叠成move缺文件；eadc使格式默认关闭保护消费者。仍缺统一直接日志/CreatorError、失败时工作盘容量证据，mktemp和move前存在/完整性防御仍未修。两次历史QB使用的是旧实现，最可能写失败cleanup，ENOSPC中等置信；这些新提交不能逆推出当时errno。证据见 [signature_experiment.md](signature_experiment.md)、[sparse_experiment.md](sparse_experiment.md)。

## 消费端兼容性与部署条件

GNU稀疏成员要识别洞映射，直接刷写的普通tar专用消费者不应默认接受。旧bootstrap spec说bsdtar sparse pax不能由lthor刷写，但现代lthor3.4+本机libarchive3.7.2读本实验GNU稀疏档案补零/hash正确；顺序读本身不是不兼容证明，亦未验证实际设备。-S应opt-in，loop/raw/fs名字不等于消费端许可，详见sparse_experiment。

- [ ] QB worker真正执行的宿主mic升级至包含3cc580e诊断依赖、c446578和eadc8fd5的版本；不能只复制两份diff且忽略缺上下文。分支HEAD包内__version__仍为2.1.0，需核验commit/文件hash而非只看版本字符串。
- [ ] QB实际KS的bootloader加--sparse-tar，输入hash和解析结果可追溯；CLI是另一开启入口。通常发布KS方式需要“新worker mic + KS启用”同时满足。
- [ ] 默认bootstrap复制宿主mic（rt_util.py L165–175，sync_mic L277–306）；只升级bootstrap RPM不能替代宿主。use_mic_in_bootstrap=True和旧py2分支则须核验/更新bootstrap实际mic。
- [ ] bootstrap内GNU tar支持选定格式；fallocate存在且-d适用于工作文件系统；日志证明实际-S，而非回退普通tar。
- [ ] 最终消费者/库/设备验证逻辑内容与稀疏格式兼容；未知或只支持普通格式的刷写链路关闭-S。
- [ ] 仍为实际工作盘预留源分配块、稀疏tar、压缩输出、缓存/bootstrap及其他并发负载；记录失败时空间/配额/内核资源。
- [ ] 若采用我们的 [complementary.patch](complementary.patch)，保留总部fallback并完成下面的真实叠加/普通用户测试验证。

## dry-run：每文件每hunk原文

命令都为`patch --batch --verbose -p1 --dry-run -i <原始patch绝对路径>`，原始downloads/src/mic只读、不修改；不编辑任何总部patch、hunk或上下文。

第一份c446对干净2.1.3四个压缩hunk通过，archive hunk5因缺3cc诊断两行context失败；loop/misc通过。第二份对同一干净2.1.3作为单独兼容性探针，archive hunk2缺c446的-S/fallback及3cc诊断而失败，其余hunk为成功/offset。**因为首份dry-run失败，没有假称第二份是在“首份已成功应用”的后态上测试。** 两份单独探针rc都为1；“仅2.1.3+两份补丁”并不是可直接落地的基线。

另外在work/私有复制的2.1.3上顺序dry-run并实际apply三份真实提交：3cc580e→c446578→eadc8fd5，均成功，无fuzz；eadc的raw.py hunk1 offset+17。所有original patch逐字未改。以下记录完整保留每文件/hunk成功、offset、fuzz（没有）与失败信息；执行状态见 [patch-validation.json](../evidence/hq/patch-validation.json)。

### c446578：直接2.1.3，rc1

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|From c446578d87b055984e5eeca04e2f485436f55759 Mon Sep 17 00:00:00 2001
|From: Jaehoon Chung <jh80.chung@samsung.com>
|Date: Wed, 7 Oct 2026 17:45:16 +0900
|Subject: [PATCH] Improve toybox compatibility and sparse file handling during
| packaging
|
|- Update get_file_size() in mic/utils/misc.py to use native os.stat
|  for files and add POSIX du -s -k fallback for directories, ensuring
|  compatibility with toybox and busybox.
|- Run fallocate -d in mic/imager/loop.py to restore sparse holes in
|  image files before packaging.
|- Apply sparse archiving (tar -S) with fallback in mic/archive.py to
|  prevent expanding sparse holes and avoid disk space exhaustion.
|- Verify exit codes in compression functions (_do_gzip, _do_bzip2,
|  _do_lzop, _do_zstd) to ensure failures are raised explicitly.
|
|Signed-off-by: Jaehoon Chung <jh80.chung@samsung.com>
|---
| mic/archive.py     | 33 +++++++++++++++++++++++++++------
| mic/imager/loop.py |  8 ++++++--
| mic/utils/misc.py  | 40 ++++++++++++++++++++++++++++------------
| 3 files changed, 61 insertions(+), 20 deletions(-)
|
|diff --git a/mic/archive.py b/mic/archive.py
|index b9ea5cf..32672b1 100644
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 99.
Hunk #2 succeeded at 129.
Hunk #3 succeeded at 156.
Hunk #4 succeeded at 186.
Hunk #5 FAILED at 299.
1 out of 5 hunks FAILED
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/loop.py b/mic/imager/loop.py
|index 1d71f78..1d23e79 100644
|--- a/mic/imager/loop.py
|+++ b/mic/imager/loop.py
--------------------------
checking file mic/imager/loop.py
Using Plan A...
Hunk #1 succeeded at 517.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/utils/misc.py b/mic/utils/misc.py
|index 185fe08..6162750 100644
|--- a/mic/utils/misc.py
|+++ b/mic/utils/misc.py
--------------------------
checking file mic/utils/misc.py
Using Plan A...
Hunk #1 succeeded at 405.
Hmm...  Ignoring the trailing garbage.
done
```

### eadc8fd5：直接2.1.3，rc1

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|From eadc8fd5c1288206601485c1dbff0ecdb1425bcd Mon Sep 17 00:00:00 2001
|From: Jaehoon Chung <jh80.chung@samsung.com>
|Date: Wed, 7 Oct 2026 19:31:54 +0900
|Subject: [PATCH] Support optional sparse tar archiving via kickstart and CLI
|
|- Add --sparse-tar option to the bootloader command in
|  mic/kickstart/custom_commands/micboot.py, allowing kickstart
|  files to selectively opt in to sparse tar archiving.
|- Add --sparse-tar CLI option to tools/mic and mic/cmd_create.py.
|- Pass sparse_tar flag through mic/conf.py and image creators
|  (loop, raw, fs) to mic/archive.py.
|- Keep standard non-sparse tar (tar -cf) as default to ensure
|  100% backward compatibility, while enabling tar -S with
|  automatic fallback when --sparse-tar is explicitly specified.
|
|Signed-off-by: Jaehoon Chung <jh80.chung@samsung.com>
|---
| mic/archive.py                           | 36 +++++++++++++++---------
| mic/cmd_create.py                        |  3 ++
| mic/conf.py                              |  4 +++
| mic/imager/fs.py                         |  3 ++
| mic/imager/loop.py                       |  2 +-
| mic/imager/raw.py                        |  2 +-
| mic/kickstart/custom_commands/micboot.py |  5 ++++
| tools/mic                                |  2 ++
| 8 files changed, 42 insertions(+), 15 deletions(-)
|
|diff --git a/mic/archive.py b/mic/archive.py
|index 32672b1..7ea7ac0 100644
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 267 (offset -12 lines).
Hunk #2 FAILED at 300.
Hunk #3 succeeded at 325 (offset -27 lines).
Hunk #4 succeeded at 423 (offset -27 lines).
Hunk #5 succeeded at 453 (offset -27 lines).
1 out of 5 hunks FAILED
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/cmd_create.py b/mic/cmd_create.py
|index ed8a7c9..8e6e49c 100644
|--- a/mic/cmd_create.py
|+++ b/mic/cmd_create.py
--------------------------
checking file mic/cmd_create.py
Using Plan A...
Hunk #1 succeeded at 165.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/conf.py b/mic/conf.py
|index 0666d1f..320c826 100644
|--- a/mic/conf.py
|+++ b/mic/conf.py
--------------------------
checking file mic/conf.py
Using Plan A...
Hunk #1 succeeded at 82.
Hunk #2 succeeded at 218.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/fs.py b/mic/imager/fs.py
|index 870bce8..90e5a7b 100644
|--- a/mic/imager/fs.py
|+++ b/mic/imager/fs.py
--------------------------
checking file mic/imager/fs.py
Using Plan A...
Hunk #1 succeeded at 85 (offset -2 lines).
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/loop.py b/mic/imager/loop.py
|index 1d23e79..89d4c31 100644
|--- a/mic/imager/loop.py
|+++ b/mic/imager/loop.py
--------------------------
checking file mic/imager/loop.py
Using Plan A...
Hunk #1 succeeded at 530 (offset -4 lines).
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/raw.py b/mic/imager/raw.py
|index d9ea698..9b0504d 100644
|--- a/mic/imager/raw.py
|+++ b/mic/imager/raw.py
--------------------------
checking file mic/imager/raw.py
Using Plan A...
Hunk #1 succeeded at 494 (offset 17 lines).
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/kickstart/custom_commands/micboot.py b/mic/kickstart/custom_commands/micboot.py
|index d978be8..b70204b 100644
|--- a/mic/kickstart/custom_commands/micboot.py
|+++ b/mic/kickstart/custom_commands/micboot.py
--------------------------
checking file mic/kickstart/custom_commands/micboot.py
Using Plan A...
Hunk #1 succeeded at 31.
Hunk #2 succeeded at 40.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/tools/mic b/tools/mic
|index 7b01a1f..71e5173 100755
|--- a/tools/mic
|+++ b/tools/mic
--------------------------
checking file tools/mic
Using Plan A...
Hunk #1 succeeded at 99.
Hmm...  Ignoring the trailing garbage.
done
```

### 额外真实依赖3cc580e：work复制基线，rc0

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|From 3cc580ebf07677610d58bd8f4b2c3b9ba0a7c15d Mon Sep 17 00:00:00 2001
|From: Jaehoon Chung <jh80.chung@samsung.com>
|Date: Wed, 7 Oct 2026 11:39:10 +0900
|Subject: [PATCH] Add diagnostics for /var/tmp usage and ulimit before tar
| operations
|
|Display filesystem disk space of /var/tmp (total, used, free),
|directory usage of /var/tmp and /var/tmp/mic, and process resource
|limits (ulimit via /proc/self/limits) prior to creating tar archives.
|This helps troubleshoot build failures caused by disk space exhaustion
|or resource limitations during tar operations.
|
|Signed-off-by: Jaehoon Chung <jh80.chung@samsung.com>
|---
| mic/archive.py    |  8 +++++++-
| mic/imager/fs.py  |  2 ++
| mic/utils/misc.py | 43 +++++++++++++++++++++++++++++++++++++++++++
| 3 files changed, 52 insertions(+), 1 deletion(-)
|
|diff --git a/mic/archive.py b/mic/archive.py
|index 9942db8..b9ea5cf 100644
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 284.
Hunk #2 succeeded at 316.
Hunk #3 succeeded at 349.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/fs.py b/mic/imager/fs.py
|index 0fd6b46..870bce8 100644
|--- a/mic/imager/fs.py
|+++ b/mic/imager/fs.py
--------------------------
checking file mic/imager/fs.py
Using Plan A...
Hunk #1 succeeded at 79.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/utils/misc.py b/mic/utils/misc.py
|index 21c92ff..185fe08 100644
|--- a/mic/utils/misc.py
|+++ b/mic/utils/misc.py
--------------------------
checking file mic/utils/misc.py
Using Plan A...
Hunk #1 succeeded at 1074.
Hmm...  Ignoring the trailing garbage.
done
```

### c446578：已补齐3cc580e后，rc0

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|From c446578d87b055984e5eeca04e2f485436f55759 Mon Sep 17 00:00:00 2001
|From: Jaehoon Chung <jh80.chung@samsung.com>
|Date: Wed, 7 Oct 2026 17:45:16 +0900
|Subject: [PATCH] Improve toybox compatibility and sparse file handling during
| packaging
|
|- Update get_file_size() in mic/utils/misc.py to use native os.stat
|  for files and add POSIX du -s -k fallback for directories, ensuring
|  compatibility with toybox and busybox.
|- Run fallocate -d in mic/imager/loop.py to restore sparse holes in
|  image files before packaging.
|- Apply sparse archiving (tar -S) with fallback in mic/archive.py to
|  prevent expanding sparse holes and avoid disk space exhaustion.
|- Verify exit codes in compression functions (_do_gzip, _do_bzip2,
|  _do_lzop, _do_zstd) to ensure failures are raised explicitly.
|
|Signed-off-by: Jaehoon Chung <jh80.chung@samsung.com>
|---
| mic/archive.py     | 33 +++++++++++++++++++++++++++------
| mic/imager/loop.py |  8 ++++++--
| mic/utils/misc.py  | 40 ++++++++++++++++++++++++++++------------
| 3 files changed, 61 insertions(+), 20 deletions(-)
|
|diff --git a/mic/archive.py b/mic/archive.py
|index b9ea5cf..32672b1 100644
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 99.
Hunk #2 succeeded at 129.
Hunk #3 succeeded at 156.
Hunk #4 succeeded at 186.
Hunk #5 succeeded at 299.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/loop.py b/mic/imager/loop.py
|index 1d71f78..1d23e79 100644
|--- a/mic/imager/loop.py
|+++ b/mic/imager/loop.py
--------------------------
checking file mic/imager/loop.py
Using Plan A...
Hunk #1 succeeded at 517.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/utils/misc.py b/mic/utils/misc.py
|index 185fe08..6162750 100644
|--- a/mic/utils/misc.py
|+++ b/mic/utils/misc.py
--------------------------
checking file mic/utils/misc.py
Using Plan A...
Hunk #1 succeeded at 405.
Hmm...  Ignoring the trailing garbage.
done
```

### eadc8fd5：已应用3cc580e+c446578后，rc0

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|From eadc8fd5c1288206601485c1dbff0ecdb1425bcd Mon Sep 17 00:00:00 2001
|From: Jaehoon Chung <jh80.chung@samsung.com>
|Date: Wed, 7 Oct 2026 19:31:54 +0900
|Subject: [PATCH] Support optional sparse tar archiving via kickstart and CLI
|
|- Add --sparse-tar option to the bootloader command in
|  mic/kickstart/custom_commands/micboot.py, allowing kickstart
|  files to selectively opt in to sparse tar archiving.
|- Add --sparse-tar CLI option to tools/mic and mic/cmd_create.py.
|- Pass sparse_tar flag through mic/conf.py and image creators
|  (loop, raw, fs) to mic/archive.py.
|- Keep standard non-sparse tar (tar -cf) as default to ensure
|  100% backward compatibility, while enabling tar -S with
|  automatic fallback when --sparse-tar is explicitly specified.
|
|Signed-off-by: Jaehoon Chung <jh80.chung@samsung.com>
|---
| mic/archive.py                           | 36 +++++++++++++++---------
| mic/cmd_create.py                        |  3 ++
| mic/conf.py                              |  4 +++
| mic/imager/fs.py                         |  3 ++
| mic/imager/loop.py                       |  2 +-
| mic/imager/raw.py                        |  2 +-
| mic/kickstart/custom_commands/micboot.py |  5 ++++
| tools/mic                                |  2 ++
| 8 files changed, 42 insertions(+), 15 deletions(-)
|
|diff --git a/mic/archive.py b/mic/archive.py
|index 32672b1..7ea7ac0 100644
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 279.
Hunk #2 succeeded at 300.
Hunk #3 succeeded at 355.
Hunk #4 succeeded at 453.
Hunk #5 succeeded at 483.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/cmd_create.py b/mic/cmd_create.py
|index ed8a7c9..8e6e49c 100644
|--- a/mic/cmd_create.py
|+++ b/mic/cmd_create.py
--------------------------
checking file mic/cmd_create.py
Using Plan A...
Hunk #1 succeeded at 165.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/conf.py b/mic/conf.py
|index 0666d1f..320c826 100644
|--- a/mic/conf.py
|+++ b/mic/conf.py
--------------------------
checking file mic/conf.py
Using Plan A...
Hunk #1 succeeded at 82.
Hunk #2 succeeded at 218.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/fs.py b/mic/imager/fs.py
|index 870bce8..90e5a7b 100644
|--- a/mic/imager/fs.py
|+++ b/mic/imager/fs.py
--------------------------
checking file mic/imager/fs.py
Using Plan A...
Hunk #1 succeeded at 87.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/loop.py b/mic/imager/loop.py
|index 1d23e79..89d4c31 100644
|--- a/mic/imager/loop.py
|+++ b/mic/imager/loop.py
--------------------------
checking file mic/imager/loop.py
Using Plan A...
Hunk #1 succeeded at 534.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/imager/raw.py b/mic/imager/raw.py
|index d9ea698..9b0504d 100644
|--- a/mic/imager/raw.py
|+++ b/mic/imager/raw.py
--------------------------
checking file mic/imager/raw.py
Using Plan A...
Hunk #1 succeeded at 494 (offset 17 lines).
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/mic/kickstart/custom_commands/micboot.py b/mic/kickstart/custom_commands/micboot.py
|index d978be8..b70204b 100644
|--- a/mic/kickstart/custom_commands/micboot.py
|+++ b/mic/kickstart/custom_commands/micboot.py
--------------------------
checking file mic/kickstart/custom_commands/micboot.py
Using Plan A...
Hunk #1 succeeded at 31.
Hunk #2 succeeded at 40.
Hmm...  The next patch looks like a unified diff to me...
The text leading up to this was:
--------------------------
|diff --git a/tools/mic b/tools/mic
|index 7b01a1f..71e5173 100755
|--- a/tools/mic
|+++ b/tools/mic
--------------------------
checking file tools/mic
Using Plan A...
Hunk #1 succeeded at 99.
Hmm...  Ignoring the trailing garbage.
done
```

## 我们的补充diff叠加与测试

[docs/complementary.patch](complementary.patch)只改archive.py的imports和_call_external，**未改总部已修改的四压缩函数、_do_tar、_make_tarball、make_archive或imager/config**。原四路径rc检查保留，通过新共享调用层先抛CreatorError、直接记录rc/argv和stderr原文；压缩前记录输入.tar字节大小及其输出目录shutil.disk_usage.free，解压不误写压缩容量记录。没有实现流式、mktemp替换或额外move防御，按本轮收窄要求只记录残留风险。

只有首个tar -S非零允许返回tuple给总部既有回退；它也记录原始stderr。若这里一概先抛异常，总部fallback就永远到不了，故此兼容例外必须保留。普通tar最终失败及所有压缩/解压非零仍抛CreatorError，不改总部同处代码。[范围/叠加记录](../evidence/hq/complementary-validation.json)。

先在`2.1.3 + 真实3cc580e依赖 + c446578 + eadc8fd5`上候选diff dry-run通过，再写docs/complementary.patch并在work复制基线apply；真实Gerrit HEAD也dry-run通过。不能虚报缺依赖的“两份直接叠加”通过。下方是逐hunk原文：

### complementary-dryrun.log

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 32.
Hunk #2 succeeded at 66.
done
```

### complementary-gerrit-dryrun.log

```text
Hmm...  Looks like a unified diff to me...
The text leading up to this was:
--------------------------
|--- a/mic/archive.py
|+++ b/mic/archive.py
--------------------------
checking file mic/archive.py
Using Plan A...
Hunk #1 succeeded at 32.
Hunk #2 succeeded at 66.
done
```

28组普通用户测试覆盖gzip/pigz/bzip2/zstd/lzop各压缩/解压的exit1与中途SIGKILL，rc/真实CreatorError/stderr保留/压缩前容量日志；真实gzip roundtrip、真实稀疏gztar、tar拒-S回退、失败保留已有最终档案。仅msger和递归/var/tmp诊断stub，子进程/tar/gzip真实；此外独立用实际mic包、实际CreatorError和实际msger文件日志核验import/原样stderr写日志。见 [results.json](../evidence/complementary/results.json)、[驱动](../evidence/complementary/test_archive.py)、[真实日志验证](../evidence/complementary/real-import-logging.log)。没有设备/root/镜像构建。

副作用：stdout/stderr分别communicate后按stdout+stderr返回，失去原先跨流时间交织；异常只带最后20行，但日志不截断stderr。非UTF8按replace形成文本而不是字节完保；仍有communicate无界输出缓冲，未扩大范围改I/O架构。Before compression容量只观察，不以input_size>free拒绝（输入可以压缩）；资源查询失败警告不覆盖原始压缩错误。tar-S任意失败的自动普通tar回退、mktemp、无独立move前存在/完整性检查仍是总部残留行为。
