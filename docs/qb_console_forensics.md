# QB 控制台日志取证（stage2a，2026-10-06）

五份材料是用户新增的 QB 完整控制台输出，包含 mic stdout/stderr、外层脚本与 QB 状态，区别于之前发布的三份 mic `.log`。原文件不改写；行号按换行计数（长 `ks_data` 仍为一行），sha256、尾部换行与逐关键词索引见 [元数据](../evidence/qb_console_metadata.json)。控制台只有时分秒，不自行补日期/时区；与公开 mic.log 重叠段一致，下面只计算同份日志的时间差。

**当前判定：两次均在预期 `.tar.gz` 缺失后由 mic 抛出 `shutil.move` 的 FileNotFoundError、返回 1，再被 QB 标记失败；mic 被直接杀死/步骤超时的解释不符合控制台收尾。压缩器的原始 rc 和输出被丢弃，ENOSPC 是优先验证的资源假设（低至中置信），压缩器自身受 OOM/SIGKILL 或其他失败尚不能定性。** 证据：`1187398full-log.txt` L8878–8926、8936、8951–8955；`1189686full-log.txt` L8878–8926、8936、8951–8955；[archive.py](../evidence/src_snapshot/mic/mic/archive.py) L66–110、327–348。

## 一、逐日志命令、环境、worker、步骤边界和状态

`starting mic to create image` 的打印在执行及 rsync 之后，是外层输出顺序/缓冲现象，不能把那一行的时间当成 mic 的真实启动时刻；首个 mic 版本行只能作为已经启动的最早可见证据。例：`1189686full-log.txt` L130、8878、8927–8936。

### 1178308full-log.txt

- worker 为 `ip-192-168-56-202`；工作目录/宿主版本依据 `1178308full-log.txt` L48、132，宿主为 Ubuntu 24.04。image 子步骤的 `Running step` 在 `1178308full-log.txt` L43，外层命令开始输出在 `1178308full-log.txt` L46；结束边界见下方状态原文（成功日志只给 post-execute，没有显式数字退出码）。
- 完整 mic 命令（原文）：

```text
8968: 19:13:09,579 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified-toolchain_20260917.132101 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log
```

- 命令显式含 `cr auto <ks> --release <RID> -o <outdir> -k <cachedir> --logfile=...`；没有显式 `--runtime`、`--pack-to`、`--tmpdir`、`-c`、`--non-interactive`，不补造这些选项（`1178308full-log.txt` L8968）。选中 KS 头部提供 `-A aarch64 -f loop --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license`（`1178308full-log.txt` L24，该行是长字典，以下只引用头部，不替代原件）。
- 全文没有 `mic.conf` 字符串，无法据此还原配置文件内容；明确的环境及 bootstrap 行如下（`1178308full-log.txt` L48、73、147、148、157）。`TMPDIR=/home/tizenbuild/tmp` 是外层环境；实际打包仍在 `/var/tmp/mic/build`（下方 tar 原文），二者不可混同。runtime bootstrap 由执行行为确认。

```text
47: export QB_SCRIPTS='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-202_8812/master/QB-Scripts'
48: export WORKSPACE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-202_8812'
49: export REPO_ARCH=''
50: export REPOSITORY=''
51: export ARCHITECTURE=''
52: export TARGET_SNAPSHOT_URL='http://download.tizen.org/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260917.132101'
53: export ALL_CHILD_CONFIG='standard-armv7l,standard-aarch64,standard-x86_64,'
54: export QB_CUR_STEP='image'
55: export META_PACKAGES_COMMIT_ID=''
56: export FIXED_VARIABLES_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-202_8812/variable_files/fixed_variables.yaml'
57: export BUILD_PKG_LIST_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-202_8812/BUILD_PKG_LIST_FILE'
58: export CHILD_CONFIGURATIONS='standard-armv7l,standard-aarch64,standard-x86_64,'
59: export USE_BRANCH_POLICY='false'
60: export FAIL_FAST='no'
61: export QB_TRIGGER_ID='1178308'
62: export IMAGE_BUILD_ID=''
63: export DOCKER_NAME='gbsbuild_ip-192-168-56-202_8812'
64: 
65: 
66: export KS_NAME=tizen-headed-aarch64.ks
67: export IMG_WORKSPACE=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
68: mkdir -p $IMG_WORKSPACE
69: 
70: export QB_SCRIPTS=$(mktemp -d $IMG_WORKSPACE/QB_SCRIPTS_XXXXXX)
71: export WORKSPACE=$IMG_WORKSPACE/WORKSPACE
72: export GBSBUILD_WORKSPACE=$IMG_WORKSPACE
73: export TMPDIR='/home/tizenbuild/tmp'
147: 18:47:09,459 INFO  - INFO: Copy host mic to bootstrap
148: 18:47:09,623 INFO  - INFO: Start mic in bootstrap: /var/tmp/mic-bootstrap/tizen2ujo66v9/bootstrap
157: 18:47:10,679 INFO  - mic 2.1.3 (ip-192-168-56-202 tizen)
```

- 步骤开始和结束/最终状态：

```text
1: 18:46:30,031 INFO  - Executing pre-execute action...
43: 18:46:39,236 INFO  - Running step...
46: 18:46:39,496 DEBUG - Executing command: 
8949: 19:13:07,524 INFO  - INFO: Finished.
8974: 19:13:09,579 INFO  - The build was successful.
8976: 19:13:09,674 INFO  - Executing post-execute action...
8978: 19:13:10,037 INFO  - Executing post-execute action...
```

### 1182527full-log.txt

- worker 为 `ip-192-168-56-118`；工作目录/宿主版本依据 `1182527full-log.txt` L57、148，宿主为 Ubuntu 24.04。image 子步骤的 `Running step` 在 `1182527full-log.txt` L52，外层命令开始输出在 `1182527full-log.txt` L55；结束边界见下方状态原文（成功日志只给 post-execute，没有显式数字退出码）。
- 完整 mic 命令（原文）：

```text
8938: 09:50:22,347 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified_20260923.050314 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314_tizen-headed-aarch64.log
```

- 命令显式含 `cr auto <ks> --release <RID> -o <outdir> -k <cachedir> --logfile=...`；没有显式 `--runtime`、`--pack-to`、`--tmpdir`、`-c`、`--non-interactive`，不补造这些选项（`1182527full-log.txt` L8938）。选中 KS 头部提供 `-A aarch64 -f loop --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license`（`1182527full-log.txt` L33，该行是长字典，以下只引用头部，不替代原件）。
- 全文没有 `mic.conf` 字符串，无法据此还原配置文件内容；明确的环境及 bootstrap 行如下（`1182527full-log.txt` L57、82、163、164、173）。`TMPDIR=/home/tizenbuild/tmp` 是外层环境；实际打包仍在 `/var/tmp/mic/build`（下方 tar 原文），二者不可混同。runtime bootstrap 由执行行为确认。

