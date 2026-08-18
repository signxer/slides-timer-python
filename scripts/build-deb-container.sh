#!/usr/bin/env bash
# slides-timer - 麒麟 V10 deb 容器内构建入口
#
# 在 ubuntu:20.04（glibc 2.31，与麒麟 V10 桌面版一致）容器内完成：
#   1. 编译 CPython 3.11 —— 使打包进单文件的 libpython 只要求 glibc ≤ 2.31
#   2. 先装 deb 运行依赖（libglib/libxcb 等 + xdotool）再调用 scripts/build-deb.sh 打 deb
#      —— PyInstaller 分析期必须能 import PySide6.QtCore 探测 Qt 插件目录，
#         缺 libglib 会静默丢插件（运行时报 platform plugin "in"），见下文注释
#   3. 用「deb 声明的运行依赖」做启动冒烟，验证产物能在 glibc 2.31 上真正启动
#   4. 端到端安装验证：dpkg -i 安装真正的 deb 后运行 /usr/bin/slides-timer，
#      模拟用户双击时图形安装器（kylin-installer）后端执行的同一路径
#   5. 精简环境实验：卸载「已从 Depends 移除的库」后再启动——
#      (a) offscreen 验证 Qt 核心库已打进单文件，
#      (b) xcb 桌面路径验证 libqxcb 及其 xcb 依赖已打进单文件；
#      双端都通过才证明 Depends 精简到「麒麟 V10 桌面版必然自带」的最小集是安全的，
#      保证图形安装器的依赖检查永远成功（不触发其 UnboundLocalError 报错分支）
#
# 为什么必须这么做（勿回退到 setup-python）：
#   GitHub 托管 runner 的 setup-python（python-build-standalone）现在提供的 libpython
#   要求 GLIBC_2.38，而麒麟 V10 桌面版只有 glibc 2.31；PySide6 8.x/6.8+ 的 arm64 wheel
#   更是要求 GLIBC_2.39。此前打包出的程序在麒麟上一点就报
#   "Failed to load Python shared library ... GLIBC_2.38 not found"，双击无反应。
#   因此在 glibc 2.31 环境里编译 CPython，并钉 PySide6==6.7.3（最后一个 arm64 wheel
#   基线为 manylinux_2_31 的版本，见 scripts/build-deb.sh），产物与麒麟 V10 的 glibc
#   完全一致，可直接运行。
#
# 用法（在对应架构的 Linux 主机上，挂载仓库根目录到 /src）：
#   docker run --platform linux/$ARCH --rm -v "$PWD:/src" -w /src ubuntu:20.04 \
#     bash -c "bash scripts/build-deb-container.sh $ARCH"
set -euo pipefail

ARCH="${1:-$(dpkg --print-architecture)}"
PYVER="3.11.9"
PREFIX="/opt/py311"
PYBIN="$PREFIX/bin/python3.11"
APPNAME="slides-timer"
PKG="slides-timer"
VER="${VERSION:-1.0.0}"
# 已实证打进单文件、故不再列入 Depends 的包（精简实验卸载它们后程序必须仍能启动）。
# 若任一个其实未入包 → 双路径验证会报缺库并失败，需把它加回 build-deb.sh 的 Depends。
DROPPED_DEPS="libxcb-xinerama0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-render-util0 libxcb-cursor0 libxcb-randr0 libglib2.0-0 libfontconfig1 libxkbcommon-x11-0 libxkbcommon0 libdbus-1-3"

export DEBIAN_FRONTEND=noninteractive

echo "== 安装编译依赖 =="
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  build-essential zlib1g-dev libssl-dev libffi-dev libbz2-dev \
  liblzma-dev libreadline-dev libsqlite3-dev libncurses-dev \
  ca-certificates curl

echo "== 编译 CPython ${PYVER}（glibc 2.31）=="
curl -fsSL -o /tmp/Python.tgz "https://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz"
tar -xzf /tmp/Python.tgz -C /tmp
cd "/tmp/Python-${PYVER}"
./configure --enable-shared --prefix="$PREFIX" --with-ensurepip=install \
  LDFLAGS="-Wl,-rpath,$PREFIX/lib"
