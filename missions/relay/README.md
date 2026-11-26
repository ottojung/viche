# Retired PnP proof transport

The former billy-dev to external-host relay is disabled unconditionally under
the current host assignment. No environment variable, installed-client
fallback, service command or legacy CLI may re-enable proof generation or
checking outside billy-dev. `marceline-request` and `pnp-remote-check.py` are
local refusal stubs (status `remote_transport_disabled`, exit 9); they spawn no
network subprocess. Do not install, start, query, submit to, wait on, or cancel
the retired service from this repository.

Local proof generation remains available where bounded and does not imply
verification. Lean compilation/checking must use
`PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile -- lake env lean FILE`
from an exact active bound workspace. Unbound and asynchronous checks remain
disabled. Existing candidate files and historical receipts are preserved and
not relabeled. GitHub-hosted Actions CI is allowed and is not a Viche agent
execution host.

The remaining relay implementation files are historical source only. The
retired command wrappers are deliberately not an operational interface.
