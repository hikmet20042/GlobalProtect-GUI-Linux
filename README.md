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

## Linux Mint (latest) step-by-step

This project is optimized for Mint/Ubuntu-style packaging (`.deb`) and installs to:

- app files: `/usr/lib/globalprotect-gui`
- launcher: `/usr/bin/globalprotect-gui`
- desktop entry: `/usr/share/applications/globalprotect-gui.desktop`

### Step 1) Install dependencies

```bash
sudo apt update
sudo apt install -y build-essential dpkg-dev desktop-file-utils python3 python3-tk xdg-utils
```

### Step 2) Build the Mint package

```bash
./scripts/build-deb.sh 0.1.0
# or
make package-mint
```

Expected output artifact:

- `build/deb/globalprotect-gui_0.1.0_amd64.deb`

### Step 3) Install the package

```bash
sudo apt install ./build/deb/globalprotect-gui_0.1.0_amd64.deb
```

### Step 4) Install your company GlobalProtect CLI package

> Important: This GUI is only a frontend. Your company-provided GlobalProtect Linux package must be installed first.

Typical flow on Mint (adjust filename/version):

```bash
sudo apt install ./GlobalProtect_deb-*.deb
```

### Step 5) Verify CLI is available

```bash
which globalprotect
globalprotect --help
```

### Step 6) Launch GUI

```bash
globalprotect-gui
```

You can also launch from the Mint application menu (**GlobalProtect GUI**).

## Troubleshooting: "globalprotect not found in PATH"

If log shows lines like:

```text
[2026-02-05 17:24:09] GlobalProtect GUI started.
[2026-02-05 17:24:09] GlobalProtect binary 'globalprotect' was not found in PATH.
[2026-02-05 17:24:09] Error: GlobalProtect binary 'globalprotect' was not found in PATH.
```

Use this checklist on Linux Mint:

1. Install your company GlobalProtect client `.deb` package.
2. Run `which globalprotect` and ensure it prints a path (for example `/usr/bin/globalprotect`).
3. If binary is installed in a non-standard location, add it to PATH:
   ```bash
   echo 'export PATH="$PATH:/opt/paloaltonetworks/globalprotect"' >> ~/.profile
   source ~/.profile
   ```
4. Re-open terminal/session and run `globalprotect --help`.
5. Restart GlobalProtect GUI.

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
