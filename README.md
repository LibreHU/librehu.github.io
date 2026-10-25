# librehu.github.io

LibreHU website, published by GitHub Pages at <https://librehu.github.io>.
Site de LibreHU, publié par GitHub Pages sur <https://librehu.github.io>.

- `index.html`: features, downloads (latest build of each app and edition), install steps, compatibility, FAQ.
- `headunits.html`: Android head unit platforms (chip, CPU, architecture, real Android version and the one
  manufacturers display), with sources.
- `assets/`: stylesheet (light / dark from the system), `lang.js` (EN / FR buttons), favicon, screenshots.

## Languages / Langues

Both languages are in each page (`lang="en"` and `lang="fr"` elements); CSS shows one. A script in `<head>` picks it
before drawing: the saved choice (`localStorage`), else the browser's first French or English language
(`navigator.languages`), else English. Without JavaScript the page shows English.

Les deux langues sont dans chaque page ; un script dans `<head>` choisit avant l'affichage : le choix enregistré,
sinon la première langue française ou anglaise du navigateur, sinon l'anglais.

## Editing / Modifier

Plain HTML and CSS, no build step: edit, commit, push; GitHub Pages publishes the default branch. Every text goes in
twice (EN then FR). Download links point to the rolling `latest-<branch>` releases of each repository.

HTML et CSS simples, sans compilation. Chaque texte est écrit deux fois (EN puis FR).
