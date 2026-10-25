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

## Sources and build

The pages are written in `src/` and expanded by `tools/build.py` (Python 3, no dependency) into the HTML files at the
root, which are committed (GitHub Pages serves them as is):

```
python3 tools/gallery.py   # src/screenshots/*.html from assets/shots/<app>/*.png and tools/shots.json
python3 tools/build.py     # src/**/*.html -> *.html
```

Shorthand in `src/` (see `tools/build.py`): `<t>English<fr>Français</t>` for inline text, `<p bi>English<fr>Français</p>`
for any element, `{{head:…}}`, `{{bar:<page>}}`, `{{foot}}` for the shared head, top bar and footer.

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
