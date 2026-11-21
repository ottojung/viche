#!/usr/bin/env python3
"""Act 32 prospective cost baseline: real source, no invented outcomes."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"government/statistics-trial-meter.py"
s=importlib.util.spec_from_file_location("statistics_trial_meter",TOOL)
mod=importlib.util.module_from_spec(s)
s.loader.exec_module(mod)
VICHE="/var/lib/lubko/wd/viche-seats/branches/executive"
OTHER="/home/lubko/soring-fronts/curator"


def record(n, tokens, directory=VICHE, created=1000):
    return {"directory":directory,"time_created_ms":created,
            "time_updated_ms":max(created,1100+n),
            "tokens":{k:(tokens if k=="tokens_input" else 0) for k in mod.FIELDS}}


def snap(when,cpu,sessions,boot="12345678-1234-1234-1234-123456789abc"):
    return {"schema":mod.SCHEMA,"created_at_utc":str(when),
            "time_epoch_ms":when*1000,
            "cpu":{"cpu_seconds":cpu,"cpu_boot_id":boot,
                   "cpu_source":"proc-stat-host-busy-upper-bound-v1"},
            "sessions":sessions}


class TestTrialMeter(unittest.TestCase):
    def test_token_delta_and_whole_host_upper_bound(self):
        a=snap(10,1000,{"id1":record(1,120)})
        b=snap(20,1090,{"id1":record(3,145),
                          "id2":record(4,19,created=15000)})
        x=mod.compare(a,b)
        self.assertEqual(x["viche_directory_tokens"],44)
        self.assertEqual(x["host_cpu_upper_bound_seconds"],90)
        self.assertEqual(x["new_sessions"],1)
        self.assertIsNone(x["outcome_numerator"])
        self.assertIsNone(x["independent_factual_verdict"])

    def test_missing_sessions_reset_and_reboot_are_errors(self):
        a=snap(10,1000,{"id1":record(1,120)})
        with self.assertRaisesRegex(ValueError,"vanished"):
            mod.compare(a,snap(20,1100,{}))
        with self.assertRaisesRegex(ValueError,"counter reset"):
            mod.compare(a,snap(20,1100,{"id1":record(3,119)}))
        with self.assertRaisesRegex(ValueError,"reboot"):
            mod.compare(a,snap(20,1100,{"id1":record(3,190)},
                boot="87654321-1234-1234-1234-123456789abc"))
        with self.assertRaisesRegex(ValueError,"source incomplete"):
            mod.compare(a,snap(20,1100,{"id1":record(1,120),
                "id2":record(4,40,created=1000)}))

    def test_private_immutable_fsynced_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"attested"/"first.json"
            a=snap(10,1000,{"id":record(1,55)})
            digest=mod.write_new(p,a)
            self.assertEqual(len(digest),64)
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
            self.assertEqual(json.loads(p.read_text()),a)
            with self.assertRaises(FileExistsError):
                mod.write_new(p,snap(11,1001,{}))

    def test_real_sqlite_readonly_prefix_filter_and_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"meter.db"
            with sqlite3.connect(p) as db:
                db.execute("CREATE TABLE session_v2 (id TEXT,directory TEXT,time_created INTEGER,time_updated INTEGER,"+
                           ",".join(k+" INTEGER" for k in mod.FIELDS)+")")
                db.execute("INSERT INTO session_v2 VALUES(?,?,?,?,?,?,?,?,?)",
                           ("viche",VICHE,1000,1001,2,3,4,5,6))
                db.execute("INSERT INTO session_v2 VALUES(?,?,?,?,?,?,?,?,?)",
                           ("other",OTHER,1000,1001,2000,0,0,0,0))
            result,total=mod.sessions(p)
            self.assertEqual(total,2)
            self.assertEqual(list(result),["viche"])
            self.assertEqual(sum(result["viche"]["tokens"].values()),20)
            # A read-only meter cannot silently create or mutate schema.
            with sqlite3.connect(p) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM session_v2").fetchone()[0],2)

    def test_snapshot_db_unavailable_does_not_mean_zero(self):
        with self.assertRaisesRegex(ValueError,"missing"):
            mod.sessions("/does/not/exist/act32-usage.sqlite3")


if __name__=="__main__":
    unittest.main()
