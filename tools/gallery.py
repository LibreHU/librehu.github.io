#!/usr/bin/env python3
"""Screenshot gallery: src/screenshots/index.html and one src/screenshots/<app>.html per folder of assets/shots/.

Images come from the Screenshots workflow of LibreHU-OTA-app (Android 9 emulator, 1280x720, 160 dpi, French UI):
copy each app's PNGs to assets/shots/<app>/, then run this script and tools/build.py.
Titles: tools/shots.json ({"apps": {id: [en name, fr name, en blurb, fr blurb]}, "names": {png name: [en, fr]},
"order": {id: [names]}, "skip": {id: [names left out: duplicates, failed taps]}}).
"""

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "assets" / "shots"
META = json.loads((ROOT / "tools" / "shots.json").read_text(encoding="utf-8"))


def order(app: str, names: list) -> list:
    """Plan order when known (tools/shots.json "order"), else alphabetical; "-2", "-3" right after their page."""
    known = META.get("order", {}).get(app, [])

    def key(n):
        base = re.sub(r"-\d+$", "", n)
        part = int(n[len(base) + 1:]) if n != base else 1
        return (known.index(base) if base in known else len(known), base, part)

    return sorted(names, key=key)


def caption(name: str) -> tuple:
    base = re.sub(r"-\d+$", "", name)
    part = name[len(base) + 1:]
    en, fr = META["names"].get(base, [base.replace("-", " ").capitalize()] * 2)
    if part:
        en, fr = f"{en} ({part})", f"{fr} ({part})"
    return en, fr


def t(en: str, fr: str) -> str:
    return f"<t>{html.escape(en)}<fr>{html.escape(fr)}</t>"


def main() -> None:
    out = ROOT / "src" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    apps = [a for a in META["apps"] if (SHOTS / a).is_dir() and any((SHOTS / a).glob("*.png"))]
    cards = []
    for app in apps:
        en_name, fr_name, en_blurb, fr_blurb = META["apps"][app]
        skip = META.get("skip", {}).get(app, [])
        names = order(app, [p.stem for p in (SHOTS / app).glob("*.png") if p.stem not in skip])
        cover = next((c for c in ("home", "main", "apps", "report", "favorites", "settings") if c in names), names[0])
        cards.append(
            f'<a class="card shot-card" href="{app}.html"><img src="../assets/shots/{app}/{cover}.png" width="1280" height="720" '
            f'loading="lazy" alt="{html.escape(en_name)}"><h3>{t(en_name, fr_name)}</h3><p>{t(en_blurb, fr_blurb)} '
            f'· {len(names)} <t>screens<fr>écrans</t></p></a>'
        )
        figs = []
        for n in names:
            en, fr = caption(n)
            figs.append(
                f'<figure id="{n}"><a href="../assets/shots/{app}/{n}.png"><img src="../assets/shots/{app}/{n}.png" width="1280" '
                f'height="720" loading="lazy" alt="{html.escape(en)}"></a><figcaption>{t(en, fr)}</figcaption></figure>'
            )
        (out / f"{app}.html").write_text(
            f"""{{{{head:{en_name} screenshots – LibreHU|Captures {fr_name} – LibreHU|Screenshots of {en_name}, LibreHU.}}}}
{{{{bar:screenshots/index.html}}}}
<main>
<div class="hero"><div class="wrap">
  <p><a href="index.html">← {t("All screenshots", "Toutes les captures")}</a></p>
  <h1>{t(en_name, fr_name)}</h1>
  <p class="lead">{t(en_blurb, fr_blurb)}</p>
</div></div>
<section><div class="wrap">
<div class="gallery">
{chr(10).join(figs)}
</div>
<p class="note info">{t(META["note"][0], META["note"][1])}</p>
</div></section>
</main>
{{{{foot}}}}
""",
            encoding="utf-8",
        )
    (out / "index.html").write_text(
        f"""{{{{head:Screenshots – LibreHU|Captures d'écran – LibreHU|Screenshots of every LibreHU app.}}}}
{{{{bar:screenshots/index.html}}}}
<main>
<div class="hero"><div class="wrap">
  <h1>{t("Screenshots", "Captures d'écran")}</h1>
  <p class="lead">{t(META["intro"][0], META["intro"][1])}</p>
</div></div>
<section><div class="wrap">
<div class="grid shots-index">
{chr(10).join(cards)}
</div>
<p class="note info">{t(META["note"][0], META["note"][1])}</p>
</div></section>
</main>
{{{{foot}}}}
""",
        encoding="utf-8",
    )
    print("gallery:", ", ".join(apps))


if __name__ == "__main__":
    main()
