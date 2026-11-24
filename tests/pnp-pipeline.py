#!/usr/bin/env python3
"""Offline, mocked acceptance tests for the PnP subsystem.

No real desk claim, Git push or upstream PR is made here; real external
effects are exercised only after these tests are green.
"""
import hashlib
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
TMP = tempfile.mkdtemp(prefix="pnp-tests-")
os.environ["PNP_STATE_ROOT"] = os.path.join(TMP, "state")

from missions.pnp import config, desk, gitctl, github, publish, reconcile, state, validate  # noqa: E402

GAP = "L-meta-582"
PATH = "lean/PEqualNP/Outside/L_meta_582.lean"
MODULE = "PEqualNP.Outside.L_meta_582"
STATEMENT = "1 + 1 = 2"
SHA = "a" * 40
GOOD = """import Mathlib

namespace PEqualNP.Outside.L_meta_582
lemma helper : 1 = 1 := rfl
end PEqualNP.Outside.L_meta_582

theorem PEqualNP.Outside.L_meta_582 : 1 + 1 = 2 := by
  norm_num
"""


def gap_meta():
    return {"id": GAP, "file": PATH, "module": MODULE,
            "statement": STATEMENT, "imports": []}


def new_state(status="CANDIDATE_READY", **extra):
    fields = dict(state="CANDIDATE_READY", statement=STATEMENT,
                  module=MODULE, path=PATH, imports=[],
                  lease="lease-1", lease_expires_at=time.time() + 1200,
                  candidate_digest=hashlib.sha256(GOOD.encode()).hexdigest())
    fields.update(extra)
    fields["state"] = status
    return state.create(GAP, **fields)


def candidate_file(content=GOOD):
    p = os.path.join(TMP, "candidate.lean")
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


class FakeDesk:
    def __init__(self, beat=200):
        self.beat_status = beat
        self.beats = []
        self.releases = []

    def docs(self, refresh=False):
        return "join.txt"

    def status(self):
        return {"open_gaps": 1, "gaps": [{"id": GAP}]}

    def beat(self, lease):
        self.beats.append(lease)
        return self.beat_status

    def release(self, lease, reason, program=None):
        self.releases.append((lease, reason))
        return {}


class FakeGit:
    def __init__(self, remote=None, build_ok=True):
        self.remote = remote
        self.build_ok = build_ok
        self.calls = []

    def ensure_mirror(self):
        return "base1"

    def fresh_worktree(self, gid, base, branch):
        self.calls.append(("worktree", gid, branch))
        return os.path.join(TMP, "wt")

    def pin_candidate(self, wt, path, data):
        self.calls.append(("pin", path))

    def build(self, wt, module, statement, runner=None):
        return self.build_ok, "ok" if self.build_ok else "boom"

    def signed_commit(self, wt, base, message, signer=None):
        self.calls.append(("commit", message))
        return SHA

    def remote_branch_sha(self, branch):
        return self.remote

    def push_branch(self, branch, pusher=None):
        self.calls.append(("push", branch))
        return SHA

    def all_new_commits_signed(self, wt, base):
        return True

    def new_commits(self, wt, base):
        return [SHA]


class FakeGH:
    def __init__(self, verified=True, existing=None):
        self.verified = verified
        self.existing = existing
        self.created = 0

    def identity(self):
        return "renamed-contributor"

    def repository_id(self, name):
        return config.UPSTREAM_ID if name in ("old-owner/proofs", "new-owner/proofs") else 999

    def commit_verification(self, sha):
        return {"sha": sha, "verified": self.verified,
                "name": config.AUTHOR_NAME, "email": config.AUTHOR_EMAIL}

    def pr_exists_for(self, branch, gap, api=None):
        return self.existing

    def create_pr(self, branch, gap):
        self.created += 1
        return "123"

    def validate_created(self, number, sha, path, expected_commits=None):
        return {"url": "https://example.test/pr/123"}, []


def fresh(gap=GAP):
    """Isolate each test's state directory."""
    state_path = state.state_path(gap)
    if os.path.exists(state_path):
        os.unlink(state_path)
    d = state.gap_dir(gap)
    events = state.events_path(gap)
    if os.path.exists(events):
        os.unlink(events)


