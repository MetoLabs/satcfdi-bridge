from __future__ import annotations

from typing import Any

from ..credentials import load_signer
from ..errors import InvalidRequestError, UpstreamError
from ..registry import operation


def session(params):
    signer = load_signer(params.get("credentials"))
    try:
        from satcfdi.portal import SATFacturaElectronica
        client = SATFacturaElectronica(signer)
        client.login()
        return client
    except Exception as exc:
        raise UpstreamError("SAT Electronic Invoice Portal login failed.", retryable=True) from exc


@operation("portal.rfc_valid", description="Validate whether an RFC exists in SAT's electronic invoice portal.", credentials=True)
def rfc_valid(params: dict[str, Any]) -> Any:
    rfc = params.get("rfc")
    if not rfc:
        raise InvalidRequestError("rfc is required.")
    client = session(params)
    try:
        return {"rfc": rfc.upper(), "valid": client.rfc_valid(rfc)}
    except Exception as exc:
        raise UpstreamError("SAT RFC validation failed.", retryable=True) from exc


@operation("portal.legal_name_valid", description="Validate RFC and legal-name correspondence.", credentials=True)
def legal_name_valid(params: dict[str, Any]) -> Any:
    rfc, legal_name = params.get("rfc"), params.get("legal_name")
    if not rfc or not legal_name:
        raise InvalidRequestError("rfc and legal_name are required.")
    client = session(params)
    try:
        return {"rfc": rfc.upper(), "legal_name": legal_name, "valid": client.legal_name_valid(rfc, legal_name)}
    except Exception as exc:
        raise UpstreamError("SAT legal-name validation failed.", retryable=True) from exc


@operation("portal.lco_details", description="Retrieve LCO details for an RFC.", credentials=True)
def lco_details(params: dict[str, Any]) -> Any:
    rfc = params.get("rfc")
    if not rfc:
        raise InvalidRequestError("rfc is required.")
    client = session(params)
    try:
        return client.lco_details(rfc, apply_border_region=bool(params.get("apply_border_region", True)))
    except Exception as exc:
        raise UpstreamError("SAT LCO lookup failed.", retryable=True) from exc
