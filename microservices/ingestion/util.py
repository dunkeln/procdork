from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from hashlib import sha1
from pathlib import PurePosixPath


def now() -> datetime:
    return datetime.now(UTC)


def env(*names: str) -> str | None:
    return next((os.environ[name] for name in names if os.environ.get(name)), None)


def stable_id(prefix: str, *parts: object) -> str:
    digest = sha1("|".join(str(part) for part in parts).encode()).hexdigest()[:12]
    return f"{prefix}_{digest}"


def clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" .,:;-")


def canonical_name(name: str) -> str:
    return re.sub(r"\b(?:llc|inc|ltd|corp|co)\.?\b", "", name, flags=re.I).strip(" ,.-").title()


def filename(url: str) -> str:
    name = PurePosixPath(url.split("?", 1)[0]).name
    return name or "document"
