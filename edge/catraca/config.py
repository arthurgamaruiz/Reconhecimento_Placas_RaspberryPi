"""Configuração via variáveis de ambiente com prefixo CATRACA_."""
import os
from collections.abc import Mapping
from dataclasses import dataclass, fields

_TRUTHY = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    ocr_conf_threshold: float = 0.85
    min_decision_conf: float = 0.5
    cooldown_s: float = 10.0
    motion_threshold: float = 0.02
    db_path: str = "catraca.db"
    cloud_url: str = ""
    cloud_api_key: str = ""
    sync_interval_s: float = 30.0
    fallback_enabled: bool = False
    button_enabled: bool = False
    button_pin: int = 23
    button_window_s: float = 30.0
    preview_port: int = 8088

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Config":
        env = os.environ if env is None else env
        kwargs = {}
        for f in fields(cls):
            raw = env.get(f"CATRACA_{f.name.upper()}")
            if raw is None:
                continue
            if f.type in (bool, "bool"):
                kwargs[f.name] = raw.strip().lower() in _TRUTHY
            elif f.type in (int, "int"):
                kwargs[f.name] = int(raw)
            elif f.type in (float, "float"):
                kwargs[f.name] = float(raw)
            else:
                kwargs[f.name] = raw
        return cls(**kwargs)
