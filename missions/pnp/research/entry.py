"""Installed agent command; prefer canonical code when integration lands."""
import importlib
import sys
from pathlib import Path
def main():
    root=Path("/var/lib/lubko/wd/viche")
    sys.path.insert(0,str(root))
    import missions.pnp
    if not (root/"missions/pnp/research/knowledge.py").is_file():
        missions.pnp.__path__.append(str(Path(__file__).resolve().parent.parent))
    commands={"knowledge":"knowledge","obligations":"obligations","yield":"yield_model","star":"star","dispatch":"roles"}
    if len(sys.argv)<2 or sys.argv[1] not in commands:
        print("pnp-research knowledge|obligations|yield|star|dispatch --help")
        return 0 if len(sys.argv)==1 or sys.argv[1]=="--help" else 2
    command=commands[sys.argv.pop(1)]
    if command=="yield_model":
        import json
        print(json.dumps(importlib.import_module("missions.pnp.research."+command).view(),indent=2))
        return 0
    return importlib.import_module("missions.pnp.research."+command).main()
if __name__=="__main__":raise SystemExit(main())
