# coding: utf-8
import os
from typing import Optional
from pathlib import Path

import yaml

from demo.core.config.config import Config

g_config: Optional[Config] = None

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(**data)


def deep_merge(base: dict, override: dict) -> dict:
    """递归合并字典"""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config_with_merge(base_path: str, override_path: str) -> Config:
    with open(base_path, "r", encoding="utf-8") as f:
        base_conf = yaml.safe_load(f)

    with open(override_path, "r", encoding="utf-8") as f:
        override_config = yaml.safe_load(f)

    merged = deep_merge(base_conf, override_config)

    return Config(**merged)


def set_up():
    global g_config

    env = os.getenv("APP_ENV", "dev")

    g_config = load_config(BASE_DIR / f"config-{env}.yaml")


def get_config() -> Config:
    return g_config
