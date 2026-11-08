#!/usr/bin/env python3
"""Builds the long pages of the site from src/*.html (no dependency, Python 3.8+).

Shorthand in the sources, expanded into the two languages the pages carry (CSS shows one):
  <t>English<fr>Français</t>                  -> <span lang="en">…</span><span lang="fr">…</span>
  <p class="x" bi>English<fr>Français</p>     -> <p class="x"><span lang="en">…</span><span lang="fr">…</span></p>
    (any tag: h1-h4, p, li, td, th, summary, figcaption…; one element, so ids and table columns stay single;
    the tag must not contain itself)
  {{head:<en title>|<fr title>|<description>}}, {{bar:<page>}}, {{foot}}: shared head, top bar, footer.
  {{apps}}, {{zips}}, {{changelog}}: download tables and changelog, from data/releases.json and data/changelog.json
    (written by tools/releases.py from what LibreHU Apps reads) and tools/site.json.

Run from the repository root: python3 tools/build.py   (writes <name>.html next to index.html)
"""

import datetime
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{en}</title>
<meta name="title-en" content="{en}">
<meta name="title-fr" content="{fr}">
<meta name="description" content="{desc}">
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
<script>
  // Language before drawing: saved choice, else the browser's first French or English language, else English.
  (function () {{
    var l = null;
    try {{ l = localStorage.getItem("lang"); }} catch (e) {{}}
    if (l !== "fr" && l !== "en") {{
      l = "en";
      var langs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"];
      for (var i = 0; i < langs.length; i++) {{
        var c = String(langs[i]).toLowerCase().slice(0, 2);
        if (c === "fr" || c === "en") {{ l = c; break; }}
      }}
    }}
    document.documentElement.setAttribute("data-lang", l);
    document.documentElement.lang = l;
  }})();
</script>
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>"""

NAV = [
    ("index.html#download", "Download", "Télécharger"),
    ("changelog.html", "Changelog", "Nouveautés"),
    ("docs.html", "Docs", "Docs"),
    ("engine.html", "Engine", "Moteur"),
    ("tutorials.html", "Tutorials", "Tutos"),
    ("developers.html", "Developers", "Développeurs"),
    ("screenshots/index.html", "Screenshots", "Captures"),
    ("headunits.html", "Head units", "Autoradios"),
    ("index.html#roadmap", "Roadmap", "Feuille de route"),
]

DISCORD = "https://discord.gg/aP4JZMavxB"
DISCORD_PATH = re.search(r'd="([^"]+)"', (ROOT / "assets" / "discord.svg").read_text()).group(1)
LIBERAPAY = "https://liberapay.com/DokT/donate"
LIBERAPAY_PATH = re.search(r'd="([^"]+)"', (ROOT / "assets" / "liberapay.svg").read_text()).group(1)


def bar(page: str, up: str) -> str:
    links = []
    for href, en, fr in NAV:
        current = ' aria-current="page"' if "#" not in href and href == page else ""
        links.append(f'<a href="{up}{href}"{current}><span lang="en">{en}</span><span lang="fr">{fr}</span></a>')
    nav = "\n      ".join(links)
    return f"""
<header class="bar">
  <div class="wrap">
    <a class="brand" href="{up}index.html"><img src="{up}assets/favicon.svg" alt="" width="28" height="28"> LibreHU</a>
    <nav id="nav" aria-label="Sections">
      {nav}
    </nav>
    <a class="liberapay-link" href="{LIBERAPAY}" rel="noopener" title="Liberapay"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="{LIBERAPAY_PATH}"/></svg><span class="sr"><span lang="en">Donate (Liberapay)</span><span lang="fr">Faire un don (Liberapay)</span></span></a>
    <a class="discord-link" href="{DISCORD}" rel="noopener" title="Discord"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="{DISCORD_PATH}"/></svg><span class="sr">Discord</span></a>
    <div class="lang" role="group" aria-label="Language / Langue">
      <button type="button" data-lang="en" aria-pressed="false">EN</button>
      <button type="button" data-lang="fr" aria-pressed="false">FR</button>
    </div>
    <button class="menu" type="button" aria-controls="nav" aria-expanded="false"><span class="sr">Menu</span><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
  </div>
</header>"""


def foot(up: str) -> str:
    return f"""
