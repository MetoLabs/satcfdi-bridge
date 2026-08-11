from __future__ import annotations

import json
import traceback
from typing import Any

from .errors import BridgeError, InvalidRequestError, UpstreamError
from .protocol import Timer, failure, new_request_id, success
from .registry import execute
from . import operations  # noqa: F401


def run_request(request: Any, *, debug: bool = False) -> tuple[dict[str, Any], int]:
    request_id = new_request_id(request.get("request_id") if isinstance(request, dict) else None)
    operation = request.get("operation") if isinstance(request, dict) else None

    with Timer() as timer:
        try:
            if not isinstance(request, dict):
                raise InvalidRequestError("Request must be a JSON object.")
            if request.get("schema_version", "1.0") != "1.0":
                raise InvalidRequestError("Unsupported schema_version.")
            if not isinstance(operation, str) or not operation:
                raise InvalidRequestError("operation is required.")
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise InvalidRequestError("params must be an object.")
            result = execute(operation, params)
            return success(request_id, operation, result, timer.elapsed_ms), 0
        except BridgeError as exc:
            if debug:
                traceback.print_exc()
            return failure(request_id, operation, exc, timer.elapsed_ms), exc.exit_code
        except Exception as exc:
            if debug:
                traceback.print_exc()
            error = UpstreamError("Unhandled bridge error.", details={"type": type(exc).__name__})
            return failure(request_id, operation, error, timer.elapsed_ms), 70


def parse_stdin(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidRequestError("stdin must contain valid JSON.", {"line": exc.lineno, "column": exc.colno}) from exc