class TestValidate(unittest.TestCase):
    def test_good_candidate(self):
        self.assertEqual(len(validate.validate(gap_meta(), GOOD.encode())), 64)

    def test_rejections(self):
        bad = {
            "sorry": GOOD.replace("norm_num", "sorry"),
            "axiom": "axiom foo : 1 = 2\n" + GOOD,
            "native_decide": GOOD.replace("norm_num", "native_decide"),
            "hash": GOOD + "\n#eval 1\n",
            "quotes": GOOD.replace("1 = 1 := rfl", '1 = 1 := by exact "x"'),
            "wrong statement": GOOD.replace("1 + 1 = 2", "1 + 1 = 3"),
            "extra theorem": GOOD + "\ntheorem other : True := by trivial\n",
            "bad import": GOOD.replace("import Mathlib", "import Mathlib\nimport Evil"),
            "bad option": GOOD.replace("theorem", "set_option pp.all true in\ntheorem"),
            "bad namespace": GOOD.replace("namespace PEqualNP.Outside.L_meta_582",
                                           "namespace Other"),
        }
        for name, content in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(validate.InvalidCandidate):
                    validate.validate(gap_meta(), content.encode())

    def test_size_and_encoding(self):
        with self.assertRaises(validate.InvalidCandidate):
            validate.validate(gap_meta(), GOOD.encode() + b"x" * (513 * 1024))
        with self.assertRaises(validate.InvalidCandidate):
            validate.validate(gap_meta(), b"import Mathlib\n\xff")

    def test_bad_gap_id(self):
        m = gap_meta()
        m["id"] = "not a gap; rm -rf /"
        with self.assertRaises(validate.InvalidCandidate):
            validate.validate(m, GOOD.encode())