```text
56: export QB_SCRIPTS='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-118_8812/master/QB-Scripts'
57: export WORKSPACE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-118_8812'
58: export REPO_ARCH=''
59: export REPOSITORY=''
60: export ARCHITECTURE=''
61: export TARGET_SNAPSHOT_URL='http://download.tizen.org/RBS/TIZEN/Tizen/Tizen-Unified/tizen-unified_20260923.050314'
62: export ALL_CHILD_CONFIG='standard-armv7l,standard-aarch64,standard-x86_64,standard_gcov-armv7l,emulator-x86_64,'
63: export QB_CUR_STEP='image'
64: export META_PACKAGES_COMMIT_ID=''
65: export FIXED_VARIABLES_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-118_8812/variable_files/fixed_variables.yaml'
66: export BUILD_PKG_LIST_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-118_8812/BUILD_PKG_LIST_FILE'
67: export CHILD_CONFIGURATIONS='standard-armv7l,standard-aarch64,standard-x86_64,standard_gcov-armv7l,emulator-x86_64,'
68: export USE_BRANCH_POLICY='true'
69: export FAIL_FAST='yes'
70: export QB_TRIGGER_ID='1182527'
71: export IMAGE_BUILD_ID=''
72: export DOCKER_NAME='gbsbuild_ip-192-168-56-118_8812'
73: 
74: 
75: export KS_NAME=tizen-headed-aarch64.ks
76: export IMG_WORKSPACE=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
77: mkdir -p $IMG_WORKSPACE
78: 
79: export QB_SCRIPTS=$(mktemp -d $IMG_WORKSPACE/QB_SCRIPTS_XXXXXX)
80: export WORKSPACE=$IMG_WORKSPACE/WORKSPACE
81: export GBSBUILD_WORKSPACE=$IMG_WORKSPACE
82: export TMPDIR='/home/tizenbuild/tmp'
163: 09:24:46,095 INFO  - INFO: Copy host mic to bootstrap
164: 09:24:46,203 INFO  - INFO: Start mic in bootstrap: /var/tmp/mic-bootstrap/tizenbt29ybny/bootstrap
173: 09:24:47,243 INFO  - mic 2.1.3 (ip-192-168-56-118 tizen)
```

- 步骤开始和结束/最终状态：

```text
1: 09:24:15,216 INFO  - Executing pre-execute action...
52: 09:24:24,248 INFO  - Running step...
55: 09:24:24,514 DEBUG - Executing command: 
8919: 09:50:20,177 INFO  - INFO: Finished.
8944: 09:50:22,347 INFO  - The build was successful.
8946: 09:50:22,437 INFO  - Executing post-execute action...
8948: 09:50:22,644 INFO  - Executing post-execute action...
```

### 1187398full-log.txt

- worker 为 `ip-192-168-56-91`；工作目录/宿主版本依据 `1187398full-log.txt` L48、130，宿主为 Ubuntu 24.04。image 子步骤的 `Running step` 在 `1187398full-log.txt` L43，外层命令开始输出在 `1187398full-log.txt` L46；结束边界见下方状态原文（成功日志只给 post-execute，没有显式数字退出码）。
- 完整 mic 命令（原文）：

```text
8935: 16:55:08,254 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified-toolchain_20260930.105301 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log
```

- 命令显式含 `cr auto <ks> --release <RID> -o <outdir> -k <cachedir> --logfile=...`；没有显式 `--runtime`、`--pack-to`、`--tmpdir`、`-c`、`--non-interactive`，不补造这些选项（`1187398full-log.txt` L8935）。选中 KS 头部提供 `-A aarch64 -f loop --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license`（`1187398full-log.txt` L24，该行是长字典，以下只引用头部，不替代原件）。
- 全文没有 `mic.conf` 字符串，无法据此还原配置文件内容；明确的环境及 bootstrap 行如下（`1187398full-log.txt` L48、73、145、146、155）。`TMPDIR=/home/tizenbuild/tmp` 是外层环境；实际打包仍在 `/var/tmp/mic/build`（下方 tar 原文），二者不可混同。runtime bootstrap 由执行行为确认。

```text
47: export QB_SCRIPTS='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-91_8812/master/QB-Scripts'
48: export WORKSPACE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-91_8812'
49: export REPO_ARCH=''
50: export REPOSITORY=''
51: export ARCHITECTURE=''
52: export TARGET_SNAPSHOT_URL='http://download.tizen.org/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260930.105301'
53: export ALL_CHILD_CONFIG='standard-armv7l,standard-aarch64,standard-x86_64,'
54: export QB_CUR_STEP='image'
55: export META_PACKAGES_COMMIT_ID=''
56: export FIXED_VARIABLES_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-91_8812/variable_files/fixed_variables.yaml'
57: export BUILD_PKG_LIST_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-91_8812/BUILD_PKG_LIST_FILE'
58: export CHILD_CONFIGURATIONS='standard-armv7l,standard-aarch64,standard-x86_64,'
59: export USE_BRANCH_POLICY='false'
60: export FAIL_FAST='no'
61: export QB_TRIGGER_ID='1187398'
62: export IMAGE_BUILD_ID=''
63: export DOCKER_NAME='gbsbuild_ip-192-168-56-91_8812'
64: 
65: 
66: export KS_NAME=tizen-headed-aarch64.ks
67: export IMG_WORKSPACE=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
68: mkdir -p $IMG_WORKSPACE
69: 
70: export QB_SCRIPTS=$(mktemp -d $IMG_WORKSPACE/QB_SCRIPTS_XXXXXX)
71: export WORKSPACE=$IMG_WORKSPACE/WORKSPACE
72: export GBSBUILD_WORKSPACE=$IMG_WORKSPACE
73: export TMPDIR='/home/tizenbuild/tmp'
145: 16:30:00,368 INFO  - INFO: Copy host mic to bootstrap
146: 16:30:00,557 INFO  - INFO: Start mic in bootstrap: /var/tmp/mic-bootstrap/tizen7m7k8ses/bootstrap
155: 16:30:01,787 INFO  - mic 2.1.3 (ip-192-168-56-91 tizen)
```

- 步骤开始和结束/最终状态：

```text
1: 16:27:26,735 INFO  - Executing pre-execute action...
43: 16:27:35,733 INFO  - Running step...
46: 16:27:36,035 DEBUG - Executing command: 
8951: 16:55:08,423 ERROR - Step 'master>IMAGE>Image_Create' is failed:     raise LocalError('Error: Image Creation Failed')
8936: 16:55:08,254 INFO  - Error: mic returned 1
8950: 16:55:08,423 INFO  - Executing post-execute action...
8955: 16:55:08,716 ERROR - Step 'master' is failed: Composite step 'master' failed due to unsatisfied success condition.
```

### 1189686full-log.txt

- worker 为 `ip-192-168-56-168`；工作目录/宿主版本依据 `1189686full-log.txt` L48、130，宿主为 Ubuntu 24.04。image 子步骤的 `Running step` 在 `1189686full-log.txt` L43，外层命令开始输出在 `1189686full-log.txt` L46；结束边界见下方状态原文（成功日志只给 post-execute，没有显式数字退出码）。
- 完整 mic 命令（原文）：

```text
8935: 16:22:32,343 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified-toolchain_20261003.102419 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log
```

- 命令显式含 `cr auto <ks> --release <RID> -o <outdir> -k <cachedir> --logfile=...`；没有显式 `--runtime`、`--pack-to`、`--tmpdir`、`-c`、`--non-interactive`，不补造这些选项（`1189686full-log.txt` L8935）。选中 KS 头部提供 `-A aarch64 -f loop --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license`（`1189686full-log.txt` L24，该行是长字典，以下只引用头部，不替代原件）。
- 全文没有 `mic.conf` 字符串，无法据此还原配置文件内容；明确的环境及 bootstrap 行如下（`1189686full-log.txt` L48、73、145、146、155）。`TMPDIR=/home/tizenbuild/tmp` 是外层环境；实际打包仍在 `/var/tmp/mic/build`（下方 tar 原文），二者不可混同。runtime bootstrap 由执行行为确认。

