from __future__ import annotations

import json
import platform
import time
import uuid
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from . import PROTOCOL_VERSION, __version__


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def new_request_id(value: str | None = None) -> str:
    return value or str(uuid.uuid4())


@dataclass
class Timer:
    started: float = 0.0

    def __enter__(self) -> "Timer":
        self.started = time.monotonic()
        return self

    @property
    def elapsed_ms(self) -> int:
        return round((time.monotonic() - self.started) * 1000)

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def meta(duration_ms: int) -> dict[str, Any]:
    return {
        "bridge_version": __version__,
        "protocol_version": PROTOCOL_VERSION,
        "satcfdi_version": package_version("satcfdi"),
        "python_version": platform.python_version(),
        "duration_ms": duration_ms,
    }


def success(request_id: str, operation: str, result: Any, duration_ms: int) -> dict[str, Any]:
    return {
        "schema_version": PROTOCOL_VERSION,
        "ok": True,
        "request_id": request_id,
        "operation": operation,
        "result": result,
        "error": None,
        "meta": meta(duration_ms),
    }


def failure(request_id: str, operation: str | None, error, duration_ms: int) -> dict[str, Any]:
    return {
        "schema_version": PROTOCOL_VERSION,
        "ok": False,
        "request_id": request_id,
        "operation": operation,
        "result": None,
        "error": {
            "code": error.code,
            "message": error.message,
            "retryable": error.retryable,
            "details": error.details,
        },
        "meta": meta(duration_ms),
    }


def dump_json(value: Any, *, pretty: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=pretty,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
        default=str,
    )
