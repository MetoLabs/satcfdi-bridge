# JSON protocol v1

For application-to-application integration, use `satcfdi-bridge exec`. The process reads exactly one UTF-8 JSON object from **stdin** and emits exactly one JSON object to **stdout**.

## Why stdin

Secrets must not be command-line arguments. Command arguments are commonly visible in process listings (`ps`, `/proc/<pid>/cmdline`) and may be captured by process supervisors or shell history. A wrapper should start:

```text
satcfdi-bridge exec
```

and write the request directly to the child's stdin pipe.

Do not build a shell command such as `echo '{...password...}' | satcfdi-bridge exec`; the shell command itself may be persisted in history or logs.

## Request

```json
{
  "schema_version": "1.0",
  "request_id": "caller-generated-id",
  "operation": "csf.download",
  "params": {}
}
```

`request_id` is optional. The bridge generates a UUID when omitted. Consumers should provide one for cross-process tracing.

## Response

Success:

```json
{
  "schema_version": "1.0",
  "ok": true,
  "request_id": "caller-generated-id",
  "operation": "csf.download",
  "result": {},
  "error": null,
  "meta": {
    "bridge_version": "0.1.0",
    "protocol_version": "1.0",
    "satcfdi_version": "26.7.4",
    "python_version": "3.13.0",
    "duration_ms": 1250
  }
}
```

Failure:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "request_id": "caller-generated-id",
  "operation": "csf.download",
  "result": null,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "The e.firma credentials could not be loaded.",
    "retryable": false,
    "details": {}
  },
  "meta": {}
}
```

## stdout and stderr

- stdout is the protocol channel. In `exec` mode it contains JSON only.
- stderr is diagnostic only. It may contain tracebacks when `--debug` is explicitly enabled.
- A consumer must never parse stderr as part of the API response.

## Binary artifacts

Default to `output.mode = "file"`. The bridge writes the artifact and returns its absolute path, byte size, MIME type, and SHA-256 digest. This avoids Base64 overhead and large JSON payloads.

Use `output.mode = "base64"` only where sharing a filesystem with the caller is impossible. Base64 increases payload size by roughly one third.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Success |
| 2 | Invalid request / unsupported operation |
| 10 | Invalid credentials |
| 20 | SAT/upstream/network error |
| 50 | Local I/O error |
| 70 | Unexpected internal error |

Always inspect the JSON `error.code`; exit codes intentionally group classes of errors.

## JSON Schemas

Machine-readable base schemas are included in `schemas/request-v1.schema.json` and `schemas/response-v1.schema.json`. Operation-specific validation remains part of the operation registry in v1; a later release can expose per-operation schemas through `capabilities` without breaking protocol v1.
