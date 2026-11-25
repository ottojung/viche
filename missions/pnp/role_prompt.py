"""Compatibility entry point; research playbook is the single source of guidance."""
import sys
from pathlib import Path

def instructions(role):
    from missions.pnp.research.playbook import guide
    return guide(role)

def main():
    from missions.pnp.research.roles import main as dispatch
    return dispatch()

if __name__=="__main__":
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    raise SystemExit(main())
