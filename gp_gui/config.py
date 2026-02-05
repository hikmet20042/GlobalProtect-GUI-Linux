from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "globalprotect-gui"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass(slots=True)
class AppConfig:
    portal: str = ""
    username: str = ""
    auto_refresh_seconds: int = 5


def load_config() -> AppConfig:
    try:
        if not CONFIG_PATH.exists():
            return AppConfig()
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return AppConfig(
            portal=str(data.get("portal", "")),
            username=str(data.get("username", "")),
            auto_refresh_seconds=max(2, int(data.get("auto_refresh_seconds", 5))),
        )
    except Exception:
        return AppConfig()


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
