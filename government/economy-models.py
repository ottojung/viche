#!/usr/bin/env python3
"""Model funding instrument of the Ministry of Economy (Act 29).

Antonina tries the models in ~/.config/antonina/config.json in order. The Town's
reliable funding is therefore the ORDER of that list: free models first, so the
Town keeps running at no cost; paid models last, as a fallback of last resort.

This script is the deterministic half of the Ministry. It discovers what exists
(`opencode models`), verifies that candidate free models actually answer, and
rewrites the Antonina list so that the tier order can never be violated, whatever
the Ministry's agent proposes. The agent supplies judgment (what to exclude, what
to prefer within a tier, which sources to read) through
state/economy/model-policy.json; it does not hand-edit the config.

Tiers, best first (a model's tier is decided by this table, not by the agent):
  0 free         id carries a "-free" component (opencode/beam-free, ...). Only
                 added to the list after a probe succeeds; probes are free.
  1 contributor  "-contributor" models of opencode-go: included with the
                 contributor plan. Never auto-added, only kept.
  2 luna         authorized Luna models, before paid fallbacks.
  3 paid         every other paid model. Never auto-added, only kept.
All configured models request the low reasoning variant.

Commands
  refresh [--probe-limit N] [--no-apply]   catalogue + probes + plan + apply + report
  plan                                      print the planned order, change nothing
  check                                     exit 1 if the live config breaks the tier order
  report                                    print the latest report

Environment
  VICHE_ANTONINA_CONFIG   config path (default ~/.config/antonina/config.json)
  VICHE_OPENCODE_MODELS   file with `opencode models` output (tests)
  VICHE_STATE_ROOT        state root; files live under economy/
"""
import argparse
import datetime
import fcntl
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

STATE = pathlib.Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
ROOT = STATE / "economy"
HOME = pathlib.Path(os.environ.get("HOME", "/home/lubko"))
CONFIG = pathlib.Path(os.environ.get(
    "VICHE_ANTONINA_CONFIG",
    str(pathlib.Path(os.environ.get("ANTONINA_HOST_XDG_CONFIG_HOME",
        os.environ.get("XDG_CONFIG_HOME", str(HOME / ".config")))) / "antonina" / "config.json")))
COOLDOWNS = pathlib.Path(os.environ.get(
    "VICHE_ANTONINA_COOLDOWNS",
    str(pathlib.Path(os.environ.get("ANTONINA_HOST_XDG_STATE_HOME",
        os.environ.get("XDG_STATE_HOME", str(HOME / ".local" / "state")))) / "antonina" / "model-cooldowns")))
LIVE_TOWN = pathlib.Path("/var/lib/lubko/wd/viche")
LIVE_STATE = pathlib.Path("/var/lib/lubko/wd/viche-state")
MAX_MODELS = int(os.environ.get("VICHE_ECONOMY_MAX_MODELS", "32"))
PROBE_FRESH_SECONDS = 14 * 86400
PROBE_TIMEOUT = int(os.environ.get("VICHE_ECONOMY_PROBE_TIMEOUT", "120"))
TIER_NAMES = ["free", "contributor", "luna", "paid"]

# Antonina's runtime rules, mirrored here so Economy's health reporting means
# what the agent will actually do. Sources in the installed release:
# agent-runtime/src/model-config.js, model-failover.js, model-cooldowns.js,
# model-health.js. These are observations of runtime behaviour, not authority
# to add or remove a configured model.
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VARIANT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
HARD_COOLDOWN_REASONS = {"quota_exhausted", "rate_limited"}
MAX_PROVIDER_COOLDOWN_SECONDS = 7 * 86400
MODEL_HEALTH_WINDOW_SECONDS = 10 * 60
MODEL_HEALTH_DISTINCT_AGENTS = 2
MODEL_HEALTH_EVENT_RE = re.compile(r"^\d{13}-[a-f0-9]{16}\.json$")
MAX_COOLDOWN_FILES = 200
MAX_MODEL_HEALTH_EVENTS = 1500
MODEL_HEALTH = pathlib.Path(os.environ.get(
    "VICHE_ANTONINA_MODEL_HEALTH", str(COOLDOWNS.parent / "model-health")))
