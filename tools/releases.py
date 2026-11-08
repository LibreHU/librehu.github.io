#!/usr/bin/env python3
"""Reads what LibreHU Apps reads, for the site (no dependency, Python 3.8+).

  - catalog.json of LibreHU-OTA-app: the apps and their branches;
  - release.txt of each latest-<branch> release: version, date, APK;
  - index.json of the zips release of LibreHU-flashablesZips: TWRP, kernels, mods;
  - the commits of every repository and the TWRP builds (GitHub API, GITHUB_TOKEN if set): the changelog.

Writes data/releases.json (what is published now) and data/changelog.json (kept from run to run: the commits seen
and each version published since the first run). tools/build.py makes the download tables and changelog.html of
them. Run from the repository root: python3 tools/releases.py   (every hour by .github/workflows/releases.yml)
"""

import datetime as dt
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "tools" / "site.json").read_text(encoding="utf-8"))
DATA = ROOT / "data"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
API = "https://api.github.com"
WEB = "https://github.com"
# Commits read per branch at most (100 a page): the kernel has about 12,500 since 09/2026.
MAX_PAGES = 200
# Commits read again before the newest one seen at the last run (late pushes, branches merged later).
OVERLAP = dt.timedelta(days=3)
# Oldest entries dropped beyond this.
MAX_ENTRIES = 6000
SKIP = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]")


def get(url: str, api: bool = False, tries: int = 4):
    """Text of [url]; None when it does not exist (404)."""
    headers = {"User-Agent": "librehu-site"}
    if api:
        headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        if TOKEN:
            headers["Authorization"] = "Bearer " + TOKEN
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            # Refused or rate limited: stop, the files of the last run stay as they are.
            if i == tries - 1 or (api and e.code in (401, 403, 422, 429)):
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == tries - 1:
                raise
        time.sleep(2 ** (i + 1))
    return None


def notes(text: str) -> dict:
    """`key=value` lines of a release.txt, the first other line under "" (as LibreHU Apps reads them)."""
    out = {}
    for line in text.splitlines():
        t = line.strip()
        if not t:
            continue
        k, eq, v = t.partition("=")
        if eq and k.isalnum():
            out[k] = v
        elif "" not in out:
            out[""] = t
    return out


def slug(branch: str) -> str:
    return branch.replace("/", "-")


def build(repo: str, tag: str, name: str, branch: str, label):
    text = get(f"{WEB}/{repo}/releases/download/{tag}/{name}")
    if not text:
        return None
    n = notes(text)
    asset = n.get("apk") or n.get("ipa") or ""
    if not asset or "/" in asset:
        return None
    return {
        "branch": branch or n.get("branch", ""),
        "label": label,
        "url": f"{WEB}/{repo}/releases/download/{tag}/{asset}",
        "versionCode": int(n.get("versionCode") or 0),
        "versionName": n.get("versionName", ""),
        "date": n.get("date", ""),
        "size": int(n.get("size") or 0),
        "commit": n.get("commit", ""),
        "summary": n.get("", "")[:400],
    }


def apps() -> list:
    catalog = json.loads(get(SITE["catalog"]))["apps"] + SITE.get("extra", [])
    out = []
    for a in catalog:
        conf = SITE["apps"].get(a["id"], {})
        if conf.get("hidden"):
            continue
        branches = a.get("branches") or ["main"]
        files = a.get("files") or [{"tag": "latest-" + slug(b), "file": "release.txt", "branch": b} for b in branches]
        builds = [] if a.get("tagged") else [b for f in files if (b := build(a["repo"], f["tag"], f["file"], f["branch"], f.get("label")))]
        out.append({
            "id": a["id"],
            "name": a["name"],
            "repo": a["repo"],
            "branches": branches,
            "description": a.get("description", ""),
            "tagged": bool(a.get("tagged")),
            "builds": builds,
        })
    return out


