#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
TOPDIR="$(pwd)/build/rpm"
SRCROOT="${TOPDIR}/SOURCES/globalprotect-gui-${VERSION}"
TARBALL="${TOPDIR}/SOURCES/globalprotect-gui-${VERSION}.tar.gz"

command -v rpmbuild >/dev/null 2>&1 || { echo "rpmbuild is required" >&2; exit 1; }

rm -rf "$TOPDIR"
mkdir -p "$TOPDIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

mkdir -p "$SRCROOT/gp_gui" "$SRCROOT/scripts" "$SRCROOT/packaging"
cp app.py "$SRCROOT/"
cp gp_gui/__init__.py gp_gui/client.py gp_gui/config.py "$SRCROOT/gp_gui/"
cp scripts/globalprotect-gui "$SRCROOT/scripts/"
cp packaging/globalprotect-gui.desktop "$SRCROOT/packaging/"

(
  cd "${TOPDIR}/SOURCES"
  tar -czf "globalprotect-gui-${VERSION}.tar.gz" "globalprotect-gui-${VERSION}"
)

cp packaging/globalprotect-gui.spec "$TOPDIR/SPECS/globalprotect-gui.spec"

rpmbuild --define "_topdir ${TOPDIR}" --define "pkg_version ${VERSION}" -bb "$TOPDIR/SPECS/globalprotect-gui.spec"

echo "Built RPM(s):"
find "$TOPDIR/RPMS" -type f -name '*.rpm' -print