class TestState(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_transitions_events_and_intent(self):
        new_state()
        self.assertEqual(state.load(GAP)["state"], "CANDIDATE_READY")
        state.intent(GAP, "push", {"sha": SHA})
        self.assertEqual(state.load(GAP)["intent"]["what"], "push")
        state.clear_intent(GAP)
        self.assertIsNone(state.load(GAP)["intent"])
        state.transition(GAP, "LOCAL_CHECKED")
        state.transition(GAP, "SIGNED", commit_sha=SHA)
        with self.assertRaises(ValueError):
            state.transition(GAP, "RESEARCHING")
        with open(state.events_path(GAP), encoding="utf-8") as f:
            kinds = [__import__("json").loads(l)["kind"] for l in f]
        self.assertIn("state", kinds)
        self.assertIn("update", kinds)

    def test_reacquire_rejects_active_states(self):
        new_state("LEASED")
        with self.assertRaises(ValueError):
            state.reacquire(GAP, lease="fresh")


class TestPublish(unittest.TestCase):
    def setUp(self):
        fresh()
        self.file = candidate_file()

    def test_success(self):
        new_state()
        d, g, h = FakeDesk(), FakeGit(), FakeGH()
        r = publish.publish(GAP, self.file, desk=d, git=g, gh=h)
        self.assertEqual(r["pr"], 123)
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        self.assertEqual(h.created, 1)
        self.assertEqual(d.releases, [("lease-1", "submitted")])
        self.assertIn(("push", config.branch_for(GAP)), g.calls)

    def test_restart_after_push_does_not_duplicate(self):
        new_state("PUSHED", commit_sha=SHA, base_sha="base1",
                  branch=config.branch_for(GAP))
        d, g, h = FakeDesk(), FakeGit(remote=SHA), FakeGH(existing="123")
        r = publish.publish(GAP, self.file, desk=d, git=g, gh=h)
        self.assertEqual(r["pr"], 123)
        self.assertEqual(h.created, 0)
        self.assertNotIn(("push", config.branch_for(GAP)), g.calls)

    def test_pr_creation_network_error_keeps_recoverable_push(self):
        class Outage(FakeGH):
            def create_pr(self, branch, gap):
                raise RuntimeError("temporary GitHub outage")
        new_state()
        g = FakeGit()
        gh = Outage()
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, candidate_file(), desk=FakeDesk(),
                            git=g, gh=gh)
        rec = state.load(GAP)
        self.assertEqual(rec["state"], "PUSHED")
        self.assertIsNone(rec["pr_number"])
        self.assertEqual(rec["commit_sha"], SHA)

    def test_existing_pr_is_reused(self):
        new_state("LOCAL_CHECKED")
        g, h = FakeGit(remote=SHA), FakeGH(existing="77")
        r = publish.publish(GAP, self.file, desk=FakeDesk(), git=g, gh=h)
        self.assertEqual(r["pr"], 77)
        self.assertEqual(h.created, 0)

    def test_compilation_not_a_publication_gate(self):
        new_state()
        g, h = FakeGit(build_ok=False), FakeGH()
        with mock.patch.object(g, "build", side_effect=AssertionError("pre-PR build")):
            r = publish.publish(GAP, self.file, desk=FakeDesk(), git=g, gh=h)
        self.assertEqual(r["pr"], 123)
        self.assertEqual(state.load(GAP)["local_check_status"], "pending")
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")

    def test_exact_evidence_skips_postcheck(self):
        from missions.pnp import evidence
        rec = new_state()
        state.update(GAP, build_evidence={
            "lease": rec["lease"], "base": "base1", "digest": rec["candidate_digest"],
            "module": MODULE, "path": PATH, "statement": STATEMENT, "imports": []})
        self.assertTrue(evidence.matching(state.load(GAP), rec["candidate_digest"], "base1"))
        self.assertFalse(evidence.matching(state.load(GAP), "changed", "base1"))
        self.assertFalse(evidence.matching(state.load(GAP), rec["candidate_digest"], "base2"))
        publish.publish(GAP, self.file, desk=FakeDesk(), git=FakeGit(), gh=FakeGH())
        self.assertEqual(state.load(GAP)["local_check_status"], "passed")

    def test_bad_candidate_stops_before_git(self):
        new_state()
        g = FakeGit()
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, candidate_file(GOOD.replace("norm_num", "sorry")),
                            desk=FakeDesk(), git=g, gh=FakeGH())
        self.assertNotIn(("push", config.branch_for(GAP)), g.calls)
        self.assertEqual(state.load(GAP)["state"], "RESEARCHING")

    def test_lease_410_stops(self):
        new_state()
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, self.file, desk=FakeDesk(beat=410),
                            git=FakeGit(), gh=FakeGH())
        self.assertEqual(state.load(GAP)["state"], "STALE")

    def test_failed_local_check_can_queue_same_pr_correction(self):
        from missions.pnp import jobs
        new_state("PR_OPEN", local_check_status="failed", pr_number=123,
                  pr_url="u", commit_sha=SHA)
        corrected = candidate_file(GOOD.replace("norm_num", "decide"))
        with mock.patch.object(jobs, "launch") as launch:
            jobs.submit(GAP, corrected)
            launch.assert_called_once()
        rec = state.load(GAP)
        self.assertEqual(rec["state"], "REJECTED")
        self.assertEqual(rec["pr_number"], 123)
        self.assertEqual(rec["queued_lease"], "lease-1")

    def test_correction_uses_same_pr_and_can_resume(self):
        new_state("REJECTED", pr_number=123, pr_url="u", commit_sha=SHA,
                  base_sha="base1", branch=config.branch_for(GAP))
        new_sha = "b" * 40
        class CorrectionGit(FakeGit):
            def pin_candidate(self, wt, path, data, correction=False):
                self.calls.append(("pin", correction))
            def signed_commit(self, wt, base, message, signer=None, correction=False):
                self.calls.append(("commit", correction))
                return new_sha
            def new_commits(self, wt, base):
                return [SHA, new_sha]
            def push_branch(self, branch, pusher=None):
                self.remote = new_sha
                return new_sha
        g = CorrectionGit(remote=SHA)
        h = FakeGH()
        h.get_pr = lambda n: {"state": "open", "head_sha": g.remote}
        h.commit_verification = lambda sha: {"sha": sha, "verified": True,
            "name": config.AUTHOR_NAME, "email": config.AUTHOR_EMAIL}
        h.validate_created = lambda n, sha, path, expected_commits=None: (
            {"url": "u"}, [] if expected_commits == [SHA, new_sha] else ["wrong range"])
        d = FakeDesk()
        r = publish.publish(GAP, candidate_file(GOOD.replace("norm_num", "decide")),
                            desk=d, git=g, gh=h)
        self.assertEqual(r["pr"], 123)
        self.assertEqual(h.created, 0)
        self.assertEqual(d.releases, [])
        self.assertEqual(state.load(GAP)["commit_sha"], new_sha)
        self.assertEqual(state.load(GAP)["local_check_status"], "pending")

    def test_gap_settled_during_build_never_pushes(self):
        new_state()
        d, g, h = FakeDesk(), FakeGit(), FakeGH()
        def beat(lease):
            d.beats.append(lease)
            return 200 if len(d.beats) == 1 else 410
        d.beat = beat
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, self.file, desk=d, git=g, gh=h)
        self.assertEqual(state.load(GAP)["state"], "STALE")
        self.assertEqual(h.created, 0)
        self.assertFalse(any(c[0] == "push" for c in g.calls))

    def test_confirmed_stale_reply_does_not_touch_new_lease(self):
        new_state("LEASED")
        self.assertFalse(state.stale_lease(GAP, "old-lease", "old reply"))
        self.assertEqual(state.load(GAP)["state"], "LEASED")

    def test_partial_frontier_does_not_invalidate_live_assignment(self):
        new_state("LEASED")
        d = FakeDesk(beat=410)
        reconcile.reconcile_gap(GAP, desk=d, git=FakeGit(), gh=FakeGH(),
                                observed={"complete": False, "gaps": {}})
        self.assertEqual(state.load(GAP)["state"], "LEASED")
        self.assertEqual(d.beats, [])
        reconcile.reconcile_gap(GAP, desk=d, git=FakeGit(), gh=FakeGH(),
                                observed={"complete": True, "gaps": {}})
        self.assertEqual(state.load(GAP)["state"], "STALE")

    def test_github_verification_false_means_no_pr(self):
        new_state()
        h = FakeGH(verified=False)
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, self.file, desk=FakeDesk(),
                            git=FakeGit(), gh=h)
        self.assertEqual(h.created, 0)
        self.assertEqual(state.load(GAP)["state"], "PUSHED")


