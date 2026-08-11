from __future__ import annotations

from typing import Any

from .errors import CredentialError, InvalidRequestError
from .files import read_bytes


def load_signer(credentials: dict[str, Any]):
    if not isinstance(credentials, dict):
        raise InvalidRequestError("credentials must be an object.")

    certificate = credentials.get("certificate")
    key = credentials.get("key")
    password = credentials.get("password")

    if not isinstance(certificate, dict) or not isinstance(key, dict):
        raise InvalidRequestError("credentials.certificate and credentials.key are required.")
    if not isinstance(password, str) or not password:
        raise InvalidRequestError("credentials.password is required in the stdin JSON request.")

    cert_path = certificate.get("path")
    key_path = key.get("path")
    if not cert_path or not key_path:
        raise InvalidRequestError("Only path-based certificate/key inputs are supported in v1.")

    try:
        from satcfdi.models import Signer

        return Signer.load(
            certificate=read_bytes(cert_path, "certificate"),
            key=read_bytes(key_path, "private key"),
            password=password,
        )
    except InvalidRequestError:
        raise
    except Exception as exc:
        raise CredentialError() from exc


def signer_info(signer) -> dict[str, Any]:
    certificate = getattr(signer, "certificate", None)
    return {
        "rfc": getattr(signer, "rfc", None),
        "legal_name": getattr(signer, "legal_name", None),
        "certificate_number": getattr(certificate, "serial_number", None)
        or getattr(certificate, "certificate_number", None),
    }
