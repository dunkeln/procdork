from __future__ import annotations

import json
from pathlib import Path

from load import LoadedArtifact


def write_local_blob(key: str, payload: bytes, storage_root: Path | str) -> str:
    destination = Path(storage_root) / key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return f"local://{key}"


def append_jsonl(artifact: LoadedArtifact, manifest_path: Path | str) -> None:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as manifest:
        manifest.write(json.dumps(artifact.model_dump(mode="json"), sort_keys=True) + "\n")
