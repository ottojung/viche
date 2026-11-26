"""Authenticated GitHub access through gh-pequalnp, restricted by construction.

Only these operations exist: identity/commit-verification reads, PR reads,
pushing one branch (in gitctl), creating one PR upstream, and updating that
same PR on correction.  No merge, close, setting, delete or unrelated repo.
"""
import json
import re
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


REPO_NAME = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+")
LOGIN = re.compile(r"[A-Za-z0-9-]{1,39}")


_MEMO = {}


def _memo(key, fn):
    """Per-process memo for pinned identities: a publication asked GitHub for the same login and
    repository names about eight times (one gh process and round trip each, about 1 s)."""
    key = key + (id(gh), id(config))   # a test that swaps gh or config gets fresh answers
    if key not in _MEMO:
        _MEMO[key] = fn()
    return _MEMO[key]


def identity():
    return _memo(("identity",), _identity)


def _identity():
    account = json.loads(gh("api", "user", "--jq", "{id,login}"))
    if account.get("id") != config.CONTRIBUTOR_ID:
        raise GitHubError("authenticated account is not the authorized contributor ID")
    login = account.get("login")
    if not isinstance(login, str) or not LOGIN.fullmatch(login):
        raise GitHubError("invalid authenticated login")
    return login


def repository_name(repo_id):
    """Resolve a pinned repository ID to its current routing name."""
    if repo_id not in (config.UPSTREAM_ID, config.FORK_ID):
        raise GitHubError("repository ID is not authorized")
    return _memo(("repo", repo_id), lambda: _repository_name(repo_id))


def _repository_name(repo_id):
    data = json.loads(gh("api", "repositories/" + str(repo_id),
                         "--jq", "{id,full_name,owner_id:.owner.id}"))
    name = data.get("full_name")
    if data.get("id") != repo_id or not isinstance(name, str) or not REPO_NAME.fullmatch(name):
        raise GitHubError("repository identity mismatch")
    if repo_id == config.FORK_ID and data.get("owner_id") != config.CONTRIBUTOR_ID:
        raise GitHubError("fork is not owned by the authorized contributor")
    return name


def repository_id(name):
    """Check a GitHub link's actual repository identity, not its spelling."""
    if not isinstance(name, str) or not REPO_NAME.fullmatch(name):
        return None
    result = json.loads(gh("api", "repos/" + name, "--jq", "{id}"))
    return result.get("id")


def endpoint(repo_id, path):
    if repo_id not in (config.UPSTREAM_ID, config.FORK_ID):
        raise GitHubError("repository ID is not authorized")
    return "repositories/" + str(repo_id) + "/" + path


def commit_verification(sha):
    expr = ("{sha: .sha, verified: .commit.verification.verified, "
            "state: .commit.verification.state, "
            "name: .commit.author.name, email: .commit.author.email}")
    data = json.loads(gh("api", endpoint(config.FORK_ID, "commits/" + sha),
                         "--jq", expr))
    if data.get("sha") != sha:
        raise GitHubError("GitHub returned a different commit SHA")
    return data


def pr_exists_for(branch, gap_id, api=None):
    """Search open and closed upstream PRs before ever creating one."""
    if api:
        raw = api()
    else:
        from urllib.parse import quote
        query = ("?state=all&head=" +
                 quote(identity() + ":" + branch, safe="") + "&per_page=100")
        raw = gh("api", endpoint(config.UPSTREAM_ID, "pulls" + query))
    prs = json.loads(raw) if isinstance(raw, str) else raw
    for pr in prs:
        head = pr.get("head") or {}
        if (head.get("ref") == branch and
                (head.get("repo") or {}).get("id") == config.FORK_ID and
                pr.get("title") == gap_id and
                (pr.get("user") or {}).get("id") == config.CONTRIBUTOR_ID):
            return pr.get("number")
    return None


def create_pr(branch, gap_id, lease=None):
    from urllib.parse import urlparse
    login = identity()
    upstream = repository_name(config.UPSTREAM_ID)
    fork = repository_name(config.FORK_ID)
    if fork.split("/")[0].lower() != login.lower():
        raise GitHubError("fork owner login differs from authenticated account")
    import re
    body = "Lease: "+lease+"\n" if isinstance(lease,str) and re.fullmatch(r"[A-Za-z0-9-]{1,64}",lease) else ""
    url = gh("pr", "create", "--repo", upstream,
             "--base", config.BASE_REF,
             "--head", login + ":" + branch,
             "--title", gap_id, "--body", body).strip()
    suffix = urlparse(url).path.rstrip("/").split("/")
    if len(suffix) < 2 or suffix[-2] != "pull" or not suffix[-1].isdigit():
        raise GitHubError("gh returned an unexpected pull request URL")
    return int(suffix[-1])


def get_pr(number):
    expr = ("{number: .number, state: .state, title: .title, "
            "author: .user.login, author_id: .user.id, head_sha: .head.sha, merged: .merged, "
            "head_ref: .head.ref, head_repo: .head.repo.full_name, head_repo_id: .head.repo.id, "
            "base_ref: .base.ref, base_repo: .base.repo.full_name, base_repo_id: .base.repo.id, "
            "url: .html_url}")
    return json.loads(gh("api", endpoint(config.UPSTREAM_ID, "pulls/" + str(number)), "--jq", expr))


