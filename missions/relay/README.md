# Marceline relay — agent quick start

Temporary billy-dev → marceline-dev transport. It uses two random objects in
the existing Antonina storage namespace (via the deployed Skrynia store API),
not the Antonina application and not a new namespace.

## Agent commands (billy-dev)

Run from any directory (if PATH is minimal, use ~/.local/bin/marceline-request):
```sh
marceline-request status       # heartbeat and supported pinned Lean bases
marceline-request ping hello
marceline-request submit ping hello
marceline-request wait REQUEST_ID 90
marceline-request cancel REQUEST_ID
```

**Blocking:** ping waits for a terminal result; stdout is one JSON object,
stderr contains the ID, ACK/running state and periodic service heartbeat.
Exit 0 = operation returned a result, 1 = transport/operation error,
2 = timeout. On timeout use wait with the same ID. Do not submit duplicates.
A result is retained locally for 24 hours, including after mailbox cleanup.

**Nonblocking:** submit returns the request ID immediately. Continue useful
work and retrieve it with wait when you need the result. cancel removes the
request and asks the worker to stop; cancellation is not an instantaneous
execution guarantee. Do not poll in a busy loop. A stale heartbeat or an
infrastructure failure is a reason to use local alternatives, not stop work.

## Lean compilation — PnP researchers

From your bound research workspace (the Executive injects these commands at dispatch):

```sh
pnp-remote-check --availability
pnp-remote-check path/to/candidate.lean
pnp-remote-check --async path/to/candidate.lean
pnp-remote-check --scratch --async path/to/Scratch.lean
pnp-remote-check --wait REQUEST_ID
```

The helper checks your immutable live assignment, packs the exact source and
checks the advertised pinned base before transmitting anything. Use --scratch for intermediate files, including unfinished proofs; scratch success is not proof acceptance. A blocking check or --wait exits 0 only for successful elaboration; --wait prints the compiler result directly. Async submission exits 0
when queued. If the packer or matching cache is unavailable, use the local
managed compiler; never wait for remote infrastructure before publishing a
complete candidate.

### Low-level interface

The transport supports only named operations: ping and lean-check. It does
NOT execute shell commands. Lean compilation requires a validated PnP
remote-job JSON and an operator-provisioned isolated pinned cache on
marceline-dev.

```sh
marceline-request submit lean-check /private/path/JOB.request
pnp-remote-check --wait REQUEST_ID
# or blocking:
marceline-request lean-check /private/path/JOB.request
```

Read the result's nested result.status, not just the relay exit code.
Only elaborated with exit_code 0 and matching job/base/toolchain/source
digest is successful elaboration; it is not upstream acceptance. A missing
pinned cache, resource deferral, or unavailable runner is retryable
infrastructure, not a false theorem. Do not send credentials, raw desk
leases or arbitrary files. The PnP pack tool must validate the current
assignment and source before sending. See missions/pnp/remote/README.md
once that module lands. Local Lean and early publication remain available.

## Operator layout

- Repository source: missions/relay/ (this directory). Do not create ~/scripts.
- Installed code: ~/.local/share/viche/relay/; executable in ~/.local/bin.
- Private shared configuration: ~/.config/marceline-relay/config.json (0600).
  The request/response object IDs and 256-bit shared key must match on the
  two hosts. Never print, paste into prompts, or commit these values.
- Private runtime state: ~/.local/state/marceline-relay/ (0700);
  client pending requests/receipts and worker receipts are separate.
- Marceline service: /etc/services.d/marceline-relay/run, activated via
  the existing /run/service s6 supervisor. No new network listener.
- Optional Lean config on marceline: ~/.config/marceline-relay/lean.json
  (0600), containing only operator-selected runner_root and manifests paths.
  Each manifest is named <base-sha>.json, private, and pins the toolchain,
  image and compiled library roots. Each has a matching
  <base-sha>.provenance.json, recording the tested runner revision, shared
  dependency checkout and package Git revisions. The handler checks these
  revisions before every build and rejects absent imported modules as
  infrastructure errors. Compiled cache bytes must remain operator-owned
  and pinned; read-only container mounts do not freeze host-side files.
  No handler runs if configuration is absent.

Install client from the source checkout with ./install.sh. Install or
restart worker on marceline-dev with ./install-worker.sh. Inspect service:
```sh
/command/s6-svstat /run/service/marceline-relay
marceline-request status
```
Run offline tests using node test.mjs. They never contact the storage API.

## Wire and reliability

Both mailboxes are AES-256-GCM authenticated ciphertext with independent
random nonces and direction/object-bound associated data. TLS is required;
the storage object locators are private but secrecy of a locator alone is
not the security boundary. The store can refuse, delete, or replay objects:
this protocol protects integrity and confidentiality, not availability or
exactly-once semantics. Only idempotent operations are allowed.

Mailbox updates use ETag CAS (POST creation, conditional PUT) with bounded
retry. There are at most 8 entries and 4 MiB of ciphertext per mailbox.
Requests expire after 30 minutes with 2 minutes of clock-skew tolerance.
Responses contain ACK/running/terminal events (last 12) and a service
heartbeat. The client durably saves a receipt before removing its request;
the worker prunes responses after request removal. Private receipts are
retained for 24 hours; no unbounded remote logs. The worker holds a kernel-released single-instance lock, polls at bounded short intervals, updates idle heartbeat every ten seconds, and allows up to two isolated
Lean jobs concurrently (16 GiB aggregate requested RAM) while acknowledging queued requests and handling pings and heartbeats. The configured
compiler must enforce resource bounds and cancellation independently.

If an encrypted object is corrupted or cannot authenticate, stop using
the channel and ask the operator to investigate. Never reset a mailbox or
disable encryption to work around a failure.

Cache aliases refresh independently every two minutes against public upstream.
Only identical definition trees, Lean toolchain, package manifest and Lake configuration
reuse a compiled seed; a changed dependency tree needs a new compiled seed.