<footer>
  <div class="wrap">
    <span lang="en">LibreHU — independent project, not affiliated with Jancar, Autochips, Google or Apple.</span>
    <span lang="fr">LibreHU — projet indépendant, sans lien avec Jancar, Autochips, Google ou Apple.</span>
    <span><a href="https://github.com/LibreHU">GitHub</a> · <a href="{DISCORD}">Discord</a> · <a href="mailto:librehu@proton.me">Contact</a> · <a href="{LIBERAPAY}"><span lang="en">Donate</span><span lang="fr">Faire un don</span></a> · <a href="{up}docs.html">Docs</a> · <a href="{up}tutorials.html"><span lang="en">Tutorials</span><span lang="fr">Tutos</span></a> · <a href="{up}developers.html"><span lang="en">Developers</span><span lang="fr">Développeurs</span></a> · <a href="{up}developers.html#licences">Licence</a></span>
  </div>
</footer>

<script src="{up}assets/lang.js"></script>
</body>
</html>
"""


INLINE = re.compile(r"<t>(.*?)<fr>(.*?)</t>", re.S)
BLOCK = re.compile(r"<(\w+)((?:\s(?!bi[\s>])[^\s>]+)*)\sbi((?:\s[^>]*)?)>(.*?)<fr>(.*?)</\1>", re.S)


def expand(text: str, page: str) -> str:
    up = "../" * page.count("/")

    def head(m):
        en, fr, desc = m.group(1).split("|", 2)
        return HEAD.format(en=en.strip(), fr=fr.strip(), desc=desc.strip(), up=up)

    text = re.sub(r"\{\{head:(.*?)\}\}", head, text, flags=re.S)
    text = re.sub(r"\{\{bar:(.*?)\}\}", lambda m: bar(m.group(1).strip(), up), text)
    text = text.replace("{{foot}}", foot(up)).replace("{{discord_path}}", DISCORD_PATH)
    text = text.replace("{{liberapay_path}}", LIBERAPAY_PATH)
    text = INLINE.sub(r'<span lang="en">\1</span><span lang="fr">\2</span>', text)
    while True:
        new = BLOCK.sub(lambda m: f'<{m.group(1)}{m.group(2)}{m.group(3)}><span lang="en">{m.group(4)}</span>'
                                  f'<span lang="fr">{m.group(5)}</span></{m.group(1)}>', text)
        if new == text:
            break
        text = new
    left = re.findall(r"<fr>|\sbi[\s>]|<t>", text)
    if left:
        sys.exit(f"{page}: unexpanded markup left: {left[:5]}")
    return text


# ---- Generated from the releases (tools/releases.py) -------------------------------------------------------------

WEB = "https://github.com"
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
             "novembre", "décembre"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def both(en: str, fr: str) -> str:
    return en if en == fr else f'<span lang="en">{en}</span><span lang="fr">{fr}</span>'


def short_date(iso: str) -> str:
    """2026-11-04T… -> 2026-11-04 / 04/11/2026."""
    if len(iso) < 10:
        return ""
    y, m, d = iso[:10].split("-")
    return both(f"{y}-{m}-{d}", f"{d}/{m}/{y}")


def app_version(b: dict) -> str:
    """Version as people read it: 1.4.2, 4.0.0-beta1, else v<versionCode> (the CI's commit count)."""
    name = b.get("versionName", "")
    if b.get("branch") and name.endswith("-" + b["branch"]):
        name = name[: -len(b["branch"]) - 1]
    name = re.sub(r"-\d+-g[0-9a-f]{6,}$", "", name)
    if re.match(r"^\d+(\.\d+)+", name):
        return name
    return f"v{b.get('versionCode', 0)}"


def zip_version(v: str) -> str:
    """r146-97311f83a -> r146; plain counters (1, 2…) and commit names are not shown."""
    v = re.sub(r"^(r\d+)-[0-9a-f]+$", r"\1", v or "")
    return v if re.match(r"^[rvb]\d", v) else ""


def apps_rows(rel: dict, conf: dict) -> str:
    def order(a):
        return conf["apps"].get(a["id"], {}).get("order", 90), a["name"].lower()

    rows = []
    for a in sorted(rel["apps"], key=order):
        c = conf["apps"].get(a["id"], {})
        name = esc(c.get("name", a["name"]))
        if c.get("note"):
            name += f' <span class="muted">({esc(c["note"])})</span>'
        elif c.get("note_en"):
            name += f' <span class="muted" lang="en">({esc(c["note_en"])})</span><span class="muted" lang="fr">({esc(c["note_fr"])})</span>'
        role = both(esc(c["en"]), esc(c["fr"])) if "en" in c else esc(a.get("description", ""))
        builds = a.get("builds") or []
        if a.get("tagged") or not builds:
            buttons = [f'<a class="btn small ghost" href="{WEB}/{esc(a["repo"])}/releases">Releases</a>']
        else:
            buttons = []
            for i, b in enumerate(builds):
                if b.get("label"):
                    label = esc(b["label"])
                elif len(builds) > 1:
                    e = conf["editions"].get(b["branch"])
                    label = both(esc(e["en"]), esc(e["fr"])) if e else esc(b["branch"])
                else:
                    label = "APK"
                ghost = " ghost" if i or c.get("ghost") else ""
                buttons.append(f'<a class="btn small{ghost}" href="{esc(b["url"])}">{label}</a>')
        ver = ""
        if builds:
            b = builds[0]
            when = short_date(b.get("date", ""))
            ver = (f'<a class="ver" href="changelog.html#{esc(a["id"])}">{esc(app_version(b))}'
                   + (f" · {when}" if when else "") + "</a>")
        rows.append(f'<tr><td><strong>{name}</strong>{ver}</td>\n            <td>{role}</td>\n'
                    f'            <td><div class="dl">{" ".join(buttons)}</div></td></tr>')
    return "\n          ".join(rows)


def zips_rows(rel: dict, conf: dict) -> str:
    index = rel["zips"]
    every = {z["id"]: z for z in index["zips"]}
    shown = [z for z in index["zips"] if not z.get("hidden")]
    groups = {}
    for z in shown:
        groups.setdefault(z.get("group") or z["id"], []).append(z)
    rows = []
    for cat in index["categories"]:
        subs = [s["id"] for s in cat.get("subcategories", [])]
        members = [(k, v) for k, v in groups.items() if v[0].get("category") == cat["id"]]
        if not members:
            continue
        members.sort(key=lambda kv: (conf["zip_groups"].get(kv[0], {}).get("order", 50),
                                     subs.index(kv[1][0]["subcategory"]) if kv[1][0].get("subcategory") in subs else 99,
                                     min(z.get("order", 999) for z in kv[1]), kv[0]))
        rows.append(f'<tr class="cat"><th colspan="2">{both(esc(cat["name"]), esc(cat.get("name_fr", cat["name"])))}</th></tr>')
        for key, items in members:
            g = conf["zip_groups"].get(key)
            title = both(esc(g["en"]), esc(g["fr"])) if g else esc(items[0].get("group_name") or items[0]["name"])
            ids = {z["id"] for z in items}
            buttons = []
            for i, z in enumerate(sorted(items, key=lambda z: z.get("order", 999))):
                v = conf["zip_variants"].get(z["id"])
                label = both(esc(v["en"]), esc(v["fr"])) if v else (esc(z["variant"]) if z.get("variant") else "zip")
                version = zip_version(z.get("version", ""))
                tail = f" <small>{esc(version)}</small>" if version else ""
                buttons.append(f'<a class="btn small{" ghost" if i else ""}" href="{esc(z["url"])}">{label}{tail}</a>')
                r = every.get(z.get("restore", ""))
                if r and r.get("hidden") and r["id"] not in ids:
                    buttons.append(f'<a class="btn small ghost" href="{esc(r["url"])}">{both("undo", "retour")}</a>')
            rows.append(f'<tr><td><strong>{title}</strong></td><td><div class="dl">{" ".join(buttons)}</div></td></tr>')
    return "\n          ".join(rows)


def tag(name: str) -> str:
    """Name in a changelog line: without LibreHU (service, Launcher, Apps…)."""
    return re.sub(r"\s+", " ", re.sub(r"\bLibreHU\b", "", name)).strip() or name


def components(rel: dict, conf: dict) -> dict:
    """Component id -> (English, French) name, in the order of the filter."""
    out = {}
    for a in sorted(rel["apps"], key=lambda a: (conf["apps"].get(a["id"], {}).get("order", 90), a["name"].lower())):
        n = conf["apps"].get(a["id"], {}).get("name", a["name"])
        out[a["id"]] = (n, n)
    for s in conf["system"]:
        out[s["id"]] = (s["en"], s["fr"])
    return out


def changelog(rel: dict, log: dict, conf: dict) -> str:
    names = components(rel, conf)
    branches = {a["id"]: a["branches"] for a in rel["apps"]}
    branches.update({s["id"]: s.get("branches", []) for s in conf["system"]})
    entries = [e for e in log["entries"] if not e.get("quiet") and e.get("c") in names]
    present = {e["c"] for e in entries}

    def option(lang):
        opts = [f'<option value="">{"Everything" if lang == "en" else "Tout"}</option>']
        groups = (("Apps", "Applis", [c for c in names if c in branches and c not in {s["id"] for s in conf["system"]}]),
                  ("System", "Système", [s["id"] for s in conf["system"]]))
        for en, fr, ids in groups:
            items = "".join(f'<option value="{esc(c)}">{esc(names[c][0 if lang == "en" else 1])}</option>'
                            for c in ids if c in present)
            if items:
                opts.append(f'<optgroup label="{en if lang == "en" else fr}">{items}</optgroup>')
        return "".join(opts)

    out = ['<div class="log-filter">',
           f'  <label lang="en" for="log-en">Show</label><select lang="en" id="log-en">{option("en")}</select>',
           f'  <label lang="fr" for="log-fr">Afficher</label><select lang="fr" id="log-fr">{option("fr")}</select>',
           '</div>', '<div class="log">']
    month = day = None
    first = True
    for e in entries:
        d = e["d"][:10]
        if d[:7] != month:
            if day:
                out.append("</ul></div>")
            if month:
                out.append("</details>")
            month, day = d[:7], None
            y, m = int(d[:4]), int(d[5:7])
            count = sum(1 for x in entries if x["d"][:7] == month)
            out.append(f'<details class="month"{" open" if first else ""}><summary>'
                       f'{both(f"{MONTHS_EN[m - 1]} {y}", f"{MONTHS_FR[m - 1]} {y}")} <span class="count">{count}</span></summary>')
            first = False
        if d != day:
            if day:
                out.append("</ul></div>")
            day = d
            w = datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10])).weekday()
            dd, mm = int(d[8:10]), int(d[5:7])
            out.append(f'<div class="day-block"><h3 class="day">{both(f"{DAYS_EN[w]}, {MONTHS_EN[mm - 1]} {dd}", f"{DAYS_FR[w]} {dd} {MONTHS_FR[mm - 1]}")}</h3><ul>')
        en, fr = names[e["c"]]
        label = f'<span class="tag" title="{esc(en)}">{both(esc(tag(en)), esc(tag(fr)))}</span>'
        if e["k"] == "release":
            v = esc(e.get("v", ""))
            if e["c"] == "twrp":
                what = both("stable, in LibreHU Apps", "stable, dans LibreHU Apps") if e.get("stable") else both("beta build", "build bêta")
                text = f'<strong>{v}</strong> {what}'
            elif e.get("g"):
                g = conf["zip_groups"].get(e["g"])
                n = both(esc(g["en"]), esc(g["fr"])) if g else esc(e.get("n", ""))
                text = f'<strong>{n} {esc(zip_version(e.get("v", "")) or v)}</strong> {both("in LibreHU Apps", "dans LibreHU Apps")}'
            else:
                text = f'<strong>v{v}</strong> {both("in LibreHU Apps", "dans LibreHU Apps")}'
            out.append(f'<li class="rel" data-c="{esc(e["c"])}">{label}<a class="m" href="{esc(e.get("u", ""))}">{text}</a></li>')
        else:
            own = branches.get(e["c"], [])
            dev = "main" if "main" in own else (own[0] if own else "")
            br = ""
            if len(own) > 1 and dev not in e.get("b", []):
                br = f' <span class="br">({esc(", ".join(e["b"]))})</span>'
            out.append(f'<li data-c="{esc(e["c"])}">{label}<a class="m" href="{esc(e.get("u", ""))}" title="{esc(e["m"])}">'
                       f'{esc(e["m"])}</a>{br}</li>')
    if day:
        out.append("</ul></div>")
    if month:
        out.append("</details>")
    out.append("</div>")
    return "\n".join(out)


