# GlobalProtect GUI for Linux

A stable desktop GUI for managing the `globalprotect` Linux CLI client.

## Features

- Connect / disconnect via a straightforward UI.
- Live connection status polling.
- Optional portal and username persistence.
- Detailed output viewer for diagnostics.
- Non-blocking command execution in background threads.
- Better compatibility with different GlobalProtect CLI flag variants.
- Okta/SAML-friendly connect behavior with longer connect timeout and post-connect status wait.

## Requirements

- Python 3.10+
- GlobalProtect CLI installed and available on `PATH` as `globalprotect`.

## Run from source

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python app.py
```

## Okta / SAML usage notes

1. Enter your corporate GlobalProtect portal.
2. Click **Connect**.
3. If your company uses Okta/SAML, complete browser-based login + MFA when prompted.
4. The app will continue polling status and switch to **Connected** when the tunnel is established.

If your enterprise GlobalProtect build uses different command options or custom MFA flows, check the in-app log for CLI stderr.

## Linux Mint (latest) optimized package flow

This project is now optimized for Mint/Ubuntu-style packaging (`.deb`) and installs to Debian-policy-friendly paths:

- application files: `/usr/lib/globalprotect-gui`
- launcher: `/usr/bin/globalprotect-gui`
- desktop entry: `/usr/share/applications/globalprotect-gui.desktop`

### 1) Install Mint build dependencies

```bash
sudo apt update
sudo apt install -y build-essential dpkg-dev desktop-file-utils python3 python3-tk
```

### 2) Build package

```bash
./scripts/build-deb.sh 0.1.0
# or
make package-mint
```

Output example:

- `build/deb/globalprotect-gui_0.1.0_amd64.deb`

### 3) Install package

```bash
sudo apt install ./build/deb/globalprotect-gui_0.1.0_amd64.deb
```

### 4) Launch

```bash
globalprotect-gui
```

You can also launch from the Mint application menu (**GlobalProtect GUI**).

## RPM package flow (Fedora/RHEL/openSUSE)

```bash
./scripts/build-rpm.sh 0.1.0
```

Output example:

- `build/rpm/RPMS/noarch/globalprotect-gui-0.1.0-1.noarch.rpm`

Install:

```bash
sudo dnf install ./build/rpm/RPMS/noarch/globalprotect-gui-0.1.0-1.noarch.rpm
```

## Testing / checks

```bash
make test
make lint
```
