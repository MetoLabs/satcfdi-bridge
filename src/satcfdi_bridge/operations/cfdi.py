from __future__ import annotations

from pathlib import Path
from typing import Any

from ..errors import InvalidRequestError, UpstreamError
from ..registry import operation


def load_cfdi(params):
    source = params.get("source")
    if not isinstance(source, dict) or not source.get("path"):
        raise InvalidRequestError("source.path is required.")
    try:
        from satcfdi.cfdi import CFDI
        return CFDI.from_file(str(Path(source["path"]).expanduser()))
    except Exception as exc:
        raise UpstreamError("Unable to load CFDI XML.", details={"path": source.get("path")}) from exc


@operation("cfdi.inspect", description="Load a CFDI XML and return its JSON-compatible representation.")
def inspect_cfdi(params: dict[str, Any]) -> Any:
    invoice = load_cfdi(params)
    if hasattr(invoice, "to_dict"):
        return invoice.to_dict()
    if isinstance(invoice, dict):
        return invoice
    return {"type": invoice.__class__.__name__, "repr": str(invoice)}


@operation("cfdi.render", description="Render a CFDI XML as PDF, HTML, or JSON file.", output="artifact")
def render_cfdi(params: dict[str, Any]) -> Any:
    invoice = load_cfdi(params)
    output = params.get("output", {})
    path = output.get("path") if isinstance(output, dict) else None
    fmt = str(params.get("format", "pdf")).lower()
    if not path:
        raise InvalidRequestError("output.path is required.")
    if fmt not in {"pdf", "html", "json", "xml"}:
        raise InvalidRequestError("format must be pdf, html, json, or xml.")
    try:
        from satcfdi import render
        if fmt == "pdf":
            render.pdf_write(invoice, path)
        elif fmt == "html":
            render.html_write(invoice, path)
        elif fmt == "json":
            render.json_write(invoice, path, pretty_print=bool(params.get("pretty", False)))
        else:
            invoice.xml_write(path)
    except Exception as exc:
        raise UpstreamError("CFDI rendering failed.") from exc
    file = Path(path).expanduser().resolve()
    return {"path": str(file), "format": fmt, "size": file.stat().st_size}
