# MetoLabs SATCFDI Bridge

A stable, machine-friendly CLI façade over [`python-satcfdi`](https://github.com/SAT-CFDI/python-satcfdi).

The project is designed to be called from PHP, Node.js, Go, Ruby, Java, shell scripts, job workers, or any runtime that can spawn a process and communicate over stdin/stdout.

## Goals

- expose selected `python-satcfdi` features through a versioned contract;
- keep secrets out of command-line arguments;
- make stdout deterministic and safe to parse;
- provide stable error codes independent of Python exception names;
- keep binary payloads out of stdout by default;
- avoid reflection or arbitrary Python method execution;
- make upstream compatibility visible through `capabilities` and version metadata.

## Requirements

- Python 3.10+
- `satcfdi >= 26.7.4, < 27`

The upstream package currently supports Python 3.10 through 3.14.

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

For development:

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Recommended integration: JSON over stdin

Never put an e.firma password on the process command line. Spawn only:

```bash
satcfdi-bridge exec
```

Then write a JSON request directly to stdin:

```json
{
  "schema_version": "1.0",
  "operation": "csf.download",
  "params": {
    "credentials": {
      "certificate": {"path": "/secure/fiel.cer"},
      "key": {"path": "/secure/fiel.key"},
      "password": "secret-supplied-through-stdin"
    },
    "output": {
      "mode": "file",
      "path": "/tmp/constancia.pdf"
    }
  }
}
```

stdout contains one JSON response and nothing else.

See [`docs/PROTOCOL.md`](docs/PROTOCOL.md) and [`docs/SECURITY.md`](docs/SECURITY.md).

## Human CLI

Human-oriented commands are also provided. They prompt for the private-key password without echo:

```bash
satcfdi-bridge csf-download \
  --certificate /secure/fiel.cer \
  --key /secure/fiel.key \
  --output ./constancia.pdf
```

For automation, use `exec` instead of these convenience commands.

## Operations in v0.1

Run:

```bash
satcfdi-bridge capabilities --pretty
```

The initial stable operation registry includes:

- `credentials.inspect`
- `csf.retrieve`
- `csf.download`
- `compliance.download`
- `portal.rfc_valid`
- `portal.legal_name_valid`
- `portal.lco_details`
- `mass.cfdi.request_emitted`
- `mass.cfdi.request_received`
- `mass.cfdi.status`
- `mass.cfdi.download`
- `mass.retention.request_uuid`
- `mass.retention.status`
- `mass.retention.download`
- `cfdi.inspect`
- `cfdi.render`

This intentionally does not expose arbitrary `satcfdi` methods. New upstream features are added as explicit bridge operations so consumers get a stable contract.

## Artifact response

File outputs include integrity metadata:

```json
{
  "mode": "file",
  "path": "/tmp/constancia.pdf",
  "filename": "constancia.pdf",
  "mime_type": "application/pdf",
  "size": 123456,
  "sha256": "..."
}
```

Use Base64 only when the caller cannot share a filesystem with the subprocess:

```json
"output": { "mode": "base64" }
```

## Versioning

There are two independent versions:

- package version (`bridge_version`), following SemVer;
- JSON protocol version (`schema_version` / `protocol_version`).

A breaking JSON contract change requires a new protocol major version. Adding a new optional field or operation does not.

## Upstream

This project wraps SAT-CFDI/python-satcfdi and does not copy its implementation. `python-satcfdi` is an MIT-licensed independent project.
