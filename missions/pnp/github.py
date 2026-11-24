"""Authenticated GitHub access through gh-pequalnp, restricted by construction.

Only these operations exist: identity/commit-verification reads, PR reads,
pushing one branch (in gitctl), creating one PR upstream, and updating that
same PR on correction.  No merge, close, setting, delete or unrelated repo.
"""
import json
import subprocess

from . import config


class GitHubError(Exception):
    pass


def gh(*args):
    p = subprocess.run([config.GH_CLI] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, timeout=45)
    if p.returncode != 0:
        raise GitHubError("gh %s failed: %s" %
                          (args[0] if args else "?", p.stderr.strip()[:400]))
    return p.stdout


def identity():
    login = gh("api", "user", "--jq", ".login").strip()
    if login != config.GH_USER:
        raise GitHubError("authenticated account is %r, expected %s" %
                          (login, config.GH_USER))
    return login


def commit_verification(sha):
    expr = ("{sha: .sha, verified: .commit.verification.verified, "
            "state: .commit.verification.state, "
            "name: .commit.author.name, email: .commit.author.email}")
    data = json.loads(gh("api", "repos/" + config.FORK + "/commits/" + sha,
                         "--jq", expr))
    if data.get("sha") != sha:
        raise GitHubError("GitHub returned a different commit SHA")
    return data


def pr_exists_for(branch, gap_id, api=None):
    """Search open and closed upstream PRs before ever creating one."""
    try:
        from urllib.parse import quote
        query = ("?state=all&head=" +
                 quote(config.GH_USER + ":" + branch, safe="") +
                 "&per_page=100")
        raw = (api() if api else gh("api", "repos/" + config.UPSTREAM +
                                    "/pulls" + query))
    except Exception:
        raise
    prs = json.loads(raw) if isinstance(raw, str) else raw
    for pr in prs:
        head = pr.get("head") or {}
        if (head.get("ref") == branch and
                (head.get("repo") or {}).get("full_name") == config.FORK and
                (pr.get("title") == gap_id or gap_id in (pr.get("title") or ""))):
            return pr.get("number")
    return None


def create_pr(branch, gap_id):
    from urllib.parse import urlparse
    url = gh("pr", "create", "--repo", config.UPSTREAM,
             "--base", config.BASE_REF,
             "--head", config.GH_USER + ":" + branch,
             "--title", gap_id, "--body", "").strip()
    suffix = urlparse(url).path.rstrip("/").split("/")
    if len(suffix) < 2 or suffix[-2] != "pull" or not suffix[-1].isdigit():
        raise GitHubError("gh returned an unexpected pull request URL")
    return int(suffix[-1])


def get_pr(number):
    expr = ("{number: .number, state: .state, title: .title, "
            "author: .user.login, "
            "head_ref: .head.ref, head_repo: .head.repo.full_name, "
            "base_ref: .base.ref, base_repo: .base.repo.full_name, "
            "url: .html_url}")
    return json.loads(gh("api", "repos/" + config.UPSTREAM + "/pulls/" +
                         str(number), "--jq", expr))


def pr_files(number):
    return json.loads(gh("api", "repos/" + config.UPSTREAM + "/pulls/" +
                         str(number) + "/files", "--jq",
                         "[.[].filename]"))


def pr_commits(number):
    return json.loads(gh("api", "repos/" + config.UPSTREAM + "/pulls/" +
                         str(number) + "/commits", "--jq", "[.[].sha]"))


def pr_comments(number):
    return json.loads(gh("api", "repos/" + config.UPSTREAM + "/issues/" +
                         str(number) + "/comments", "--jq",
                         "[.[] | {body: .body, created_at: .created_at}]"))


def validate_created(number, expected_sha, expected_path,
                     expected_commits=None):
    pr = get_pr(number)
    problems = []
    if pr.get("author") != config.GH_USER:
        problems.append("PR author is not ottojung")
    if pr.get("head_repo") != config.FORK:
        problems.append("head repo is not the fork")
    if pr.get("base_repo") != config.UPSTREAM:
        problems.append("base repo is not upstream")
    if pr.get("base_ref") != config.BASE_REF:
        problems.append("base ref is not main")
    files = pr_files(number)
    if files != [expected_path]:
        problems.append("changed files are not exactly one added proof: %r" %
                        files)
    commits = pr_commits(number)
    expected = expected_commits or [expected_sha]
    if commits != expected:
        problems.append("PR commits are not the expected signed SHAs: %r" %
                        commits)
    for commit_sha in expected:
        ver = commit_verification(commit_sha)
        if ver.get("verified") is not True:
            problems.append("GitHub commit verification is not true: " +
                            commit_sha)
        if (ver.get("name") != config.AUTHOR_NAME or
                ver.get("email") != config.AUTHOR_EMAIL):
            problems.append("GitHub commit identity mismatch: " + commit_sha)
    return pr, problems