def car_display(name: str, c: dict):
    """(brand, model) shown for a car of a profile ("Renault Clio3 2005-2014, all trims" -> Renault, Clio 3); None
    for the catalogue's placeholders."""
    head = name.split(", ")[0]
    two = next((b for b in c.get("two_word_brands", []) if head.startswith(b + " ")), None)
    brand = two or head.split(" ")[0]
    rest = head[len(brand):].strip()
    m = re.match(r"^(.*?)(?:\s+(\d{2,4}(?:[-~]\S*)?)(?:\s*\(.*\))?)?$", rest)
    model = m.group(1) if m else rest
    shown = c["models"].get(f"{brand}|{model}", "")
    if shown is None:
        return None
    if shown:
        if "|" in shown:
            brand, shown = shown.split("|", 1)
        return brand, shown
    words = []
    for w in model.replace("_", " ").split():
        if w.isalpha() and (w.islower() or (w.isupper() and len(w) > 3)):
            w = w[:1].upper() + w[1:].lower()
        words.append(w)
    return brand, " ".join(words) or model


def can_table(can: dict, conf: dict) -> str:
    c = conf["can"]
    tried = set(c.get("tried", []))
    rows, total, makes = [], 0, set()
    for p in sorted(can["profiles"], key=lambda p: (min([x["since"] for x in p["cars"]] or [0]), p["id"])):
        proto = re.search(r"\(([^()]+)\)\s*$", p["name"])
        proto = proto.group(1) if proto else p.get("box", "")
        dec = [c["messages"][m] for m in dict.fromkeys(p["messages"]) if m in c["messages"]]
        what = both(esc(", ".join(x[0] for x in dec)), esc(", ".join(x[1] for x in dec))) if dec else ""
        rows.append(f'<tr class="cat"><th colspan="3">{esc(proto)}' + (f' <span class="what">{what}</span>' if what else "") + "</th></tr>")
        brands = {}
        total += len(p["cars"])
        for car in p["cars"]:
            shown = car_display(car["name"], c)
            if not shown:
                continue
            brand, model = shown
            m = brands.setdefault(brand, {}).setdefault(model, {"since": car["since"], "tried": False})
            m["since"] = min(m["since"], car["since"])
            m["tried"] = m["tried"] or f'{p["id"]}|{car["name"]}' in tried
        for brand in sorted(brands, key=str.lower):
            makes.add(brand)
            models = brands[brand]
            counts = {}
            for v in models.values():
                counts[v["since"]] = counts.get(v["since"], 0) + 1
            base = max(counts, key=lambda k: (counts[k], k))
            names = ", ".join(esc(n) + (' <span class="ok" title="tried on a car / essayée sur une voiture">✓</span>' if v["tried"] else "")
                              for n, v in sorted(models.items(), key=lambda kv: kv[0].lower()))
            other = [(n, v["since"]) for n, v in sorted(models.items(), key=lambda kv: kv[0].lower()) if v["since"] != base]
            since = f"v{base}"
            if other:
                since += "<br><small>" + "; ".join(both(f"{esc(n)}: v{s}", f"{esc(n)} : v{s}") for n, s in other) + "</small>"
            rows.append(f'<tr><td><strong>{esc(brand)}</strong></td><td>{names}</td><td class="since">{since}</td></tr>')
    head = ('<p class="sub">' + both(f"{total} cars (years and trims apart) of {len(makes)} makes in {len(can['profiles'])} profiles published by LibreHU-car-profiles (packs by make, downloaded by the service's CAN tab or LibreHU Apps), LibreHU service v{can['service']}.",
                                     f"{total} voitures (années et finitions à part) de {len(makes)} marques dans {len(can['profiles'])} profils publiés par LibreHU-car-profiles (paquets par marque, téléchargés par l'onglet CAN du service ou LibreHU Apps), LibreHU service v{can['service']}.") + "</p>")
    table = ('<div class="table"><table class="cars"><thead><tr>'
             '<th lang="en">Make</th><th lang="fr">Marque</th><th lang="en">Models</th><th lang="fr">Modèles</th>'
             '<th lang="en">Since (service)</th><th lang="fr">Depuis (service)</th></tr></thead><tbody>\n'
             + "\n".join(rows) + "\n</tbody></table></div>")
    return head + "\n" + table


