# -*- coding: utf-8 -*-
from dataclasses import dataclass, asdict
from typing import Literal
import json, os
from appdirs import user_data_dir

APP_NAME = "clipboard_sequencer"
APP_AUTHOR = "local"

def settings_path() -> str:
    d = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "settings.json")

@dataclass
class Settings:
    duplicate_policy: Literal['separate','count'] = 'count'
    dequeue_on_paste: bool = True
    paste_all_text_mode: Literal['merge','step'] = 'merge'
    joiner_mode: Literal['cjk','english','custom'] = 'cjk'
    joiner_custom_sep: str = ""
    min_interval_ms: int = 120
    max_retries: int = 1
    history_default_count: int = 50
    blacklist: list[str] | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(s: str) -> "Settings":
        obj = json.loads(s)
        if obj.get("blacklist") is None:
            obj["blacklist"] = ["1Password", "Bitwarden", "KeePass", "KeePassXC", "Terminal", "PowerShell"]
        return Settings(**obj)

def load_settings() -> Settings:
    p = settings_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return Settings.from_json(f.read())
        except Exception:
            pass
    s = Settings()
    save_settings(s)
    return s

def save_settings(s: Settings):
    p = settings_path()
    with open(p, "w", encoding="utf-8") as f:
        f.write(s.to_json())
