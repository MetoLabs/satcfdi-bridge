from __future__ import annotations

from typing import Any

from ..credentials import load_signer, signer_info
from ..errors import InvalidRequestError, UpstreamError
from ..files import write_artifact
from ..registry import operation


@operation("credentials.inspect", description="Validate e.firma files and return public certificate metadata.", credentials=True)
def credentials_inspect(params: dict[str, Any]) -> dict[str, Any]:
    signer = load_signer(params.get("credentials"))
    return signer_info(signer)


@operation("csf.retrieve", description="Retrieve public CSF data using RFC and CIF ID.")
def csf_retrieve(params: dict[str, Any]) -> Any:
    rfc = params.get("rfc")
    id_cif = params.get("id_cif")
    if not rfc or not id_cif:
        raise InvalidRequestError("rfc and id_cif are required.")
    try:
        from satcfdi import csf
        return csf.retrieve(rfc, id_cif=id_cif)
    except Exception as exc:
        raise UpstreamError("SAT CSF public retrieval failed.", retryable=True) from exc


@operation("csf.download", description="Download the Tax Status Certificate PDF using e.firma.", credentials=True, output="artifact")
def csf_download(params: dict[str, Any]) -> dict[str, Any]:
    signer = load_signer(params.get("credentials"))
    try:
        from satcfdi.portal import SATPortalConstancia
        data = SATPortalConstancia(signer).generar_constancia()
    except Exception as exc:
        raise UpstreamError("SAT Tax Status Certificate download failed.", retryable=True) from exc
    result = write_artifact(data, params.get("output", {}), default_name="constancia.pdf", mime="application/pdf")
    result["signer"] = signer_info(signer)
    return result


@operation("compliance.download", description="Download the 32-D Compliance Opinion PDF using e.firma.", credentials=True, output="artifact")
def compliance_download(params: dict[str, Any]) -> dict[str, Any]:
    signer = load_signer(params.get("credentials"))
    try:
        from satcfdi.portal import SATPortalOpinionCumplimiento
        data = SATPortalOpinionCumplimiento(signer).generar_opinion_cumplimiento()
    except Exception as exc:
        raise UpstreamError("SAT Compliance Opinion download failed.", retryable=True) from exc
    result = write_artifact(data, params.get("output", {}), default_name="opinion-32d.pdf", mime="application/pdf")
    result["signer"] = signer_info(signer)
    return result
