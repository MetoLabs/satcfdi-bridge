# Security model

## Secrets

The machine API accepts the e.firma password only inside the stdin JSON request. It is never required as a CLI argument. Human-oriented commands prompt without echo by default and optionally support `--password-stdin` or `--password-file`.

Avoid environment variables for long-lived e.firma passwords. They are convenient but can leak through debugging tools, crash diagnostics, container configuration, CI metadata, and process environments.

## Certificate and private-key files

File paths are not secrets, but the private key contents are sensitive. Production callers should keep `.key` files outside web roots, use OS permissions such as `0600`, and run the bridge under the least-privileged account that needs access.

## Logging

The bridge does not log request bodies. Do not add middleware that logs raw stdin. Diagnostic mode must not be enabled permanently in production.

## Temporary files

The bridge does not copy credentials into temporary files. Artifact outputs are written only to caller-selected paths. Callers are responsible for choosing a secure output directory and deleting artifacts when no longer needed.
