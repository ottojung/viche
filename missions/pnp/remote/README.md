# Remote build protocol (offline prototype)

Do not send these bundles over a public channel. A job contains the unpublished
Lean source, exact gap statement, allowed imports, base SHA, toolchain, hashed
attempt identity, and bounded resource requests. Its content hash detects
accidental mismatch but provides **no authentication** or confidentiality.
No raw lease or credentials are included.

The local-only command is:

    PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.remote pack FILE.lean

It checks the immutable assignment, exact source, pinned workspace HEAD and
toolchain and stores a private mode-0700 spool. It returns a job digest,
not a successful compile. `poll DIGEST` and `cancel DIGEST` apply to the current
bound assignment only. No public refs, network requests, or external execution
are performed.

The spool accepts a trusted runner callback for tests and future deployment.
The runner must enforce a verified pinned checkout, a clean immutable library
cache, strict resource controls and cancellation, and run Lean without
network access or inherited credentials. The spool serializes jobs conservatively
and checks memory headroom, but is not itself an execution sandbox. Transport
must authenticate both endpoints, encrypt private blobs, and protect against
replay and retention leakage. Host provisioning remains an operator task.

The output status `elaborated` is diagnostic evidence only: it cannot set a
gap to ACCEPTED, substitute for the upstream checker, or bypass the existing
publication state machine. Infrastructure/resource errors remain retryable.

## Operator-only isolated worker

The optional local command `python3 -m missions.pnp.remote.runner --manifest
MANIFEST --spool PRIVATE_DIR DIGEST` runs one already-staged request. It
does not create a network service or transfer a bundle. Its operator-owned
JSON manifest pins `base` (40-hex Git SHA), `toolchain`, `image` (local
sha256 image ID), `toolchain_root` (absolute directory containing bin/lean),
and `libraries` (ordered absolute compiled library directories matching the
pinned checkout). These are trusted inputs, never supplied by the job.
The operator must independently build and freeze the cache and verify its
provenance before enabling the runner. Container mounts are read-only but
do not prevent host processes from changing a cache.

The rootless Podman command disallows pulls, networking, host environment and
proxy inheritance, writable root filesystem and additional capabilities;
mounts only the pinned toolchain, libraries, and one candidate; applies
memory, CPU, PID and wall limits; caps captured diagnostics; and removes
the private job container on cancellation or exit. It does not grant
publication authority. No production worker or transport is installed.
