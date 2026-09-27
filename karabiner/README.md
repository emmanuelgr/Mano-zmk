# Karabiner-Elements (laptop keyboard + the Fn key for the ZMK keyboards)

This folder **is** Karabiner's settings folder: `~/.config/karabiner` is a symlink to it.
Karabiner's docs require linking the whole folder, not `karabiner.json` alone
(a linked file stops Karabiner from noticing changes). `automatic_backups/` is not tracked by git.

Link it on a Mac (once):

```sh
mv ~/.config/karabiner ~/.config/karabiner.old
ln -s ~/projects/Mano-zmk/karabiner ~/.config/karabiner
launchctl kickstart -k gui/$(id -u)/org.pqrs.service.agent.Karabiner-Console-User-Server
```

## What it does

### ZMK keyboards (Corne, Lily58)

- **Fn key:** holding **C** or **,** on the keyboards sends F18, and Karabiner turns F18 into the Mac's real
  **Fn / 🌐** key. ZMK can't send a real Fn by itself, because macOS only accepts it from Apple-made keyboards.
- **F1–F12 stay F-keys** on these keyboards (per-device `fn_function_keys`). Media keys are on the keyboards' Media layer.
- Karabiner normally ignores ZMK keyboards (they are also mice), so the config sets `"ignore": false` for them.
  All ZMK keyboards share vendor 7504 / product 24926, so one entry covers both.

### Built-in laptop keyboard only

Every rule below has a `device_if is_built_in_keyboard` condition, so none of it touches the ZMK keyboards.

**Space layer (hold Spacebar):**

| Combo | Sends | | Combo | Sends |
|---|---|---|---|---|
| Space + **I** | ↑ Up | | Space + **S** | Left Shift |
| Space + **K** | ↓ Down | | Space + **D** | Left Option |
| Space + **J** | ← Left | | Space + **F** | Left Command |
| Space + **L** | → Right | | Space + **V** | Left Control |
| Space + **Y** | Page Up | | | |
| Space + **H** | Page Down | | | |
| Space + **U** | Home | | | |
| Space + **O** | End | | | |

Tapping Spacebar alone still types a space.

**Press two keys together** (50 ms window, either order): **F + J** = Escape, **J + K** = Enter, **K + X** = forward Delete.
These pairs almost never appear next to each other in real words, which is why they're safe without a pause guard
(the ZMK keyboards use different combos, protected by a "only after a pause" setting that Karabiner doesn't have).

**Caps Lock ↔ Control** are swapped.

## Differences from the ZMK keyboards

The laptop is not a copy of the keyboards' layout. On the laptop, holding Space gives arrows and modifiers
(like the keyboards' L2 layer); on the keyboards, holding space (R1) gives modifiers for the other hand's letters.
The combos also differ. Making the laptop match more closely is a possible later change.
