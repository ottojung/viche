"""Optional bounded C synthesis. Never mutates desk state or claims a proof."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

# Process-private executable: never trust a preexisting binary in shared state.
@lru_cache(maxsize=1)
def executable():
    cc = shutil.which("cc")
    if cc is None:
        return None
    tmp = tempfile.TemporaryDirectory(prefix="pnp-anneal-")
    exe = Path(tmp.name)/"anneal"
    try:
        subprocess.run([cc,"-O3",str(Path(__file__).with_suffix(".c")),"-lm","-o",str(exe)],
                       check=True,timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return tmp,exe
    except (OSError,subprocess.SubprocessError):
        tmp.cleanup()
        return None


def search(problem,gen,seconds=.5):
    n,rows,target = gen.domain(problem)
    k=problem[3]
    if not (1<=len(rows)<=64 and 1<=n<=32 and 1<=k<=31 and n+k<64 and 0<seconds<=5):
        return None
    compiled=executable()
    if compiled is None:
        return None
    _,exe=compiled
    seed=int.from_bytes(hashlib.sha256(repr(problem).encode()).digest()[:8],"big") or 1
    inp=f"{n} {len(rows)} {k} {int(problem[-1]=='FanInTwo')} {target}\n"
    inp+=" ".join(map(str,gen.input_tables(n,rows)))+"\n"
    try:
        r=subprocess.run([str(exe),str(seconds),str(seed)],input=inp,text=True,capture_output=True,timeout=seconds+2)
        if r.returncode or len(r.stdout)>16384:
            return None
        sol=json.loads(r.stdout)["solution"]
        # Independently check every promise row, operation, and wire.
        if not gen.valid(problem,sol):
            return None
        compact=gen.compact(problem,*sol)
        return compact if compact and gen.valid(problem,compact) else sol
    except (OSError,subprocess.SubprocessError,ValueError,KeyError,TypeError,AssertionError,IndexError):
        return None
