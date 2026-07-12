from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def read_url_or_file(source: str) -> tuple[bytes, str | None, str]:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = Request(source, headers={"user-agent": "procdork-harness/0.1"})
        with urlopen(request, timeout=30) as response:
            return response.read(), response.headers.get_content_type(), "url"

    if parsed.scheme and parsed.scheme != "file":
        raise ValueError(f"unsupported source scheme: {parsed.scheme}")

    path = Path(parsed.path if parsed.scheme == "file" else source).expanduser()
    return path.read_bytes(), guess_type(path.name)[0], "local_file"
