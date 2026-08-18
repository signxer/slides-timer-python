#!/usr/bin/env bash
# slides-timer - 麒麟 V10（Debian/Ubuntu 系）deb 安装包构建脚本
#
# 用法：
#   bash scripts/build-deb.sh [amd64|arm64]     # 指定架构（默认取当前系统架构）
# 环境变量：
#   PYTHON_BIN    用于安装依赖与 PyInstaller 打包的 Python（默认 python3）
#   VERSION       产物版本号（默认 1.0.0）
# 产物：dist/slides-timer_<版本>_<架构>.deb
#
# 前提：Linux（含麒麟 V10），python3（麒麟桌面自带 3.7 过老，强烈建议用
#       scripts/build-deb-container.sh 内的 CPython 3.11）+ pip，可访问外网安装依赖，
#       dpkg-deb 可用（Debian/Ubuntu/麒麟 自带 dpkg 包）。
# 注意：
#   - PyInstaller 不能交叉编译：x86 的包必须在 x86 机器上打、arm64 的包必须在
#     arm64 机器上打（CI 用原生 runner + glibc 2.31 容器，见 build-deb-container.sh）。
#   - 麒麟 V10 桌面版 glibc 为 2.31，务必用 glibc ≤ 2.31 的环境构建；依赖版本固定：
#     PySide6==6.7.3（最后一个 arm64 wheel 基线 manylinux_2_31 的版本，8.x/6.8+ 都
#     超过 2.31）、PySide6-Fluent-Widgets==1.11.3。
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARCH="${1:-$(dpkg --print-architecture)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VER="${VERSION:-1.0.0}"
APPNAME="slides-timer"
PKG="slides-timer"
PYSIDE_VERSION="6.7.3"
QFW_VERSION="1.11.3"

# 1. 安装依赖（版本固定，兼容麒麟 V10 glibc 2.31）
if ! "$PYTHON_BIN" -c "import PySide6, qfluentwidgets" >/dev/null 2>&1; then
  echo "== 安装 PySide6 ${PYSIDE_VERSION} 与 PySide6-Fluent-Widgets ${QFW_VERSION} =="
  "$PYTHON_BIN" -m pip install --user "PySide6==${PYSIDE_VERSION}" "PySide6-Fluent-Widgets==${QFW_VERSION}"
fi
if ! "$PYTHON_BIN" -m PyInstaller --version >/dev/null 2>&1; then
  echo "== 安装 PyInstaller =="
  "$PYTHON_BIN" -m pip install --user pyinstaller
fi

# 2. 图标：icon_256.png 已预生成并提交（由 icon.png 1415x1415 缩到 256x256，
#    满足 hicolor 目录规范），构建不再依赖 Pillow。
if [ ! -f icon_256.png ]; then
  echo "!! 缺少 icon_256.png（预生成 256x256 图标），请在项目根目录生成并提交该文件" >&2
  exit 1
fi

# 3. 打包单文件（Linux 无 --windowed 语义；收集 Qt 插件与 qfluentwidgets 资源）
#    刻意不加 --collect-submodules PySide6：那会把 QtWebEngine / QtMultimedia / QtSql /
#    QtCharts / Qt3D / QtBluetooth 等 30 多个用不到的模块整包拽进来（体积 180MB+），并
#    连带产生 libnss3 / libgstreamer / libmysqlclient 等大量「可选 .so 找不到」警告。
#    交给依赖图自动收集即可——main.py + qfluentwidgets 实际用到的 Qt 模块（Core/Gui/
#    Widgets/Svg 等）会被正确收集，启动冒烟会构造完整窗口兜底验证。
#    qfluentwidgets 必须 --collect-all：其 qss/图标资源、多语言文件、acrylic 底层等
#    无法靠依赖图自动找到；QtSvg 是 qfluentwidgets 图标渲染的隐性依赖，显式兜底。
echo "== PyInstaller 打包（$ARCH）=="
rm -rf build dist
"$PYTHON_BIN" -m PyInstaller --onefile --clean --name "$APPNAME" \
  --collect-all qfluentwidgets \
  --add-data "ui/assets:ui/assets" \
  --add-data "config.json:." \
  --add-data "didi.wav:." \
  --add-data "icon.png:." \
  --hidden-import PySide6.QtSvg \
  --exclude-module tkinter \
  --exclude-module customtkinter \
  main.py

# 4. 组装 deb 目录结构
echo "== 组装 deb 结构 =="
PKG_DIR="debroot"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/lib/$APPNAME/ui"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