class TestSignatureFields(unittest.TestCase):
    def good(self, sig="U"):
        return [sig, config.SIGNING_KEY.rstrip("!"), config.AUTHOR_NAME,
                config.AUTHOR_EMAIL, config.AUTHOR_NAME, config.AUTHOR_EMAIL]

    def test_accepts_good_and_locally_untrusted(self):
        gitctl.check_commit_fields(self.good("G"))
        gitctl.check_commit_fields(self.good("U"))

    def test_rejects_wrong_key_author_committer_and_bad_signature(self):
        for fmt in ([self.good()[0], "AAAAAAAA", *self.good()[2:]],
                    [self.good()[0], self.good()[1], "Someone",
                     config.AUTHOR_EMAIL, *self.good()[4:]],
                    [self.good()[0], self.good()[1], *self.good()[2:4],
                     "Someone", config.AUTHOR_EMAIL],
                    self.good("N")):
            with self.subTest(fmt=fmt):
                with self.assertRaises(gitctl.GitError):
                    gitctl.check_commit_fields(fmt)


class TestGitHubValidation(unittest.TestCase):
    def test_renamed_account_and_impostor(self):
        import json
        with mock.patch.object(github, "gh", return_value=json.dumps({
            "id": config.CONTRIBUTOR_ID, "login": "new-login"})):
            self.assertEqual(github.identity(), "new-login")
        with mock.patch.object(github, "gh", return_value=json.dumps({
            "id": 999, "login": config.DESK_HANDLE})):
            with self.assertRaises(github.GitHubError):
                github.identity()

    def test_discover_repository_by_id_not_name(self):
        import json
        with mock.patch.object(github, "gh", return_value=json.dumps({
            "id": config.UPSTREAM_ID, "full_name": "future-owner/future-name"})) as call:
            self.assertEqual(github.repository_name(config.UPSTREAM_ID), "future-owner/future-name")
            self.assertEqual(call.call_args.args[1], "repositories/" + str(config.UPSTREAM_ID))
        with mock.patch.object(github, "gh", return_value=json.dumps({
            "id": config.FORK_ID, "full_name": "other/proofs", "owner_id": 999})):
            with self.assertRaises(github.GitHubError):
                github.repository_name(config.FORK_ID)


    def test_repository_rename_and_identity(self):
        pr = {"author": "renamed-contributor", "author_id": config.CONTRIBUTOR_ID, "head_repo": "renamed-contributor/proofs",
              "head_repo_id": config.FORK_ID, "base_repo": "renamed/project",
              "base_repo_id": config.UPSTREAM_ID, "head_sha": SHA, "base_ref": "main"}
        with mock.patch.object(github, "get_pr", return_value=pr), \
             mock.patch.object(github, "pr_files", return_value=[PATH]), \
             mock.patch.object(github, "pr_commits", return_value=[SHA]), \
             mock.patch.object(github, "commit_verification", return_value={
                 "verified": True, "name": config.AUTHOR_NAME, "email": config.AUTHOR_EMAIL}):
            self.assertEqual(github.validate_created(1, SHA, PATH)[1], [])
            pr.update(base_repo="new-owner/proofs", base_repo_id=999)
            self.assertIn("base repo is not upstream", github.validate_created(1, SHA, PATH)[1])

    def test_post_create_checks(self):
        pr = {"number": 1, "author": "renamed-contributor", "author_id": config.CONTRIBUTOR_ID,
              "head_repo": "renamed-contributor/proofs", "base_repo": "new-owner/proofs",
              "head_repo_id": config.FORK_ID, "base_repo_id": config.UPSTREAM_ID,
              "head_sha": SHA,
              "base_ref": "main", "url": "u"}
        with mock.patch.object(github, "get_pr", return_value=pr), \
             mock.patch.object(github, "pr_files", return_value=[PATH]), \
             mock.patch.object(github, "pr_commits", return_value=[SHA]), \
             mock.patch.object(github, "commit_verification",
                               return_value={"verified": True,
                                             "name": config.AUTHOR_NAME,
                                             "email": config.AUTHOR_EMAIL}):
            got, problems = github.validate_created(1, SHA, PATH)
            self.assertEqual(problems, [])
        with mock.patch.object(github, "get_pr", return_value=pr), \
             mock.patch.object(github, "pr_files", return_value=[PATH, "x"]), \
             mock.patch.object(github, "pr_commits", return_value=[SHA]), \
             mock.patch.object(github, "commit_verification",
                               return_value={"verified": False,
                                             "name": config.AUTHOR_NAME,
                                             "email": config.AUTHOR_EMAIL}):
            _, problems = github.validate_created(1, SHA, PATH)
            self.assertEqual(len(problems), 2)