```text
47: export QB_SCRIPTS='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812/master/QB-Scripts'
48: export WORKSPACE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812'
49: export REPO_ARCH=''
50: export REPOSITORY=''
51: export ARCHITECTURE=''
52: export TARGET_SNAPSHOT_URL='http://download.tizen.org/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261003.102419'
53: export ALL_CHILD_CONFIG='standard-armv7l,standard-aarch64,standard-x86_64,'
54: export QB_CUR_STEP='image'
55: export META_PACKAGES_COMMIT_ID=''
56: export FIXED_VARIABLES_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812/variable_files/fixed_variables.yaml'
57: export BUILD_PKG_LIST_FILE='/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812/BUILD_PKG_LIST_FILE'
58: export CHILD_CONFIGURATIONS='standard-armv7l,standard-aarch64,standard-x86_64,'
59: export USE_BRANCH_POLICY='false'
60: export FAIL_FAST='no'
61: export QB_TRIGGER_ID='1189686'
62: export IMAGE_BUILD_ID=''
63: export DOCKER_NAME='gbsbuild_ip-192-168-56-168_8812'
64: 
65: 
66: export KS_NAME=tizen-headed-aarch64.ks
67: export IMG_WORKSPACE=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
68: mkdir -p $IMG_WORKSPACE
69: 
70: export QB_SCRIPTS=$(mktemp -d $IMG_WORKSPACE/QB_SCRIPTS_XXXXXX)
71: export WORKSPACE=$IMG_WORKSPACE/WORKSPACE
72: export GBSBUILD_WORKSPACE=$IMG_WORKSPACE
73: export TMPDIR='/home/tizenbuild/tmp'
145: 15:57:23,579 INFO  - INFO: Copy host mic to bootstrap
146: 15:57:23,711 INFO  - INFO: Start mic in bootstrap: /var/tmp/mic-bootstrap/tizentofu90c6/bootstrap
155: 15:57:24,833 INFO  - mic 2.1.3 (ip-192-168-56-168 tizen)
```

- 步骤开始和结束/最终状态：

```text
1: 15:54:38,365 INFO  - Executing pre-execute action...
43: 15:54:47,661 INFO  - Running step...
46: 15:54:59,078 DEBUG - Executing command: 
8951: 16:22:32,532 ERROR - Step 'master>IMAGE>Image_Create' is failed:     raise LocalError('Error: Image Creation Failed')
8936: 16:22:32,343 INFO  - Error: mic returned 1
8950: 16:22:32,531 INFO  - Executing post-execute action...
8955: 16:22:32,955 ERROR - Step 'master' is failed: Composite step 'master' failed due to unsatisfied success condition.
```

### 1189639full-log.txt（父构建）

- 父任务工作主机标识是 `qbsource26`，工作目录 `qbsource26_8914`（`1189639full-log.txt` L26–29、44）；子任务在 `ip-192-168-56-168_8812`。子日志明确记录从父工作目录复制变量到子目录（`1189686full-log.txt` L44–45），不是同一 worker。父日志没有 mic 的版本 hostname，因此不把工作目录标识说成 `hostname` 命令的实测结果。
- 没有实际 `starting mic to create image`、`Running command: gzip/pigz`、`Pack all loop images together`、`mic.conf` 或 mic traceback（全文 L1–22544；扫描结果见元数据）；存在生成 KS 与触发 image 子构建。父 `master>IMAGE` 最后被跳过，不包含子日志中实际执行的同一 `master>IMAGE>Image_Create`（L22503–22529、22541–22542）。
- 父构建开始 L1 / master Running L10，Trigger_Image_Create 开始 L22503；六个重复触发子步骤在 L22519–22529，未分别标注对应 KS，不能指定其中一行就是 headed-aarch64 的精确开始。结束传播及 master 最终 failure 如下：

```text
1: 10:24:19,655 INFO  - Executing pre-execute action...
10: 10:24:26,845 INFO  - Running step...
29: 10:24:27,116 DEBUG - Command working directory: /home/tizenbuild/ci_tizen_workspace/qbsource26_8914
22503: 15:53:45,044 INFO  - Running step...
22536: 16:22:33,105 ERROR - Step 'master>SNAPSHOT>Trigger_Image_Create>Trigger_Each_Image_Create?KS_NAME=tizen-headed-aarch64.ks' is failed: Step is failed since the triggered build is failed, cancelled, or timed out.
22538: 16:22:33,303 ERROR - Step 'master>SNAPSHOT>Trigger_Image_Create' is failed: Composite step 'Trigger_Image_Create' failed due to unsatisfied success condition.
22540: 16:22:33,503 ERROR - Step 'master>SNAPSHOT' is failed: Composite step 'SNAPSHOT' failed due to unsatisfied success condition.
22542: 16:22:33,710 INFO  - Step execute condition not satisfied, step will be skipped.
22544: 16:22:33,829 ERROR - Step 'master' is failed: Composite step 'master' failed due to unsatisfied success condition.
```

## 二、关键判定和时间差

### 1187398：clang / gzip

- 存在 shutil.move 的双层 FileNotFoundError traceback（`1187398full-log.txt` L8879–8926），落点 `archive.py:346` 的 `shutil.move(tarball_name, archive_name)`（L8914–8915）。gzip 16:54:24,928 → 首个 traceback 16:55:07,361 = **42.433 秒**；到最终缺文件异常 L8926 是 **42.442 秒**（L8878、8879、8926）。
- 压缩启动前后直到 EOF 没有 gzip 自己的 stderr（包括 No space / Killed / ENOSPC），也没有压缩器 rc（L8876–8955；全文关键词检索见第四节）。这不是 gzip 没报错的证明，源码把 stdout/stderr 合并捕获，调用者未处理返回 tuple（archive.py L66–110）。mic 返回 **1**，外层仍完成 mic.log 同步，再抛 LocalError，QB 将 Image_Create、IMAGE、master 正常标为 failed（L8927–8955）。

### 1189686：clang / pigz

- 同样有 traceback，位置和 gzip 相同（`1189686full-log.txt` L8879–8926、8914–8915）。pigz 16:22:01,450 → 首个 traceback 16:22:31,278 = **29.828 秒**；到最终异常是 **29.836 秒**，到 `mic returned 1` 是 **30.893 秒**（L8878、8879、8926、8936）。
- 最后一行为 **L8955 / 16:22:32,955**，距离 pigz 启动 **31.505 秒**；原文见第五节。后面确有 QB 自己的正常 failed 状态链 L8951、8953、8955，没有 step killed、worker lost、timeout/aborted 的实际事件、没有压缩器数字 exit code（L8876–8955，第四节扫描）。
- **“pigz 几秒就被杀、mic 死了”被控制台否定**：mic 在约30秒后仍执行 Python 异常路径、向外层返回 1，外层继续 rsync 和 LocalError。这里排除的是 mic 自己被杀/步骤突然终止；不能排除 pigz 子进程先被 SIGKILL，因为没有保留其 rc 或输出（L8879–8955；archive.py L66–110）。

### 成功对照：1178308 clang gzip / 1182527 gcc gzip

|日志及引用|tar启动→gzip启动|gzip启动→manifest|Pack→manifest|Pack→mic Finished|Pack→QB日志末行|
|---|---:|---:|---:|---:|---:|
|`1178308full-log.txt` L8933、8934、8935、8936、8949、8978|14.793 s|73.214 s|88.008 s|90.215 s|92.728 s|
|`1182527full-log.txt` L8903、8904、8905、8906、8919、8948|15.075 s|78.918 s|93.993 s|96.314 s|98.781 s|