install -m 0755 "dist/$APPNAME" "$PKG_DIR/usr/lib/$APPNAME/$APPNAME"

# 资源文件：config.py 用 sys.executable 目录定位 config.json（冻结后即
# /usr/lib/slides-timer），didi.wav 由声音播放模块按相对/绝对路径读取，二者是运行时
# 读写文件，必须在 lib 目录保留一份；ui/assets 里的图标在窗口内按相对路径引用。
cp -r ui/assets "$PKG_DIR/usr/lib/$APPNAME/ui/"
install -m 0644 config.json "$PKG_DIR/usr/lib/$APPNAME/config.json"
install -m 0644 didi.wav "$PKG_DIR/usr/lib/$APPNAME/didi.wav"
install -m 0644 icon.png "$PKG_DIR/usr/lib/$APPNAME/icon.png"

# 启动脚本（将工作目录设为资源目录，然后执行二进制）
cat > "$PKG_DIR/usr/bin/$APPNAME" <<'LAUNCHER'
#!/bin/bash
cd /usr/lib/slides-timer
exec ./slides-timer "$@"
LAUNCHER
chmod 755 "$PKG_DIR/usr/bin/$APPNAME"

# 复制 desktop 文件和图标（Icon 名与 hicolor 图标文件保持一致）
cp slides-timer.desktop "$PKG_DIR/usr/share/applications/"
install -m 0644 icon_256.png "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/$APPNAME.png"

# 5. control 文件（Architecture 由参数决定：amd64 / arm64）
#    Depends 只保留「PyInstaller 打不进单文件、且麒麟 V10 桌面版必然自带」的最小集：
#    - libgl1 / libegl1：GL/EGL 图形驱动栈。PyInstaller 不打这类 dlopen 的驱动库，
#      容器内「卸载全部依赖后再启动」的实验证实运行时系统必需（amd64 缺 libGL、
#      arm64 缺 libEGL）；任何麒麟桌面都自带 mesa 提供。
#    - libice6 / libsm6：libqxcb（X11 平台插件）的硬链接依赖，PyInstaller 在
#      amd64 上未将其打进单文件。
#    - xdotool：程序运行时用子进程调用它检测 PPT/WPS 放映窗口（monitor.py），
#      PyInstaller 只能打包库、不能打包外部可执行文件，必须由系统提供。
#    其余 libglib2.0-0 / libfontconfig1 / libxcb-* / libxkbcommon* / libdbus-1-3
#    均已实证打进单文件、运行时不依赖系统提供（见 build-deb-container.sh 的
#    「精简环境实验」），故不列入 Depends。
#    Depends 越贴近「必然自带的最小集」，麒麟图形安装器的依赖检查越不可能失败
#    （其 UnboundLocalError 报错正是依赖检查失败时触发的），新手双击 deb 即可安装。
SIZE=$(du -sk "$PKG_DIR" | cut -f1)
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: $PKG
Version: $VER
Architecture: $ARCH
Maintainer: Livrestrela <signxer@gmail.com>
Installed-Size: $SIZE
Depends: libice6, libsm6, libgl1, libegl1, xdotool
Section: utils
Priority: optional
Description: Slides Timer - 演示计时器工具
 自动检测 PPT/WPS 放映并计时，提供时间警告与到时提醒，
 帮助控制会议时长。零配置，双击图标即可。
EOF

# 创建 postinst 脚本
cat > "$PKG_DIR/DEBIAN/postinst" <<'POSTINST'
#!/bin/bash
set -e
if [ "$1" = "configure" ]; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi
POSTINST
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# 创建 postrm 脚本（卸载时清理 /usr/lib 下的运行文件）
cat > "$PKG_DIR/DEBIAN/postrm" <<'POSTRM'
#!/bin/bash
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    rm -rf /usr/lib/slides-timer
fi
POSTRM
chmod 755 "$PKG_DIR/DEBIAN/postrm"

# 6. dpkg-deb 打包（--root-owner-group 保证文件属主为 root，无需真实 root 权限）
echo "== dpkg-deb 打包 =="
OUT="dist/${PKG}_${VER}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$PKG_DIR" "$OUT"
rm -rf "$PKG_DIR"

echo ""
echo "构建完成：$OUT"
echo "安装：sudo dpkg -i $OUT（麒麟 V10 x86 装 amd64 包，麒麟 V10 飞腾/鲲鹏装 arm64 包）"