def zips() -> dict:
    index = json.loads(get(SITE["zips"]))
    keep = ("id", "name", "category", "subcategory", "group", "group_name", "variant", "version", "order", "hidden",
            "restore", "url", "size")
    return {
        "categories": index.get("categories", []),
        "zips": [{k: z[k] for k in keep if k in z} for z in index.get("zips", [])],
    }


def twrp_builds() -> list:
    """twrp-build-<n> releases of the TWRP repository: b<n> while pre-release, v<n> once stable."""
    out = []
    for s in SITE["system"]:
        prefix = s.get("releases")
        if not prefix:
            continue
        for page in range(1, 4):
            text = get(f"{API}/repos/{s['repo']}/releases?per_page=100&page={page}", api=True)
            items = json.loads(text) if text else []
            for r in items:
                tag = r.get("tag_name", "")
                if r.get("draft") or not tag.startswith(prefix):
                    continue
                n = tag[len(prefix):]
                out.append({
                    "component": s["id"],
                    "tag": tag,
                    "version": ("b" if r.get("prerelease") else "v") + n,
                    "stable": not r.get("prerelease"),
                    "date": r.get("published_at") or r.get("created_at") or "",
                    "commit": r.get("target_commitish", ""),
                    "url": r.get("html_url", ""),
                })
            if len(items) < 100:
                break
    return sorted(out, key=lambda b: b["date"], reverse=True)


def can_profiles(releases: dict, old: dict):
    """Car profiles published by LibreHU-car-profiles (docs.html#can-cars), read from its packs (dist/index.json and
    one pack per make; the box types' pack decodes nothing and is left out): protocol, messages decoded, cars. No car
    is built into LibreHU service since its versionCode 184. The service version of the first run that saw each car
    is kept from run to run ("since")."""
    c = SITE.get("can")
    app = next((a for a in releases["apps"] if c and a["id"] == c["app"]), None)
    if not app or not app["builds"]:
        return old
    vc = app["builds"][0]["versionCode"]
    base = f"https://raw.githubusercontent.com/{c['repo']}/main/{c['path']}"
    index = json.loads(get(f"{base}/index.json"))
    since = dict((old or {}).get("since", {}))
    profiles = []
    for pack in index.get("packs", []):
        if pack["id"] in c.get("skip_packs", []):
            continue
        for d in json.loads(get(f"{base}/{pack['file']}")).get("profiles", []):
            pid = d.get("id")
            if not pid or "box_type" in d:
                continue
            names = [v["name"] for v in d.get("variants", [])] or [d.get("name", pid).split(" (")[0]]
            cars = []
            for n in names:
                key = f"{pid}|{n}"
                if key not in since:
                    since[key] = c["since"].get(key) or c["since"].get(pid) or vc
                cars.append({"name": n, "since": since[key]})
            profiles.append({"id": pid, "name": d.get("name", pid), "box": d.get("box", ""), "pack": pack["id"],
                             "messages": [m.get("name", k) for k, m in d.get("messages", {}).items()], "cars": cars})
    profiles.sort(key=lambda p: p["id"])
    return {"service": vc, "source": c["repo"], "coverage": index.get("coverage") or (old or {}).get("coverage"), "profiles": profiles,
            "since": dict(sorted(since.items()))}


def iso(t: str) -> dt.datetime:
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00"))


def add(entries: dict, component: str, branch: str, c: dict, author_since: str) -> None:
    """Commit [c] of the API into [entries]; merges, documentation pushes and older work left out."""
    info = c.get("commit", {})
    msg = info.get("message", "")
    title = msg.split("\n", 1)[0].strip()
    if len(c.get("parents") or []) > 1 or title.startswith("Merge ") or any(s in msg for s in SKIP):
        return
    author = (info.get("author") or {}).get("date", "")
    if author_since and author < author_since:
        return
    e = entries.get(c["sha"])
    if e:
        if branch not in e["b"]:
            e["b"] = sorted(e["b"] + [branch])
        return
    entries[c["sha"]] = {"k": "commit", "c": component, "s": c["sha"], "d": (info.get("committer") or {}).get("date", ""),
                         "a": author, "m": title[:400], "b": [branch], "u": c.get("html_url", "")}