make -j"$(nproc)"
make install

echo "== 升级 pip =="
"$PYBIN" -m pip install --upgrade pip

echo "== 安装 deb 声明的运行依赖（PyInstaller 分析期之前） =="
# 必须在 PyInstaller 打包（分析期）之前装好：
#   PySide6 的 hook 会启动子进程 import PySide6.QtCore 读取 Qt 库信息（QLibraryInfo），
#   缺 libglib 等运行时库时该 import 失败 → hook 探测不到插件目录，platforms/libqoffscreen.so
#   等插件不会被打进包，运行时报 "Could not find the Qt platform plugin" in ""。
#   同时 qfluentwidgets 的 --collect-all 子模块收集也会因缺 libglib 而失败。
# 这份列表覆盖「DROPPED_DEPS（已打入单文件）+ Depends 里保留的 4 个库 + xdotool」，
#   装好后既是打包前提也是冒烟前提。
apt-get install -y -qq --no-install-recommends \
  $DROPPED_DEPS libegl1 libgl1 libice6 libsm6 xdotool

echo "== 调用 build-deb.sh（$ARCH）=="
cd /src
export LD_LIBRARY_PATH="$PREFIX/lib"
export PYTHON_BIN="$PYBIN"
export VERSION="$VER"
bash scripts/build-deb.sh "$ARCH"

echo "== 启动冒烟 =="
# 验证 Depends 列表足以支撑程序运行，且产物确实能在 glibc 2.31 上启动。

echo "== 打包产物诊断（Analysis toc） =="
ANALYZE="/src/build/$APPNAME/Analysis-00.toc"
if [ -f "$ANALYZE" ]; then
  echo "-- PySide6 rthook 是否入包 --"
  grep -o "pyi_rth_pyside6" "$ANALYZE" | sort | uniq -c || echo "!! pyi_rth_pyside6 未入包"
  echo "-- 平台插件入包情况 --"
  grep -oE "platforms/libq[A-Za-z0-9_.-]+" "$ANALYZE" | sort -u || echo "!! 未找到 platforms/libq*"
  echo "-- Qt 插件目录整体 --"
  grep -oE "plugins/[A-Za-z0-9_./-]+\.so" "$ANALYZE" | sort -u | head -20
  echo "-- 系统运行库入包情况（已打包 = 运行时无需系统提供） --"
  for lib in libglib-2.0.so.0 libfontconfig.so.1 libxcb-cursor.so.0 libxcb-randr.so.0 \
             libxkbcommon.so.0 libxkbcommon-x11.so.0 libdbus-1.so.3 libEGL.so.1 libGL.so.1 \
             libICE.so.6 libSM.so.6; do
    if grep -q "$lib" "$ANALYZE"; then
      echo "  已打包: $lib"
    else
      echo "  未打包: $lib"
    fi
  done
else
  echo "!! Analysis toc 不存在：$ANALYZE"
fi

set +e
timeout 25 env HOME=/tmp QT_QPA_PLATFORM=offscreen QT_DEBUG_PLUGINS=1 \
  "/src/dist/$APPNAME" >/tmp/smoke.log 2>&1
code=$?
set -e
if [ "$code" -eq 124 ]; then
  echo "启动冒烟通过：glibc 2.31 + Depends 运行依赖下程序正常启动并持续运行（超时终止，exit 124 即启动成功标志）"
else
  echo "!! 启动冒烟失败（exit=$code），/tmp/smoke.log 尾部："
  tail -60 /tmp/smoke.log
  echo "!! Qt 插件搜索路径（QT_DEBUG_PLUGINS）："
  grep -E "paths \(sorted\)|libraryPaths|searching plugin|Found plugin|Cannot load library" /tmp/smoke.log | head -25
  exit 1
fi

