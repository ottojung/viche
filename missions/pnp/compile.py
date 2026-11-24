"""One supervised entry point for research and publisher Lean compilation."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys

from . import build_control as control, watchdog, state, assignment, evidence


def command(args):
    # No use of the upstream mkdir queue from managed builds. Both research
    # and publisher share the kernel locks above; retain the Lake artifact cache.
    tool = args[0] if args else ""
    if tool not in ("lake", "lean"):
        raise ValueError("expected lake or lean")
    if tool == "lake" and (len(args) < 2 or args[1] not in ("build", "env", "lean")):
        raise ValueError("expected lake build, lake env lean or lake lean")
    if args[:2] == ["lake", "env"] and (len(args) < 3 or args[2] != "lean"):
        raise ValueError("lake env must run lean")
    return [os.path.join(os.path.expanduser("~/.elan/bin"), tool)] + args[1:]


def run(args, cwd=None, heavy=True, publication=False,
        output=None, inherited=()):
    argv = command(args)
    # Avoid inheriting a researcher's custom path/options in publication.
    env = {k: v for k, v in os.environ.items()
           if not ((publication or os.environ.get("PNP_EVIDENCE_BUILD") == "1") and (k.startswith("LEAN_") or k.startswith("LAKE_")
                                    or k in ("PEQUALNP_IN_QUEUE", "PEQUALNP_REAL_LAKE")))}
    env.update(PNP_MANAGED_COMPILER="1", LEAN_NUM_THREADS="1", LAKE_ARTIFACT_CACHE="true",
               LAKE_RESTORE_ARTIFACTS="true",
               LAKE_CACHE_DIR=os.path.expanduser("~/.pequalnp/lake-cache"))
    # Admission is bounded; once admitted, a useful build has no wall-clock deadline.
    wait = 600 if publication else 15
    with control.slot(timeout=wait, heavy=heavy, publication=publication) as fds:
        initial = control.headroom()
        oom = control.oom_count()
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=output,
                                stderr=output, start_new_session=True,
                                pass_fds=inherited + fds)
        try:
            while True:
                if control.obsolete():
                    raise control.BuildDeferred("compilation assignment ended")
                reason = control.memory_reason(proc.pid, heavy=heavy)
                if reason:
                    required = (initial or control.HEAVY_MIN + control.RESERVE) + control.GIB // 2
                    raise control.MemoryDeferred(reason, required)
                try:
                    code = proc.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    continue
                after = control.oom_count()
                if code and (code in (-signal.SIGKILL, 137) or
                             (oom is not None and after is not None and after > oom)):
                    required = (initial or control.HEAVY_MIN + control.RESERVE) + control.GIB // 2
                    raise control.MemoryDeferred("compiler killed or host OOM during build", required)
                return code
        except BaseException:
            # Only the child group created by this invocation.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--light", action="store_true")
    p.add_argument("--gap")
    p.add_argument("--lease")
    p.add_argument("args", nargs=argparse.REMAINDER)
    ns = p.parse_args(argv)
    local = assignment.workspace(Path.cwd())
    if local or ns.gap or ns.lease:
        try:
            gap, lease = assignment.resolve(ns.gap, ns.lease)
            rec = state.load(gap)
            if not isinstance(rec, dict) or rec.get("lease") != lease:
                raise ValueError("assignment unavailable or superseded")
            os.environ["PNP_PUBLISH_GAP"] = gap
            os.environ["PNP_PUBLISH_LEASE"] = lease
        except (OSError, ValueError) as exc:
            print("RESOURCE DEFERRED:", exc, file=sys.stderr)
            return 75
    args = ns.args[1:] if ns.args[:1] == ["--"] else ns.args
    from . import tools
    tools.record("compile-light" if ns.light else "compile-full")
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        bound = assignment.binding(Path.cwd())
        rec = state.load(bound[0]) if bound else None
        before = evidence.snapshot(rec, Path.cwd(), args) if rec and not ns.light else None
        if before:
            os.environ["PNP_EVIDENCE_BUILD"] = "1"
        code = run(args, heavy=not ns.light)
        if code == 0 and before:
            try:
                evidence.record(rec, before, evidence.snapshot(rec, Path.cwd(), args))
            except (OSError, ValueError) as exc:
                print("build evidence unavailable:", exc, file=sys.stderr)
        return code
    except (control.BuildDeferred, KeyboardInterrupt, OSError) as exc:
        print("RESOURCE DEFERRED:", exc, file=sys.stderr, flush=True)
        return 75
    except ValueError as exc:
        p.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
