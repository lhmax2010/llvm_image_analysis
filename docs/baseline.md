# 基线命令修正（stage2a，2026-10-06）

首次运行的 [console.log](../evidence/baseline-20261006-211839-console.log) L19 报：

```text
mic: error: argument {chroot,create}: invalid choice: '/home/linhao/Toolchain/development/llvm_image_analysis/work/mic-baseline-20261006-211839.conf' (choose from 'chroot', 'create')
```

[原始命令](../evidence/baseline-20261006-211839-command.txt) 把 `-c <CONF>` 放在 `cr auto` 之前。实际 [tools/mic parser 快照](../evidence/src_snapshot/mic/tools/mic) L70–71 把 `-c/--config` 定义在 create 的 auto/loop 等子解析器；全局参数 L236–250 没有 `-c`。因此 argparse 在开始 create 之前返回2，与磁盘、压缩器、aarch64/%post 或 sudo 是否可用无关。不能把 L1 的 `/etc/mic/mic.conf` 缺失警告当作本次 fatal 错误，明确的错误在 L19。

另一个会在修正 `-c` 后暴露的问题是原命令末尾的 `--non-interactive`：它只定义在全局 parser（L248–250），应移到 `cr` 之前。create 子解析器有 `-i/--interactive`，没有 `--non-interactive`；main 在解析后检查 argv 并强制 `args.interactive=False`（L298–300），因此验证 JSON 中子解析器原始默认值 True 不表示实际执行会交互。

[首次 time 输出](../evidence/baseline-20261006-211839-time.txt) L1、6、11、24 是退出2、0.22秒、最大RSS44,156 KiB、exit status2；这些只描述 Python/parser 启动，**没有镜像基线、打包峰值、压缩时间或镜像内存测量**。首次所有原始材料和 sampler 保留，没有覆盖或重新执行。

## 修正前后

以下引用 shell 变量保持脚本原有含义：`ROOT=/home/linhao/Toolchain/development/llvm_image_analysis`；`MIC_PY=/usr/bin/python3`；`MIC_BIN=$ROOT/work/tools/usr/bin/mic`；`KS=$ROOT/downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks`；`CONF=$ROOT/work/mic-baseline-<STAMP>.conf`；`OUT=$ROOT/work/base`；`PREFIX=$ROOT/evidence/baseline-<STAMP>`；`RELEASE=tizen-unified-toolchain_20260917.132101`。每次未来正式运行仍生成新的 STAMP；验证用第一次的 STAMP 20261006-211839，只解析参数，不读写其 mic 日志。

修正前：

```bash
"$MIC_PY" "$MIC_BIN" -c "$CONF" cr auto "$KS" -A aarch64 --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license --cachedir "$ROOT/work/cache" --outdir "$OUT" --runtime bootstrap --non-interactive --logfile "$PREFIX-mic.log"
```

修正后（[need_sudo.sh](need_sudo.sh) 的 CMD）：

```bash
"$MIC_PY" "$MIC_BIN" --non-interactive cr auto "$KS" -c "$CONF" --release "$RELEASE" -o "$OUT" -k "$ROOT/work/cache" -A aarch64 --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license --runtime bootstrap --logfile "$PREFIX-mic.log"
```

[展开后的完整修正命令](../evidence/baseline-command-fixed.txt) 与 [原始完整命令](../evidence/baseline-20261006-211839-command.txt) 可直接比较。新增 `--release` 对齐0917成功QB命令；输出因此使用 release 子目录，采样 `OUT` 的递归占用仍覆盖它。

## 与 QB 实际命令的逐项差异

对照对象是 `1178308full-log.txt` L8968 的0917 clang/gzip成功 image 命令；L24选中KS的头部选项、L73 TMPDIR、L147–148实际bootstrap行为。失败QB命令只在release ID等运行路径值上变化：1187398/1189686 L8935。完整QB取证见 [控制台报告](qb_console_forensics.md)。

