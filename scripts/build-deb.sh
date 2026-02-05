#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
ARCH="${2:-amd64}"
PKG_ROOT="build/deb/globalprotect-gui_${VERSION}_${ARCH}"

command -v dpkg-deb >/dev/null 2>&1 || { echo "dpkg-deb is required" >&2; exit 1; }

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN" \
         "$PKG_ROOT/opt/globalprotect-gui/gp_gui" \
         "$PKG_ROOT/usr/bin" \
         "$PKG_ROOT/usr/share/applications"

cat > "$PKG_ROOT/DEBIAN/control" <<CONTROL
Package: globalprotect-gui
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Maintainer: GlobalProtect GUI Maintainers <maintainers@example.com>
Depends: python3, python3-tk
Description: Desktop GUI for GlobalProtect CLI on Linux
 A stable desktop UI wrapper around the globalprotect CLI client.
CONTROL

install -m 0644 app.py "$PKG_ROOT/opt/globalprotect-gui/app.py"
install -m 0644 gp_gui/__init__.py "$PKG_ROOT/opt/globalprotect-gui/gp_gui/__init__.py"
install -m 0644 gp_gui/client.py "$PKG_ROOT/opt/globalprotect-gui/gp_gui/client.py"
install -m 0644 gp_gui/config.py "$PKG_ROOT/opt/globalprotect-gui/gp_gui/config.py"
install -m 0755 scripts/globalprotect-gui "$PKG_ROOT/usr/bin/globalprotect-gui"
install -m 0644 packaging/globalprotect-gui.desktop "$PKG_ROOT/usr/share/applications/globalprotect-gui.desktop"

dpkg-deb --build "$PKG_ROOT"
echo "Built: ${PKG_ROOT}.deb"
