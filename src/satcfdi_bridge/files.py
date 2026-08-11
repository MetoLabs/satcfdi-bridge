from __future__ import annotations

import base64
import hashlib
import mimetypes
from pathlib import Path
from typing import Any

from .errors import InvalidRequestError, IoBridgeError


def read_bytes(path: str, label: str) -> bytes:
    file = Path(path).expanduser()
    try:
        return file.read_bytes()
    except OSError as exc:
        raise IoBridgeError(f"Unable to read {label} file.", {"path": str(file)}) from exc


def write_artifact(data: bytes, output: dict[str, Any], *, default_name: str, mime: str) -> dict[str, Any]:
    mode = output.get("mode", "file")
    digest = hashlib.sha256(data).hexdigest()

    if mode == "base64":
        return {
            "mode": "base64",
            "mime_type": mime,
            "size": len(data),
            "sha256": digest,
            "content_base64": base64.b64encode(data).decode("ascii"),
        }

    if mode != "file":
        raise InvalidRequestError("output.mode must be either 'file' or 'base64'.")

    raw_path = output.get("path")
    if not raw_path:
        raise InvalidRequestError("output.path is required when output.mode is 'file'.")

    path = Path(raw_path).expanduser().resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as exc:
        raise IoBridgeError("Unable to write output file.", {"path": str(path)}) from exc

    return {
        "mode": "file",
        "path": str(path),
        "filename": path.name or default_name,
        "mime_type": mime or mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size": len(data),
        "sha256": digest,
    }