def can_bars(can: dict) -> str:
    """The home page's CAN bars, from the packs' coverage (LibreHU-car-profiles dist/index.json, via data/can.json):
    box link and car decoded over the models of the stock app's catalogue."""
    c = (can or {}).get("coverage")
    if not c or not c.get("models"):
        return ""

    def pct(n: int) -> tuple:
        v = 100 * n / c["models"]
        t = f"{v:.1f}" if 99 <= v < 100 else f"{v:.0f}"
        return v, t + "%", t.replace(".", ",") + " %"

    def num(n: int) -> tuple:
        return f"{n:,}", f"{n:,}".replace(",", " ")

    out = []
    for key, en, fr, ok in (("box_link", "Link with the box", "Liaison avec le boîtier", True), ("decoded", "Car decoded", "Voiture décodée", False)):
        v, ten, tfr = pct(c.get(key, 0))
        out.append(f'<div class="progress"><div class="label"><t>{en}<fr>{fr}</t><strong><t>{ten}<fr>{tfr}</t></strong></div>'
                   f'<div class="bar{" ok" if ok else ""}"><span style="width: {v:.1f}%"></span></div></div>')
    m, cars, prof, gen = num(c["models"]), num(c.get("cars", 0)), num(c.get("profiles", 0)), num(c.get("generated", 0))
    src = esc(c.get("source", "").split(" (")[0])
    out.append(f'<p class="muted" lang="en">Of the {m[0]} models of Hiworld\'s catalogue ({src}): {cars[0]} cars in {prof[0]} profiles, '
               f'{gen[0]} of them generated and never tried on a car. <a href="docs.html#can-cars">Which cars?</a> <a href="engine.html">How it works</a></p>')
    out.append(f'<p class="muted" lang="fr">Sur les {m[1]} modèles du catalogue Hiworld ({src}) : {cars[1]} voitures dans {prof[1]} profils, '
               f'dont {gen[1]} générés et jamais essayés sur une voiture. <a href="docs.html#can-cars">Quelles voitures ?</a> <a href="engine.html">Comment ça marche</a></p>')
    return "\n        ".join(out)


