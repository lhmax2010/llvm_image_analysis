#!/usr/bin/env bash
# 待用户执行的复现脚本；本轮 sudo 失败后未运行，不能视为已验证。
# 用户自行认证后运行：sudo -- bash docs/need_sudo.sh baseline
# 磁盘实验：sudo -- bash docs/need_sudo.sh space <基线工作目录峰值字节数的80%>
# 内存实验：sudo -- bash docs/need_sudo.sh oom 1G （之后可试 512M）
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
if ! sudo -n true; then
  echo '没有免密 sudo。请用户自行在终端认证；本脚本不读取、猜测或记录密码。' >&2
  exit 1
fi
if (( EUID != 0 )); then
  echo '请用户自行运行 sudo -- bash docs/need_sudo.sh <模式>。' >&2
  exit 1
fi
MODE=${1:-baseline}
case "$MODE" in baseline|space|oom) ;; *) echo '模式：baseline / space <字节> / oom <1G或512M>' >&2; exit 2;; esac
# 不更改系统 apt 源、不向系统安装包。官方 mic .deb 已解压至工作目录。
# 若后续发现依赖缺失，停止并记录，另行在本目录下载/解压依赖。
MIC_PY=${MIC_PY:-/usr/bin/python3}
MIC_BIN="$ROOT/work/tools/usr/bin/mic"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/work/tools/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$ROOT/work/tmp"
mkdir -p "$TMPDIR" "$ROOT/work/cache" "$ROOT/work/bootstrap" "$ROOT/evidence"
if [[ ! -f "$MIC_BIN" ]]; then
  echo '缺少本地 mic；请先 dpkg-deb -x downloads/mic_2.1.3_all.deb work/tools。' >&2
  exit 2
fi
STAMP=$(date +%Y%m%d-%H%M%S)
PREFIX="$ROOT/evidence/${MODE}-${STAMP}"
exec > >(tee "$PREFIX-driver.log") 2>&1
printf '模式=%s；开始=%s；工作目录=%s\n' "$MODE" "$(date -Is)" "$ROOT"
"$MIC_PY" "$MIC_BIN" --version
df -h "$ROOT"
free -m
AVAIL=$(df -B1 --output=avail "$ROOT" | tail -n 1 | tr -d ' ')
if (( AVAIL < 15000000000 )); then
  echo '不足15GB，停止；不清理任何现有文件。' >&2
  exit 2
fi
KS="$ROOT/downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks"
# 注意：当前 ks 与发布 MD5SUMS 不符，仍按用户要求作为0917公开 ks复现，不能声称逐字节等同原输入。
OUT="$ROOT/work/base"
MIC_TMP="$ROOT/work/base-tmp"
MOUNT_CREATED=0
SAMPLER_PID=''
cleanup() {
  if [[ -n "$SAMPLER_PID" ]]; then
    kill "$SAMPLER_PID" 2>/dev/null || true
    wait "$SAMPLER_PID" 2>/dev/null || true
  fi
  if (( MOUNT_CREATED )); then
    # 仅卸载本脚本创建的挂载；若有残留子挂载，报错保留现场，不强删/懒卸载。
    if ! umount "$ROOT/work/smalltmp"; then
      echo 'smalltmp卸载失败，请检查 findmnt -R 后手工清理。' >&2
    fi
  fi
  if [[ -n "${SUDO_UID:-}" && -n "${SUDO_GID:-}" ]]; then
    chown -R "$SUDO_UID:$SUDO_GID" "$ROOT/evidence" "$ROOT/work" || true
  fi
}
trap cleanup EXIT
if [[ "$MODE" == space ]]; then
  BYTES=${2:-}
  if [[ ! "$BYTES" =~ ^[0-9]+$ ]] || (( BYTES < 104857600 )); then
    echo 'space必须提供按真实基线峰值乘0.8计算的字节数；尚无基线，不自动套用理论模型。' >&2
    exit 2
  fi
  LOOP="$ROOT/work/smalltmp-${STAMP}.ext4"
  mkdir -p "$ROOT/work/smalltmp"
  if mountpoint -q "$ROOT/work/smalltmp"; then
    echo 'smalltmp已有挂载，停止以保护现场。' >&2
    exit 2
  fi
  truncate -s "$BYTES" "$LOOP"
  mkfs.ext4 -F -m 0 "$LOOP"
  mount -o loop "$LOOP" "$ROOT/work/smalltmp"
  MOUNT_CREATED=1
  MIC_TMP="$ROOT/work/smalltmp/mic-tmp"
  OUT="$ROOT/work/diskfull-${STAMP}"
