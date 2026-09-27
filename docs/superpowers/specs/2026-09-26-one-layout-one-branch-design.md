# One layout, one branch: design

Date: 2026-09-26 · Status: waiting for your OK

## Goal

- The Corne and the Lily58 use **the same layout, written once**, so they can't drift apart again.
- Everything lives on **`main`**. No more one-branch-per-keyboard.
- The laptop's **Karabiner** config lives in the same repo, replacing the gist.

## Thumb names

```
Corne:           L3  L2  L1   |   R1  R2  R3
Lily58:      L4  L3  L2  L1   |   R1  R2  R3  R4      (L4, R4 unused)
```

## The layout (identical on both keyboards)

**Rule: hold any thumb and ⌘ ⌥ ⇧ ⌃ are under that same hand.**

| Hold | That hand | Other hand |
|---|---|---|
| nothing (tap) | L1 = ⌫ · R1 = ␣ | |
| **L1** or **R1** | ⌘ ⌥ ⇧ ⌃ (the top row above them is blank) | letters: the Lily58's ⌫/␣ layers as they are today, minus their F-keys |
| **R3** | ⌘ ⌥ ⇧ ⌃ | left: `- 1 2 3 4 5` on the home row, F1–F6 above (same keys as the Corne's ␣ layer today) |
| **L3** | ⌘ ⌥ ⇧ ⌃ | right: `6 7 8 9 0 =` on the home row, F7–F12 above (same keys as the Corne's ⌫ layer today) |
| **L2** | ⌘ ⌥ ⇧ ⌃ | arrows (as today) |
| **R2** | ⌘ ⌥ ⇧ ⌃ | mouse; left click on L1, right click on L2, middle click on L3 |
| **L1 + L2** or **R1 + R2** = "Media" | top row = the MacBook's media row, on the same keys as F1–F12: 🔅 🔆 Mission Control, Spotlight, (blank), (blank), ⏮ ⏯ ⏭ 🔇 🔉 🔊 · below: Bluetooth 1–3, Studio unlock, reset, bootloader | |

- **Unchanged:** the letters; the five combos (S+D esc, D+F tab, J+K ⏎, K+L ⌫, L+; ⌦, which fire only after a 150 ms pause).
- **Fn = hold C or ,**. It becomes the **real Mac Fn/🌐** (🌐+F fullscreen, Fn+arrows, window tiling, emoji, dictation). ZMK's own Globe code only half-works on a Mac, so the keyboard sends a spare key (F18) and Karabiner turns it into the real Fn. This works on Macs running this repo's Karabiner config.
- **Removed:** the Corne's home-row mods, and the F-keys from the L1/R1 layers. F-keys now live in one place only, above the numbers.
- **Small additions:** **Caps Lock = hold L1 + A** (a free key just left of ⇧). ⏎ on M and PrtSc on N in the arrows layer. The Lily58 keeps its number row and its number-row extras (volume, brightness, bootloader, Studio unlock).
- **Bluetooth:** 3 slots on both keyboards. The Lily58 drops slots 4 and 5.
- **After the pre-push review (2026-09-26):** C on the arrows layer (L2) is Fn too, so Fn+arrows works in any order. Bluetooth 1–3 and clear sit on the Media layer's bottom row (X C V B), away from the mouse keys. The keyboards' Fn is `lazy` in Karabiner: it only acts together with another key.
- **How the two-thumb hold works:** ZMK `conditional_layers`. While the L1 (or R1) layer and the L2 (or R2) layer are both on, the Media layer turns on. I checked that this works in current ZMK `main`. The Media layer must be numbered above the layers it depends on, or keys get hidden; the build will order them that way. Numbers use a single thumb (L3/R3) because they're used far more often than media or Bluetooth.

## The repo afterwards (`main` only)

```
Mano-zmk/
  README.md                 short map of the repo
  build.yaml                builds corne_left, corne_right, lily58_left, lily58_right, settings_reset
  .github/workflows/build.yml   unchanged, except Karabiner-only changes skip the firmware build
  config/
    layout.dtsi             THE layout: the only file to edit to change keys
    corne.keymap            small: puts layout.dtsi on the Corne's 42 keys
    lily58.keymap           small: puts layout.dtsi on the Lily58's 58 keys
    corne_left.conf, corne_right.conf, lily58.conf, lily58_left.conf   (as today)
    west.yml                (as today)
    boards/shields/mano/…   kept, not built (it has failed to build since Aug 2026)
  karabiner/                the laptop config: karabiner.json, README.md, assets/
  docs/superpowers/specs/   this file
```

- `layout.dtsi` writes each layer once, as 5 rows: the Lily58's number row, 3 letter rows, and thumbs. The Corne skips the number row.
- The files sit flat in `config/` because ZMK only finds a keymap there, by the keyboard's name. Separate folders per keyboard would need a non-standard build workaround.

## Karabiner

- `karabiner/` **is** the live `~/.config/karabiner` folder, linked with a folder symlink as Karabiner's docs require. Linking only the file breaks Karabiner's reloading.
- `karabiner.json` moves in with the laptop's behaviour **unchanged**; the only addition is the Fn rule below. The README is corrected: it wrongly says the laptop mirrors the boards key for key. `automatic_backups/` is left out of git.
- **One new rule, only for the two ZMK keyboards: F18 → the real Fn.** The laptop's existing rules are limited to the built-in keyboard, so they can never affect the boards.
- The gist is replaced by a short note pointing to the repo.
- Making the laptop match the new board layout is a **separate, later step**. For example, holding Space gives arrows on the laptop but modifiers on the boards, and the combos differ.

## Steps, in order

1. **Move the repo** from `~/Documents/projects/Mano-zmk` to `~/projects/Mano-zmk`, out of iCloud. Delete iCloud's junk copies: `.git/index 2`, `.git/index (1)`, `.git/ORIG_HEAD (1)` and `config/lily58 2.*` (older copies of committed files). You then reopen the folder in VS Code.
2. **Merge into `main`:** merge the `corne` and `lily58` history in. Each merge would delete the mano files, so restore them every time. Delete `main`'s broken settings_reset copy; ZMK's built-in one works. Commit this spec.
3. **Write** `layout.dtsi`, the two small keymaps, `build.yaml` and the README.
4. **Check before anything leaves your Mac:**
   - Run both keymaps through the same preprocessor ZMK uses and compare every key with this layout. Zero differences are allowed.
   - Confirm the mano files are unchanged.
   - Confirm nothing from the corne/lily58 branches is lost.
5. **Karabiner:** create the folder, add the Fn rule, symlink it and restart Karabiner. Check that the laptop still behaves as before. Replace the gist with a pointer, after asking you.
6. **Ask you, then push `main`.** Wait for a green GitHub build that produces all 5 firmware files.
7. **After you confirm:** delete the `corne`, `lily58` and `mano` branches, both locally and on GitHub.

After flashing: if you ever **saved** changes in ZMK Studio, click "Restore Stock Settings" in Studio, or the old layout stays.

## Not in this change

- Changing the laptop's Karabiner layout (next step).
- Fixing mano's build.
- Pinning the ZMK version. It's optional, and would stop an upstream ZMK change from breaking every build at once.
