Name:           globalprotect-gui
Version:        %{?pkg_version}%{!?pkg_version:0.1.0}
Release:        1%{?dist}
Summary:        Desktop GUI for GlobalProtect CLI on Linux

License:        MIT
URL:            https://example.com/globalprotect-gui
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3
Requires:       python3-tkinter

%description
A stable desktop UI wrapper around the globalprotect CLI client.

%prep
%setup -q

%build
# No build required.

%install
mkdir -p %{buildroot}/opt/globalprotect-gui/gp_gui
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications

install -m 0644 app.py %{buildroot}/opt/globalprotect-gui/app.py
install -m 0644 gp_gui/__init__.py %{buildroot}/opt/globalprotect-gui/gp_gui/__init__.py
install -m 0644 gp_gui/client.py %{buildroot}/opt/globalprotect-gui/gp_gui/client.py
install -m 0644 gp_gui/config.py %{buildroot}/opt/globalprotect-gui/gp_gui/config.py
install -m 0755 scripts/globalprotect-gui %{buildroot}/usr/bin/globalprotect-gui
install -m 0644 packaging/globalprotect-gui.desktop %{buildroot}/usr/share/applications/globalprotect-gui.desktop

%files
/opt/globalprotect-gui/app.py
/opt/globalprotect-gui/gp_gui/__init__.py
/opt/globalprotect-gui/gp_gui/client.py
/opt/globalprotect-gui/gp_gui/config.py
/usr/bin/globalprotect-gui
/usr/share/applications/globalprotect-gui.desktop

%changelog
* Wed Feb 05 2026 GlobalProtect GUI Maintainers <maintainers@example.com> - %{version}-1
- Initial RPM packaging
