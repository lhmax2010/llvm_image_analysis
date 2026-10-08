> 2026-10-08 方向调整：整镜像 baseline/space/oom 已取消。本文仅保留历史命令和非 root 启动取证；need_sudo.sh 已停用，以下历史配方不再执行，也不再要求 sudo。

# 基线启动命令修正（stage2a2，2026-10-06）

当前 `docs/need_sudo.sh` 使用 [mic_local.py](mic_local.py) 本地入口，`-c "$CONF"` 紧跟入口文件、在cr之前。入口先读取配置，再导入原始mic的插件管理器；转发给未修改的官方mic parser时，把-c放到其支持的create子命令参数位置。普通用户完整命令已执行到 `Root permission is required, abort`（rc2），没有插件目录或不支持loop警告；实际loop插件加载另行验证通过。所有验证都没有sudo、没有整镜像、没有绕过root检查。

## 当前命令

```bash
"$MIC_PY" "$MIC_BIN" -c "$CONF" --non-interactive cr auto "$KS" --release "$RELEASE" -o "$OUT" -k "$ROOT/work/cache" -A aarch64 --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license --runtime bootstrap --logfile "$PREFIX-mic.log"
```

`ROOT=/home/linhao/Toolchain/development/llvm_image_analysis`；`MIC_PY=/usr/bin/python3`；**`MIC_BIN=$ROOT/docs/mic_local.py`**；它调用的原始入口是 `$ROOT/work/tools/usr/bin/mic`。`KS=$ROOT/downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks`；`RELEASE=tizen-unified-toolchain_20260917.132101`；baseline `OUT=$ROOT/work/base`。正式脚本仍按STAMP新建CONF和PREFIX；本次非root试跑使用独立的 `work/mic-baseline-dryrun-nonroot.conf` 和 `evidence/baseline-dryrun-nonroot` 前缀，不覆盖两次历史记录。[完整展开命令](../evidence/baseline-dryrun-nonroot-command.txt)。

## 第一次尝试：全局-c在原始parser中不受支持（历史）

[211839-console.log](../evidence/baseline-20261006-211839-console.log) L19 的invalid choice指向CONF路径；[首次命令](../evidence/baseline-20261006-211839-command.txt) 把-c直接传到原始mic全局位置。官方 [tools/mic](../evidence/src_snapshot/mic/tools/mic) L70–71只在create子解析器定义-c；全局L236–250没有-c。首次返回2、0.22秒、RSS44,156KiB仅为parser启动，不是镜像基线（[time](../evidence/baseline-20261006-211839-time.txt) L1、6、11、24）。

stage2a把-c移到cr auto之后，另把全局 `--non-interactive` 移到cr之前，新增release并对齐-o/-k。其完整参数解析和help通过，证据 [历史解析结果](../evidence/baseline-command-validation.json)，但解析哨兵在parse_args后就停了，没有覆盖插件初始化。那次校验的范围不足以确认完整启动流程；这些材料保留作为历史，不当作当前入口的验证。

## 第二次尝试：-c位置错误，原因与修正，非root试跑结果

### 失败原因是加载时序，不能只把-c移回原始入口全局

[214442-console.log](../evidence/baseline-20261006-214442-console.log) L10–11：

```text
WARNING: Plugin dir is not a directory or does not exist: /usr/lib/mic/plugins/imager
ERROR: Can't support subcommand loop
```

[214442-command.txt](../evidence/baseline-20261006-214442-command.txt) 的-c位置在parser看来有效，却来不及影响插件选择：

1. `tools/mic` L38–39在入口导入configmgr/pluginmgr。[plugin.py](../evidence/src_snapshot/mic/mic/plugin.py) L42–43在PluginMgr构造时固定 `configmgr.common['plugin_dir']`；L98在模块导入时创建单例。
2. [cmd_create.py](../evidence/src_snapshot/mic/mic/cmd_create.py) L85–93先查找/加载imager，找不到loop就报错；L95–97才reset并读取 `args.config`。所以错误发生时配置仍为默认插件目录，而不是本地目录。[conf.py](../evidence/src_snapshot/mic/mic/conf.py) L43–45的默认路径就是 `/usr/lib/mic/plugins`。
3. 本机 `work/tools/usr/lib/mic/plugins/imager/loop_plugin.py` **真实存在**。第二次CONF的section/键名原本正确，无需把路径改到源码目录；配置的问题是读取太晚。

本次也用普通用户验证“直接把-c移到未修改原始mic前面”，仍得到parser invalid choice与rc2，见 [原始全局-c验证输出](../evidence/baseline-original-global-c.log)。因此本次修正包含必要的本地入口，而非声称官方2.1.3已经支持全局-c。

[mic_local.py](mic_local.py) 在导入任何mic模块前消费全局-c，检查CONF和imager子目录，设置conf.py支持的 `MIC_PLUGIN_DIR`（conf.py L150–151），随后调用 `configmgr._siteconf=CONF`；最后执行原始mic入口。它只把-c重新放到原始parser合法位置；不改变archive/插件实现、root检查、KS包列表或官方源码快照。need_sudo.sh验证的是 **plugins/imager子目录**；若不存在才选择 `downloads/src/mic/plugins`，两者都没有时停止。

