from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .errors import InvalidRequestError

Operation = Callable[[dict[str, Any]], Any]
_OPERATIONS: dict[str, Operation] = {}
_CAPABILITIES: dict[str, dict[str, Any]] = {}


def operation(name: str, *, description: str, credentials: bool = False, output: str = "json"):
    def decorator(func: Operation) -> Operation:
        _OPERATIONS[name] = func
        _CAPABILITIES[name] = {
            "description": description,
            "requires_credentials": credentials,
            "output": output,
        }
        return func
    return decorator


def execute(name: str, params: dict[str, Any]) -> Any:
    try:
        handler = _OPERATIONS[name]
    except KeyError as exc:
        raise InvalidRequestError("Unknown operation.", {"operation": name}) from exc
    return handler(params)


def capabilities() -> dict[str, dict[str, Any]]:
    return dict(sorted(_CAPABILITIES.items()))
