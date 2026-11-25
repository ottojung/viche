"""Installed agent command; prefer canonical code when integration lands."""
import importlib
import sys
import time
from pathlib import Path
def main():
    root=Path("/var/lib/lubko/wd/viche")
    sys.path.insert(0,str(root))
    import missions.pnp
    canonical=root/"missions/pnp/research"
    # A partial canonical rollout must not shadow the complete installed CLI.
    required=("entry.py","playbook.py","async_check.py","adoption.py","certificate.py","dnf_reflection.py")
    if not all((canonical/f).is_file() for f in required):
        missions.pnp.__path__.insert(0,str(Path(__file__).resolve().parent.parent))
    commands={"knowledge":"knowledge","obligations":"obligations","yield":"yield_model","star":"star","dispatch":"roles","start":"playbook","adoption":"adoption","guide":"playbook","certificate":"certificate"}
    if len(sys.argv)<2 or sys.argv[1] not in commands:
        print("pnp-research start|guide|knowledge|obligations|yield|star|certificate|adoption|dispatch --help")
        return 0 if len(sys.argv)==1 or sys.argv[1]=="--help" else 2
    from missions.pnp.research import adoption
    action=adoption.command_name(sys.argv);started=time.time();code=1
    command=commands[sys.argv.pop(1)]
    try:
        if command=="yield_model":
            import json
            print(json.dumps(importlib.import_module("missions.pnp.research."+command).view(),indent=2))
            code=0
        elif action in ("guide","guide help"):
            code=importlib.import_module("missions.pnp.research.playbook").guide_main() or 0
        else:code=importlib.import_module("missions.pnp.research."+command).main() or 0
        return code
    except (OSError,ValueError,KeyError) as exc:
        print("pnp-research:",str(exc),file=sys.stderr);code=2;return code
    except SystemExit as exc:
        code=exc.code if isinstance(exc.code,int) else 1
        raise
    finally:
        adoption.record(action,started,code)
if __name__=="__main__":raise SystemExit(main())