def commits(state: dict, entries: dict, component: str, repo: str, branch: str, since: str, author_since: str):
    """Commits of [branch] of [repo] since the last run (3 days again), at most since [since]."""
    key = f"{repo}@{branch}"
    cursor = state["cursors"].get(key)
    start = since
    if cursor:
        again = (iso(cursor) - OVERLAP).strftime("%Y-%m-%dT%H:%M:%SZ")
        start = max(start, again) if start else again
    newest = cursor or ""
    for page in range(1, MAX_PAGES + 1):
        q = f"{API}/repos/{repo}/commits?sha={urllib.parse.quote(branch, safe='')}&per_page=100&page={page}"
        if start:
            q += "&since=" + start
        text = get(q, api=True)
        if text is None:
            break
        items = json.loads(text)
        for c in items:
            newest = max(newest, (c.get("commit", {}).get("committer") or {}).get("date", ""))
            add(entries, component, branch, c, author_since)
        if len(items) < 100:
            break
    if newest:
        state["cursors"][key] = newest


def upstream(repo: str):
    """owner:branch of the repository [repo] is a GitHub fork of (its commits are not LibreHU's), else None."""
    text = get(f"{API}/repos/{repo}", api=True)
    info = json.loads(text) if text else {}
    parent = info.get("parent") or {}
    if not info.get("fork") or not parent.get("owner"):
        return None
    return f"{parent['owner']['login']}:{parent.get('default_branch') or 'main'}"


def ahead(entries: dict, component: str, repo: str, base: str, branch: str, author_since: str) -> set:
    """Commits of [branch] that the fork's origin [base] does not have: LibreHU's own work. Their shas."""
    shas = set()
    for page in range(1, 31):
        q = (f"{API}/repos/{repo}/compare/{urllib.parse.quote(base, safe=':')}..."
             f"{urllib.parse.quote(branch, safe='')}?per_page=100&page={page}")
        text = get(q, api=True)
        if text is None:
            raise RuntimeError(f"no comparison {base}...{branch}")
        items = json.loads(text).get("commits", [])
        for c in items:
            shas.add(c["sha"])
            add(entries, component, branch, c, author_since)
        if len(items) < 100:
            break
    return shas


def merge_copies(entries: dict) -> dict:
    """One entry for a commit copied to several branches (same component, message and author date: cherry-picked or
    rebased), dated by its first copy, its branches joined."""
    seen = {}
    for e in sorted(entries.values(), key=lambda e: e["d"]):
        if e["k"] != "commit":
            seen[e["id"]] = e
            continue
        k = (e["c"], e["m"], e.get("a") or e["d"])
        if k in seen:
            seen[k]["b"] = sorted(set(seen[k]["b"]) | set(e["b"]))
        else:
            seen[k] = e
    return {e.get("s") or e["id"]: e for e in seen.values()}


