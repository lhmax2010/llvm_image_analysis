# 源码阅读（2026-10-06）

## 版本与来源

Tizen cgit HTTPS 超时；review HTTPS 返回 403；git 协议返回未导出/拒绝访问。详见 `evidence/source_clone.log`、`evidence/source_clone_retry.json`、`evidence/bootstrap_clone_cgit.json`。首次超时留下目录导致两个 fallback 先报目录已存在，已改用独立超时、移开失败目录后重跑，不将这两个本地错误视为服务端不可达证据。

下载的官方 Ubuntu 24.04 源码包 `downloads/src/mic_2.1.3.tar.gz` 已解压到 `downloads/src/mic/`。该目录不是伪造的 Git checkout；`mic/__init__.py` L21 和 `packaging/mic.spec` L9 均为 2.1.3，与三份日志的宿主/bootstrap 版本相同。无法匿名取得现代 Tizen Git 的对应 tag/commit，因此严格意义的“切到对应 commit”尚未完成。Intel GitHub 镜像在 `downloads/src/mic-intel-legacy/`，HEAD 为 `d3a9cf382ce0e6c735c4bf3c30ff048127ee9f4f`，2022 年归档；镜像 tag 不能代表 2026 的官方版本。Tizenorg mic 镜像也没有 2.1.3 tag（`evidence/prepare_sources.json`）。以可复核 sha256 的官方 release 为分析基准，不拿旧源码替代。

mic-bootstrap 的 GitHub 镜像 `downloads/src/mic-bootstrap/` HEAD 为 `116b2e549d57c804549cd240078ef40c681ac41c`（2012 年）；`git fetch origin sandbox/dkson95/clang` 返回 missing remote ref，只能说明该旧镜像没有分支，不能推断 Tizen 权限库没有该分支。需用户提供有权限的 clone 或补丁原文（`evidence/prepare_sources.json`）。

已额外下载三个实际 snapshot 的 bootstrap 源 RPM：

|snapshot|spec 中 VCS commit|打包差异|证据|
|---|---|---|---|
|0917|51f241d86ecc960aaa2d4440d7da82aa45d5dbe5|强制 GNU tar；不显式装 pigz|`evidence/src_snapshot/mic-bootstrap-20260917.132101/packaging/mic-bootstrap.spec` L8、95–99|
|0930|51f241d86ecc960aaa2d4440d7da82aa45d5dbe5|源码 RPM 与成功那次 sha256 完全一致|`evidence/more_downloads.json`；同目录 0930 spec L8、95–99|
|1003|c910874621b48819566db8806b6a2251866fee31|Source1=pigz 2.8，编译并装进 bootstrap/bin|`evidence/src_snapshot/mic-bootstrap-20261003.102419/packaging/mic-bootstrap.spec` L8、20、60–65、102–108|

三份 spec 都仅 `BuildRequires: mic`，**没有固定 mic 版本**（0917/0930 L29，1003 L31）；spec 收集 buildroot 已安装 RPM 的文件（0917/0930 L64–94，1003 L71–101），不能据此确定内嵌 mic 的实际 NEVRA。更关键的是三份运行日志 L16 都写 `Copy host mic to bootstrap`，L19 打印 2.1.3。实际分支：`evidence/src_snapshot/mic/mic/rt_util.py` L165–175，默认复制宿主 mic，`--use-mic-in-bootstrap` 才选择不复制。源码 `get_bindmounts` L202–224 将 tmpdir/cachedir/outdir bind 进 bootstrap。因此 bootstrap 内置 mic 的版本并不等于本次执行源码；同版本号也不保证 worker 没有本地补丁，需 QB 提供 archive.py 的 sha256。

## 子进程及错误信息

以下行号均基于未修改的官方2.1.3源码；仓库内引用文件原样保存在 `evidence/src_snapshot/mic/`，本机完整解包在被忽略的 `downloads/src/mic/`。