“gzip→manifest”含压缩完成、返回和 move 等开销，不是纯压缩 CPU 时间；打包主体以 manifest 为边界，Finished/EOF 还包含校验清单/复制/同步/外层收尾。两份成功打包尾段 **没有 WARNING/WARN/SyntaxWarning，也没有 traceback**（`1178308full-log.txt` L8933–8978；`1182527full-log.txt` L8903–8948）。全文之前有 WARN/安装脚本警告，例如 KS 字典 WARN L21、脚本警告；不能把“打包段无警告”扩展为全文无警告。两份最终成功由 `The build was successful.` 确认（分别 L8974、8944）；没有显式 `mic returned 0`，不伪造 numeric rc。

### 父构建与 pigz 子构建关系

关系是日志直接证据：`1189686full-log.txt` L36 `trigger.getId(): 1189639`、L37 `build_url: .../1189686`、L44–45 父子变量目录。父只知道触发子任务失败并向上传播，未重复 mic 的缺文件 traceback，错误文本不相同但因果链一致。父 L22536 的 16:22:33,105 紧随子 Image_Create failed（16:22:32,532）及子 master failed（16:22:32,955）；时差分别 **0.573 s / 0.150 s**（`1189686full-log.txt` L8951、8955；`1189639full-log.txt` L22536）。

```text
36: 15:54:47,387 WARN  - trigger.getId() : 1189639
37: 15:54:47,387 WARN  - build_url : https://quickbuild.tizen.org/build/1189686
44: 15:54:47,882 WARN  - src_parent_dir :/home/tizenbuild/ci_tizen_workspace/qbsource26_8914/variable_files
45: 15:54:47,882 WARN  - dest_parent_dir :/home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812/variable_files
```

父消息 `failed, cancelled, or timed out` 是通用三选一模板，结合子日志明确的异常+返回1+failed链，应解读为子失败传播，不能据模板声称 timeout 或 cancel（父 L22536；子 L8936、8951–8955）。父 build URL、用户给定的 clang/gcc 标签不用于推断编译器因果；worker 不同、发行包不同，成功对照不是控制了所有变量的实验。

## 三、资源原因的区分与置信度

|问题|stage1 只有发布 mic.log|stage2a 控制台后的结论与依据|
|---|---|---|
|mic 自己被杀 / QB 突然终止？|不可区分|已否定作为此次终止方式；两份均 traceback、mic返回1、QB普通失败链（1187398/1189686 L8879–8955）|
|gzip vs pigz 是否只有一个有 traceback？|两份 mic.log 都没有|两个控制台都有，调用栈相同（两份 L8879–8926）|
|压缩器 exit1 / SIGKILL？|不可区分|仍不可区分；mic rc1不是压缩器rc（两份 L8936；archive.py L66–110）|
|工作盘 ENOSPC？|优先假设|没有df/空闲块/ENOSPC直接证据；机制上仍优先，低至中置信（第四节；两份L8877中间tar）|
|pigz OOM / cgroup OOM？|可能|仍无内核/cgroup证据；不能证明或排除子进程OOM，低置信（第四节）|
|缺文件触发点及诊断丢失？|源码/探针支持|QB真实 traceback与源码move行一致，置信度高（两份 L8914–8926；archive.py L66–110、327–348）|

同时 tar 的 rc 也未检查（archive.py 的 `_do_tar` / `_make_tarball`），所以不能仅从后续 gzip/pigz 启动就认定 tar 成功生成完整输入。缺失输出最可能来自被掩盖的外部打包/压缩失败；目前无法把触发原因唯一收敛到 ENOSPC。后续应测打包工作盘分配块/空闲块、压缩器 rc/stderr、cgroup memory.events 和内核记录；本阶段不运行复现。

## 四、全文关键词命中（逐行，可复核）

大小写不敏感 **literal substring** 搜索，列出全部命中行号；“无”表示0命中，不代表系统未发生该事件。原文不截断，保存在各 `evidence/qb-*-keyword_hits.txt`（行首为原日志行号）；机器可读索引在 metadata。`df/free/oom` 特意保留包名、路径、hash 等误命中，避免把搜不到独立命令和搜不到字符串混为一谈。

### 1178308full-log.txt

[全部命中行原文](../evidence/qb-1178308full-log-keyword_hits.txt)

|词|命中行数|原文件行号（连续范围包含其间每一行）|
|---|---:|---|
|`df`|34|544、555、1225、1626–1627、1756–1757、2586–2587、5207–5208、5237、5245、5253、5261、5278、5315、5352、5392、5408、5433、5496、5498、5526、5547、6214、6494、6752、7011、7363、7882、7934、7939、8899|
|`free`|24|210、452、479、564、740、1500–1501、1702–1703、1804–1805、2188–2190、2626–2627、2747–2748、5941–5942、5944–5945、5947–5948|
|`No space`|0|无|
|`ENOSPC`|0|无|
|`Killed`|0|无|
|`signal`|20|1214、3849–3850、5032、5267、5269–5270、5595、8144–8147、8455–8458、8694–8697|
|`oom`|1|5021|
|`timeout`|32|21–24、26–28、118、4721、5093、5165、5677–5697|
|`abort`|0|无|
|`cancel`|1|5337|
|`returned exit code`|0|无|
|`rc=`|0|无|

### 1182527full-log.txt

[全部命中行原文](../evidence/qb-1182527full-log-keyword_hits.txt)

|词|命中行数|原文件行号（连续范围包含其间每一行）|
|---|---:|---|
|`df`|35|152、559、571、1231、1604–1605、2028–2029、2579–2580、5202–5203、5218、5226、5247、5275、5283、5302、5380、5396、5404、5424、5487、5489、5517、5538、6215、6495、6753、7012、7364、7883、7903、7976、8866|
|`free`|24|226、468、495、580、757、1506–1507、1720–1721、1820–1822、2080–2081、2619–2620、2742–2743、5934–5935、5937–5938、5940–5941|
|`No space`|0|无|
|`ENOSPC`|0|无|
|`Killed`|0|无|
|`signal`|20|1201、3858–3859、5026、5312、5314–5315、5594、8068–8071、8491–8494、8577–8580|
|`oom`|1|5015|
|`timeout`|41|21–33、35–37、125、4715、5087、5160、5668–5688|
|`abort`|0|无|
|`cancel`|1|5353|
|`returned exit code`|0|无|
|`rc=`|0|无|

### 1187398full-log.txt

[全部命中行原文](../evidence/qb-1187398full-log-keyword_hits.txt)

|词|命中行数|原文件行号（连续范围包含其间每一行）|
|---|---:|---|
|`df`|34|541、553、1213、1616–1617、1996–1997、2562–2563、5184–5185、5216、5229、5260、5272、5288、5312、5324、5358、5385、5407、5470、5472、5500、5521、6189、6469、6727、6986、7338、8179、8187、8227、8737|
|`free`|24|208、450、477、562、739、1488–1489、1694–1695、1841–1843、2046–2047、2602–2603、2725–2726、5917–5918、5920–5921、5923–5924|
|`No space`|0|无|
|`ENOSPC`|0|无|
|`Killed`|0|无|
|`signal`|20|1183、3841–3842、5008、5397、5399–5400、5591、7888–7891、8430–8433、8623–8626|
|`oom`|1|4997|
|`timeout`|32|21–24、26–28、116、4697、5069、5142、5650–5670|
|`abort`|0|无|
|`cancel`|1|5347|
|`returned exit code`|0|无|
|`rc=`|0|无|

