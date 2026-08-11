from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any

from . import PROTOCOL_VERSION, __version__
from .engine import parse_stdin, run_request
from .errors import BridgeError
from .protocol import dump_json, package_version
from .registry import capabilities
from . import operations  # noqa: F401


def machine_exec(args: argparse.Namespace) -> int:
    try:
        request = parse_stdin(sys.stdin.read())
    except BridgeError as exc:
        payload, code = run_request({"operation": "__invalid__", "params": {}}, debug=args.debug)
        payload["error"] = {"code": exc.code, "message": exc.message, "retryable": exc.retryable, "details": exc.details}
        print(dump_json(payload, pretty=args.pretty))
        return exc.exit_code
    payload, code = run_request(request, debug=args.debug)
    print(dump_json(payload, pretty=args.pretty))
    return code


def make_credentials(args) -> dict[str, Any]:
    password = None
    if getattr(args, "password_stdin", False):
        password = sys.stdin.read().rstrip("\r\n")
    elif getattr(args, "password_file", None):
        password = Path(args.password_file).expanduser().read_text(encoding="utf-8").rstrip("\r\n")
    else:
        password = getpass.getpass("e.firma private-key password: ")
    return {
        "certificate": {"path": args.certificate},
        "key": {"path": args.key},
        "password": password,
    }


def human_request(args) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if hasattr(args, "certificate"):
        params["credentials"] = make_credentials(args)
    for key in ("rfc", "legal_name", "id_cif", "start_date", "end_date", "request_id", "package_id", "uuid"):
        value = getattr(args, key, None)
        if value is not None:
            params[key] = value
    if getattr(args, "output", None):
        params["output"] = {"mode": "file", "path": args.output}
    if getattr(args, "base64", False):
        params["output"] = {"mode": "base64"}
    if getattr(args, "format", None):
        params["format"] = args.format
    if getattr(args, "source", None):
        params["source"] = {"path": args.source}
    return {"schema_version": "1.0", "operation": args.operation, "params": params}


def human_exec(args) -> int:
    payload, code = run_request(human_request(args), debug=args.debug)
    print(dump_json(payload, pretty=True if not args.compact else False))
    return code


def add_creds(parser):
    parser.add_argument("--certificate", required=True, help="Path to the .cer file")
    parser.add_argument("--key", required=True, help="Path to the .key file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--password-stdin", action="store_true", help="Read the key password from stdin")
    group.add_argument("--password-file", help="Read the key password from a file")


def add_common(parser):
    parser.add_argument("--debug", action="store_true", help="Write diagnostic tracebacks to stderr")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="satcfdi-bridge", description="Machine-friendly bridge for python-satcfdi")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("exec", help="Execute one JSON request read entirely from stdin (recommended for wrappers)")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.set_defaults(func=machine_exec)

    p = sub.add_parser("capabilities", help="List stable operations")
    p.add_argument("--pretty", action="store_true")
    p.set_defaults(func=lambda a: (print(dump_json({"schema_version": PROTOCOL_VERSION, "bridge_version": __version__, "satcfdi_version": package_version("satcfdi"), "operations": capabilities()}, pretty=a.pretty)) or 0))

    def command(name, operation, help_text, creds=False, artifact=False):
        q = sub.add_parser(name, help=help_text)
        q.set_defaults(func=human_exec, operation=operation)
        if creds:
            add_creds(q)
        if artifact:
            out = q.add_mutually_exclusive_group(required=True)
            out.add_argument("--output")
            out.add_argument("--base64", action="store_true")
        add_common(q)
        return q

    command("credentials-inspect", "credentials.inspect", "Validate e.firma and show public metadata", True)
    q = command("csf-retrieve", "csf.retrieve", "Retrieve public CSF data")
    q.add_argument("--rfc", required=True); q.add_argument("--id-cif", required=True)
    command("csf-download", "csf.download", "Download CSF PDF", True, True)
    command("compliance-download", "compliance.download", "Download 32-D Compliance Opinion PDF", True, True)
    q = command("rfc-valid", "portal.rfc_valid", "Validate an RFC", True); q.add_argument("--rfc", required=True)
    q = command("legal-name-valid", "portal.legal_name_valid", "Validate RFC/legal name", True); q.add_argument("--rfc", required=True); q.add_argument("--legal-name", required=True)
    q = command("lco-details", "portal.lco_details", "Retrieve LCO details", True); q.add_argument("--rfc", required=True)
    q = command("mass-cfdi-emitted", "mass.cfdi.request_emitted", "Request issued CFDIs", True); q.add_argument("--start-date", required=True); q.add_argument("--end-date", required=True)
    q = command("mass-cfdi-received", "mass.cfdi.request_received", "Request received CFDIs", True); q.add_argument("--start-date", required=True); q.add_argument("--end-date", required=True)
    q = command("mass-cfdi-status", "mass.cfdi.status", "Get CFDI massive-download status", True); q.add_argument("--request-id", required=True)
    q = command("mass-cfdi-download", "mass.cfdi.download", "Download CFDI package ZIP", True, True); q.add_argument("--package-id", required=True)
    q = command("mass-retention-uuid", "mass.retention.request_uuid", "Request retention by UUID", True); q.add_argument("--uuid", required=True)
    q = command("mass-retention-status", "mass.retention.status", "Get retention request status", True); q.add_argument("--request-id", required=True)
    q = command("mass-retention-download", "mass.retention.download", "Download retention package ZIP", True, True); q.add_argument("--package-id", required=True)
    q = command("cfdi-inspect", "cfdi.inspect", "Inspect CFDI XML"); q.add_argument("--source", required=True)
    q = command("cfdi-render", "cfdi.render", "Render CFDI XML"); q.add_argument("--source", required=True); q.add_argument("--format", choices=["pdf","html","json","xml"], default="pdf"); q.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
