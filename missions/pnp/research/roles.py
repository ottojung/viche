"""Executive-only dispatch helper for independent research workstreams."""
import argparse
import subprocess
from pathlib import Path

from .playbook import ROLES, guide
from . import adoption

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("role",choices=sorted(ROLES));p.add_argument("--task",default="")
    p.add_argument("--agent");p.add_argument("--cwd",type=Path)
    a=p.parse_args();text=guide(a.role)+("\nAssigned task: "+a.task if a.task else "")
    if not a.agent:
        print(text);return 0
    if not a.cwd or not a.cwd.is_dir() or not a.task:p.error("explicit task and existing cwd required")
    # Existing agents are created and selected only by Executive.
    did=adoption.planned(a.agent,a.cwd,a.role,text)
    result=subprocess.run(["antonina","agent","run","--id",a.agent,"--cwd",str(a.cwd.resolve()),
                            "--prompt",text,"--detach","--json"],capture_output=True,text=True)
    print(result.stdout,end="")
    if result.stderr:print(result.stderr,end="",file=__import__("sys").stderr)
    if result.returncode==0:
        try:
            if __import__("json").loads(result.stdout).get("state")=="running":adoption.confirmed(did)
        except ValueError:pass
    return result.returncode
if __name__=="__main__":raise SystemExit(main())
