"""Optional lab backends loaded from environment variables.

Set these if you have site-specific BBU / UE libraries:

- LAB_BBU_ADMIN_MODULE: module that exposes ``admin``
- LAB_BBU_EXCEPTION_MODULE: module that exposes
  ``AdminApiConnectionClosedException``
- LAB_UE_MODULE: module that exposes ``PythonApi``

A gitignored ``.env`` or ``.env.local`` in the repo root is loaded first.
When unset, in-repo stubs keep the toolkit importable.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _load_dotenv() -> None:
    root = Path(__file__).resolve().parents[1]
    for name in (".env", ".env.local"):
        path = root / name
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


def _env_pkg(key: str) -> str | None:
    value = os.environ.get(key, "").strip()
    return value or None


class AdminApiConnectionClosedException(Exception):
    pass


class _AdminClient:
    def connect_to(self, bts_host: str | None = None, **kwargs: Any) -> None:
        raise RuntimeError("Set LAB_BBU_ADMIN_MODULE to use a BBU admin backend.")

    def get_active_alarms(self):
        return []

    def teardown(self) -> None:
        pass


def admin() -> _AdminClient:
    return _AdminClient()


class _StubPythonApi:
    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = config_path

    def require_ue(self, *args: Any, **kwargs: Any):
        raise RuntimeError("Set LAB_UE_MODULE to use a UE backend.")

    def shutdown(self) -> None:
        pass


ue_lib = SimpleNamespace(PythonApi=_StubPythonApi)

_admin_mod = _env_pkg("LAB_BBU_ADMIN_MODULE")
if _admin_mod:
    admin = getattr(importlib.import_module(_admin_mod), "admin")

_exc_mod = _env_pkg("LAB_BBU_EXCEPTION_MODULE")
if _exc_mod:
    AdminApiConnectionClosedException = getattr(
        importlib.import_module(_exc_mod), "AdminApiConnectionClosedException"
    )

_ue_mod = _env_pkg("LAB_UE_MODULE")
if _ue_mod:
    ue_lib = importlib.import_module(_ue_mod)