class TestCli(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_submit_snapshots_and_launches_without_agent_git(self):
        from missions.pnp import cli, jobs
        new_state("LEASED")
        seen = []
        def launch(gap_id, fd):
            seen.append((gap_id, state.load(gap_id)["state"]))
        with mock.patch.object(jobs, "launch", side_effect=launch):
            self.assertEqual(cli.cmd_submit(
                type("Args", (), {"gap": GAP, "candidate": candidate_file()})()), 0)
            self.assertEqual(seen, [(GAP, "CANDIDATE_READY")])
            self.assertTrue(jobs.resume(GAP))
        with open(jobs.candidate_path(GAP)) as f:
            self.assertEqual(f.read(), GOOD)
        self.assertEqual(state.load(GAP)["queued_lease"], "lease-1")

    def test_superseded_workspace_cannot_queue_candidate(self):
        from missions.pnp import jobs, publish
        new_state("LEASED")
        with mock.patch.object(jobs, "launch") as launch:
            with self.assertRaises(publish.StopPublish):
                jobs.submit(GAP, candidate_file(), expected_lease="old-lease")
            launch.assert_not_called()
        self.assertEqual(state.load(GAP)["state"], "LEASED")
        self.assertIsNone(state.load(GAP).get("queued_lease"))

    def test_publication_retry_backoff_preserves_candidate(self):
        from missions.pnp import jobs
        new_state("LEASED")
        with mock.patch.object(jobs, "launch"):
            jobs.submit(GAP, candidate_file())
        jobs.defer(GAP, "old-lease")
        self.assertIsNone(state.load(GAP).get("publisher_retry_at"))
        jobs.defer(GAP, "lease-1")
        rec = state.load(GAP)
        self.assertEqual(rec["publisher_failures"], 1)
        self.assertGreater(rec["publisher_retry_at"], time.time())
        with mock.patch.object(jobs, "launch") as launch:
            self.assertTrue(jobs.resume(GAP))
            launch.assert_not_called()
        self.assertTrue(os.path.isfile(jobs.candidate_path(GAP)))
        self.assertEqual(rec["state"], "CANDIDATE_READY")

    def test_concurrent_publisher_lock_prevents_duplicate_launch(self):
        from missions.pnp import jobs
        new_state("LEASED")
        fd = jobs.claim(GAP)
        try:
            with mock.patch.object(jobs, "launch") as launch:
                self.assertEqual(jobs.submit(GAP, candidate_file())["status"],
                                 "publishing")
                launch.assert_not_called()
        finally:
            os.close(fd)

    def test_reacquire_adopts_fresh_lease_without_releasing(self):
        """A re-offered released/stale gap must be re-leased, not handed back.

        Releasing with 'other' re-arms the desk's one-hour cooldown and the
        ten-minute step rate limit; churning workers used to lock the handle
        out of the desk entirely.
        """
        from missions.pnp import cli
        args = type("Args", (), {"hard": False, "another": False})()
        answer = {"gap": gap_meta(), "lease": "fresh-lease"}
        for previous in ("RELEASED", "STALE"):
            with self.subTest(previous=previous):
                fresh()
                new_state(previous, lease="old-lease",
                          failure_reason="out_of_time",
                          base_sha="old-base", branch="pnp/old",
                          worktree="/tmp/old-wt", commit_sha="old-sha",
                          pr_number=7, pr_url="https://old/pr/7",
                          external_verdict="REJECTED")
                fake = FakeDesk()
                fake._next_gap = lambda **kw: answer
                with mock.patch.object(cli.desk_mod, "Desk",
                                       return_value=fake):
                    self.assertEqual(cli.cmd_acquire(args), 0)
                # Crucially, no 'other'/'out_of_time' release -> no cooldown.
                self.assertEqual(fake.releases, [])
                rec = state.load(GAP)
                self.assertEqual(rec["state"], "LEASED")
                self.assertEqual(rec["lease"], "fresh-lease")
                self.assertIsNone(rec["failure_reason"])
                # Reviewer finding: stale publish artifacts must be cleared so
                # a fresh candidate can be checked and submitted without a
                # false "candidate digest changed since local check" FAULT.
                for stale in ("candidate_digest", "base_sha", "branch",
                              "worktree", "commit_sha", "pr_number",
                              "pr_url", "external_verdict"):
                    self.assertIsNone(rec[stale], stale)

    def test_active_lease_duplicate_is_not_released_into_cooldown(self):
        from missions.pnp import cli
        fresh()
        new_state("RESEARCHING", lease="active-lease")
        fake = FakeDesk()
        fake._next_gap = lambda **kw: {"gap": gap_meta(),
                                      "lease": "spare-lease"}
        args = type("Args", (), {"hard": False, "another": False})()
        with mock.patch.object(cli.desk_mod, "Desk", return_value=fake):
            self.assertEqual(cli.cmd_acquire(args), 1)
        self.assertEqual(fake.releases, [])
        self.assertEqual(state.load(GAP)["state"], "RESEARCHING")
        self.assertEqual(state.load(GAP)["lease"], "active-lease")


def verdict_comment(sha, verdict, author="renamed-checker", date="2026"):
    return {"author": author, "author_id": config.CHECKER_ID if author != "other" else 999, "created_at": date,
            "body": "Checked on the base repository at commit `%s`.\n\n**%s (checker exit 0)**\n\nRun: https://github.com/old-owner/proofs/actions/runs/123" % (sha[:10], verdict)}


def owned_pr_identity():
    return {"author_id": config.CONTRIBUTOR_ID, "head_repo_id": config.FORK_ID,
            "base_repo_id": config.UPSTREAM_ID, "base_ref": config.BASE_REF,
            "head_ref": config.branch_for(GAP), "title": GAP}


class TestReconcile(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_pushed_to_accepted(self):
        new_state("PUSHED", commit_sha=SHA, base_sha="base1",
                  branch=config.branch_for(GAP))
        gh = FakeGH(existing="123")
        gh.get_pr = lambda n: {**owned_pr_identity(), "url": "u", "number": n, "head_sha": SHA, "merged": True}
        gh.pr_comments = lambda n: [verdict_comment(SHA, "ACCEPTED")]
        g = FakeGit(remote=SHA)
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=g)
        self.assertEqual(state.load(GAP)["state"], "ACCEPTED")
        self.assertEqual(r["state"], "ACCEPTED")

    def test_fault_adopts_existing_validated_pr_without_duplicate(self):
        new_state("FAULT", commit_sha=SHA, branch=config.branch_for(GAP),
                  queued_lease="lease-1", expected_commits=[SHA])
        gh = FakeGH(existing=8143)
        gh.get_pr = lambda n: {**owned_pr_identity(), "url": "u", "head_sha": SHA, "state": "open"}
        gh.pr_comments = lambda n: []
        d = FakeDesk()
        reconcile.reconcile_gap(GAP, desk=d, gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        self.assertEqual(state.load(GAP)["pr_number"], 8143)
        self.assertIsNone(state.load(GAP)["queued_lease"])
        self.assertEqual(gh.created, 0)
        self.assertEqual(d.releases, [("lease-1", "submitted")])

    def test_release_retry_does_not_lose_pr(self):
        new_state("FAULT", commit_sha=SHA, pending_pr_number=8143)
        gh = FakeGH()
        gh.get_pr = lambda n: {**owned_pr_identity(), "url": "u", "head_sha": SHA, "state": "open"}
        gh.pr_comments = lambda n: []
        d = FakeDesk()
        with mock.patch.object(d, "release", side_effect=OSError("offline")):
            reconcile.reconcile_gap(GAP, desk=d, gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        self.assertTrue(state.load(GAP)["release_pending"])
        reconcile.reconcile_gap(GAP, desk=d, gh=gh, git=FakeGit(remote=SHA))
        self.assertFalse(state.load(GAP)["release_pending"])
        self.assertEqual(d.releases, [("lease-1", "submitted")])

    def test_fault_does_not_adopt_wrong_pr(self):
        new_state("FAULT", commit_sha=SHA, pending_pr_number=8143)
        gh = FakeGH()
        gh.validate_created = lambda *a, **k: ({}, ["head mismatch"])
        d = FakeDesk()
        reconcile.reconcile_gap(GAP, desk=d, gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(state.load(GAP)["state"], "FAULT")
        self.assertIsNone(state.load(GAP)["pr_number"])
        self.assertEqual(d.releases, [])

    def test_renamed_checker_link(self):
        c = verdict_comment(SHA, "ACCEPTED")
        resolve = FakeGH().repository_id
        self.assertEqual(reconcile.current_verdict([c], SHA, resolve), "ACCEPTED")
        c["body"] = c["body"].replace("old-owner/proofs", "new-owner/proofs")
        self.assertEqual(reconcile.current_verdict([c], SHA, resolve), "ACCEPTED")
        c["body"] = c["body"].replace("new-owner/proofs", "unrelated/proofs")
        self.assertIsNone(reconcile.current_verdict([c], SHA, resolve))
        c["body"] = c["body"].replace("unrelated/proofs", "new-owner/proofs")
        c["author_id"] = 999
        self.assertIsNone(reconcile.current_verdict([c], SHA, resolve))

    def test_intake_app_requires_both_numeric_ids(self):
        c = verdict_comment(SHA, "ACCEPTED", author="pequalnp-intake[bot]")
        c["author_id"] = config.CHECKER_INTAKE_BOT_ID
        resolve = FakeGH().repository_id
        self.assertIsNone(reconcile.current_verdict([c], SHA, resolve))
        c["app_id"] = config.CHECKER_INTAKE_APP_ID
        self.assertEqual(reconcile.current_verdict([c], SHA, resolve), "ACCEPTED")
        c["app_id"] = 999
        self.assertIsNone(reconcile.current_verdict([c], SHA, resolve))
        c["app_id"] = config.CHECKER_INTAKE_APP_ID
        c["author_id"] = 999
        self.assertIsNone(reconcile.current_verdict([c], SHA, resolve))

    def test_competitor_pr_cannot_credit_our_gap(self):
        new_state("PR_OPEN", commit_sha=SHA, pr_number=123)
        gh = FakeGH()
        gh.get_pr = lambda n: {**owned_pr_identity(), "author_id": 999,
                               "head_sha": SHA, "merged": True}
        gh.pr_comments = mock.Mock(return_value=[verdict_comment(SHA, "ACCEPTED")])
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(r["result"], "invalid-pr")
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        gh.pr_comments.assert_not_called()

    def test_old_or_untrusted_verdict_ignored(self):
        new_state("PR_OPEN", commit_sha=SHA, pr_number=123)
        gh = FakeGH()
        gh.get_pr = lambda n: {**owned_pr_identity(), "url": "u", "head_sha": SHA, "state": "open"}
        gh.pr_comments = lambda n: [verdict_comment("b"*40, "REJECTED", date="2027"),
                                    verdict_comment(SHA, "ACCEPTED", author="other")]
        reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        gh.pr_comments = lambda n: [verdict_comment(SHA, "REJECTED")]
        reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(state.load(GAP)["state"], "REJECTED")

    def test_checker_acceptance_without_merge_is_not_terminal(self):
        new_state("PR_OPEN", commit_sha=SHA, pr_number=123)
        gh = FakeGH()
        gh.get_pr = lambda n: {**owned_pr_identity(), "url": "u", "head_sha": SHA, "state": "open", "merged": False}
        gh.pr_comments = lambda n: [verdict_comment(SHA, "ACCEPTED")]
        reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=FakeGit(remote=SHA))
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        self.assertEqual(state.load(GAP)["external_verdict"], "ACCEPTED")

    def test_signed_push_without_pr_is_recovered_to_one_pr(self):
        from pathlib import Path
        candidate = candidate_file()
        new_state("PUSHED", commit_sha=SHA, base_sha="base1",
                  worktree=str(Path(candidate).parent), path=Path(candidate).name,
                  branch=config.branch_for(GAP))
        gh = FakeGH()
        gh.get_pr = lambda number: {**owned_pr_identity(), "url": "https://example.test/pr/123",
                                    "number": number}
        gh.pr_comments = lambda number: []
        g = FakeGit(remote=SHA)
        # The retained candidate path in a real worktree is a Lean path;
        # keep the test fixture identical to the expected module path.
        Path(candidate).parent.joinpath(PATH).parent.mkdir(
            parents=True, exist_ok=True)
        Path(candidate).parent.joinpath(PATH).write_text(GOOD)
        state.update(GAP, worktree=str(Path(candidate).parent), path=PATH)
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=g)
        self.assertEqual(r["state"], "PR_OPEN")
        self.assertEqual(gh.created, 1)
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=g)
        self.assertEqual(gh.created, 1)

    def test_lease_410_becomes_stale(self):
        new_state("LEASED", lease_expires_at=time.time() - 1)
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(beat=410),
                                    gh=FakeGH(), git=FakeGit())
        self.assertEqual(state.load(GAP)["state"], "STALE")