def events(state: dict, entries: dict, releases: dict):
    """A new version published (app of the recommended edition, zip, TWRP build): one entry each."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    first = "events" not in state.get("seeded", [])
    for a in releases["apps"]:
        if not a["builds"]:
            continue
        b = a["builds"][0]
        eid = f"app:{a['id']}:{b['branch']}:{b['versionCode']}"
        if eid not in entries:
            entries[eid] = {"k": "release", "id": eid, "c": a["id"], "d": b["date"] or now, "v": b["versionCode"],
                            "n": b["versionName"], "u": b["url"]}
    for z in releases["zips"]["zips"]:
        if z.get("hidden"):
            continue
        group = z.get("group") or z["id"]
        eid = f"zip:{group}:{z.get('version', '')}"
        if eid in entries:
            continue
        component = {"recovery": "twrp", "kernel": "kernel"}.get(z.get("category", ""), "zips")
        if component == "twrp":
            continue  # its builds below (b<n>, v<n> once stable)
        # First run: only noted (the index does not say when each zip was published).
        entries[eid] = {"k": "release", "id": eid, "c": component, "d": now, "v": z.get("version", ""), "g": group,
                        "n": z.get("group_name") or z.get("name", ""), "u": z.get("url", ""), "quiet": first}
    for t in releases["twrp"]:
        eid = f"twrp:{t['tag']}"
        entries[eid] = {"k": "release", "id": eid, "c": t["component"], "d": t["date"], "v": t["version"],
                        "stable": t["stable"], "u": t["url"]}
    state.setdefault("seeded", [])
    if first:
        state["seeded"].append("events")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    releases = {"apps": apps(), "zips": zips(), "twrp": twrp_builds()}
    path = DATA / "changelog.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    state = {"cursors": old.get("cursors", {}), "seeded": old.get("seeded", [])}
    entries = {e.get("s") or e["id"]: e for e in old.get("entries", [])}
    start = SITE.get("since", "")
    repos = [(a["id"], a["repo"], [b for b in a["branches"] if b != "ios"], start, start) for a in releases["apps"]]
    repos += [(s["id"], s["repo"], s.get("branches", []), s.get("since", start), s.get("author_since", start)) for s in SITE["system"]]
    for component, repo, branches, since, author_since in repos:
        # Work older than LibreHU (a fork's origin, history imported with the code) is not listed.
        for k in [k for k, e in entries.items() if e["k"] == "commit" and e["c"] == component and (e.get("a") or e["d"]) < author_since]:
            del entries[k]
        try:
            base = upstream(repo)
        except Exception as e:  # noqa: BLE001
            print(f"warning: {repo}: {e}")
            continue
        if base:
            # A fork: only the commits its origin does not have, all read again at each run (a few hundred at most).
            try:
                own = set()
                for branch in branches:
                    own |= ahead(entries, component, repo, base, branch, author_since)
                for k in [k for k, e in entries.items() if e["k"] == "commit" and e["c"] == component and e["s"] not in own]:
                    del entries[k]
                continue
            except Exception as e:  # noqa: BLE001 (origin gone or renamed: its whole history, after the start date)
                print(f"warning: {repo} against {base}: {e}")
        for branch in branches:
            try:
                commits(state, entries, component, repo, branch, since, author_since)
            except Exception as e:  # noqa: BLE001 (one repository refused or rate limited: its commits wait for the next run)
                print(f"warning: commits of {repo}@{branch}: {e}")
    events(state, entries, releases)
    can_path = DATA / "can.json"
    can_old = json.loads(can_path.read_text(encoding="utf-8")) if can_path.exists() else None
    try:
        can = can_profiles(releases, can_old)
        if can:
            can_path.write_text(json.dumps(can, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 (the table keeps the last profiles read)
        print(f"warning: CAN profiles: {e}")
    entries = merge_copies(entries)
    ordered = sorted(entries.values(), key=lambda e: (e["d"], e.get("s") or e["id"]), reverse=True)[:MAX_ENTRIES]
    (DATA / "releases.json").write_text(json.dumps(releases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # One entry a line: small diffs from run to run.
    lines = ",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":"), sort_keys=True) for e in ordered)
    head = json.dumps({"cursors": dict(sorted(state["cursors"].items())), "seeded": state["seeded"]}, ensure_ascii=False, indent=1)
    path.write_text(head[:-2] + ',\n "entries": [\n' + lines + "\n]}\n", encoding="utf-8")
    print(f"{len(releases['apps'])} apps, {len(releases['zips']['zips'])} zips, {len(releases['twrp'])} TWRP builds, "
          f"{len(ordered)} changelog entries")


if __name__ == "__main__":
    main()