def generated(text: str) -> str:
    """{{apps}}, {{zips}}, {{changelog}} filled from data/ (left as a link to GitHub when it is missing)."""
    if not any(k in text for k in ("{{apps}}", "{{zips}}", "{{changelog}}", "{{can_cars}}", "{{can_bars}}")):
        return text
    if "{{can_bars}}" in text:
        text = text.replace("{{can_bars}}", can_bars(load(ROOT / "data" / "can.json")))
    if "{{can_cars}}" in text:
        can = load(ROOT / "data" / "can.json")
        conf = load(ROOT / "tools" / "site.json")
        text = text.replace("{{can_cars}}", can_table(can, conf) if can else
                            f'<p><a href="{WEB}/LibreHU/LibreHU-service/blob/main/docs/can-vehicles.md">docs/can-vehicles.md</a></p>')
    conf = load(ROOT / "tools" / "site.json")
    rel = load(ROOT / "data" / "releases.json")
    log = load(ROOT / "data" / "changelog.json")
    if rel is None:
        missing = f'<tr><td colspan="3"><a href="{WEB}/LibreHU">GitHub</a></td></tr>'
        return text.replace("{{apps}}", missing).replace("{{zips}}", missing).replace("{{changelog}}", missing)
    text = text.replace("{{apps}}", apps_rows(rel, conf)).replace("{{zips}}", zips_rows(rel, conf))
    if "{{changelog}}" in text:
        text = text.replace("{{changelog}}", changelog(rel, log or {"entries": []}, conf))
    return text


def main() -> None:
    src = ROOT / "src"
    for path in sorted(src.rglob("*.html")):
        page = path.relative_to(src).as_posix()
        out = ROOT / page
        out.parent.mkdir(parents=True, exist_ok=True)
        # The generated parts go in after the shorthand is expanded: commit messages are text, never markup.
        out.write_text(generated(expand(path.read_text(encoding="utf-8"), page)), encoding="utf-8")
        print("built", page)


if __name__ == "__main__":
    main()