### 1189639full-log.txt

[全部命中行原文](../evidence/qb-1189639full-log-keyword_hits.txt)

|词|命中行数|原文件行号（连续范围包含其间每一行）|
|---|---:|---|
|`df`|598|114、120、127–128、148–149、167、170、182、186、192、195、197、207、217、225、231–232、239、241、256、274–275、278–279、294–296、299、304、312、314–315、324–325、329、331–332、340、364、368、370、375、386、388、396、405–406、414、417、435、438、443、450、470–471、499、503、506–507、519、530–533、536、546、554、587、593、612、615、617、626、637–638、642、644、653、665、671、673、682–683、689、695、697–698、702、737、751–752、761–762、773、803、831–832、836、839、846、849、852、854、862、867–868、905、908、913、916、926、939–941、943、954、959、971、980、982、986、1004–1005、1007、1009、1012、1019、1023–1025、1031、1035–1036、1040、1056、1067、1083–1084、1094–1096、1113、1121、1126、1134、1138–1139、1307、1313、1320–1321、1341–1342、1360、1363、1375、1379、1385、1388、1390、1400、1410、1418、1424–1425、1432、1434、1449、1467–1468、1471–1472、1487–1489、1492、1497、1505、1507–1508、1517–1518、1522、1524–1525、1533、1557、1561、1563、1568、1579、1581、1589、1598–1599、1607、1610、1628、1631、1636、1643、1663–1664、1692、1696、1699–1700、1712、1723–1726、1729、1739、1747、1780、1786、1805、1808、1810、1819、1830–1831、1835、1837、1846、1858、1864、1866、1875–1876、1882、1888、1890–1891、1895、1930、1944–1945、1954–1955、1966、1996、2024–2025、2029、2032、2039、2042、2045、2047、2055、2060–2061、2098、2101、2106、2109、2119、2132–2134、2136、2147、2152、2164、2173、2175、2179、2197–2198、2200、2202、2205、2212、2216–2218、2224、2228–2229、2233、2249、2260、2276–2277、2287–2289、2306、2314、2319、2327、2331–2332、2356、2362、2369–2370、2390–2391、2409、2412、2424、2428、2434、2437、2439、2449、2459、2467、2473–2474、2481、2483、2498、2516–2517、2520–2521、2536–2538、2541、2546、2554、2556–2557、2566–2567、2571、2573–2574、2582、2606、2610、2612、2617、2628、2630、2638、2647–2648、2656、2659、2677、2680、2685、2692、2712–2713、2741、2745、2748–2749、2761、2772–2775、2778、2788、2796、2829、2835、2854、2857、2859、2868、2879–2880、2884、2886、2895、2907、2913、2915、2924–2925、2931、2937、2939–2940、2944、2979、2993–2994、3003–3004、3015、3045、3073–3074、3078、3081、3088、3091、3094、3096、3104、3109–3110、3147、3150、3155、3158、3168、3181–3183、3185、3196、3201、3213、3222、3224、3228、3246–3247、3249、3251、3254、3261、3265–3267、3273、3277–3278、3282、3298、3309、3325–3326、3336–3338、3355、3363、3368、3376、3380–3381、3926、3940、4171–4172、4529、5001、5006、5013–5014、5031、5042、5046、5052、5067–5068、5077、5082、5089、5097、5100、5109、5117、5120、5127、5130、5145、5158、5162、5164、5177–5178、5181、5184、5187、5192、5204–5207、5209、5216–5217、5232、5234、5239、5246、5250、5252、5259、5284、5292–5293、5307、5323、5327、5341–5342、5345、5350、5358、5374–5375、5383、5388、5392、5399、5402、5406、5408、5414、5419、5427、5431、5462–5463、5487、5495、5499、5513、5516、5527、5532、5543、5547–5548、5565、5576–5578、5584、5595、5603–5604、5621、5640、5649–5650、5655、5668、5673、5702、5719、5724、5726、5729、5734、5737、5741、5748、5751、5755、5762、5790、5795、5800、5804、5818–5819、5829–5830、5837、5843、5845、5862、5869、5872、5877、5893–5894、5897、5900、5907–5908、5912–5913、5915–5916、5921、5925、5935、5945、5954、5969、5971、5984、5986、5995、6000、6010、6015、6022、6024、6030、6477|
|`free`|19|662–664、1855–1857、2904–2906、3501、3926、3940、4502–4504、5554、5560、5573、6477|
|`No space`|0|无|
|`ENOSPC`|0|无|
|`Killed`|0|无|
|`signal`|8|1018、2211、3260、3926、3940、4858、5901、6477|
|`oom`|0|无|
|`timeout`|56|1193、3724、6527、6780、7033、7287、7554、7847、8106、8367、8627、8890、9194、9458、9722、9981、10240、10504、10763、11022、11283、11543、11803、12062、12321、12592、12860、13127、13186、13456、13891、14328、14764、15200、15633、16068、16505、16941、17377、17814、18248、18681、19114、19548、19981、20414、20847、21106、21808、22492–22498|
|`abort`|0|无|
|`cancel`|1|22536|
|`returned exit code`|0|无|
|`rc=`|0|无|

### 1189686full-log.txt

[全部命中行原文](../evidence/qb-1189686full-log-keyword_hits.txt)

|词|命中行数|原文件行号（连续范围包含其间每一行）|
|---|---:|---|
|`df`|34|541、553、1213、1616–1617、1996–1997、2562–2563、5184–5185、5256、5266、5282、5350、5358、5375、5383、5391、5399、5407、5470、5472、5500、5521、6189、6469、6727、6986、7338、7783、7799、7958、8760|
|`free`|24|208、450、477、562、739、1488–1489、1694–1695、1795–1797、2046–2047、2602–2603、2725–2726、5917–5918、5920–5921、5923–5924|
|`No space`|0|无|
|`ENOSPC`|0|无|
|`Killed`|0|无|
|`signal`|20|1183、3841–3842、5008、5364、5366–5367、5587、8157–8160、8424–8427、8670–8673|
|`oom`|1|4997|
|`timeout`|32|21–24、26–28、116、4697、5069、5142、5650–5670|
|`abort`|0|无|
|`cancel`|1|5329|
|`returned exit code`|0|无|
|`rc=`|0|无|

### 命中语义复核

- 四份 image 日志 `oom` 各1命中，实际上是 `screen_zoom`：1178308 L5021、1182527 L5015、1187398 L4997、1189686 L4997；不是 OOM。`signal` 是 system-signal-sender 包/路径，父是 rust-signal-hook-registry 项目（逐行原文见上方链接）。
- `df` 为 dfs-adaptation/dfs-opencv/libsndfile、hash/path 等；`free` 为 libfreebl/libfreetype/freedesktop 等，未见独立 df/free 命令及其磁盘/内存统计输出（五份全文索引及命中原文）。因此不能据这些 substring 命中认定 worker 有资源采样。
- image 的 `timeout` 命中来自 KS `bootloader --timeout=3`、`syspopup timeout[-1]` 等，例如1178308 L21、L5697；`cancel` 是 libaction-cancel-alarm.so（1178308 L5337、1182527 L5353、1187398 L5329、1189686 L5329）。父 `timeout` 有 `timeout 9h/6h gbs build` 的命令配置（L1193、3724）及KS内容，**不是 image 超时事件**；父 `cancel` 的唯一命中是上述通用传播模板（L22536）。
- 五份均无 `No space`、`ENOSPC`、`Killed`、`abort`、`returned exit code`、`rc=` 字符串。实际 mic 数字返回记录采用 `Error: mic returned 1`（两个失败子日志 L8936），必须额外检索，不能因 requested phrase 无命中就漏掉它。

