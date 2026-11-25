"""Executive-only dispatch helper for independent research workstreams."""
import argparse
import subprocess
from pathlib import Path

from .. import config
from .playbook import ROLES, guide
from . import adoption

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("role",choices=sorted(ROLES));p.add_argument("--task",default="")
    p.add_argument("--agent");p.add_argument("--cwd",type=Path)
    p.add_argument("--steer",action="store_true",help="replace work at a justified checkpoint")
    a=p.parse_args();text=guide(a.role)+("\nAssigned task: "+a.task if a.task else "")
    if not a.agent:
        print(text);return 0
    if not a.cwd or not a.cwd.is_dir() or not a.task:p.error("explicit task and existing cwd required")
    if Path(config.STATE_ROOT).resolve() == Path("/var/lib/lubko/wd/viche-state/pnp"):
        p.error("staffing controller owns research launches; use its policy and health")
    # Legacy noncanonical fixture entry point.
    did=adoption.planned(a.agent,a.cwd,a.role,text)
    result=subprocess.run(["antonina","agent","run","--id",a.agent,"--cwd",str(a.cwd.resolve()),
                            "--prompt",text,"--detach","--json"]+(["--steer"] if a.steer else []),capture_output=True,text=True)
    if result.returncode==0:
        try:
            if __import__("json").loads(result.stdout).get("state")=="running":adoption.confirmed(did)
        except ValueError:pass
    # Record acknowledgement before writing to a potentially closed output
    # pipe, e.g. an Executive capturing the first few output lines.
    print(result.stdout,end="")
    if result.stderr:print(result.stderr,end="",file=__import__("sys").stderr)
    return result.returncode
if __name__=="__main__":raise SystemExit(main())
