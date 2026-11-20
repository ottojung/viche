#!/usr/bin/env python3
"""Post public-data barrier: rejection, audit, archive quarantine and liveness."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

POST=Path(__file__).resolve().parents[1]/"government/post.py"

class PostGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/"post.sqlite3"
        self.env=dict(os.environ,VICHE_POST_DB=str(self.db))

    def cli(self,*args,ok=True):
        result=subprocess.run(["python3",str(POST),*args],env=self.env,
                              text=True,capture_output=True,timeout=25)
        if ok:
            self.assertEqual(result.returncode,0,result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode,0,result.stdout)
        return result.stderr

    def send(self,body="Ordinary public message"):
        return self.cli("send","--public","--sender","office-a",
                        "--to","office-b","--subject","Administrative note",
                        "--body",body)

    def test_secrets_rejected_without_echo_and_audited(self):
        sample="sk-"+"A"*32
        error=self.cli("send","--public","--sender","office-a",
            "--to","office-b","--subject","Bad","--body",sample,ok=False)
        self.assertIn("credential-like content",error)
        self.assertNotIn(sample,error)
        self.assertEqual(self.cli("health")["messages"],0)
        with sqlite3.connect(self.db) as db:
            event=db.execute("SELECT action,details FROM events").fetchone()
        self.assertEqual(event[0],"credential-like-content-rejected")
        self.assertNotIn(sample,event[1])
        self.assertEqual(self.send()["delivered"],1)

    def test_credential_like_sources_and_resolutions_rejected(self):
        secret="AKIA"+"A"*16
        err=self.cli("publish","--sender","office-a",
            "--topic","statistics/test","--subject","Data",
            "--kind","observation","--condition","measured daily",
            "--source","file:ref?key="+secret,
            "--body","Measurement",ok=False)
        self.assertNotIn(secret,err)
        self.assertEqual(self.cli("health")["messages"],0)
        message=self.send()["id"]
        err=self.cli("resolve","--office","office-b","--id",message,
                     "--reason","credential="+secret,ok=False)
        self.assertNotIn(secret,err)
        self.assertEqual(self.cli("inbox","--office","office-b")[0]["status"],"new")

    def test_archive_quarantine_masks_all_read_apis(self):
        self.cli("health")
        leaked="Bearer "+"Y"*32
        raw="WARNING Authorization: "+leaked
        with sqlite3.connect(self.db) as db:
            db.execute("""INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       ("legacy","mail","legacy-import","office-b",None,
                        "letter","Sensitive legacy","Copied "+raw,123,
                        "legacy-key",None,0,"normal","[]","[]","","","",""))
            db.execute("""INSERT INTO deliveries(message_id,recipient,status,alert,created_at)
                          VALUES(?,?,'new',0,?)""",("legacy","office-b",123))
            db.commit()
        first=self.cli("archive-scan")
        self.assertEqual(first["newly_quarantined"],1)
        self.assertFalse(first["disk_confidentiality"])
        self.assertEqual(self.cli("archive-scan")["newly_quarantined"],0)
        h=self.cli("health")
        self.assertFalse(h["healthy"])
        self.assertEqual(h["quarantined_messages"],1)
        for entry in (self.cli("inbox","--office","office-b")[0],
                      self.cli("trace","--id","legacy")["message"],
                      self.cli("thread","--id","legacy")["messages"][0],
                      self.cli("search","--text","Sensitive legacy")[0]):
            self.assertTrue(entry["quarantined"])
            self.assertNotIn(leaked,json.dumps(entry))
            self.assertIn("REDACTED",entry["body"])
        self.assertEqual(self.cli("lineage","--id","legacy")["count"],0)
        with sqlite3.connect(self.db) as db:
            original=db.execute("SELECT body FROM messages WHERE id='legacy'").fetchone()[0]
            audit=db.execute("SELECT details FROM events WHERE action LIKE '%quarantined'").fetchone()[0]
        self.assertIn(leaked,original)  # Explicit shared-UID limitation.
        self.assertNotIn(leaked,audit)
        self.assertEqual(self.send()["delivered"],1)  # No global mail outage.

    def test_archive_scan_quarantines_legacy_resolution(self):
        mid=self.send()["id"]
        sample="sk-"+"Z"*35
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE deliveries SET resolution=?,status='resolved' WHERE message_id=?",
                       ("Old unsafe receipt "+sample,mid))
            db.commit()
        self.assertEqual(self.cli("archive-scan")["newly_quarantined"],1)
        entry=self.cli("inbox","--office","office-b")[0]
        self.assertTrue(entry["quarantined"])
        self.assertNotIn(sample,json.dumps(entry))
        details=self.cli("trace","--id",mid)
        self.assertNotIn(sample,json.dumps(details))
        self.assertEqual(self.cli("archive-scan")["newly_quarantined"],0)

    def test_placeholder_examples_do_not_block(self):
        sample="Documentation: password=REDACTED, api_key=PLACEHOLDER"
        self.assertEqual(self.send(sample)["delivered"],1)
        path=Path(self.tmp.name)/"body.txt"
        path.write_text("-----BEGIN PRIVATE KEY-----")
        err=self.cli("send","--public","--sender","office-a","--to","office-b",
                     "--subject","Bad","--body-file",str(path),ok=False)
        self.assertIn("private-key",err)
        self.assertEqual(self.cli("health")["messages"],1)

if __name__=="__main__":
    unittest.main()