## 五、从 Pack all loop images together 到 EOF 的每一行原文

四份 image 日志的打包之后没有下一条 `Running step...`，因此每段保留到 EOF；行首数字只是取证索引，冒号后逐字保留时间戳和原文。空输出的 QB 行也保留。父日志没有这条打包起点，故没有可摘录的打包段（`1189639full-log.txt` L1–22544；metadata packing=[]）。

### 1178308full-log.txt L8933–L8978

```text
8933: 19:11:37,309 INFO  - INFO: Pack all loop images together to tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.tar.gz
8934: 19:11:37,310 INFO  - INFO: Running command: tar -C /var/tmp/mic/build/imgcreate-eyu_1uwy/tmp-k4mpfzpk -cf /var/tmp/mic/build/imgcreate-eyu_1uwy/out/tmpq8ca4l2r.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
8935: 19:11:52,103 INFO  - INFO: Running command: gzip -f /var/tmp/mic/build/imgcreate-eyu_1uwy/out/tmpq8ca4l2r.tar
8936: 19:13:05,317 INFO  - INFO: Creating manifest file...
8937: 19:13:07,507 INFO  - INFO: The new image can be found here:
8938: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/MD5SUMS
8939: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/SHA1SUMS
8940: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/SHA256SUMS
8941: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/manifest.json
8942: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.files
8943: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks
8944: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.license
8945: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.packages
8946: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.tar.gz
8947: 19:13:07,507 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/images/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.xml
8948: 19:13:07,507 INFO  - 
8949: 19:13:07,524 INFO  - INFO: Finished.
8950: 19:13:08,118 INFO  - building file list ... done
8951: 19:13:08,119 INFO  - images/
8952: 19:13:08,119 INFO  - images/standard/
8953: 19:13:08,119 INFO  - images/standard/tizen-headed-aarch64/
8954: 19:13:08,119 INFO  - images/standard/tizen-headed-aarch64/MD5SUMS
8955: 19:13:08,119 INFO  - images/standard/tizen-headed-aarch64/SHA1SUMS
8956: 19:13:08,119 INFO  - images/standard/tizen-headed-aarch64/SHA256SUMS
8957: 19:13:08,119 INFO  - images/standard/tizen-headed-aarch64/manifest.json
8958: 19:13:08,119 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.files
8959: 19:13:08,121 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks
8960: 19:13:08,121 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.license
8961: 19:13:08,121 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log
8962: 19:13:08,123 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.packages
8963: 19:13:08,123 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.tar.gz
8964: 19:13:09,529 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.xml
8965: 19:13:09,578 INFO  - 
8966: 19:13:09,578 INFO  - sent 698,781,503 bytes  received 242 bytes  465,854,496.67 bytes/sec
8967: 19:13:09,578 INFO  - total size is 698,609,851  speedup is 1.00
8968: 19:13:09,579 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified-toolchain_20260917.132101 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.log
8969: 19:13:09,579 INFO  - sync_src:/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101, sync_dest:rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260917.132101
8970: 19:13:09,579 INFO  - os.getcwd() is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-202_8812
8971: 19:13:09,579 INFO  - current working directory is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-202_8812
8972: 19:13:09,579 INFO  - rsync -av --delay-updates  /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101/* rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260917.132101
8973: 19:13:09,579 INFO  - Success sync /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260917.132101 to rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260917.132101
8974: 19:13:09,579 INFO  - The build was successful.
8975: 19:13:09,615 INFO  - Remove /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
8976: 19:13:09,674 INFO  - Executing post-execute action...
8977: 19:13:09,826 INFO  - Executing post-execute action...
8978: 19:13:10,037 INFO  - Executing post-execute action...
```

### 1182527full-log.txt L8903–L8948

```text
8903: 09:48:43,863 INFO  - INFO: Pack all loop images together to tizen-unified_20260923.050314_tizen-headed-aarch64.tar.gz
8904: 09:48:43,863 INFO  - INFO: Running command: tar -C /var/tmp/mic/build/imgcreate-txe2d1d2/tmp-31fc67my -cf /var/tmp/mic/build/imgcreate-txe2d1d2/out/tmpca32pvfm.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
8905: 09:48:58,938 INFO  - INFO: Running command: gzip -f /var/tmp/mic/build/imgcreate-txe2d1d2/out/tmpca32pvfm.tar
8906: 09:50:17,856 INFO  - INFO: Creating manifest file...
8907: 09:50:20,155 INFO  - INFO: The new image can be found here:
8908: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/MD5SUMS
8909: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/SHA1SUMS
8910: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/SHA256SUMS
8911: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/manifest.json
8912: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.files
8913: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.ks
8914: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.license
8915: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.packages
8916: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.tar.gz
8917: 09:50:20,155 INFO  -   /data/workspace/gbsbuild-ROOT/IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/images/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.xml
8918: 09:50:20,155 INFO  - 
8919: 09:50:20,177 INFO  - INFO: Finished.
8920: 09:50:20,682 INFO  - building file list ... done
8921: 09:50:20,683 INFO  - images/
8922: 09:50:20,683 INFO  - images/standard/
8923: 09:50:20,683 INFO  - images/standard/tizen-headed-aarch64/
8924: 09:50:20,683 INFO  - images/standard/tizen-headed-aarch64/MD5SUMS
8925: 09:50:20,683 INFO  - images/standard/tizen-headed-aarch64/SHA1SUMS
8926: 09:50:20,683 INFO  - images/standard/tizen-headed-aarch64/SHA256SUMS
8927: 09:50:20,683 INFO  - images/standard/tizen-headed-aarch64/manifest.json
8928: 09:50:20,683 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.files
8929: 09:50:20,685 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.ks
8930: 09:50:20,685 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.license
8931: 09:50:20,685 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.log
8932: 09:50:20,687 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.packages
8933: 09:50:20,687 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.tar.gz
8934: 09:50:22,297 INFO  - images/standard/tizen-headed-aarch64/tizen-unified_20260923.050314_tizen-headed-aarch64.xml
8935: 09:50:22,346 INFO  - 
8936: 09:50:22,346 INFO  - sent 722,004,533 bytes  received 242 bytes  288,801,910.00 bytes/sec
8937: 09:50:22,346 INFO  - total size is 721,827,243  speedup is 1.00
8938: 09:50:22,347 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified_20260923.050314 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314_tizen-headed-aarch64.log
8939: 09:50:22,347 INFO  - sync_src:/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314, sync_dest:rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified/tizen-unified_20260923.050314
8940: 09:50:22,347 INFO  - os.getcwd() is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-118_8812
8941: 09:50:22,347 INFO  - current working directory is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-118_8812
8942: 09:50:22,347 INFO  - rsync -av --delay-updates  /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314/* rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified/tizen-unified_20260923.050314
8943: 09:50:22,347 INFO  - Success sync /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified_20260923.050314 to rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified/tizen-unified_20260923.050314
8944: 09:50:22,347 INFO  - The build was successful.
8945: 09:50:22,380 INFO  - Remove /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
8946: 09:50:22,437 INFO  - Executing post-execute action...
8947: 09:50:22,499 INFO  - Executing post-execute action...
8948: 09:50:22,644 INFO  - Executing post-execute action...
```

