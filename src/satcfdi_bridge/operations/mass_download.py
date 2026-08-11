from __future__ import annotations

import base64
from datetime import date
from typing import Any

from ..credentials import load_signer
from ..errors import InvalidRequestError, UpstreamError
from ..files import write_artifact
from ..registry import operation


def service(params):
    signer = load_signer(params.get("credentials"))
    from satcfdi.pacs.sat import SAT
    return SAT(signer=signer)


def parse_date(value: str | None, name: str) -> date:
    if not value:
        raise InvalidRequestError(f"{name} is required.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidRequestError(f"{name} must use YYYY-MM-DD format.") from exc


def enum_value(module, enum_name: str, value: str | None, default: str | None = None):
    text = value or default
    if text is None:
        return None
    enum = getattr(module, enum_name)
    try:
        return enum[text.upper()]
    except KeyError as exc:
        raise InvalidRequestError(f"Invalid {enum_name} value.", {"value": text}) from exc


@operation("mass.cfdi.request_emitted", description="Create a massive-download request for issued CFDIs.", credentials=True)
def request_emitted(params: dict[str, Any]) -> Any:
    try:
        import satcfdi.pacs.sat as satmod
        sat = service(params)
        return sat.recover_comprobante_emitted_request(
            fecha_inicial=parse_date(params.get("start_date"), "start_date"),
            fecha_final=parse_date(params.get("end_date"), "end_date"),
            rfc_emisor=params.get("rfc_emisor") or sat.signer.rfc,
            tipo_solicitud=enum_value(satmod, "TipoDescargaMasivaTerceros", params.get("request_type"), "CFDI"),
            estado_comprobante=enum_value(satmod, "EstadoComprobante", params.get("status"), "VIGENTE"),
        )
    except InvalidRequestError:
        raise
    except Exception as exc:
        raise UpstreamError("Massive download request for issued CFDIs failed.", retryable=True) from exc


@operation("mass.cfdi.request_received", description="Create a massive-download request for received CFDIs.", credentials=True)
def request_received(params: dict[str, Any]) -> Any:
    try:
        import satcfdi.pacs.sat as satmod
        sat = service(params)
        return sat.recover_comprobante_received_request(
            fecha_inicial=parse_date(params.get("start_date"), "start_date"),
            fecha_final=parse_date(params.get("end_date"), "end_date"),
            rfc_receptor=params.get("rfc_receptor") or sat.signer.rfc,
            tipo_solicitud=enum_value(satmod, "TipoDescargaMasivaTerceros", params.get("request_type"), "CFDI"),
            estado_comprobante=enum_value(satmod, "EstadoComprobante", params.get("status"), "VIGENTE"),
        )
    except InvalidRequestError:
        raise
    except Exception as exc:
        raise UpstreamError("Massive download request for received CFDIs failed.", retryable=True) from exc


@operation("mass.cfdi.status", description="Get the status of a CFDI massive-download request.", credentials=True)
def cfdi_status(params: dict[str, Any]) -> Any:
    request_id = params.get("request_id")
    if not request_id:
        raise InvalidRequestError("request_id is required.")
    try:
        return service(params).recover_comprobante_status(request_id)
    except Exception as exc:
        raise UpstreamError("Massive download status query failed.", retryable=True) from exc


@operation("mass.cfdi.download", description="Download a CFDI massive-download package ZIP.", credentials=True, output="artifact")
def cfdi_download(params: dict[str, Any]) -> Any:
    package_id = params.get("package_id")
    if not package_id:
        raise InvalidRequestError("package_id is required.")
    try:
        response, package = service(params).recover_comprobante_download(id_paquete=package_id)
        data = base64.b64decode(package)
    except Exception as exc:
        raise UpstreamError("Massive download package retrieval failed.", retryable=True) from exc
    artifact = write_artifact(data, params.get("output", {}), default_name=f"{package_id}.zip", mime="application/zip")
    return {"package_id": package_id, "sat_response": response, "artifact": artifact}


@operation("mass.retention.request_uuid", description="Create a retention massive-download request by UUID.", credentials=True)
def retention_uuid(params: dict[str, Any]) -> Any:
    uuid = params.get("uuid")
    if not uuid:
        raise InvalidRequestError("uuid is required.")
    try:
        return service(params).recover_retencion_uuid_request(folio=uuid)
    except Exception as exc:
        raise UpstreamError("Retention UUID download request failed.", retryable=True) from exc


@operation("mass.retention.status", description="Get the status of a retention massive-download request.", credentials=True)
def retention_status(params: dict[str, Any]) -> Any:
    request_id = params.get("request_id")
    if not request_id:
        raise InvalidRequestError("request_id is required.")
    try:
        return service(params).recover_retencion_status(request_id)
    except Exception as exc:
        raise UpstreamError("Retention massive download status query failed.", retryable=True) from exc


@operation("mass.retention.download", description="Download a retention massive-download package ZIP.", credentials=True, output="artifact")
def retention_download(params: dict[str, Any]) -> Any:
    package_id = params.get("package_id")
    if not package_id:
        raise InvalidRequestError("package_id is required.")
    try:
        response, package = service(params).recover_retencion_download(id_paquete=package_id)
        data = base64.b64decode(package)
    except Exception as exc:
        raise UpstreamError("Retention massive download package retrieval failed.", retryable=True) from exc
    artifact = write_artifact(data, params.get("output", {}), default_name=f"{package_id}.zip", mime="application/zip")
    return {"package_id": package_id, "sat_response": response, "artifact": artifact}
