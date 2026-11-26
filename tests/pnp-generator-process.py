"""Regression: child and grandchild die with a timed-out or dead generator."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert import process

def dead(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()[0] == "Z"
    except FileNotFoundError:
        return True

class TestProcess(unittest.TestCase):
    def test_timeout_cleans_grandchild(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d)/"pid"
            code = ("import subprocess,sys,time,pathlib; "
                    "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)']); "
                    "pathlib.Path(sys.argv[1]).write_text(str(p.pid));time.sleep(90)")
            with self.assertRaises(subprocess.TimeoutExpired):
                process.run([sys.executable,"-c",code,str(marker)],timeout=1,
                            capture_output=True)
            pid=int(marker.read_text())
            for _ in range(100):
                if dead(pid):break
                time.sleep(.02)
            self.assertTrue(dead(pid))

    def test_parent_death_cleans_grandchild(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d)/"pid"
            script = Path(d)/"outer.py"
            script.write_text("import sys,os,time\n"
                "from missions.pnp.lbcert import process\n"
                "process.run([sys.executable,'-c',"
                "'import pathlib,os,time,sys;pathlib.Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(90)',"
                "sys.argv[1]],timeout=120)\n")
            env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
            p=subprocess.Popen([sys.executable,str(script),str(marker)],env=env)
            try:
                for _ in range(150):
                    if marker.exists():break
                    time.sleep(.02)
                self.assertTrue(marker.exists())
                pid=int(marker.read_text())
                p.kill();p.wait()
                for _ in range(100):
                    if dead(pid):break
                    time.sleep(.02)
                self.assertTrue(dead(pid))
            finally:
                if p.poll() is None:p.kill();p.wait()

if __name__ == "__main__":unittest.main()