### 1187398full-log.txt L8876–L8955

```text
8876: 16:54:10,781 INFO  - INFO: Pack all loop images together to tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.tar.gz
8877: 16:54:10,782 INFO  - INFO: Running command: tar -C /var/tmp/mic/build/imgcreate-b62wua5u/tmp-7zn1w9sc -cf /var/tmp/mic/build/imgcreate-b62wua5u/out/tmplxoqzh3o.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
8878: 16:54:24,928 INFO  - INFO: Running command: gzip -f /var/tmp/mic/build/imgcreate-b62wua5u/out/tmplxoqzh3o.tar
8879: 16:55:07,361 INFO  - Traceback (most recent call last):
8880: 16:55:07,367 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 918, in move
8881: 16:55:07,367 INFO  -     os.rename(src, real_dst)
8882: 16:55:07,367 INFO  -     ~~~~~~~~~^^^^^^^^^^^^^^^
8883: 16:55:07,367 INFO  - FileNotFoundError: [Errno 2] No such file or directory: '/var/tmp/mic/build/imgcreate-b62wua5u/out/tmplxoqzh3o.tar.gz' -> '/var/tmp/mic/build/imgcreate-b62wua5u/out/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.tar.gz'
8884: 16:55:07,367 INFO  - 
8885: 16:55:07,367 INFO  - During handling of the above exception, another exception occurred:
8886: 16:55:07,367 INFO  - 
8887: 16:55:07,367 INFO  - Traceback (most recent call last):
8888: 16:55:07,370 INFO  -   File "/usr/bin/mic", line 327, in <module>
8889: 16:55:07,370 INFO  -     sys.exit(main(sys.argv))
8890: 16:55:07,370 INFO  -              ~~~~^^^^^^^^^^
8891: 16:55:07,370 INFO  -   File "/usr/bin/mic", line 323, in main
8892: 16:55:07,370 INFO  -     return module.main(parser, args, argv[1:])
8893: 16:55:07,370 INFO  -            ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
8894: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/cmd_create.py", line 59, in main
8895: 16:55:07,370 INFO  -     do_auto(parser, args.ksfile, argv)
8896: 16:55:07,370 INFO  -     ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
8897: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/cmd_create.py", line 272, in do_auto
8898: 16:55:07,370 INFO  -     main(parser, args, options)
8899: 16:55:07,370 INFO  -     ~~~~^^^^^^^^^^^^^^^^^^^^^^^
8900: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/cmd_create.py", line 216, in main
8901: 16:55:07,370 INFO  -     creater.do_create(args)
8902: 16:55:07,370 INFO  -     ~~~~~~~~~~~~~~~~~^^^^^^
8903: 16:55:07,370 INFO  -   File "/usr/lib/mic/plugins/imager/loop_plugin.py", line 64, in do_create
8904: 16:55:07,370 INFO  -     creator.package(creatoropts["destdir"])
8905: 16:55:07,370 INFO  -     ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
8906: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/imager/baseimager.py", line 1499, in package
8907: 16:55:07,370 INFO  -     self._stage_final_image()
8908: 16:55:07,370 INFO  -     ~~~~~~~~~~~~~~~~~~~~~~~^^
8909: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/imager/loop.py", line 533, in _stage_final_image
8910: 16:55:07,370 INFO  -     packing(dstfile, self._imgdir)
8911: 16:55:07,370 INFO  -     ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
8912: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/archive.py", line 453, in make_archive
8913: 16:55:07,370 INFO  -     return func(archive_name, target_name, **kwargs)
8914: 16:55:07,370 INFO  -   File "/usr/lib/python3.14/site-packages/mic/archive.py", line 346, in _make_tarball
8915: 16:55:07,370 INFO  -     shutil.move(tarball_name, archive_name)
8916: 16:55:07,370 INFO  -     ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
8917: 16:55:07,370 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 938, in move
8918: 16:55:07,370 INFO  -     copy_function(src, real_dst)
8919: 16:55:07,370 INFO  -     ~~~~~~~~~~~~~^^^^^^^^^^^^^^^
8920: 16:55:07,370 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 529, in copy2
8921: 16:55:07,370 INFO  -     copyfile(src, dst, follow_symlinks=follow_symlinks)
8922: 16:55:07,370 INFO  -     ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
8923: 16:55:07,370 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 313, in copyfile
8924: 16:55:07,370 INFO  -     with open(src, 'rb') as fsrc:
8925: 16:55:07,370 INFO  -          ~~~~^^^^^^^^^^^
8926: 16:55:07,370 INFO  - FileNotFoundError: [Errno 2] No such file or directory: '/var/tmp/mic/build/imgcreate-b62wua5u/out/tmplxoqzh3o.tar.gz'
8927: 16:55:08,210 INFO  - building file list ... done
8928: 16:55:08,211 INFO  - images/
8929: 16:55:08,211 INFO  - images/standard/
8930: 16:55:08,211 INFO  - images/standard/tizen-headed-aarch64/
8931: 16:55:08,211 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log
8932: 16:55:08,254 INFO  - 
8933: 16:55:08,254 INFO  - sent 743,753 bytes  received 52 bytes  1,487,610.00 bytes/sec
8934: 16:55:08,254 INFO  - total size is 743,317  speedup is 1.00
8935: 16:55:08,254 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified-toolchain_20260930.105301 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260930.105301_tizen-headed-aarch64.log
8936: 16:55:08,254 INFO  - Error: mic returned 1
8937: 16:55:08,254 INFO  - sync_src:/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260930.105301, sync_dest:rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260930.105301
8938: 16:55:08,255 INFO  - os.getcwd() is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-91_8812
8939: 16:55:08,255 INFO  - current working directory is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-91_8812
8940: 16:55:08,255 INFO  - rsync -av --delay-updates  /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260930.105301/* rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260930.105301
8941: 16:55:08,255 INFO  - Success sync /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20260930.105301 to rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260930.105301
8942: 16:55:08,329 INFO  - Traceback (most recent call last):
8943: 16:55:08,329 INFO  -   File "/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/QB_SCRIPTS_5cFtEA/exec_image_creation.py", line 440, in <module>
8944: 16:55:08,330 INFO  -     sys.exit(main())
8945: 16:55:08,330 INFO  -              ^^^^^^
8946: 16:55:08,330 INFO  -   File "/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/QB_SCRIPTS_5cFtEA/exec_image_creation.py", line 436, in main
8947: 16:55:08,331 ERROR -     raise LocalError('Error: Image Creation Failed')
8948: 16:55:08,331 INFO  - LocalError: Error: Image Creation Failed
8949: 16:55:08,382 INFO  - Remove /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
8950: 16:55:08,423 INFO  - Executing post-execute action...
8951: 16:55:08,423 ERROR - Step 'master>IMAGE>Image_Create' is failed:     raise LocalError('Error: Image Creation Failed')
8952: 16:55:08,588 INFO  - Executing post-execute action...
8953: 16:55:08,588 ERROR - Step 'master>IMAGE' is failed: Composite step 'IMAGE' failed due to unsatisfied success condition.
8954: 16:55:08,695 INFO  - Executing post-execute action...
8955: 16:55:08,716 ERROR - Step 'master' is failed: Composite step 'master' failed due to unsatisfied success condition.
```

### 1189686full-log.txt L8876–L8955