- `mic/archive.py` L66–83：列表参数以 `shell=False` 调用 `Popen`；字符串以 shell 调用；stdout 设 PIPE，stderr 合并到 STDOUT。`communicate()` 返回 `(outdata, None)`，函数再返回 `(proc.returncode, outdata, None)`。子进程错误文字留在 bytes 型 outdata，不自动进入 mic log。
- L76 只打印启动命令，不打印完成/退出码。字符串命令的日志还会错误地按字符 join，但本次 tar/gzip/pigz 都传列表。
- gzip/pigz L102、bzip2/pbzip2 L129、lzop L153、zstd L180 和 tar L289 都调用 `_call_external` 后丢弃结果，没有 rc 检查。压缩函数返回预期输出路径，并不证明文件成功生成。
- untar L303–305 试图检查 rc，但在失败时对 bytes 和 None 执行字符串 `join`，可能触发额外 TypeError；补丁应一并统一错误类型和解码。
- `tools/mic` L330–344：仅 errno=ENOSPC 的 Python IOError 会主动写 mic error；`FileNotFoundError`（ENOENT）会重新抛出。普通未捕获 Python traceback 走进程 stderr，不能假定会进入 mic file handler。msger 的 stderr 重定向主要在 RPM 安装段启用/关闭（`plugins/backend/zypppkgmgr.py` L822–826、914–918；`mic/msger.py` L379–387）。
- 无需 root 的原始源码探针验证：fake gzip exit1 的 tuple 是 `(1, b'...No space left...', None)`，SIGKILL 是 `(-9, b'', None)`；两次 packing 都转成 `shutil.move` 的 FileNotFoundError，mic log 同样只到启动行。证据 `evidence/original_archive_probe.json`，脚本原样快照 `evidence/probe_scripts/original_archive_probe.py`（原执行位置为work/）。ENOSPC 文字为测试注入，**未构造真实磁盘满；SIGKILL 不等于 OOM**。

## 临时文件真实路径和磁盘峰值

`mic/archive.py` L327–348：`archive_dir=os.path.dirname(archive_name)`，`tempfile.mktemp(suffix='.tar', dir=archive_dir)`，先 `_do_tar` 写完整 `.tar`，再 `_do_gzip` 就地压缩，最后 `shutil.move`。`mktemp` 还存在名称竞争问题，应改用安全临时文件并做失败清理。

`mic/imager/loop.py` L520–534：原始分区文件在 `_imgdir`；打包目标是 `_outdir/self.pack_to`，并通过共享 `packing()` 调用 archive 模块。`mic/imager/baseimager.py` L254–258 指定 `_outdir=__builddir/out`；L709–721 指定 `__builddir=<tmpdir>/build/imgcreate-*`；loop L340–342、base L659–662 指定 `_imgdir` 是同一 builddir 下的另一个临时子目录。因此完整 tar 写在 **工作临时目录的 out 子目录**，而不是 CLI 最终 outdir，也不由默认 tempfile 全局 TMPDIR 单独决定。

此版本 CLI `tools/mic` 没有 `--tmpdir` 参数（其 parser L65–146）；正确方式是使用 `-c <本地 mic.conf>` 的 `[create] tmpdir=...`。`mic/conf.py` L48、`etc/mic.conf` L9 默认 `/var/tmp/mic`。`--cachedir` 和 `--outdir` 在 `tools/mic` L72–76，均不替代工作 tmpdir。`baseimager.py` L807–817 的 `--tmpfs` 实验路径执行 `mount -t tmpfs -o size=4G ...`，三份公开日志未见此命令。

`baseimager.py` L1497–1499 先 `_stage_final_image()`；L1518 才在向最终 destdir 移动时调用 `misc.check_space_pre_cp`。`mic/utils/misc.py` L211–227 的检查只针对这次输出复制，**不对打包前工作文件系统的完整 tar + gzip 峰值做预算**。loop L348–423 的建盘挂载路径也没有相应预检查。

记镜像实际分配块为 `I_alloc`，tar 文件为 `T`，压缩输出为 `C`，其他安装目录/缓存/bootstrap 等为 `O`。旧流程压缩接近完成时 `O + I_alloc + T + C` 同时存在，gzip 成功才删 tar，creator 最后才清理输入镜像。打包输出跨文件系统交付还可能出现双份 C，需单独采样。

