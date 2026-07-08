from __future__ import annotations

import os
from pathlib import Path

import duckdb


DEFAULT_DUCKDB_PATH = "data/harness.duckdb"
_ENV_LOADED = False


def duckdb_path(value: Path | str | None = None) -> str:
    load_dotenv_once()
    return str(value or os.environ.get("DUCKDB_PATH") or DEFAULT_DUCKDB_PATH)


def connect_duckdb(value: Path | str | None = None) -> duckdb.DuckDBPyConnection:
    load_dotenv_once()
    path = duckdb_path(value)
    if is_local_duckdb_path(path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path)


def is_local_duckdb_path(path: str) -> bool:
    return path not in {":memory:"} and "://" not in path and not path.startswith(("md:", "motherduck:"))


def load_dotenv_once() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    for directory in [Path.cwd(), *Path.cwd().parents]:
        env_path = directory / ".env"
        if env_path.exists():
            load_dotenv_file(env_path)
            break
    if os.environ.get("MOTHERDUCK_TOKEN") and not os.environ.get("motherduck_token"):
        os.environ["motherduck_token"] = os.environ["MOTHERDUCK_TOKEN"]


def load_dotenv_file(path: Path) -> None:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))