### 配置section与键名核验

本次 [配置文本](../evidence/baseline-dryrun-nonroot.conf.txt) 与 [核验JSON](../evidence/baseline-dryrun-nonroot-result.json) 记录所有读取值；用实际ConfigMgr.DEFAULTS逐键检查，不依赖猜测的拼法。

|section|键及本地值|读取逻辑|
|---|---|---|
|common|`distro_name=Tizen`；`plugin_dir=$ROOT/work/tools/usr/lib/mic/plugins`|conf.py L43–45定义；L169–176读section并把common合并到其余section。plugin_dir是imager父目录，插件管理器再拼 `/imager`（plugin.py L93）|
|create|`tmpdir=$ROOT/work/base-tmp`；`cachedir=$ROOT/work/cache`；`outdir=$ROOT/work/base`；`runtime=bootstrap`；`pkgmgr=auto`|conf.py L47–53、L75、L169–171；不是tmp_dir/cache_dir/outputdir。命令-o/-k后续按cmd_create.py L99–102覆盖相同值|
|bootstrap|`rootdir=$ROOT/work/bootstrap`；`packages=mic-bootstrap-x86-arm`|conf.py L92–95；L194–201把packages字符串转成列表，实际读到 `['mic-bootstrap-x86-arm']`|

### 普通用户完整试跑

[验证驱动](../evidence/baseline_nonroot_validation.py)只从need_sudo.sh提取CMD赋值，固定本地变量后**运行完整命令**；没有解析哨兵、没有sudo、没有mock UID。UID/EUID均1000，结果存到用户指定的 [baseline-dryrun-nonroot.log](../evidence/baseline-dryrun-nonroot.log)。

- 结果rc=2，现在原因是明确的 `Root permission is required, abort`（L10），而不是“不支持loop”。没有 `Plugin dir is not a directory` 或 `Can't support subcommand`。
- 原始非root检查位于cmd_create.py L41–42，**早于真正get_plugins**。因此“非root输出没有插件警告”本身不足以证明插件能导入；另以同样配置、普通用户调用 `pluginmgr.get_plugins('imager')`，确认loop类和do_create存在，并实际加载fs/loop/qcow/raw（[JSON](../evidence/baseline-dryrun-nonroot-result.json)、[探针输出](../evidence/baseline-local-plugin-probe.log)）。没有调用do_create。
- 仍有一次 `/etc/mic/mic.conf` 不存在的初始化警告（L1），因为ConfigMgr第一次导入读取默认站点文件，随后显式配置已加载。未屏蔽该警告；JSON证明实际pluginmgr目录和配置各键值已指向本地。
- 完整整镜像基线、挂载、bootstrap依赖、网络仓库、aarch64/%post和打包峰值仍未验证。本轮root guard未被绕过，因而没有创建整镜像或访问镜像仓库。

日志最后5行原文：

```text
OS of Image creation server for projects using python3 : have to be equal or higher than ubuntu 22.04 and openuse 15.2.
=================================================================================================================================

mic 2.1.3 (linhao-linux ubuntu 24.04 Noble Numbat)
ERROR: Root permission is required, abort
```

## 与 QB 实际命令的逐项差异

对照 `1178308full-log.txt` L8968：`sudo /usr/bin/mic cr auto KS --release RID -o OUT -k CACHE --logfile=LOG`；KS头部提供-A/pack-to/record-pkgs（L24），bootstrap由执行行为确认（L147–148）。控制台完整分析见 [qb_console_forensics.md](qb_console_forensics.md)。

|项目|QB|本机当前选择及差异|
|---|---|---|
|入口及config|sudo /usr/bin/mic，未显式-c|本地mic_local.py全局-c预加载配置，转发未修改的本地解包入口；本轮仅以普通用户验证|
|子命令/发行ID|cr auto，0917 release|相同|
|KS|QB工作目录的生成KS|本地下载的0917 KS；MD5与发布MD5SUMS不符，仍不能保证原始输入逐字节一致|
|outdir/cachedir/logfile|QB工作目录|全部换本地路径；输出baseline为work/base，正式log按STAMP保存|
|tmpdir|外层TMPDIR=/home/tizenbuild/tmp，实际tar在/var/tmp/mic/build|外层work/tmp、create.tmpdir=work/base-tmp；原parser没有--tmpdir选项|
|runtime|命令无显式参数，实际bootstrap|显式--runtime bootstrap|
|arch/pack-to/record-pkgs|命令无显式参数，选中KS头部提供|显式重复KS同值，维持已有复现选择|
|non-interactive|未显式设置|全局--non-interactive在cr之前；官方main L298–300强制关闭交互|
|压缩器/资源配置|PATH选择gzip或pigz，worker资源未知|未改变压缩器选择；未做root基线或资源实验|

本阶段修正配置生效时序，仍不是archive打包补丁交付。