|项目|QB 1178308|修正的本机基线|原因 / 影响|
|---|---|---|---|
|启动器|`sudo /usr/bin/mic`|未来由用户以root运行脚本，使用 `/usr/bin/python3 $ROOT/work/tools/usr/bin/mic`|本地解压官方deb；当前验证完全未调用sudo；实际宿主/依赖/内核仍不同|
|子命令|`cr auto`|相同|保持通过KS头部自动选择loop|
|KS|`/data/workspace/gbsbuild-ROOT//IMG_WORKSPACE/8812/WORKSPACE/mic/out/tizen-headed-aarch64.ks`|本地已下载0917 KS|其MD5与发布MD5SUMS不符，不能保证逐字节同原输入，见log_forensics.md发布校验|
|release|`tizen-unified-toolchain_20260917.132101`|相同（本次新增）|匹配宏替换与发布目录命名|
|outdir|`-o .../mic/out`|`-o $ROOT/work/base`|仅换本地路径；正式运行可能产生release子目录|
|cachedir|`-k .../mic/cache`|`-k $ROOT/work/cache`|同一选项；由旧长拼法改成QB短拼法，语义不变|
|logfile|`--logfile=.../<release>_tizen-headed-aarch64.log`|`--logfile $PREFIX-mic.log`|本地按运行时间分开保存，完整控制台另存console.log|
|config|没有显式 `-c`，五份全文没有mic.conf内容|`-c $CONF` 位于 `cr auto KS` 之后|明确本地plugin_dir、tmpdir、bootstrap rootdir，保证产物在工作目录；不声称配置与QB逐项相同|
|tmpdir|命令无 `--tmpdir`；外层TMPDIR=/home/tizenbuild/tmp；实际tar在/var/tmp/mic/build|环境TMPDIR=$ROOT/work/tmp；配置create.tmpdir=$ROOT/work/base-tmp|分清Python外层临时目录与mic配置；该版本parser没有 `--tmpdir` 选项，不补造它|
|runtime|无显式参数；执行日志证实bootstrap|显式 `--runtime bootstrap`|保证相同模式；实际bootstrap包/宿主仍可能不同|
|architecture|无显式参数；KS头部 `-A aarch64`|显式 `-A aarch64`，KS同值|保留已有复现选择，值与选中KS一致|
|pack-to|无显式参数；KS头部 `--pack-to=@NAME@.tar.gz`|同值显式参数|保留旧打包路径，未改流式实现|
|record-pkgs|无显式参数；选中KS头部name,content,license|同值显式参数|保留已有复现选择|
|non-interactive|没有显式参数|全局 `--non-interactive` 位于cr之前|避免未来自动实验等待交互；差异明确保留|
|compressor|实际gzip；失败1003实际pigz|无额外压缩器参数|源码按bootstrap PATH有无pigz选择，未运行镜像不能声称本地一定使用gzip|
|tmpfs / memory limit|没有直接资源配置证据|baseline不启用tmpfs/MemoryMax；后续模式另行配置|本轮不执行资源实验，不拿默认值推断QB真实配置|

## 只读验证

[验证脚本](../evidence/baseline_parameter_validation.py) 从 need_sudo.sh **只提取 CMD 赋值**，固定本地变量展开argv；不运行整个脚本。确认本地deb的mic入口与 downloads/src/mic/tools/mic 逐字节相同后，调用真实 `main`，在真实 `ArgumentParser.parse_args` 返回的下一瞬间抛停止哨兵，禁止进入 `cmd_create` 导入/镜像创建。旧命令重现退出2，修正命令完整argv被接受；另外对修正命令追加 `--help` 得到退出0。

证据：[参数解析结果](../evidence/baseline-command-validation.json)、[解析控制台](../evidence/baseline-command-parser-console.txt)、[实际子命令help](../evidence/baseline-command-help.txt)。`cmd_create_imported=false`，没有sudo调用、镜像运行或网络仓库访问。`bash -n docs/need_sudo.sh` 仅做shell语法检查。

这只验证参数层级/拼写/值可被parser接受，不代表bootstrap依赖、挂载、跨架构执行、KS所有语义或真实基线已通过。下一阶段才重新执行完整基线并重新测峰值。
