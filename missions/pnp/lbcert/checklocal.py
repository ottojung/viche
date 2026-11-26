"""Run an exact candidate check through the managed compiler in a bound workspace."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .. import assignment, config, focus, state, support, host_boundary


def check(path, module, timeout=900):
    """Compile candidate bytes only when cwd is the active exact bound workspace.

    The source is copied into that workspace's Lean tree, and the canonical
    managed compiler is the only Lean subprocess. No network fallback exists.
    """
    bound = assignment.binding(Path.cwd())
    ws = assignment.workspace(Path.cwd())
    if not bound or not ws:
        return 2, {"status": "bound_workspace_required"}
    gap, lease = bound
    rec = state.load(gap)
    if not rec or rec.get("lease") != lease or not support.active(rec) or not focus.eligible(rec):
        return 2, {"status": "assignment_obsolete"}
    work = ws[1].resolve()
    lean = work / "lean"
    try:
        data = Path(path).read_bytes()
        if not data or len(data) > 512 * 1024:
            return 2, {"status": "invalid_proof_size"}
        if not lean.is_dir() or not (lean / "lean-toolchain").is_file():
            return 2, {"status": "exact_workspace_unavailable"}
        base = subprocess.check_output(["git", "-C", str(work), "rev-parse", "HEAD"],
                                       text=True, timeout=5).strip()
        if rec.get("base_sha") and base != rec["base_sha"]:
            return 2, {"status": "exact_base_mismatch"}
        fd, tmp = tempfile.mkstemp(prefix=".pnp-local-check-", suffix=".lean", dir=str(lean))
        os.close(fd)
        try:
            Path(tmp).write_bytes(data)
            env = host_boundary.managed_compile_env()
            cmd = host_boundary.managed_compile_command(["lake", "env", "lean", Path(tmp).name])
            proc = subprocess.run(cmd, cwd=str(lean), env=env, capture_output=True,
                                  text=True, timeout=timeout)
        finally:
            os.unlink(tmp)
        output = (proc.stdout + "\n" + proc.stderr)[-16000:]
        result = {"status": "ok" if proc.returncode == 0 else "compile_error",
                  "compiled": proc.returncode == 0,
                  "sha256": hashlib.sha256(data).hexdigest(),
                  "checked_base": base, "id": "managed-local", "log": output,
                  "returncode": proc.returncode}
        return (0 if proc.returncode == 0 else 1), result
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return 2, {"status": "managed_compile_unavailable", "detail": str(exc)[-500:]}