elif [[ "$MODE" == oom ]]; then
  LIMIT=${2:-1G}
  if [[ ! "$LIMIT" =~ ^[0-9]+[MG]$ ]]; then echo '内存值示例：1G、512M' >&2; exit 2; fi
  MIC_TMP="$ROOT/work/oom-${STAMP}-tmp"
  OUT="$ROOT/work/oom-${STAMP}"
fi
mkdir -p "$MIC_TMP" "$OUT"
CONF="$ROOT/work/mic-${MODE}-${STAMP}.conf"
cat > "$CONF" <<EOF
[common]
distro_name = Tizen
plugin_dir = $ROOT/work/tools/usr/lib/mic/plugins
[create]
tmpdir = $MIC_TMP
cachedir = $ROOT/work/cache
outdir = $OUT
runtime = bootstrap
pkgmgr = auto
[bootstrap]
rootdir = $ROOT/work/bootstrap
packages = mic-bootstrap-x86-arm
EOF
# 根据.deb实际插件布局调整本地路径；不会修改目录外配置。
if [[ ! -d "$ROOT/work/tools/usr/lib/mic/plugins" ]]; then
  sed -i "s|^plugin_dir = .*|plugin_dir = $ROOT/downloads/src/mic/plugins|" "$CONF"
fi
CSV="$ROOT/evidence/${MODE}_sampler.csv"
# 多次执行保留旧采样，避免覆盖证据。
if [[ -e "$CSV" ]]; then CSV="$ROOT/evidence/${MODE}-${STAMP}_sampler.csv"; fi
"$MIC_PY" "$ROOT/docs/sampler.py" --workdir "$MIC_TMP" --outdir "$OUT" --csv "$CSV" &
SAMPLER_PID=$!
# 公开日志未提供完整QB命令。下面保留已证实选项，其余目录选项为本机复现选择。
CMD=("$MIC_PY" "$MIC_BIN" -c "$CONF" cr auto "$KS" -A aarch64 --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license --cachedir "$ROOT/work/cache" --outdir "$OUT" --runtime bootstrap --non-interactive --logfile "$PREFIX-mic.log")
printf '%q ' "${CMD[@]}" > "$PREFIX-command.txt"
printf '\n' >> "$PREFIX-command.txt"
KERNEL_SINCE=$(date --iso-8601=seconds)
set +e
if [[ "$MODE" == oom ]]; then
  UNIT="mic-repro-${STAMP}"
  systemd-run --scope --unit="$UNIT" -p "MemoryMax=$LIMIT" -p MemoryAccounting=yes \
    /usr/bin/time -v -o "$PREFIX-time.txt" "${CMD[@]}" > "$PREFIX-console.log" 2>&1
  RC=$?
  systemctl show "$UNIT.scope" -p ControlGroup -p MemoryPeak -p MemoryCurrent -p Result > "$PREFIX-scope.txt" 2>&1
  journalctl -k --since "$KERNEL_SINCE" --no-pager > "$PREFIX-kernel-journal.txt" 2>&1
  dmesg --time-format iso > "$PREFIX-dmesg.txt" 2>&1
else
  /usr/bin/time -v -o "$PREFIX-time.txt" "${CMD[@]}" > "$PREFIX-console.log" 2>&1
  RC=$?
fi
set -e
printf '返回码=%s；结束=%s\n' "$RC" "$(date -Is)" | tee "$PREFIX-result.txt"
df -B1 "$MIC_TMP" "$OUT" > "$PREFIX-final-df.txt"
free -m > "$PREFIX-final-free.txt"
# 若aarch64 %post失败，保留日志后停止；不要未经检查自动改架构或包清单。
# 后续可根据现场选armv7l或小ks进行“打包阶段”等价实验，并明确报告差异。
exit "$RC"