RUNTIME_FAILURE_MODES = [
    "quota_exhausted/rate_limited: shared hard cooldown, other configured models are tried",
    "model_unavailable or provider auth/billing failure: permanent per-agent exclusion, invisible in shared cooldown files",
    "unsupported #low variant: provider.no-route marks the model unavailable at launch",
    "stalled request with no tokens: transient penalty, model stays in the last-resort lottery",
    "provider-wide exclusion: every configured model of that provider is skipped together",
    "all configured models excluded: Antonina refuses dispatch; no automatic paid fallback",
]


def now():
    return int(os.environ.get("VICHE_ECONOMY_NOW", time.time()))


def tier_of(model):
    """The tier table. Luna precedes paid fallbacks, after free and contributor."""
    name = model.lower()
    if "luna" in name:
        return 2
    if re.search(r"(^|[-/])free($|[-/])", name):
        return 0
    if "contributor" in name:
        return 1
    return 3


def atomic_write(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".tmp.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return default


def read_config():
    data = load(CONFIG, None)
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise SystemExit("Antonina config unreadable or has no models list: %s" % CONFIG)
    return data


def entry_model(entry):
    return entry if isinstance(entry, str) else entry.get("model", "")


def config_problems(entries):
    """The exact shape Antonina's configuredModels() accepts from config.json.

    This is checked locally *before* publishing as well as through the installed
    CLI: `antonina agent model select` only prints the first model, so a pass
    there does not prove that later entries are usable at runtime.
    """
    problems = []
    seen = set()
    for index, entry in enumerate(entries):
        model = entry_model(entry)
        if not isinstance(model, str) or not MODEL_ID_RE.match(model):
            problems.append("models[%d] is not a valid Antonina model id: %r" % (index, model))
            continue
        if model in seen:
            problems.append("duplicate configured model: " + model)
        seen.add(model)
        if isinstance(entry, dict):
            if not isinstance(entry.get("comment"), str):
                problems.append("models[%d].comment must be a string" % index)
            variant = entry.get("variant")
            if variant is not None and (not isinstance(variant, str) or not VARIANT_RE.match(variant)):
                problems.append("models[%d].variant is invalid: %r" % (index, variant))
        elif isinstance(entry, str):
            problems.append("models[%d] must be an object with a string comment" % index)
        else:
            problems.append("models[%d] is neither a string nor an object" % index)
    return problems


def repair_entries(entries):
    """Normalize entries without ever changing which models are authorized."""
    repaired = []
    for entry in entries:
        if isinstance(entry, str):
            repaired.append({"model": entry, "comment": ""})
        elif isinstance(entry, dict):
            record = dict(entry)
            if not isinstance(record.get("comment"), str):
                record["comment"] = ""
            repaired.append(record)
        else:
            repaired.append(entry)
    return repaired


def service_env():
    """Use Antonina's authenticated v2 service, never a second CLI server."""
    env = dict(os.environ)
    root = COOLDOWNS.parent / "opencode-service"
    for variable, name in (("XDG_CONFIG_HOME", "config"),
                           ("XDG_DATA_HOME", "data"),
                           ("XDG_STATE_HOME", "state")):
        env[variable] = str(root / name)
    return env


def fetch_catalogue():
    override = os.environ.get("VICHE_OPENCODE_MODELS")
    if override:
        text = pathlib.Path(override).read_text()
    else:
        done = subprocess.run(["opencode", "models"], capture_output=True, text=True, timeout=90, env=service_env())
        if done.returncode != 0:
            raise RuntimeError("opencode models failed: " + done.stderr.strip()[:200])
        text = done.stdout
    ids = [line.strip() for line in text.splitlines() if re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._#:-]+$", line.strip())]
    if len(ids) < 10:
        raise RuntimeError("model catalogue implausibly small (%d); refusing to act on it" % len(ids))
    return sorted(set(ids))


def update_catalogue(ids, current):
    store = load(ROOT / "catalogue.json", {"models": {}})
    models = store.get("models", {})
    stamp = datetime.datetime.fromtimestamp(current, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_free = []
    for model in ids:
        entry = models.setdefault(model, {"first_seen": stamp})
        entry["last_seen"] = stamp
        entry["tier"] = TIER_NAMES[tier_of(model)]
        if entry["first_seen"] == stamp and store.get("models") and tier_of(model) == 0 and "fetched_at" in store:
            new_free.append(model)
    gone = sorted(m for m in models if m not in ids)
    store = {"fetched_at": stamp, "models": models, "gone": gone}
    atomic_write(ROOT / "catalogue.json", json.dumps(store, sort_keys=True, indent=1) + "\n")
    return models, new_free, gone


def probe(model):
    prompt = "Reply with the single word OK and nothing else."
    try:
        done = subprocess.run(["opencode", "run", "-m", model + "#low", "--format", "json", prompt],
                              capture_output=True, text=True, timeout=PROBE_TIMEOUT, cwd="/tmp", env=service_env())
    except subprocess.TimeoutExpired:
        return False, "timeout after %ds" % PROBE_TIMEOUT
    out = done.stdout
    if done.returncode != 0:
        return False, ("exit %d: %s" % (done.returncode, done.stderr.strip()[:160]))
    if '"type":"error"' in out:
        return False, "provider error event"
    texts = []
    for line in out.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        part = event.get("part", {})
        if event.get("type") == "text" and isinstance(part.get("text"), str):
            texts.append(part["text"])
    if any("OK" in t.upper() for t in texts):
        return True, "answered OK"
    return False, "no usable answer"


def run_probes(candidates, limit, current):
    probes = load(ROOT / "probes.json", {})
    stale = [m for m in candidates
             if m not in probes or current - probes[m].get("at", 0) > PROBE_FRESH_SECONDS]
    stale.sort(key=lambda m: probes.get(m, {}).get("at", 0))
    ran = []
    for model in stale[:limit]:
        ok, detail = probe(model)
        probes[model] = {"ok": ok, "at": current, "detail": detail}
        ran.append(model)
    atomic_write(ROOT / "probes.json", json.dumps(probes, sort_keys=True, indent=1) + "\n")
    return probes, ran


def policy():
    data = load(ROOT / "model-policy.json", {})
    exclude = {}
    for item in data.get("exclude", []):
        if isinstance(item, dict) and item.get("model"):
            if int(item.get("until", 0)) > now():
                exclude[item["model"]] = item
    return {"exclude": exclude, "prefer": [m for m in data.get("prefer", []) if isinstance(m, str)]}


def plan_order(cfg, catalogue_ids, probes, pol, current):
    configured = [entry_model(e) for e in cfg["models"] if entry_model(e)]
    in_catalogue = set(catalogue_ids)
    wanted = {0: [], 1: [], 2: [], 3: []}
    dropped = []
    seen = set()

    def consider(model, grandfathered):
        if model in seen:
            return
        seen.add(model)
        tier = tier_of(model)
        # Authorization is durable. Discovery, failed probes, temporary policy
        # and capacity limits may never remove any configured model.
        if grandfathered:
            wanted[tier].append(model)
            return
        # Catalogue ids may carry : or # suffixes that Antonina's config
        # rejects outright. Never publish a config the runtime cannot load.
        if not MODEL_ID_RE.match(model):
            dropped.append((model, "not a valid Antonina config id"))
            return
        if model not in in_catalogue:
            dropped.append((model, "not in catalogue"))
            return
        if model in pol["exclude"]:
            dropped.append((model, "excluded by policy: " + str(pol["exclude"][model].get("reason", ""))))
            return
        if tier == 0:
            result = probes.get(model)
            if result is not None and not result.get("ok") and current - result.get("at", 0) < PROBE_FRESH_SECONDS:
                dropped.append((model, "probe failed: " + str(result.get("detail", ""))))
                return
            if not result or not result.get("ok"):
                return  # unprobed newcomers wait for their probe
        elif not grandfathered:
            return  # contributor/paid/luna models are only ever kept, never auto-added
        wanted[tier].append(model)

    for model in configured:
        consider(model, True)
    for model in catalogue_ids:
        if tier_of(model) == 0:
            consider(model, False)

    def rank(model):
        prefer = pol["prefer"]
        p = prefer.index(model) if model in prefer else len(prefer)
        c = configured.index(model) if model in configured else len(configured)
        return (model in pol["exclude"], p, c, model)

    fallback = [m for tier in (1, 2, 3) for m in sorted(wanted[tier], key=rank)]
    # The size limit applies to additions, never existing authorization.
    existing_free = [m for m in wanted[0] if m in configured]
    additions = [m for m in wanted[0] if m not in configured]
    room = max(0, MAX_MODELS - len(existing_free) - len(fallback))
    final = sorted(existing_free + sorted(additions, key=rank)[:room], key=rank) + fallback
    if not final:
        raise SystemExit("plan would leave Antonina with no models; refusing")
    return configured, final, dropped


def violations(models):
    tiers = [tier_of(m) for m in models]
    return [(models[i], models[i + 1]) for i in range(len(models) - 1) if tiers[i] > tiers[i + 1]]


def apply_order(cfg, final, probes, dropped, current):
    repaired = repair_entries(cfg["models"])
    problems = config_problems(repaired)
    if problems:
        raise SystemExit("Refusing to publish an invalid Antonina config: " + "; ".join(problems))
    existing = {entry_model(e): e for e in repaired}
    stamp = datetime.datetime.fromtimestamp(current, datetime.timezone.utc).strftime("%Y-%m-%d")
    new_entries = []
    for model in final:
        entry = existing.get(model)
        if entry is None:
            entry = {"model": model, "comment": "Ministry of Economy %s: free model, probe answered OK." % stamp}
        elif isinstance(entry, str):
            entry = {"model": entry, "comment": ""}
        new_entries.append({**entry, "variant": "low"})
    updated = dict(cfg)
    updated["models"] = new_entries
    if not set(existing).issubset(final):
        raise SystemExit("Refusing to revoke an authorized model")
    # Validate a candidate outside the live configuration. A failed or hung
    # validator must never transiently publish a candidate or restore stale bytes.
    with tempfile.TemporaryDirectory(prefix=".model-candidate-", dir=CONFIG.parent) as scratch:
        candidate = pathlib.Path(scratch) / "antonina" / "config.json"
        atomic_write(candidate, json.dumps(updated, indent=2) + "\n")
        env = dict(os.environ, VICHE_ANTONINA_CONFIG=str(candidate),
                   XDG_CONFIG_HOME=scratch, ANTONINA_HOST_XDG_CONFIG_HOME=scratch)
        try:
            listed = subprocess.run(["antonina", "agent", "model", "select"],
                                    capture_output=True, text=True, timeout=60, env=env)
            ok = listed.returncode == 0 and final[0] in listed.stdout.splitlines()
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        if not ok and os.environ.get("VICHE_ECONOMY_SKIP_VALIDATE") != "1":
            raise SystemExit("Antonina rejected candidate; live config untouched")
    with CONFIG.with_name(CONFIG.name + ".write.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if read_config() != cfg:
            raise SystemExit("Configuration changed during discovery; live config untouched")
        backup = CONFIG.with_name(CONFIG.name + ".bak-" + str(time.time_ns()))
        shutil.copy2(CONFIG, backup)
        atomic_write(CONFIG, json.dumps(updated, indent=2) + "\n")
    return str(backup)


def cooldown_state(models, current):
    """Hard cooldowns Antonina actually honours, plus entries it ignores.

    Antonina's model-cooldowns.js refuses files with the wrong reason, name,
    model id, size or an implausibly distant `until`. Counting one of those as
    a real cooldown would understate funding; counting a soft transient
    penalty as hard would misstate failover, because the runtime still uses
    softly penalised models in its last-resort lottery.
    """
    active = {}
    ignored = []
    if COOLDOWNS.is_dir():
        for path in sorted(COOLDOWNS.glob("*.json"))[:MAX_COOLDOWN_FILES]:
            data = load(path, {})
            model = data.get("model") if isinstance(data, dict) else None
            if not isinstance(model, str) or model not in models:
                continue
            reason = data.get("reason")
            until = data.get("until")
            why = None
            if not MODEL_ID_RE.match(model) or path.name != model.replace("/", "@") + ".json":
                why = "filename or model id mismatch"
            elif reason not in HARD_COOLDOWN_REASONS:
                why = "not a hard provider cooldown"
            elif isinstance(until, bool) or not isinstance(until, (int, float)):
                why = "until is not a number"
            elif not current < until <= current + MAX_PROVIDER_COOLDOWN_SECONDS + 60:
                why = "until outside the runtime bound"
            try:
                size = path.stat().st_size
            except OSError:
                size = None
            if size is None or size > 1024:
                why = "unreadable or oversized"
            if why:
                ignored.append({"model": model, "file": path.name, "why": why})
                continue
            active[model] = {"reason": reason, "until": int(until)}
    return active, ignored


def soft_unhealthy(models, current):
    """Fleet-wide soft signal from Antonina model-health observations.

    Two distinct agents failing unrecognisedly on one model within ten minutes
    put it in the runtime's last-resort lottery. It is health evidence, never
    a reason to revoke authorization or to change the funding ladder.
    """
    by_model = {}
    if MODEL_HEALTH.is_dir():
        events = [p for p in MODEL_HEALTH.glob("*.json") if MODEL_HEALTH_EVENT_RE.match(p.name)]
        for path in sorted(events, reverse=True)[:MAX_MODEL_HEALTH_EVENTS]:
            try:
                if path.stat().st_size > 1024:
                    continue
            except OSError:
                continue
            data = load(path, {})
            model = data.get("model")
            agent = data.get("agent_id")
            at = data.get("at")
            if not isinstance(model, str) or model not in models:
                continue
            if not isinstance(agent, str) or not agent:
                continue
            if isinstance(at, bool) or not isinstance(at, (int, float)):
                continue
            if not current - MODEL_HEALTH_WINDOW_SECONDS <= at <= current + 5:
                continue
            by_model.setdefault(model, set()).add(agent)
    return {m: sorted(agents) for m, agents in by_model.items()
            if len(agents) >= MODEL_HEALTH_DISTINCT_AGENTS}


def build_report(final, cfg_before, dropped, new_free, ran, changed, backup, current, catalogue_ids):
    cooling, ignored_cooldowns = cooldown_state(set(final), current)
    soft = soft_unhealthy(set(final), current)
    free = [m for m in final if tier_of(m) == 0]
    free_available = [m for m in free if m in catalogue_ids and m not in cooling]
    fallback_eligible = [m for m in final if tier_of(m) != 0 and m in catalogue_ids and m not in cooling]
    missing_fallback = [m for m in final if tier_of(m) != 0 and m not in catalogue_ids]
    returns = sorted(v["until"] for m, v in cooling.items() if m in free)
    failover_depth = len(free_available) + len(fallback_eligible)
    providers = sorted({m.split("/", 1)[0] for m in free_available})
    return {
        "at": datetime.datetime.fromtimestamp(current, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "order": [{"model": m, "tier": TIER_NAMES[tier_of(m)]} for m in final],
        "free_models": len(free),
        "free_missing_from_catalogue": [m for m in free if m not in catalogue_ids],
        "free_available_now": len(free_available),
        "fallback_eligible_now": len(fallback_eligible),
        "fallback_eligible_models": fallback_eligible,
        "fallback_missing_from_catalogue": missing_fallback,
        "model_eligibility_note": "Catalogue presence and no known cooldown are not proof of a successful invocation.",
        "next_free_returns_at": returns[0] if (returns and not free_available) else None,
        "cooling": cooling,
        "cooldown_ignored": ignored_cooldowns,
        "soft_unhealthy": {m: {"agents": a} for m, a in sorted(soft.items())},
        "failover_depth_now": failover_depth,
        "free_providers_now": providers,
        "provider_concentration": len(providers) <= 1 and len(free_available) > 0,
        "runtime_failure_modes": RUNTIME_FAILURE_MODES,
        "changed": changed,
        "previous_order": cfg_before,
        "dropped": [{"model": m, "why": why} for m, why in dropped],
        "new_free_models_seen": new_free,
        "probes_run": ran,
        "backup": backup,
        "paid_before_free_violations": [list(v) for v in violations(final)],
        "funding_risk": "none" if len(free_available) >= 2 else ("high" if not free_available else "elevated"),
        "failover_risk": ("high" if failover_depth < 2 else
                          ("elevated" if len(providers) <= 1 else "none")),
    }


def refresh(args):
    # Smoke tests and temporary checkouts must never probe or rewrite the
    # production Antonina service, even when inherited HOME is real.
    canonical = (pathlib.Path(__file__).resolve().parent.parent == LIVE_TOWN
                 and STATE.resolve() == LIVE_STATE
                 and pathlib.Path(os.environ.get("VICHE_TOWN_ROOT", str(LIVE_TOWN))).resolve() == LIVE_TOWN)
    if not canonical:
        fixture = all(os.environ.get(k) for k in (
            "VICHE_ANTONINA_CONFIG", "VICHE_ANTONINA_COOLDOWNS", "VICHE_OPENCODE_MODELS"))
        live_config = pathlib.Path.home() / ".config/antonina/config.json"
        live_cooldowns = pathlib.Path.home() / ".local/state/antonina/model-cooldowns"
        if (not fixture or CONFIG.resolve() == live_config.resolve()
                or COOLDOWNS.resolve() == live_cooldowns.resolve()
                or STATE.resolve() == LIVE_STATE):
            print("economy: noncanonical refresh skipped before discovery or writes", file=sys.stderr)
            return 1
    current = now()
    ROOT.mkdir(parents=True, exist_ok=True)
    cfg = read_config()
    try:
        ids = fetch_catalogue()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        atomic_write(ROOT / "report.json", json.dumps({"at": current, "error": str(error),
                     "note": "catalogue unavailable; model list left untouched"}, sort_keys=True) + "\n")
        print("economy: " + str(error), file=sys.stderr)
        return 1
    models, new_free, gone = update_catalogue(ids, current)
    pol = policy()
    free_candidates = [m for m in ids if tier_of(m) == 0 and m not in pol["exclude"]]
    probes, ran = run_probes(free_candidates, args.probe_limit, current)
    before, final, dropped = plan_order(cfg, ids, probes, pol, current)
    repaired = repair_entries(cfg["models"])
    changed = (before != final or repaired != cfg["models"]
               or any(not isinstance(e, dict) or e.get("variant") != "low" for e in repaired))
    backup = None
    if changed and not args.no_apply:
        backup = apply_order(cfg, final, probes, dropped, current)
    report = build_report(before if args.no_apply else final, before, dropped, new_free, ran, changed and not args.no_apply, backup, current, ids)
    if args.no_apply:
        report["proposed_order"] = final
    atomic_write(ROOT / "report.json", json.dumps(report, sort_keys=True, indent=1) + "\n")
    print(json.dumps({"changed": report["changed"], "free_available_now": report["free_available_now"],
                      "funding_risk": report["funding_risk"]}, sort_keys=True))
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    refresh_p = sub.add_parser("refresh")
    refresh_p.add_argument("--probe-limit", type=int, default=3)
    refresh_p.add_argument("--no-apply", action="store_true")
    sub.add_parser("plan")
    sub.add_parser("check")
    sub.add_parser("report")
    args = parser.parse_args(argv)
    if args.command == "refresh":
        return refresh(args)
    if args.command == "check":
        entries = read_config()["models"]
        bad = violations([entry_model(e) for e in entries])
        for first, second in bad:
            print("tier violation: %s (%s) is ahead of %s (%s)" % (
                first, TIER_NAMES[tier_of(first)], second, TIER_NAMES[tier_of(second)]))
        missing_low = [entry_model(e) for e in entries if not isinstance(e, dict) or e.get("variant") != "low"]
        for model in missing_low:
            print("low reasoning variant required: " + model)
        problems = config_problems(entries)
        for problem in problems:
            print("invalid Antonina config: " + problem)
        return 1 if bad or missing_low or problems else 0
    if args.command == "plan":
        cfg = read_config()
        ids = fetch_catalogue()
        before, final, dropped = plan_order(cfg, ids, load(ROOT / "probes.json", {}), policy(), now())
        print(json.dumps({"before": before, "after": final,
                          "dropped": [{"model": m, "why": w} for m, w in dropped]}, indent=1))
        return 0
    if args.command == "report":
        print(json.dumps(load(ROOT / "report.json", {}), indent=1, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