def get_prs(numbers):
    """Bounded read-only batch; normalize to the existing REST record shape.

    Repository and PR IDs are checked before using a response. The caller
    still revalidates contributor/fork/base/head identity and authenticates
    nonempty checker comments through the REST path.
    """
    ids = list(dict.fromkeys(numbers))
    if not ids:
        return {}
    if len(ids) > 50 or any(type(n) is not int or n <= 0 for n in ids):
        raise GitHubError("invalid PR batch")
    owner, name = repository_name(config.UPSTREAM_ID).split("/")
    fields = ("number title state merged url author {login ... on User {databaseId}} "
              "headRefOid headRefName baseRefName headRepository {databaseId nameWithOwner} "
              "repository {databaseId nameWithOwner} comments(first:1){totalCount}")
    aliases = " ".join("p%d:pullRequest(number:%d){%s}" % (n, n, fields) for n in ids)
    query = 'query {repository(owner:%s,name:%s){databaseId %s}}' % (
        json.dumps(owner), json.dumps(name), aliases)
    data = json.loads(gh("api", "graphql", "-f", "query=" + query))
    if data.get("errors"):
        raise GitHubError("GraphQL PR batch returned errors")
    repo = (data.get("data") or {}).get("repository") or {}
    if repo.get("databaseId") != config.UPSTREAM_ID:
        raise GitHubError("batch repository identity mismatch")
    result = {}
    for n in ids:
        row = repo.get("p%d" % n)
        if not row or row.get("number") != n:
            continue  # ordinary REST fallback for incomplete response
        state = row.get("state")
        if state not in ("OPEN", "CLOSED", "MERGED") or type(row.get("merged")) is not bool:
            continue
        if row["merged"] != (state == "MERGED"):
            continue
        author, head, base = (row.get(k) or {} for k in ("author", "headRepository", "repository"))
        count = (row.get("comments") or {}).get("totalCount")
        result[n] = {
            "number": n, "state": "open" if state == "OPEN" else "closed",
            "title": row.get("title"), "merged": row["merged"], "url": row.get("url"),
            "author": author.get("login"), "author_id": author.get("databaseId"),
            "head_sha": row.get("headRefOid"), "head_ref": row.get("headRefName"),
            "base_ref": row.get("baseRefName"), "head_repo": head.get("nameWithOwner"),
            "head_repo_id": head.get("databaseId"), "base_repo": base.get("nameWithOwner"),
            "base_repo_id": base.get("databaseId"),
            "comment_count": count if type(count) is int and count >= 0 else None,
        }
    return result


def pr_files(number):
    return json.loads(gh("api", endpoint(config.UPSTREAM_ID, "pulls/" + str(number)) + "/files", "--jq",
                         "[.[].filename]"))


def pr_commits(number):
    return json.loads(gh("api", endpoint(config.UPSTREAM_ID, "pulls/" + str(number)) + "/commits", "--jq", "[.[].sha]"))


def pr_comments(number):
    return json.loads(gh("api", endpoint(config.UPSTREAM_ID, "issues/" + str(number)) + "/comments", "--jq",
                         "[.[] | {body: .body, created_at: .created_at, author: .user.login, author_id: .user.id, app_id: .performed_via_github_app.id}]"))


def validate_created(number, expected_sha, expected_path,
                     expected_commits=None):
    pr = get_pr(number)
    problems = []
    if pr.get("author_id") != config.CONTRIBUTOR_ID:
        problems.append("PR author is not the authorized contributor ID")
    if pr.get("head_repo_id") != config.FORK_ID:
        problems.append("head repo is not the fork")
    if pr.get("base_repo_id") != config.UPSTREAM_ID:
        problems.append("base repo is not upstream")
    if pr.get("head_sha") != expected_sha:
        problems.append("PR head SHA differs from the signed revision")
    if pr.get("base_ref") != config.BASE_REF:
        problems.append("base ref is not main")
    expected = expected_commits or [expected_sha]
    # Independent reads: run them together (each is one gh round trip of about 1-2 s).
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2 + len(expected)) as ex:
        f_files = ex.submit(pr_files, number)
        f_commits = ex.submit(pr_commits, number)
        f_vers = [ex.submit(commit_verification, c) for c in expected]
        files = f_files.result()
        commits = f_commits.result()
        vers = [f.result() for f in f_vers]
    if files != [expected_path]:
        problems.append("changed files are not exactly one added proof: %r" %
                        files)
    if commits != expected:
        problems.append("PR commits are not the expected signed SHAs: %r" %
                        commits)
    for commit_sha, ver in zip(expected, vers):
        if ver.get("verified") is not True:
            problems.append("GitHub commit verification is not true: " +
                            commit_sha)
        if (ver.get("name") != config.AUTHOR_NAME or
                ver.get("email") != config.AUTHOR_EMAIL):
            problems.append("GitHub commit identity mismatch: " + commit_sha)
    return pr, problems