echo "== 端到端安装验证（模拟图形安装器 dpkg 后端） =="
# 用户双击 deb 时，kylin-installer 后端执行的就是 dpkg 安装。这里安装真正的 deb
# 再运行装好的 /usr/bin/slides-timer，验证整个安装-启动链路（依赖检查 → 装包 → 可运行）。
# 若这一步失败，说明图形安装器也会在同一处失败 —— 必须在此拦截，CI 即失败。
DEB="/src/dist/${PKG}_${VER}_${ARCH}.deb"
if [ ! -f "$DEB" ]; then
  echo "!! 未找到 deb 产物：$DEB"
  exit 1
fi
set +e
dpkg -i "$DEB" >/tmp/dpkg-install.log 2>&1
ic=$?
set -e
if [ "$ic" -ne 0 ]; then
  echo "!! dpkg -i 安装失败（exit=$ic）—— 图形安装器将同步失败："
  tail -30 /tmp/dpkg-install.log
  exit 1
fi
echo "dpkg -i 安装成功：/usr/bin/slides-timer 与桌面图标已就位"
set +e
timeout 15 env HOME=/tmp QT_QPA_PLATFORM=offscreen \
  /usr/bin/slides-timer >/tmp/smoke-installed.log 2>&1
ipc=$?
set -e
if [ "$ipc" -eq 124 ]; then
  echo "装后启动通过：deb 安装路径可直接运行（等效图形安装器安装结果）"
else
  echo "!! 装后启动失败（exit=$ipc），/tmp/smoke-installed.log 尾部："
  tail -30 /tmp/smoke-installed.log
  exit 1
fi

echo "== 精简环境实验（卸载已移除的 Depends 库后启动，回归门） =="
# 目的：防止「某库实际未入包却被移出 Depends」的回归。
# 卸载 DROPPED_DEPS（已实证打进单文件、故从 Depends 移除的 13 个库）后：
#   (a) offscreen 启动 —— 验证 Qt 核心库（glib/fontconfig/xkbcommon/dbus）自带；
#   (b) xcb 桌面路径 —— 无显示器下强制 xcb，若报「缺共享库」而非「连不上显示器」，
#       说明 libqxcb 及其 libxcb-* 依赖未入包 → Depends 必须加回。
# 任一失败即 CI 失败。注意 amd64 的 libqxcb 依赖系统 libICE/libSM（未入包），
# 它们仍在 Depends 里、此处不卸载，故 xcb 路径能正常加载。
dpkg --purge --force-depends --force-remove-reinstreq $DROPPED_DEPS >/tmp/purge.log 2>&1 || true

# (a) offscreen：验证 Qt 核心运行库已打进单文件
set +e
timeout 15 env HOME=/tmp QT_QPA_PLATFORM=offscreen \
  /usr/bin/slides-timer >/tmp/smoke-lean.log 2>&1
lc=$?
set -e
if [ "$lc" -eq 124 ]; then
  echo "精简环境 offscreen 启动通过：Qt 核心运行库均已打进单文件"
else
  echo "!! 精简环境 offscreen 启动失败（exit=$lc）→ 以下库未入包、Depends 必须保留："
  grep -oE "lib[a-zA-Z0-9_.-]+\.so(\.[0-9]+)*" /tmp/smoke-lean.log | sort -u
  tail -30 /tmp/smoke-lean.log
  exit 1
fi

# (b) xcb 桌面路径：无显示器下强制 xcb，只有「连不上显示器」才算通过
set +e
timeout 15 env HOME=/tmp QT_QPA_PLATFORM=xcb \
  /usr/bin/slides-timer >/tmp/smoke-xcb.log 2>&1
xc=$?
set -e
if grep -qiE "error while loading shared libraries|cannot open shared object file|ImportError: lib|could not find the Qt platform plugin" /tmp/smoke-xcb.log; then
  echo "!! xcb 桌面路径验证失败（exit=$xc）→ libqxcb 依赖未入包，Depends 必须加回以下库："
  grep -oE "lib[a-zA-Z0-9_.-]+\.so(\.[0-9]+)*" /tmp/smoke-xcb.log | sort -u
  tail -30 /tmp/smoke-xcb.log
  exit 1
else
  echo "xcb 桌面路径验证通过：libqxcb 及其依赖库均已入包（报错仅为无显示器连接，属预期）"
fi

echo "== 容器内构建与全部验证通过 =="
