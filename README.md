# Freedoom in your browser

**[Play online](https://dzod992-bit.github.io/freedoom-web/)** — desktop Chrome or Edge recommended.

Chocolate Doom compiled with Emscripten, SDL2, SDL2_mixer and Asyncify. Includes Freedoom 2 v0.13.0. Saves are stored locally in IndexedDB.

WASD: move; mouse: turn; click/Ctrl: fire; Space: use; Shift: run; F2: save; F3: load; Esc: menu/release mouse.

The initial download is approximately 31 MB. No account or installation is needed.

## Source and licenses

[Corresponding source](source/) includes the engine archive, patches, build scripts and browser integration. See [build instructions](source/README.md).

Chocolate Doom and engine modifications: GPL-2.0-or-later. Freedoom: BSD-3-Clause. Third-party notices are in [licenses/](licenses/).

## Hosting

GitHub Pages serves the main branch root. `.nojekyll` keeps compiled assets intact. This repository contains only the static release and its corresponding source.
