# Mano-zmk

My keyboards (ZMK firmware) and my laptop's Karabiner config, in one place.

- **Cheat sheet:** open [docs/layout.html](docs/layout.html). It has every layer and the Mac setup steps.
- **Change a key:** edit `config/layout.dtsi`. The Corne and the Lily58 share it, so they always match. Then run `python3 scripts/layout_html.py` to refresh the cheat sheet, and push. GitHub Actions builds the firmware; download the `firmware` artifact from the run.
- **Keyboards:** Corne (`config/corne.*`), Lily58 (`config/lily58.*`), mano (`config/boards/shields/mano/`; not built, its build has failed since Aug 2026).
- **Laptop:** `karabiner/` is the live `~/.config/karabiner` folder (symlinked). See `karabiner/README.md`.
- **Design notes:** `docs/superpowers/`.