成功日志五个镜像逻辑大小合计 2,580,786,618 字节；按 GNU tar 普通非稀疏存储估算 T≈2,580,797,440 字节；目录 C=696,473,433 字节。若用逻辑 I 代替 I_alloc，旧打包模型约 5,858,057,491 字节（5.46 GiB），流式约 3,277,260,051 字节（3.05 GiB），可减少约 **2.40 GiB / 44%** 的这部分占用。只是模型，**不是本机基线实测**；O 未计入，稀疏镜像实际块数也未知。复现预算仍按至少 15 GB。证据 `evidence/disk_model.json` 和 `docs/log_forensics.md` 的原始分区行号。

## gzip/pigz 选择和内存量级

`archive.py` L92–100：PATH 中有可执行 pigz 就选它，否则 gzip。无内存检测、无线程上限；1003 bootstrap spec 装进 `/bin/pigz` 足以改变压缩器，真实日志 L7367 与之吻合。换成 pigz 仍写完整中间 tar，不消除该磁盘成本。

使用对应 SRPM 内的 pigz-2.8 源码（编译于 `work/pigz-src/pigz-2.8/`，引用源码保存于 `evidence/src_snapshot/pigz-2.8/`），不是直接用当前主分支代替。源码 `pigz.c` L521–522：输入池上限 `2p+3`，默认块 128 KiB（L241；默认值赋值见同文件）；L1619–1622 配置输入、输出、字典池，L1718 `deflateInit2(..., -15, 8, ...)`。普通 zlib 每压缩线程约 256 KiB deflate 状态，加输入/输出缓冲约数百 KiB，粗估每线程增量 **0.6–1 MiB**，另有进程库、主线程和栈实际触页。线程的数 MiB 虚拟栈预约不能直接当作 RSS。

`-p 2` 将 p 的输入池上限从 `2p+3` 降到 7 个 128 KiB 缓冲（0.875 MiB），两个 deflate 状态约 0.5 MiB，加输出/字典/进程基线通常为数 MiB。默认 32 线程与 p2 的粗估差约 18–30 MiB，256 线程时约 150–250 MiB；这不是数 GiB 的常规压缩器 RSS，也不包含文件页缓存/整个 mic 的内存。不能凭 `-p 2` 宣称修复 worker OOM。

对应压缩器资源探针使用 64 MiB 随机数据、`/usr/bin/time -v` 比较 gzip、pigz 默认、pigz p2，结果见 `evidence/compressor_probe.json`、`evidence/compressor-*.time.txt`，命令脚本原样快照 `evidence/probe_scripts/compressor_probe.py`（原执行位置work/），编译记录 `evidence/pigz-build.log`。该测量仅验证量级，不是 mic 或 QB worker 的基线 RSS。

## sandbox 补丁评审边界

未取得 `sandbox/dkson95/clang`，三份实际 snapshot 源 RPM 中也没有 `packaging/patch_archive.py`。不能假称逐项评审了未知脚本；请提供该分支 clone 或脚本路径。

可核实且有价值的是 bootstrap spec 中强制 GNU tar 的软链接（避免 bsdtar 自动稀疏 pax 影响 lthor），应保留；1003 显式提供 pigz 2.8 可改善速度，不能当作 ENOSPC 修复。任务举例的 pigz `-p 2` 只是待评审假设，不是已读取分支事实。后续源码补丁应共享 archive 层检查 rc、输出命令/错误末尾、流式压缩、pack 前后资源日志；gzip/bzip2/lzop/zstd 及其他 imager 调用须一致，不把修复藏在 bootstrap 的文本替换脚本里。

补充校验：本地解压的官方 Ubuntu .deb 内 archive.py 与官方源码的 archive.py sha256 相同（6bf6d3a6f60300e94ac66f1d9fd9f3b0585b809b7a8f222fe72d3972480c6ba4）。本机 20 CPU 的 64 MiB 随机数据探针：gzip峰值RSS 1,804 KiB；pigz默认17,392 KiB；pigz p2 3,800 KiB，降低13,592 KiB。详见 `evidence/compressor_probe.json`。
