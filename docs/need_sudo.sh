#!/usr/bin/env bash
# 2026-10-08：用户取消整镜像 baseline/space/oom；旧版本可从 Git 历史查询。
# 保留为停用提示：不认证、不提权、不建镜像、不挂载。
set -euo pipefail
echo '整镜像 baseline/space/oom 已取消；本入口停用。当前实验使用普通用户文件操作。' >&2
exit 2
