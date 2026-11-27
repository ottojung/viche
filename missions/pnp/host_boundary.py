"""Fail-closed billy-dev host boundary for PnP proof transports.

Authority: Executive delegation of 2026-11-26 after a confirmed deployed
violation. Viche/PnP agent execution, worktrees and proof/check subprocesses
are permitted only on billy-dev. GitHub-hosted Actions CI is a separate host
that the Founder explicitly allows; this module does not touch it.

This is the single source of truth for the refusal contract. It executes
nothing, reads no credentials and inspects no network state. No environment
variable, config file, installed executable or hidden fallback can relax it:
each retired capability calls `refuse()` unconditionally. Legacy entry points
keep their import surface so historical callers fail closed with a clear
machine-readable status and zero spawned subprocesses.

Already generated candidates and receipts are never rewritten. A refusal is
not a mathematical verdict: it must never be read as "false", "unsupported"
or "kernel checked".
"""
import json
import os

ALLOWED_HOST = "billy-dev"
STATUS = "remote_transport_disabled"
EXIT = 9
PYTHONPATH = "/var/lib/lubko/wd/viche"
REASON = (
    "Out-of-host proof generation and check transport is prohibited on "
    "billy-dev under the current authority; no environment variable, fallback "
    "or legacy client may re-enable it. The only permitted Lean route is the "
    "managed compiler from an exact bound workspace: "
    "PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile -- "
    "lake env lean FILE. GitHub-hosted CI remains allowed."
)


class RemoteTransportDisabled(RuntimeError):
    """Raised when a retired out-of-host capability is invoked."""


def refusal(capability=None):
    """Stable machine-readable result for every disabled entry point."""
    out = {"status": STATUS, "reason": REASON}
    if capability:
        out["capability"] = capability
    return out


def refuse(capability=None):
    raise RemoteTransportDisabled(json.dumps(refusal(capability), sort_keys=True))


def print_refusal(capability=None, stream=None):
    (stream or __import__("sys").stdout).write(
        json.dumps(refusal(capability), sort_keys=True) + "\n")


def managed_compile_command(args, light=False):
    """Canonical managed Lean invocation. `args` must begin with lake/lean."""
    cmd = ["python3", "-m", "missions.pnp.compile"]
    if light:
        cmd.append("--light")
    cmd.append("--")
    cmd.extend(args)
    return cmd


def managed_compile_env(base=None):
    """Environment for a managed compile: force the canonical PYTHONPATH."""
    env = dict(os.environ if base is None else base)
    env["PYTHONPATH"] = PYTHONPATH
    return env


def is_managed_compile(argv):
    """Recognise exactly the canonical managed-compile command shape."""
    a = list(argv)
    if len(a) < 5 or a[0] != "python3" or a[1:3] != ["-m", "missions.pnp.compile"]:
        return False
    rest = a[3:]
    if rest[0] == "--light":
        rest = rest[1:]
    if len(rest) < 2 or rest[0] != "--":
        return False
    tail = rest[1:]
    return tail[0] in ("lake", "lean")
