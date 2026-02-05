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

## Quick start

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

If your enterprise GlobalProtect build uses different command options or custom MFA flows, check the in-app log for CLI stderr and adapt portal/auth policies as needed.

## Testing

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py gp_gui/*.py
```