```text
8876: 16:21:46,940 INFO  - INFO: Pack all loop images together to tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.tar.gz
8877: 16:21:46,943 INFO  - INFO: Running command: tar -C /var/tmp/mic/build/imgcreate-q3ebnnd3/tmp-oi7izcgd -cf /var/tmp/mic/build/imgcreate-q3ebnnd3/out/tmpvupuwmim.tar system-data.img user.img rootfs.img ramdisk-recovery.img ramdisk.img
8878: 16:22:01,450 INFO  - INFO: Running command: pigz -f /var/tmp/mic/build/imgcreate-q3ebnnd3/out/tmpvupuwmim.tar
8879: 16:22:31,278 INFO  - Traceback (most recent call last):
8880: 16:22:31,283 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 918, in move
8881: 16:22:31,283 INFO  -     os.rename(src, real_dst)
8882: 16:22:31,283 INFO  -     ~~~~~~~~~^^^^^^^^^^^^^^^
8883: 16:22:31,283 INFO  - FileNotFoundError: [Errno 2] No such file or directory: '/var/tmp/mic/build/imgcreate-q3ebnnd3/out/tmpvupuwmim.tar.gz' -> '/var/tmp/mic/build/imgcreate-q3ebnnd3/out/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.tar.gz'
8884: 16:22:31,283 INFO  - 
8885: 16:22:31,283 INFO  - During handling of the above exception, another exception occurred:
8886: 16:22:31,283 INFO  - 
8887: 16:22:31,283 INFO  - Traceback (most recent call last):
8888: 16:22:31,286 INFO  -   File "/usr/bin/mic", line 327, in <module>
8889: 16:22:31,286 INFO  -     sys.exit(main(sys.argv))
8890: 16:22:31,286 INFO  -              ~~~~^^^^^^^^^^
8891: 16:22:31,286 INFO  -   File "/usr/bin/mic", line 323, in main
8892: 16:22:31,286 INFO  -     return module.main(parser, args, argv[1:])
8893: 16:22:31,286 INFO  -            ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
8894: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/cmd_create.py", line 59, in main
8895: 16:22:31,286 INFO  -     do_auto(parser, args.ksfile, argv)
8896: 16:22:31,286 INFO  -     ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
8897: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/cmd_create.py", line 272, in do_auto
8898: 16:22:31,286 INFO  -     main(parser, args, options)
8899: 16:22:31,286 INFO  -     ~~~~^^^^^^^^^^^^^^^^^^^^^^^
8900: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/cmd_create.py", line 216, in main
8901: 16:22:31,286 INFO  -     creater.do_create(args)
8902: 16:22:31,286 INFO  -     ~~~~~~~~~~~~~~~~~^^^^^^
8903: 16:22:31,286 INFO  -   File "/usr/lib/mic/plugins/imager/loop_plugin.py", line 64, in do_create
8904: 16:22:31,286 INFO  -     creator.package(creatoropts["destdir"])
8905: 16:22:31,286 INFO  -     ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
8906: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/imager/baseimager.py", line 1499, in package
8907: 16:22:31,286 INFO  -     self._stage_final_image()
8908: 16:22:31,286 INFO  -     ~~~~~~~~~~~~~~~~~~~~~~~^^
8909: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/imager/loop.py", line 533, in _stage_final_image
8910: 16:22:31,286 INFO  -     packing(dstfile, self._imgdir)
8911: 16:22:31,286 INFO  -     ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
8912: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/archive.py", line 453, in make_archive
8913: 16:22:31,286 INFO  -     return func(archive_name, target_name, **kwargs)
8914: 16:22:31,286 INFO  -   File "/usr/lib/python3.14/site-packages/mic/archive.py", line 346, in _make_tarball
8915: 16:22:31,286 INFO  -     shutil.move(tarball_name, archive_name)
8916: 16:22:31,286 INFO  -     ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
8917: 16:22:31,286 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 938, in move
8918: 16:22:31,286 INFO  -     copy_function(src, real_dst)
8919: 16:22:31,286 INFO  -     ~~~~~~~~~~~~~^^^^^^^^^^^^^^^
8920: 16:22:31,286 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 529, in copy2
8921: 16:22:31,286 INFO  -     copyfile(src, dst, follow_symlinks=follow_symlinks)
8922: 16:22:31,286 INFO  -     ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
8923: 16:22:31,286 INFO  -   File "/usr/lib64/python3.14/shutil.py", line 313, in copyfile
8924: 16:22:31,286 INFO  -     with open(src, 'rb') as fsrc:
8925: 16:22:31,286 INFO  -          ~~~~^^^^^^^^^^^
8926: 16:22:31,286 INFO  - FileNotFoundError: [Errno 2] No such file or directory: '/var/tmp/mic/build/imgcreate-q3ebnnd3/out/tmpvupuwmim.tar.gz'
8927: 16:22:32,299 INFO  - building file list ... done
8928: 16:22:32,299 INFO  - images/
8929: 16:22:32,299 INFO  - images/standard/
8930: 16:22:32,299 INFO  - images/standard/tizen-headed-aarch64/
8931: 16:22:32,299 INFO  - images/standard/tizen-headed-aarch64/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log
8932: 16:22:32,342 INFO  - 
8933: 16:22:32,342 INFO  - sent 743,709 bytes  received 52 bytes  1,487,522.00 bytes/sec
8934: 16:22:32,342 INFO  - total size is 743,273  speedup is 1.00
8935: 16:22:32,343 INFO  - starting mic to create image: sudo /usr/bin/mic cr auto /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks --release tizen-unified-toolchain_20261003.102419 -o /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out -k /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/cache --logfile=/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20261003.102419_tizen-headed-aarch64.log
8936: 16:22:32,343 INFO  - Error: mic returned 1
8937: 16:22:32,343 INFO  - sync_src:/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20261003.102419, sync_dest:rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261003.102419
8938: 16:22:32,343 INFO  - os.getcwd() is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812
8939: 16:22:32,343 INFO  - current working directory is : /home/tizenbuild/ci_tizen_workspace/ip-192-168-56-168_8812
8940: 16:22:32,343 INFO  - rsync -av --delay-updates  /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20261003.102419/* rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261003.102419
8941: 16:22:32,343 INFO  - Success sync /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-unified-toolchain_20261003.102419 to rsync://download.prod.infra.tizen.org/_quickbuild_RW_/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261003.102419
8942: 16:22:32,420 INFO  - Traceback (most recent call last):
8943: 16:22:32,420 INFO  -   File "/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/QB_SCRIPTS_aGjENJ/exec_image_creation.py", line 440, in <module>
8944: 16:22:32,422 INFO  -     sys.exit(main())
8945: 16:22:32,422 INFO  -              ^^^^^^
8946: 16:22:32,422 INFO  -   File "/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/QB_SCRIPTS_aGjENJ/exec_image_creation.py", line 436, in main
8947: 16:22:32,422 ERROR -     raise LocalError('Error: Image Creation Failed')
8948: 16:22:32,422 INFO  - LocalError: Error: Image Creation Failed
8949: 16:22:32,479 INFO  - Remove /data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812
8950: 16:22:32,531 INFO  - Executing post-execute action...
8951: 16:22:32,532 ERROR - Step 'master>IMAGE>Image_Create' is failed:     raise LocalError('Error: Image Creation Failed')
8952: 16:22:32,741 INFO  - Executing post-execute action...
8953: 16:22:32,741 ERROR - Step 'master>IMAGE' is failed: Composite step 'IMAGE' failed due to unsatisfied success condition.
8954: 16:22:32,941 INFO  - Executing post-execute action...
8955: 16:22:32,955 ERROR - Step 'master' is failed: Composite step 'master' failed due to unsatisfied success condition.
```