class TestPostcheck(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_exact_published_revision_checked_and_failure_recorded(self):
        from missions.pnp import postcheck, build_control
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as wt:
            proof = P(wt, PATH)
            proof.parent.mkdir(parents=True)
            proof.write_text(GOOD)
            new_state("PR_OPEN", commit_sha=SHA, pr_number=123, worktree=wt,
                      local_check_status="pending")
            g = FakeGit(build_ok=False)
            g.run = lambda args: type("Result", (), {"stdout": SHA if "rev-parse" in args else ""})()
            with mock.patch.dict(os.environ, {}, clear=False):
                with mock.patch.object(g, "build", wraps=g.build) as build:
                    postcheck.run(GAP, git=g)
                    build.assert_called_once()
            rec = state.load(GAP)
            self.assertEqual(rec["state"], "PR_OPEN")
            self.assertEqual(rec["local_check_status"], "failed")
            self.assertIsNone(rec["external_verdict"])
            with mock.patch.dict(os.environ, {"PNP_POSTCHECK_SHA": SHA}):
                self.assertTrue(build_control.obsolete(GAP, "lease-1"))

    def test_pending_postcheck_admitted_only_for_matching_revision(self):
        from missions.pnp import build_control
        new_state("PR_OPEN", commit_sha=SHA, local_check_status="pending")
        with mock.patch.dict(os.environ, {"PNP_POSTCHECK_SHA": SHA}):
            self.assertFalse(build_control.obsolete(GAP, "lease-1"))
            self.assertTrue(build_control.obsolete(GAP, "wrong-lease"))
            state.update(GAP, commit_sha="b"*40)
            self.assertTrue(build_control.obsolete(GAP, "lease-1"))

class TestDeskNextGap(unittest.TestCase):
    """join.txt documents an explicit null gap as 'no gaps right now'."""

    def setUp(self):
        self.d = desk.Desk(min_interval=0, sleep=lambda _: None)

    def call(self, data):
        with mock.patch.object(self.d, "_call", return_value=(200, data)):
            return self.d._next_gap()

    def test_documented_empty_frontier_without_lease_key_is_no_gap(self):
        self.assertIsNone(self.call({
            "gap": None,
            "note": "every open gap is held right now; ask again in a few minutes",
            "retry_after_s": 300,
        }))

    def test_both_null_keys_is_no_gap(self):
        self.assertIsNone(self.call({"gap": None, "lease": None}))

    def test_hard_and_another_flags_still_use_next(self):
        for flags in ({"hard": True}, {"another": True}):
            with self.subTest(flags=flags):
                with mock.patch.object(self.d, "_call", return_value=(200, {"gap": None})) as call:
                    self.assertIsNone(self.d._next_gap(**flags))
                self.assertEqual(call.call_args[0][1], "/next")
                expected = {"handle": config.DESK_HANDLE}
                expected.update({k: "1" for k in flags})
                self.assertEqual(call.call_args[0][2], expected)

    def test_offered_gap_requires_lease(self):
        gap = {"id": "L-meta-1", "file": PATH, "module": MODULE}
        self.assertEqual(self.call({"gap": gap, "lease": "L1"}),
                         {"gap": gap, "lease": "L1"})
        with self.assertRaises(desk.DeskError):
            self.call({"gap": gap})

    def test_malformed_answers_are_errors_not_empty_frontier(self):
        for bad in ({}, {"lease": "L1"}, {"gap": "not-an-object", "lease": "L1"},
                    "not-a-json-object"):
            with self.subTest(bad=bad):
                with self.assertRaises(desk.DeskError):
                    self.call(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
