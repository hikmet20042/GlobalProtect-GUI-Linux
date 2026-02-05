#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
ARCH="${2:-$(dpkg --print-architecture 2>/dev/null || echo amd64)}"
PKG_NAME="globalprotect-gui"
PKG_ROOT="build/deb/${PKG_NAME}_${VERSION}_${ARCH}"

command -v dpkg-deb >/dev/null 2>&1 || { echo "dpkg-deb is required" >&2; exit 1; }
command -v install >/dev/null 2>&1 || { echo "install tool is required" >&2; exit 1; }

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN" \
         "$PKG_ROOT/usr/lib/${PKG_NAME}/gp_gui" \
         "$PKG_ROOT/usr/bin" \
         "$PKG_ROOT/usr/share/applications"

cat > "$PKG_ROOT/DEBIAN/control" <<CONTROL
Package: ${PKG_NAME}
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Maintainer: GlobalProtect GUI Maintainers <maintainers@example.com>
Depends: python3 (>= 3.10), python3-tk, xdg-utils
Recommends: desktop-file-utils
Description: Desktop GUI for GlobalProtect CLI on Linux Mint/Ubuntu
 Stable desktop UI wrapper around the globalprotect CLI client.
 Optimized for Debian-family desktops such as Linux Mint.
CONTROL

cat > "$PKG_ROOT/DEBIAN/postinst" <<'POSTINST'
#!/usr/bin/env bash
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
POSTINST

cat > "$PKG_ROOT/DEBIAN/postrm" <<'POSTRM'
#!/usr/bin/env bash
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
POSTRM

chmod 0755 "$PKG_ROOT/DEBIAN/postinst" "$PKG_ROOT/DEBIAN/postrm"

install -m 0644 app.py "$PKG_ROOT/usr/lib/${PKG_NAME}/app.py"
install -m 0644 gp_gui/__init__.py "$PKG_ROOT/usr/lib/${PKG_NAME}/gp_gui/__init__.py"
install -m 0644 gp_gui/client.py "$PKG_ROOT/usr/lib/${PKG_NAME}/gp_gui/client.py"
install -m 0644 gp_gui/config.py "$PKG_ROOT/usr/lib/${PKG_NAME}/gp_gui/config.py"
install -m 0755 scripts/globalprotect-gui "$PKG_ROOT/usr/bin/globalprotect-gui"
install -m 0644 packaging/globalprotect-gui.desktop "$PKG_ROOT/usr/share/applications/globalprotect-gui.desktop"

(
  cd "$PKG_ROOT"
  find usr -type f -print0 | xargs -0 md5sum > DEBIAN/md5sums
)

dpkg-deb --build "$PKG_ROOT"
echo "Built: ${PKG_ROOT}.deb"
