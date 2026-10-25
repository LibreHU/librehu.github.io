#!/usr/bin/env python3
"""Builds the long pages of the site from src/*.html (no dependency, Python 3.8+).

Shorthand in the sources, expanded into the two languages the pages carry (CSS shows one):
  <t>English<fr>Français</t>                  -> <span lang="en">…</span><span lang="fr">…</span>
  <p class="x" bi>English<fr>Français</p>     -> <p class="x"><span lang="en">…</span><span lang="fr">…</span></p>
    (any tag: h1-h4, p, li, td, th, summary, figcaption…; one element, so ids and table columns stay single;
    the tag must not contain itself)
  {{head:<en title>|<fr title>|<description>}}, {{bar:<page>}}, {{foot}}: shared head, top bar, footer.

Run from the repository root: python3 tools/build.py   (writes <name>.html next to index.html)
"""

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
    ("docs.html", "Docs", "Docs"),
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
    <span><a href="https://github.com/LibreHU">GitHub</a> · <a href="{DISCORD}">Discord</a> · <a href="{LIBERAPAY}"><span lang="en">Donate</span><span lang="fr">Faire un don</span></a> · <a href="{up}docs.html">Docs</a> · <a href="{up}tutorials.html"><span lang="en">Tutorials</span><span lang="fr">Tutos</span></a> · <a href="{up}developers.html"><span lang="en">Developers</span><span lang="fr">Développeurs</span></a></span>
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


def main() -> None:
    src = ROOT / "src"
    for path in sorted(src.rglob("*.html")):
        page = path.relative_to(src).as_posix()
        out = ROOT / page
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(expand(path.read_text(encoding="utf-8"), page), encoding="utf-8")
        print("built", page)


if __name__ == "__main__":
    main()
