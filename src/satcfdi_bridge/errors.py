from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BridgeError(Exception):
    code: str
    message: str
    exit_code: int = 70
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class InvalidRequestError(BridgeError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__("INVALID_REQUEST", message, 2, False, details or {})


class CredentialError(BridgeError):
    def __init__(self, message: str = "The e.firma credentials could not be loaded."):
        super().__init__("INVALID_CREDENTIALS", message, 10, False)


class UpstreamError(BridgeError):
    def __init__(self, message: str, *, retryable: bool = False, details=None):
        super().__init__("UPSTREAM_ERROR", message, 20, retryable, details or {})


class IoBridgeError(BridgeError):
    def __init__(self, message: str, details=None):
        super().__init__("IO_ERROR", message, 50, False, details or {})
