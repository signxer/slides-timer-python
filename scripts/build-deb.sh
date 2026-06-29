#!/bin/bash
set -e

# 用法: ./build-deb.sh [amd64|arm64]
ARCH=${1:-amd64}
VERSION="1.0.0"
APP_NAME="slides-timer"
PKG_DIR="dist/${APP_NAME}_${VERSION}_${ARCH}"

echo "Building ${APP_NAME} deb for ${ARCH}..."

# 清理旧构建
rm -rf "${PKG_DIR}"

# 创建目录结构
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/lib/${APP_NAME}/ui"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/DEBIAN"

# 复制 PyInstaller 可执行文件到 lib 目录
cp "dist/slides-timer" "${PKG_DIR}/usr/lib/${APP_NAME}/slides-timer"
chmod 755 "${PKG_DIR}/usr/lib/${APP_NAME}/slides-timer"

# 复制资源文件
cp -r ui/assets "${PKG_DIR}/usr/lib/${APP_NAME}/ui/"
cp config.json "${PKG_DIR}/usr/lib/${APP_NAME}/"
cp didi.wav "${PKG_DIR}/usr/lib/${APP_NAME}/"
cp icon.png "${PKG_DIR}/usr/lib/${APP_NAME}/"

# 创建启动脚本（将工作目录设为资源目录，然后执行二进制）
cat > "${PKG_DIR}/usr/bin/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
cd /usr/lib/slides-timer
exec ./slides-timer "$@"
LAUNCHER
chmod 755 "${PKG_DIR}/usr/bin/${APP_NAME}"

# 复制 desktop 文件和图标
cp slides-timer.desktop "${PKG_DIR}/usr/share/applications/"
cp icon.png "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

# 创建 DEBIAN/control
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Architecture: ${ARCH}
Depends: libxcb-xinerama0, libxkbcommon-x11-0, xdotool
Maintainer: Livrestrela <signxer@gmail.com>
Description: Slides Timer - 演示计时器工具
 Slides Timer 是一款演示计时工具，支持自动检测 PPT 放映状态，
 提供时间警告和时间到提醒，帮助控制会议时长。
EOF

# 创建 postinst 脚本
cat > "${PKG_DIR}/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e
if [ "$1" = "configure" ]; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi
POSTINST
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# 创建 postrm 脚本（卸载时清理）
cat > "${PKG_DIR}/DEBIAN/postrm" << 'POSTRM'
#!/bin/bash
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    rm -rf /usr/lib/slides-timer
fi
POSTRM
chmod 755 "${PKG_DIR}/DEBIAN/postrm"

# 构建 deb
dpkg-deb --build "${PKG_DIR}"

echo "Done: ${PKG_DIR}.deb"
