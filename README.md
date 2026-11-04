# librehu.github.io

LibreHU website, published by GitHub Pages at <https://librehu.github.io>.
Site de LibreHU, publié par GitHub Pages sur <https://librehu.github.io>.

| Page | Content |
|---|---|
| `index.html` | features, downloads (latest build of each app and edition), install, compatibility, roadmap (custom kernel, LineageOS, other platforms), Discord, FAQ |
| `docs.html` | user documentation of every app |
| `tutorials.html` | step-by-step tutorials |
| `developers.html` | technical reference: hardware, MCU and CAN protocols, service API, Bridge protocol, build, CI, kernel, TWRP, LineageOS, porting |
| `screenshots/` | gallery: one page per app |
| `headunits.html` | Android head unit chips, real and displayed Android versions, sources |
| `changelog.html` | every change of the apps, kernel, TWRP and zips (commits, versions published), generated |

## Sources and build

The pages are written in `src/` and expanded by `tools/build.py` (Python 3, no dependency) into the HTML files at the
root, which are committed (GitHub Pages serves them as is):

```
python3 tools/gallery.py   # src/screenshots/*.html from assets/shots/<app>/*.png and tools/shots.json
python3 tools/build.py     # src/**/*.html -> *.html
```

Shorthand in `src/` (see `tools/build.py`): `<t>English<fr>Français</t>` for inline text, `<p bi>English<fr>Français</p>`
for any element, `{{head:…}}`, `{{bar:<page>}}`, `{{foot}}` for the shared head, top bar and footer.

## Versions and changelog, updated every hour / Versions et nouveautés, mises à jour toutes les heures

The download tables of `index.html` and `changelog.html` come from what **LibreHU Apps** reads, so publishing an app,
a kernel or a zip updates the site with nothing to do by hand:

- `tools/releases.py` reads `catalog.json` of LibreHU-OTA-app (the apps and their branches), the `release.txt` of each
  `latest-<branch>` release (version, date, APK), `index.json` of the `zips` release of LibreHU-flashablesZips
  (TWRP, kernels, mods), the `twrp-build-<n>` releases and the commits of every repository (GitHub API). It writes
  `data/releases.json` (published now) and `data/changelog.json` (kept from run to run: commits seen, each version
  published since 04/11/2026). Commits left out: merges, documentation pushes (`[skip ci]`), and in the kernel the
  linux-stable fixes (author date before 09/2026).
- The same run reads the built-in car profiles of LibreHU service at its published commit into `data/can.json`
  (protocol, messages decoded, cars, the first service version of each car, kept from run to run; seeds in
  `tools/site.json` → `can` for the cars older than the table): the table of `docs.html#can-cars`.
- `tools/build.py` fills `{{apps}}`, `{{zips}}`, `{{changelog}}` and `{{can_cars}}` from them; `tools/site.json` adds what the site
  shows on top (English / French roles, order, editions, short names of the zips). An app added to the catalog appears
  with its catalog name until it gets a line there.
- `.github/workflows/releases.yml` runs both every hour (and on a push of `src/`, `tools/`), then commits the pages
  if something changed. GitHub may delay scheduled runs and disables them after 60 days without activity in the
  repository ([docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)):
  *Actions → Releases → Run workflow* starts one by hand.

## Languages / Langues

Both languages are in each page (`lang="en"` and `lang="fr"` elements); CSS shows one. A script in `<head>` picks it
before drawing: the saved choice (`localStorage`), else the browser's first French or English language
(`navigator.languages`), else English. Without JavaScript the page shows English.

## Screenshots

`assets/shots/<app>/` holds the PNGs of the **Screenshots** workflow of
[LibreHU-OTA-app](https://github.com/LibreHU/LibreHU-OTA-app/tree/main/screenshots) (Android 9 / 11 emulator,
1280 × 720, 160 dpi, French UI, published APKs). Titles and order: `tools/shots.json`.

## Discord

The top bar links to the official server (<https://discord.gg/aP4JZMavxB>); the home page shows its member and online
counts, read from Discord's public invite API in the browser. The server's own widget is disabled on Discord's side:
enabling it (Server settings → Widget) would allow an embedded member list.

## Donations / Dons

The top bar (Liberapay icon), the home page (« Support the project » card, `#donate`) and the footer link to
<https://liberapay.com/DokT/donate>; the card shows the patron count as a Shields.io badge. No third-party script is
loaded (Liberapay's own widgets need JavaScript from liberapay.com). Logo: `assets/liberapay.svg` (Simple Icons, CC0).
