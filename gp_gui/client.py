from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
import subprocess
import time
from typing import Sequence


class GlobalProtectError(RuntimeError):
    """Raised when GlobalProtect CLI cannot be used."""


@dataclass(slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(slots=True)
class ConnectionStatus:
    state: str
    portal: str | None = None
    gateway: str | None = None
    user: str | None = None
    ip: str | None = None
    raw: str = ""


class GlobalProtectClient:
    def __init__(self, binary: str = "globalprotect", timeout_seconds: int = 60):
        self.binary = binary
        self.timeout_seconds = timeout_seconds
        self._connect_help_cache: str | None = None

    def ensure_available(self) -> None:
        if shutil.which(self.binary) is None:
            raise GlobalProtectError(
                f"GlobalProtect binary '{self.binary}' was not found in PATH."
            )

    def run(self, args: Sequence[str], timeout_seconds: int | None = None) -> CommandResult:
        self.ensure_available()
        try:
            completed = subprocess.run(
                [self.binary, *args],
                text=True,
                capture_output=True,
                timeout=timeout_seconds if timeout_seconds is not None else self.timeout_seconds,
                check=False,
            )
            return CommandResult(
                returncode=completed.returncode,
                stdout=completed.stdout.strip(),
                stderr=completed.stderr.strip(),
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                returncode=124,
                stdout=(exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "").strip() if isinstance(exc.stderr, str) else "Command timed out.",
            )

    def _connect_help(self) -> str:
        if self._connect_help_cache is not None:
            return self._connect_help_cache
        result = self.run(["connect", "--help"], timeout_seconds=10)
        self._connect_help_cache = (result.stdout + "\n" + result.stderr).lower()
        return self._connect_help_cache

    def _supports(self, *options: str) -> bool:
        help_text = self._connect_help()
        return any(opt.lower() in help_text for opt in options)

    def connect(self, portal: str, username: str | None = None) -> CommandResult:
        if not portal.strip():
            raise GlobalProtectError("Portal is required to connect.")

        args = ["connect"]

        # CLI argument compatibility across client versions.
        if self._supports("--portal"):
            args.extend(["--portal", portal.strip()])
        elif self._supports("-p"):
            args.extend(["-p", portal.strip()])
        else:
            args.append(portal.strip())

        if username and username.strip():
            if self._supports("--username"):
                args.extend(["--username", username.strip()])
            elif self._supports("-u"):
                args.extend(["-u", username.strip()])

        # For Okta/SAML, auth flow can take time due to browser + MFA.
        return self.run(args, timeout_seconds=600)

    def disconnect(self) -> CommandResult:
        return self.run(["disconnect"], timeout_seconds=60)

    def show_status(self) -> CommandResult:
        return self.run(["show", "--status"], timeout_seconds=30)

    def show_details(self) -> CommandResult:
        return self.run(["show", "--details"], timeout_seconds=30)

    def wait_for_connected(self, max_wait_seconds: int = 300, poll_seconds: int = 3) -> ConnectionStatus:
        deadline = time.time() + max_wait_seconds
        latest = ConnectionStatus(state="unknown", raw="")
        while time.time() < deadline:
            status_result = self.show_status()
            parsed = parse_status_output(status_result.stdout or status_result.stderr)
            latest = parsed
            if parsed.state == "connected":
                return parsed
            time.sleep(max(1, poll_seconds))
        return latest


def parse_status_output(raw_output: str) -> ConnectionStatus:
    text = raw_output.strip()
    lower = text.lower()

    if not text:
        return ConnectionStatus(state="unknown", raw=raw_output)

    if "connected" in lower and "not connected" not in lower:
        state = "connected"
    elif "not connected" in lower or "disconnected" in lower:
        state = "disconnected"
    elif "connecting" in lower:
        state = "connecting"
    else:
        state = "unknown"

    portal = _capture_value(text, [r"Portal:\s*(.+)", r"Portal\s+Address:\s*(.+)"])
    gateway = _capture_value(text, [r"Gateway:\s*(.+)", r"Gateway\s+Address:\s*(.+)"])
    user = _capture_value(text, [r"User:\s*(.+)", r"Username:\s*(.+)"])
    ip = _capture_value(text, [r"IP:\s*(.+)", r"IP\s+Address:\s*(.+)"])

    return ConnectionStatus(
        state=state,
        portal=portal,
        gateway=gateway,
        user=user,
        ip=ip,
        raw=raw_output,
    )


def _capture_value(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
