# One layout, one branch: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the Corne and the Lily58 on one shared layout on `main`, with the Karabiner config (and a real Mac Fn key) in the same repo.

**Architecture:** `config/layout.dtsi` holds every layer once, as `LAYOUT_LAYER(...)` rows; `config/corne.keymap` and `config/lily58.keymap` each define that macro for their own key shape and include it. One `build.yaml` builds both keyboards. `karabiner/` is the live `~/.config/karabiner` (folder symlink). `docs/layout.html` is generated from `layout.dtsi` by `scripts/layout_html.py`.

**Tech Stack:** ZMK firmware (Zephyr devicetree + C preprocessor), GitHub Actions (`zmkfirmware/zmk/.github/workflows/build-user-config.yml@main`), Karabiner-Elements 16.3.0, Python 3 (stdlib), Apple clang (preprocessor only, for checks).

**Spec:** `docs/superpowers/specs/2026-09-26-one-layout-one-branch-design.md`

## Global Constraints

- Thumb names: Corne `L3 L2 L1 | R1 R2 R3` = key positions 36-41; Lily58 `L4 L3 L2 L1 | R1 R2 R3 R4` = 50-57 (L4/R4 unused).
- Both keyboards must be identical on the 42 shared keys in every layer.
- Layer numbers: BASE 0, MODS_R 1, MODS_L 2, NAV 3, MOUSE 4, NUM_L 5, NUM_R 6, MEDIA 7. MEDIA (conditional) must stay the highest.
- Keymaps live flat in `config/` (ZMK finds `<keyboard>.keymap` only there).
- Never `git merge` corne/lily58 without restoring `config/boards/shields/mano` afterwards (both branches delete it).
- Ask the user before: pushing `main`, editing the gist, deleting branches.
- Repo moves to `~/projects/Mano-zmk`; every path below uses the new location once Task 1 is done.
- The files in the code blocks below were staged and tested in `/tmp/kbviz/out/` (identical content). Checks use `/tmp/kbviz/verify_keymaps.py` with headers in `/tmp/kbviz/stub` (empty stand-ins) and `/tmp/kbviz/zmkinc` (ZMK + Zephyr `v4.1.0+zmk-fixes` dt-bindings).

---

### Task 1: Move the repo out of iCloud

**Files:** whole repo `~/Documents/projects/Mano-zmk` → `~/projects/Mano-zmk`; delete `.git/index 2`, `.git/index (1)`, `.git/ORIG_HEAD (1)`, `config/lily58 2.keymap`, `config/lily58 2.conf`.

- [ ] **Step 1: Check preconditions**

```bash
test ! -e ~/projects/Mano-zmk && echo "target free"
find ~/Documents/projects/Mano-zmk -name '*.icloud' | wc -l          # expect 0 (nothing evicted to iCloud)
git -C ~/Documents/projects/Mano-zmk status --short                   # expect only: config/lily58 2.*, docs/
```

- [ ] **Step 2: Move, clean iCloud junk, check integrity**

```bash
cd ~ && mv ~/Documents/projects/Mano-zmk ~/projects/Mano-zmk
cd ~/projects/Mano-zmk
rm ".git/index 2" ".git/index (1)" ".git/ORIG_HEAD (1)" "config/lily58 2.keymap" "config/lily58 2.conf"
git fsck --no-dangling                        # expect no errors
git status --short                            # expect only: docs/
```

- [ ] **Step 3: Keep Claude's saved notes for the new path**

```bash
mkdir -p ~/.claude/projects/-Users-mano-projects-Mano-zmk
cp -R ~/.claude/projects/-Users-mano-Documents-projects-Mano-zmk/memory ~/.claude/projects/-Users-mano-projects-Mano-zmk/
```

Tell the user to reopen `~/projects/Mano-zmk` in VS Code.

### Task 2: Put the corne and lily58 history on main (keeping mano)

**Files:** `config/corne.keymap`, `config/corne_left.conf`, `config/corne_right.conf`, `config/lily58.keymap`, `config/lily58.conf`, `config/lily58_left.conf` arrive from the branches; `config/boards/shields/settings_reset/` is deleted; `config/boards/shields/mano/` stays; `build.yaml` resolved in Task 3.

- [ ] **Step 1: Merge corne, restore mano**

```bash
cd ~/projects/Mano-zmk && git switch main
git merge --no-ff --no-commit corne
git checkout HEAD -- config/boards/shields/mano      # corne deleted it
git status --short                                   # settings_reset deleted, corne files added
git commit -m "Merge corne into main (keep mano)"
```

- [ ] **Step 2: Merge lily58, restore mano, take corne's build.yaml for now**

```bash
git merge --no-ff --no-commit lily58                 # stops: conflict in build.yaml
git checkout HEAD -- config/boards/shields/mano      # lily58 deleted it too
git checkout --ours build.yaml && git add build.yaml # replaced in Task 3
git commit -m "Merge lily58 into main (keep mano)"
```

- [ ] **Step 3: Verify nothing was lost**

```bash
git diff corne HEAD -- config/corne.keymap config/corne_left.conf config/corne_right.conf    # expect empty
git diff lily58 HEAD -- config/lily58.keymap config/lily58.conf config/lily58_left.conf     # expect empty
git diff 7be1b5c4 HEAD -- config/boards/shields/mano                                        # expect empty
git merge-base --is-ancestor corne main && git merge-base --is-ancestor lily58 main && echo "both merged"
test ! -e config/boards/shields/settings_reset && echo "stale settings_reset gone"
```

- [ ] **Step 4: Commit the design docs**

```bash
git add docs/superpowers && git commit -m "docs: design spec and implementation plan for one layout, one branch"
```

### Task 3: Shared layout, both keymaps, build config

**Files:**
- Create: `config/layout.dtsi`
- Replace: `config/corne.keymap`, `config/lily58.keymap`, `build.yaml`, `.github/workflows/build.yml`, `.gitignore`
- Test: `/tmp/kbviz/verify_keymaps.py` (throwaway; compares against the approved layout data in `/tmp/kbviz/gen7.py`)

**Interfaces:**
- Produces: macro `LAYOUT_LAYER(layer_node, layer_label, num_l, num_r, top_l, top_r, home_l, home_r, bot_l, bot_r, thumb_l, thumb_r)` (defined per board), combo positions `POS_S POS_D POS_F POS_J POS_K POS_L POS_SEMI` (per board), layer names `BASE MODS_R MODS_L NAV MOUSE NUM_L NUM_R MEDIA` (in layout.dtsi), behavior `&fnh` (hold-tap).

- [ ] **Step 1: The test**

```python
#!/usr/bin/env python3
"""Check config/corne.keymap and config/lily58.keymap against the approved layout.

Usage: python3 verify_keymaps.py <config dir>
Exit 0 and print "ALL CHECKS PASSED" if every check passes; otherwise list failures.

Pass 1 (stub headers): keycode names stay symbolic, so every binding can be compared
with the approved layout (/tmp/kbviz/gen7.py via make_dtsi.py's renames).
Pass 2 (real ZMK headers): every keycode must expand to a number; a leftover
UPPERCASE name means a typo or a keycode ZMK doesn't have.
"""
import contextlib
import importlib.util
import io
import re
import subprocess
import sys

CONFIG = sys.argv[1]
STUB = "/tmp/kbviz/stub"
REAL = "/tmp/kbviz/zmkinc"
LAYER_INDEX = {"BASE": 0, "MODS_R": 1, "MODS_L": 2, "NAV": 3, "MOUSE": 4, "NUM_L": 5, "NUM_R": 6, "MEDIA": 7}
ORDER = [("default_layer", "Base"), ("mods_r_layer", "R1 mods"), ("mods_l_layer", "L1 mods"),
         ("nav_layer", "L2 arrows"), ("mouse_layer", "R2 mouse"), ("num_l_layer", "R3 numbers"),
         ("num_r_layer", "L3 numbers"), ("media_layer", "Media")]
COMBOS = {"combo_esc": (14, 15), "combo_tab": (15, 16), "combo_enter": (19, 20),
          "combo_bspc": (20, 21), "combo_del": (21, 22)}
failures = []


def fail(msg):
    failures.append(msg)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, [path, "-"]
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    sys.argv = argv
    return mod


def preprocess(board, inc):
    r = subprocess.run(["clang", "-E", "-P", "-x", "assembler-with-cpp", "-nostdinc", "-undef",
                        "-D__DTS__", "-I", inc, f"{CONFIG}/{board}.keymap"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{board}: preprocessor failed: {r.stderr.strip()[:500]}")
        return ""
    return r.stdout


def layers(text):
    km = text[text.find('compatible = "zmk,keymap"'):]
    return [(m.group(1), m.group(2), [" ".join(t.split()) for t in re.findall(r"&[^&]+", m.group(3))])
            for m in re.finditer(r'(\w+)\s*\{\s*display-name\s*=\s*"([^"]*)"\s*;\s*bindings\s*=\s*<(.*?)>\s*;',
                                 km, re.S)]


mk = load("/tmp/kbviz/make_dtsi.py", "mk")
g = mk.g
SRC = {node: src for src, node, _, _ in mk.LAYERS}


def expected(board, node):
    data = (g.ca if board == "corne" else g.la)[SRC[node]]
    out = []
    for b in data:
        b = mk.fix(b)
        parts = b.split()
        if parts[0] in ("&mo", "&lt") and parts[1] in LAYER_INDEX:
            parts[1] = str(LAYER_INDEX[parts[1]])
        out.append(" ".join(parts))
    return out


for board, n, off in (("corne", 42, 0), ("lily58", 58, 12)):
    # ---- pass 1: symbolic comparison with the approved layout ----
    text = preprocess(board, STUB)
    if not text:
        continue
    got = layers(text)
    if [(a, b) for a, b, _ in got] != ORDER:
        fail(f"{board}: layer order/names {[(a, b) for a, b, _ in got]} != {ORDER}")
    for node, disp, binds in got:
        if len(binds) != n:
            fail(f"{board} {node}: {len(binds)} bindings, expected {n}")
            continue
        if node in SRC:
            exp = expected(board, node)
            diffs = [f"pos {p}: got '{a}' expected '{e}'" for p, (a, e) in enumerate(zip(binds, exp)) if a != e]
            if diffs:
                fail(f"{board} {node}: {len(diffs)} differences: " + "; ".join(diffs[:6]))
    for name, (a, b) in COMBOS.items():
        m = re.search(name + r"\s*\{[^}]*key-positions\s*=\s*<\s*(\d+)\s+(\d+)\s*>", text)
        want = (a + off, b + off)
        if not m or (int(m.group(1)), int(m.group(2))) != want:
            fail(f"{board} {name}: key-positions {m.groups() if m else None} != {want}")
    for rule, want in (("media_left", ("2", "3")), ("media_right", ("1", "4"))):
        m = re.search(rule + r"\s*\{\s*if-layers\s*=\s*<\s*(\d+)\s+(\d+)\s*>\s*;\s*then-layer\s*=\s*<\s*(\d+)\s*>", text)
        if not m or m.groups()[:2] != want or m.group(3) != "7":
            fail(f"{board} {rule}: {m.groups() if m else 'missing'} != if {want} then 7")
    # ---- pass 2: every keycode must exist in ZMK ----
    real = preprocess(board, REAL)
    for node, disp, binds in layers(real):
        for p, bnd in enumerate(binds):
            leftover = [w for w in re.findall(r"\b[A-Z_][A-Z0-9_]*\b", " ".join(bnd.split()[1:]))]
            if leftover:
                fail(f"{board} {node} pos {p}: unknown name(s) {leftover} in '{bnd}'")
    print(f"{board}: {len(got)} layers checked")

if failures:
    print("FAILED:")
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
```

- [ ] **Step 2: Run it on the merged (old) keymaps: expect FAIL** (old layer names/content)

Run: `python3 /tmp/kbviz/verify_keymaps.py ~/projects/Mano-zmk/config` → `FAILED:` with layer-order differences.

- [ ] **Step 3: Write `config/layout.dtsi`**

```c
/*
 * layout.dtsi: THE keyboard layout, shared by the Corne and the Lily58.
 * Change keys here only. corne.keymap and lily58.keymap just place these
 * rows on their own keys (the Corne skips the Lily58's number row).
 *
 * Each layer is written as rows of  <left half> , <right half> ,
 *   number row (Lily58 only), top, home, bottom: 6 keys per half
 *   thumbs: 3 per half, in the order L3 L2 L1 , R1 R2 R3
 *
 * Rules:
 *   - Keep exactly 6 keys per half-row and 3 per thumb half.
 *   - Never use // comments inside a #define (use slash-star comments).
 *   - MEDIA must stay the highest-numbered layer (it is a conditional layer).
 *   - After editing, refresh the cheat sheet: python3 scripts/layout_html.py
 */

#include <behaviors.dtsi>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/bt.h>
#include <dt-bindings/zmk/pointing.h>

#define BASE    0
#define MODS_R  1   /* hold R1 (space) */
#define MODS_L  2   /* hold L1 (backspace) */
#define NAV     3   /* hold L2 */
#define MOUSE   4   /* hold R2 */
#define NUM_L   5   /* hold R3 */
#define NUM_R   6   /* hold L3 */
#define MEDIA   7   /* hold L1+L2 or R1+R2; must stay the highest layer */

/ {
    behaviors {
        /* C and , : tap = the letter, hold = F18. Karabiner (karabiner/karabiner.json)
         * turns F18 into the real Mac Fn/Globe key. tap-preferred: typing "ct" or ",a"
         * quickly still gives the letters; only a deliberate 200 ms hold gives Fn. */
        fnh: fn_hold_tap {
            compatible = "zmk,behavior-hold-tap";
            #binding-cells = <2>;
            flavor = "tap-preferred";
            tapping-term-ms = <200>;
            quick-tap-ms = <150>;
            bindings = <&kp>, <&kp>;
        };
    };

    combos {
        compatible = "zmk,combos";
        /* Base layer only, and only after a 150 ms pause, so fast typing never fires them. */
        combo_esc   { timeout-ms = <50>; require-prior-idle-ms = <150>; key-positions = <POS_S POS_D>;    bindings = <&kp ESC>;    layers = <BASE>; };
        combo_tab   { timeout-ms = <50>; require-prior-idle-ms = <150>; key-positions = <POS_D POS_F>;    bindings = <&kp TAB>;    layers = <BASE>; };
        combo_enter { timeout-ms = <50>; require-prior-idle-ms = <150>; key-positions = <POS_J POS_K>;    bindings = <&kp RETURN>; layers = <BASE>; };
        combo_bspc  { timeout-ms = <50>; require-prior-idle-ms = <150>; key-positions = <POS_K POS_L>;    bindings = <&kp BSPC>;   layers = <BASE>; };
        combo_del   { timeout-ms = <50>; require-prior-idle-ms = <150>; key-positions = <POS_L POS_SEMI>; bindings = <&kp DELETE>; layers = <BASE>; };
    };

    conditional_layers {
        compatible = "zmk,conditional-layers";
        media_left  { if-layers = <MODS_L NAV>;   then-layer = <MEDIA>; };   /* L1 + L2 */
        media_right { if-layers = <MODS_R MOUSE>; then-layer = <MEDIA>; };   /* R1 + R2 */
    };

    keymap {
        compatible = "zmk,keymap";

    /* Normal typing. Thumbs: L3 L2 L1 | R1 R2 R3. */
    LAYOUT_LAYER(default_layer, "Base",
        &kp MINUS  &kp N1  &kp N2  &kp N3      &kp N4  &kp N5 ,   &kp N6  &kp N7  &kp N8          &kp N9   &kp N0    &kp EQUAL  ,   /* number row (Lily58 only) */
        &kp LBKT   &kp Q   &kp W   &kp E       &kp R   &kp T  ,   &kp Y   &kp U   &kp I           &kp O    &kp P     &kp RBKT   ,   /* top */
        &kp TAB    &kp A   &kp S   &kp D       &kp F   &kp G  ,   &kp H   &kp J   &kp K           &kp L    &kp SEMI  &kp APOS   ,   /* home */
        &kp ESC    &kp Z   &kp X   &fnh F18 C  &kp V   &kp B  ,   &kp N   &kp M   &fnh F18 COMMA  &kp DOT  &kp FSLH  &kp RETURN ,   /* bottom */
                                   &mo NUM_R  &mo NAV  &lt MODS_L BSPC ,   &lt MODS_R SPACE  &mo MOUSE  &mo NUM_L
    )

    /* Hold R1 (space): mods under the right hand, the left hand types letters. */
    LAYOUT_LAYER(mods_r_layer, "R1 mods",
        &trans   &trans  &trans  &trans  &trans  &trans ,   &none     &none      &none     &kp C_VOL_DN  &kp C_VOL_UP  &kp C_MUTE ,   /* number row (Lily58 only) */
        &trans   &trans  &trans  &trans  &trans  &trans ,   &none     &none      &none     &none         &none         &none      ,   /* top */
        &kp TAB  &trans  &trans  &trans  &trans  &trans ,   &kp BSLH  &kp RGUI   &kp RALT  &kp RSHFT     &none         &none      ,   /* home */
        &kp ESC  &trans  &trans  &trans  &trans  &trans ,   &kp PIPE  &kp RCTRL  &kp BSPC  &kp DELETE    &none         &kp RETURN ,   /* bottom */
                                 &none  &none  &trans   ,   &trans  &trans  &none
    )

    /* Hold L1 (backspace): mods under the left hand, the right hand types letters. L1 + A = Caps Lock. */
    LAYOUT_LAYER(mods_l_layer, "L1 mods",
        &kp C_BRI_DEC  &kp C_BRI_INC  &none      &none     &none      &none     ,   &trans  &trans  &trans  &trans  &trans  &trans     ,   /* number row (Lily58 only) */
        &none          &none          &none      &none     &none      &none     ,   &trans  &trans  &trans  &trans  &trans  &trans     ,   /* top */
        &kp TAB        &kp CAPS       &kp LSHFT  &kp LALT  &kp LGUI   &kp GRAVE ,   &trans  &trans  &trans  &trans  &trans  &trans     ,   /* home */
        &kp ESC        &none          &none      &none     &kp LCTRL  &kp TILDE ,   &trans  &trans  &trans  &trans  &trans  &kp RETURN ,   /* bottom */
                                                 &none  &trans  &trans          ,   &trans  &none  &none
    )

    /* Hold L2: arrows on the right, mods under the left hand. */
    LAYOUT_LAYER(nav_layer, "L2 arrows",
        &none    &none  &none      &none     &none      &none ,   &none            &none       &none     &none       &none  &none      ,   /* number row (Lily58 only) */
        &none    &none  &none      &none     &none      &none ,   &kp PG_UP        &kp HOME    &kp UP    &kp END     &none  &none      ,   /* top */
        &kp TAB  &none  &kp LSHFT  &kp LALT  &kp LGUI   &none ,   &kp PG_DN        &kp LEFT    &kp DOWN  &kp RIGHT   &none  &none      ,   /* home */
        &kp ESC  &none  &none      &none     &kp LCTRL  &none ,   &kp PRINTSCREEN  &kp RETURN  &kp BSPC  &kp DELETE  &none  &kp RETURN ,   /* bottom */
                                   &none  &none  &trans       ,   &trans  &none  &none
    )

    /* Hold R2: mouse on the left, clicks on L1/L2/L3, mods under the right hand. */
    LAYOUT_LAYER(mouse_layer, "R2 mouse",
        &bootloader  &studio_unlock  &none           &none           &none            &none          ,   &bt BT_CLR  &bt BT_SEL 0  &bt BT_SEL 1  &bt BT_SEL 2  &none  &none      ,   /* number row (Lily58 only) */
        &none        &none           &msc SCRL_LEFT  &mmv MOVE_UP    &msc SCRL_RIGHT  &msc SCRL_UP   ,   &none       &none         &none         &none         &none  &none      ,   /* top */
        &kp TAB      &none           &mmv MOVE_LEFT  &mmv MOVE_DOWN  &mmv MOVE_RIGHT  &msc SCRL_DOWN ,   &none       &kp RGUI      &kp RALT      &kp RSHFT     &none  &none      ,   /* home */
        &kp ESC      &none           &none           &none           &none            &none          ,   &none       &kp RCTRL     &kp BSPC      &kp DELETE    &none  &kp RETURN ,   /* bottom */
                                                     &mkp MCLK  &mkp RCLK  &mkp LCLK                 ,   &trans  &trans  &none
    )

    /* Hold R3: numbers on the left home row, F1-F6 above, mods under the right hand. */
    LAYOUT_LAYER(num_l_layer, "R3 numbers",
        &trans     &trans  &trans  &trans  &trans  &trans ,   &trans    &trans     &trans    &trans     &trans  &trans ,   /* number row (Lily58 only) */
        &kp F1     &kp F2  &kp F3  &kp F4  &kp F5  &kp F6 ,   &none     &none      &none     &none      &none   &none  ,   /* top */
        &kp MINUS  &kp N1  &kp N2  &kp N3  &kp N4  &kp N5 ,   &kp BSLH  &kp RGUI   &kp RALT  &kp RSHFT  &none   &none  ,   /* home */
        &trans     &none   &none   &none   &none   &none  ,   &kp BSLH  &kp RCTRL  &none     &none      &none   &none  ,   /* bottom */
                                   &none  &none  &trans   ,   &trans  &none  &trans
    )

    /* Hold L3: numbers on the right home row, F7-F12 above, mods under the left hand. */
    LAYOUT_LAYER(num_r_layer, "L3 numbers",
        &trans  &trans  &trans     &trans    &trans     &trans    ,   &trans  &trans  &trans  &trans   &trans   &trans    ,   /* number row (Lily58 only) */
        &none   &none   &none      &none     &none      &none     ,   &kp F7  &kp F8  &kp F9  &kp F10  &kp F11  &kp F12   ,   /* top */
        &none   &none   &kp LSHFT  &kp LALT  &kp LGUI   &kp GRAVE ,   &kp N6  &kp N7  &kp N8  &kp N9   &kp N0   &kp EQUAL ,   /* home */
        &none   &none   &none      &none     &kp LCTRL  &kp TILDE ,   &none   &none   &none   &none    &none    &trans    ,   /* bottom */
                                   &trans  &none  &trans          ,   &trans  &none  &none
    )

    /* Hold L1+L2 or R1+R2: MacBook media row on the F1-F12 keys, Bluetooth, bootloader. */
    LAYOUT_LAYER(media_layer, "Media",
        &none         &none         &none         &none          &none  &none          ,   &none       &none     &none       &none       &none         &none        ,   /* number row (Lily58 only) */
        &kp C_BRI_DN  &kp C_BRI_UP  &kp LC(UP)    &kp LG(SPACE)  &none  &none          ,   &kp C_PREV  &kp C_PP  &kp C_NEXT  &kp C_MUTE  &kp C_VOL_DN  &kp C_VOL_UP ,   /* top */
        &bt BT_CLR    &bt BT_SEL 0  &bt BT_SEL 1  &bt BT_SEL 2   &none  &studio_unlock ,   &none       &none     &none       &none       &none         &none        ,   /* home */
        &bootloader   &sys_reset    &none         &none          &none  &none          ,   &none       &none     &none       &none       &sys_reset    &bootloader  ,   /* bottom */
                                                  &none  &trans  &trans                ,   &trans  &trans  &none
    )
    };
};
```

- [ ] **Step 4: Replace `config/corne.keymap`**

```c
/*
 * Corne: 42 keys. The layout itself lives in layout.dtsi, shared with the Lily58.
 * This file only says where those keys sit on the Corne.
 */

/* Combo key positions on the Corne (rows of 12; the home row starts at 12). */
#define POS_S    14
#define POS_D    15
#define POS_F    16
#define POS_J    19
#define POS_K    20
#define POS_L    21
#define POS_SEMI 22

/* The Corne has no number row, so num_l and num_r are dropped. No // comments in here. */
#define LAYOUT_LAYER(layer_node, layer_label, num_l, num_r, top_l, top_r, home_l, home_r, bot_l, bot_r, thumb_l, thumb_r) \
    layer_node {                     \
        display-name = layer_label;  \
        bindings = <                 \
            top_l   top_r            \
            home_l  home_r           \
            bot_l   bot_r            \
            thumb_l thumb_r          \
        >;                           \
    };

#include "layout.dtsi"
```

- [ ] **Step 5: Replace `config/lily58.keymap`**

```c
/*
 * Lily58: 58 keys = the Corne's 42 + a number row, 2 middle keys and one extra
 * thumb key per side (L4 / R4). The layout itself lives in layout.dtsi.
 */

/* Combo key positions on the Lily58 (the Corne's + 12: one extra row on top). */
#define POS_S    26
#define POS_D    27
#define POS_F    28
#define POS_J    31
#define POS_K    32
#define POS_L    33
#define POS_SEMI 34

/* The 2 middle keys and L4 / R4 are unused (&none). No // comments in here. */
#define LAYOUT_LAYER(layer_node, layer_label, num_l, num_r, top_l, top_r, home_l, home_r, bot_l, bot_r, thumb_l, thumb_r) \
    layer_node {                              \
        display-name = layer_label;           \
        bindings = <                          \
            num_l   num_r                     \
            top_l   top_r                     \
            home_l  home_r                    \
            bot_l   &none &none   bot_r       \
            &none   thumb_l  thumb_r   &none  \
        >;                                    \
    };

#include "layout.dtsi"
```

- [ ] **Step 6: Run the test: expect `ALL CHECKS PASSED`**

Run: `python3 /tmp/kbviz/verify_keymaps.py ~/projects/Mano-zmk/config`

- [ ] **Step 7: `build.yaml`, CI trigger, `.gitignore`**

`build.yaml`:

```yaml
# Every keyboard in this repo, built in one GitHub Actions run.
# Download the "firmware" artifact from the run to get all .uf2 files.
# The layout is in config/layout.dtsi (shared by the Corne and the Lily58).

include:
  # Corne (left half is the central half and runs ZMK Studio)
  - board: nice_nano//zmk
    shield: corne_left
    snippet: studio-rpc-usb-uart
  - board: nice_nano//zmk
    shield: corne_right

  # Lily58 (left half is the central half and runs ZMK Studio)
  - board: nice_nano//zmk
    shield: lily58_left
    snippet: studio-rpc-usb-uart
  - board: nice_nano//zmk
    shield: lily58_right

  # Settings reset (ZMK's built-in one; works for both keyboards)
  - board: nice_nano//zmk
    shield: settings_reset

  # mano (config/boards/shields/mano) is not built: its build has failed since
  # Aug 2026 (CONFIG_WS2812_STRIP no longer exists in ZMK). Fix it, then uncomment.
  # - board: xiao_ble//zmk
  #   shield: mano_left
  # - board: xiao_ble//zmk
  #   shield: mano_right
```

`.github/workflows/build.yml`:

```yaml
on:
  push:
    # Changes to only these paths don't need new firmware.
    paths-ignore:
      - "karabiner/**"
      - "docs/**"
      - "scripts/**"
      - "README.md"
  pull_request:
  workflow_dispatch:

jobs:
  build:
    uses: zmkfirmware/zmk/.github/workflows/build-user-config.yml@main
```

`.gitignore`:

```
.DS_Store
karabiner/automatic_backups/
```

- [ ] **Step 8: Commit**

```bash
git add config/layout.dtsi config/corne.keymap config/lily58.keymap build.yaml .github/workflows/build.yml .gitignore
git commit -m "feat: one shared layout for corne and lily58 (layout.dtsi)"
```

### Task 4: Layout page (docs/layout.html) and README

**Files:** Create `scripts/layout_html.py`, `docs/layout.html` (generated), `README.md`.

- [ ] **Step 1: Write `scripts/layout_html.py`**

```python
#!/usr/bin/env python3
"""Make docs/layout.html (the cheat sheet) from config/layout.dtsi.

Run from the repo root after changing config/layout.dtsi:
    python3 scripts/layout_html.py
Standard library only. The page shows every layer (the keys both keyboards
share, plus the Lily58's number row) and the one-time Mac setup steps.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "config" / "layout.dtsi"
OUT = ROOT / "docs" / "layout.html"

THUMBS = ["L3", "L2", "L1", "R1", "R2", "R3"]      # key positions 36..41
SYM = {
    "LBKT": "[", "RBKT": "]", "SEMI": ";", "APOS": "'", "COMMA": ",", "DOT": ".", "FSLH": "/",
    "BSLH": "\\", "PIPE": "|", "MINUS": "-", "EQUAL": "=", "GRAVE": "`", "TILDE": "~",
    "TAB": "tab", "ESC": "esc", "RETURN": "⏎", "BSPC": "⌫", "DELETE": "⌦", "SPACE": "␣",
    "PG_UP": "PgUp", "PG_DN": "PgDn", "HOME": "Home", "END": "End", "UP": "↑", "DOWN": "↓",
    "LEFT": "←", "RIGHT": "→", "PRINTSCREEN": "PrtSc", "CAPS": "caps",
}
SYM.update({f"N{i}": str(i) for i in range(10)})
MODS = {"GUI": ("⌘", "cmd"), "ALT": ("⌥", "opt"), "SHFT": ("⇧", "shift"), "CTRL": ("⌃", "ctrl")}
MEDIA = {"C_BRI_DN": ("🔅", "bri−"), "C_BRI_UP": ("🔆", "bri+"), "C_BRI_DEC": ("🔅", "bri−"),
         "C_BRI_INC": ("🔆", "bri+"), "LC(UP)": ("⌃↑", "Mission"), "LG(SPACE)": ("⌘␣", "Spotlight"),
         "C_PREV": ("⏮", "prev"), "C_PP": ("⏯", "play"), "C_NEXT": ("⏭", "next"),
         "C_MUTE": ("🔇", "mute"), "C_VOL_DN": ("🔉", "vol−"), "C_VOL_UP": ("🔊", "vol+")}
LAYER_KEY = {"MODS_R": "mods", "MODS_L": "mods", "NAV": "arrows", "MOUSE": "mouse",
             "NUM_L": "123", "NUM_R": "123", "MEDIA": "media"}
ARROW = {"UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→"}


def strip_comments(s):
    return re.sub(r"/\*.*?\*/", " ", s, flags=re.S)


def split_args(s):
    args, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            args.append(cur)
            cur = ""
        else:
            cur += ch
    args.append(cur)
    return [a.strip() for a in args]


def parse(text):
    layer_index = {m.group(1): int(m.group(2)) for m in re.finditer(r"#define\s+(\w+)\s+(\d+)\b", text)}
    rules = [(m.group(1), m.group(2).split(), m.group(3).strip()) for m in re.finditer(
        r"(\w+)\s*\{\s*if-layers\s*=\s*<([^>]*)>\s*;\s*then-layer\s*=\s*<([^>]*)>", text)]
    layers = []
    for m in re.finditer(r"(?:/\*((?:(?!\*/).)*)\*/\s*)?LAYOUT_LAYER\(", text, re.S):
        start, depth, i = m.end(), 1, m.end()
        while depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        args = split_args(strip_comments(text[start:i - 1]))
        assert len(args) == 12, f"LAYOUT_LAYER needs 12 arguments, got {len(args)}: {args[:2]}"
        rows = [[" ".join(t.split()) for t in re.findall(r"&[^&]+", a)] for a in args[2:]]
        num = rows[0] + rows[1]
        core = rows[2] + rows[3] + rows[4] + rows[5] + rows[6] + rows[7] + rows[8] + rows[9]
        assert len(num) == 12 and len(core) == 42, f"{args[0]}: {len(num)} number-row keys, {len(core)} keys"
        layers.append({"node": args[0], "name": args[1].strip('"'),
                       "about": " ".join((m.group(1) or "").split()), "num": num, "core": core})
    return layer_index, rules, layers


def label(b):
    """-> (main text, small text, css class)"""
    beh, *args = b[1:].split()
    if beh == "none":
        return "", "", "none"
    if beh == "kp":
        k = args[0]
        if k in MEDIA:
            return (*MEDIA[k], "")
        for suffix, (s, w) in MODS.items():
            if k.endswith(suffix) and len(k) <= 6:
                return s, w, "mod"
        return SYM.get(k, k), "", ""
    if beh == "fnh":
        return SYM.get(args[1], args[1]), "hold: fn", ""
    if beh == "lt":
        return SYM.get(args[1], args[1]), "hold: " + LAYER_KEY.get(args[0], args[0].lower()), ""
    if beh == "mo":
        return LAYER_KEY.get(args[0], args[0].lower()), "hold", ""
    if beh == "mkp":
        return {"LCLK": "left", "RCLK": "right", "MCLK": "middle"}[args[0]], "click", ""
    if beh == "mmv":
        return "🖱" + ARROW[args[0].split("_")[1]], "move", ""
    if beh == "msc":
        return ARROW[args[0].split("_")[1]], "scroll", ""
    if beh == "bt":
        return ("BT", "clear", "") if args[0] == "BT_CLR" else (f"BT {int(args[1]) + 1}", "device", "")
    return {"sys_reset": ("reset", "", ""), "bootloader": ("boot", "loader", ""),
            "studio_unlock": ("studio", "unlock", "")}.get(beh, (beh, "", ""))


def held_thumbs(layer, layer_index, rules, base):
    """Thumb positions to highlight, plus alternative thumb groups (for two-thumb holds)."""
    idx = {v: k for k, v in layer_index.items()}

    def thumbs_for(name):
        return [p for p in range(36, 42) if base[p].split()[:2] in (["&mo", name], ["&lt", name])]

    name = next((n for n, i in layer_index.items() if n in LAYER_KEY and i == LAYER_ORDER[layer["node"]]), None)
    direct = thumbs_for(name) if name else []
    if direct:
        return direct, []
    groups = [sum((thumbs_for(n) for n in ifs), []) for _, ifs, then in rules if then == name]
    return (groups[0] if groups else []), groups[1:]


def key_html(b, base_b, cls_extra, held=False):
    if held:
        return f'<div class="k held {cls_extra}"><span class="m">HELD</span></div>'
    if b == "&trans":
        main, small, cls = label(base_b)
        cls = "pass"
    else:
        main, small, cls = label(b)
    inner = f'<span class="m">{html.escape(main)}</span>'
    if small:
        inner += f'<span class="s">{html.escape(small)}</span>'
    return f'<div class="k {cls} {cls_extra}">{inner}</div>'


def board_html(layer, base, held):
    cells = []
    for c in range(12):   # Lily58-only number row
        col = c + 1 if c < 6 else c + 2
        base_b = BASE_NUM[c]
        cells.append(f'<div style="grid-row:1;grid-column:{col}">'
                     f'{key_html(layer["num"][c], base_b, "lily")}</div>')
    for p in range(36):
        r, c = divmod(p, 12)
        col = c + 1 if c < 6 else c + 2
        cells.append(f'<div style="grid-row:{r + 2};grid-column:{col}">'
                     f'{key_html(layer["core"][p], base[p], "")}</div>')
    for i, p in enumerate(range(36, 42)):
        col = [4, 5, 6, 8, 9, 10][i]
        cells.append(f'<div class="thumbcell" style="grid-row:5;grid-column:{col}">'
                     f'{key_html(layer["core"][p], base[p], "thumb", held=p in held)}'
                     f'<span class="tn">{THUMBS[i]}</span></div>')
    return f'<div class="kb">{"".join(cells)}</div>'


CSS = """
:root { --bg:#f5f5f7; --card:#fff; --line:#d1d1d6; --soft:#e5e5e7; --text:#1d1d1f; --dim:#86868b;
        --faint:#aeaeb2; --accent:#0071e3; --mod:#ff9f0a; --k:48px; }
@media (prefers-color-scheme: dark) { :root { --bg:#1d1d1f; --card:#2d2d2f; --line:#424245; --soft:#3d3d3f;
        --text:#f5f5f7; --dim:#98989d; --faint:#636366; --accent:#0a84ff; } }
* { box-sizing: border-box; }
body { margin: 0; padding: 28px; background: var(--bg); color: var(--text);
       font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
h1 { margin: 0 0 4px; font-size: 26px; } h2 { margin: 34px 0 10px; font-size: 20px; }
h3 { margin: 0 0 2px; font-size: 16px; }
.sub { color: var(--dim); margin: 0 0 18px; max-width: 900px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px 20px; max-width: 900px; }
table { border-collapse: collapse; } td { padding: 4px 18px 4px 0; vertical-align: top; }
td:first-child { font-weight: 600; white-space: nowrap; }
.grid { display: flex; flex-wrap: wrap; gap: 30px 46px; }
.layer p { margin: 0 0 10px; font-size: 13px; color: var(--dim); max-width: 660px; min-height: 38px; }
.kb { display: grid; gap: 4px; grid-template-columns: repeat(6, var(--k)) 20px repeat(6, var(--k));
      grid-template-rows: calc(var(--k) * .8) repeat(3, var(--k)) calc(var(--k) + 22px); }
.k { height: 100%; border: 1px solid var(--line); border-radius: 8px; background: var(--card);
     display: flex; flex-direction: column; align-items: center; justify-content: center;
     text-align: center; line-height: 1.1; font-size: 15px; overflow: hidden; }
.k .s { font-size: 9px; color: var(--dim); white-space: nowrap; }
.k.lily { opacity: .75; border-style: dotted; font-size: 13px; }
.k.none { background: transparent; border: 1px dashed var(--soft); }
.k.pass { background: transparent; color: var(--faint); }
.k.mod { background: rgba(255,159,10,.16); border-color: var(--mod); font-weight: 600; }
.k.held { background: var(--accent); border-color: var(--accent); color: #fff; font-size: 12px; font-weight: 600; }
.thumbcell { display: flex; flex-direction: column; align-items: stretch; }
.thumbcell .k { height: var(--k); }
.thumbcell .tn { font-size: 10px; color: var(--accent); text-align: center; font-weight: 600; }
.legend span { display: inline-block; padding: 1px 8px; border-radius: 6px; margin-right: 8px; font-size: 13px; }
code { background: var(--soft); padding: 1px 5px; border-radius: 5px; font-size: 13px; }
ol li, ul li { margin: 4px 0; } .steps { max-width: 900px; }
"""

SETUP = """
<h2>Set up a Mac (once)</h2>
<div class="steps card">
<h3>1. Flash both keyboards</h3>
<ol>
  <li>GitHub → <b>Actions</b> → the latest run → download <b>firmware</b>.</li>
  <li>For each half: plug it in by USB, double-tap its reset button, and drag the matching file
      (<code>corne_left…uf2</code> / <code>corne_right…uf2</code>, or <code>lily58_left…</code> / <code>lily58_right…</code>)
      onto the drive that appears.</li>
  <li>If you ever <b>saved</b> changes in ZMK Studio: open Studio and click <b>Restore Stock Settings</b>.
      Otherwise the keyboard keeps the old layout.</li>
</ol>
<h3>2. Turn on the Fn key (Karabiner)</h3>
<p>Holding <b>C</b> or <b>,</b> sends F18. Karabiner turns F18 into the Mac's real <b>Fn / 🌐</b> key, so 🌐+F (full
screen), Fn+← (Home), window tiling, emoji and dictation all work. ZMK can't send a real Fn by itself: a Mac only accepts
Fn from Apple-made keyboards.</p>
<ol>
  <li>The <code>karabiner/</code> folder in this repo <i>is</i> Karabiner's settings folder. On a new Mac, link it once:<br>
      <code>mv ~/.config/karabiner ~/.config/karabiner.old; ln -s ~/projects/Mano-zmk/karabiner ~/.config/karabiner</code></li>
  <li>Karabiner-Elements → Settings → <b>Devices</b>: the keyboard shown as <b>Corne</b> or <b>Lily58</b>
      (maker "ZMK Project") must have <b>Modify events</b> switched on. The repo's config switches it on; check it once.</li>
  <li>Test: open <b>Karabiner-EventViewer</b> and hold C. You should see <code>fn</code>. Then try 🌐+F in any window.</li>
  <li>F1–F12 on the keyboards stay real F-keys (the config says so for these keyboards). For media keys, hold L1+L2 or R1+R2.</li>
  <li>On a Mac without this Karabiner config, holding C or , does nothing extra; tapping still types c and ,.</li>
</ol>
<h3>3. Choose what a single tap of Fn does</h3>
<p>System Settings → Keyboard → <b>Press 🌐 key to</b> (on this Mac: <i>Change Input Source</i>). Pick <i>Show Emoji &amp;
Symbols</i> or <i>Start Dictation</i> if you prefer.</p>
</div>
"""

LAYER_ORDER = {}
BASE_NUM = []


def main():
    global LAYER_ORDER, BASE_NUM
    text = SRC.read_text()
    layer_index, rules, layers = parse(text)
    LAYER_ORDER = {layer["node"]: i for i, layer in enumerate(layers)}
    base = layers[0]["core"]
    BASE_NUM = layers[0]["num"]
    rule_rows = []
    parts = []
    for layer in layers:
        held, alts = held_thumbs(layer, layer_index, rules, base)
        how = " + ".join(THUMBS[p - 36] for p in held)
        if alts:
            how += "  (or " + ", ".join(" + ".join(THUMBS[p - 36] for p in g) for g in alts) + ")"
        title = f"Hold {how}" if held else layer["name"]
        if held:
            rule_rows.append(f"<tr><td>Hold {html.escape(how)}</td><td>{html.escape(layer['about'])}</td></tr>")
        parts.append(f'<div class="layer"><h3>{html.escape(title)} · {html.escape(layer["name"])}</h3>'
                     f'<p>{html.escape(layer["about"])}</p>{board_html(layer, base, held)}</div>')
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Keyboard layout: Corne + Lily58</title><style>{CSS}</style></head><body>
<h1>Keyboard layout: Corne + Lily58</h1>
<p class="sub">Both keyboards use exactly the same layout (from <code>config/layout.dtsi</code>). The Lily58 also has a
number row (the dotted top row). Thumb names are under each thumb key: <b>L3 L2 L1 | R1 R2 R3</b>, counted from the
middle outward (the Lily58's extra outer thumb keys L4 / R4 are unused).</p>
<div class="card"><b>Rule: hold any thumb and ⌘ ⌥ ⇧ ⌃ are under that same hand.</b>
<table>{''.join(rule_rows)}</table>
<p class="legend" style="margin:10px 0 0"><span style="background:var(--accent);color:#fff">thumb you hold</span>
<span style="background:rgba(255,159,10,.16);border:1px solid var(--mod)">⌘ ⌥ ⇧ ⌃</span>
<span style="color:var(--faint)">grey = types the normal key</span>
Combos (plain typing, after a short pause): S+D esc · D+F tab · J+K ⏎ · K+L ⌫ · L+; ⌦</p></div>
<h2>Layers</h2>
<div class="grid">{''.join(parts)}</div>
{SETUP}
</body></html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(layers)} layers)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate and check the page**

```bash
python3 scripts/layout_html.py        # expect: wrote docs/layout.html (8 layers)
grep -c 'class="kb"' docs/layout.html  # expect 8
grep -q 'Hold L1 + L2  (or R1 + R2)' docs/layout.html && grep -q 'hold: fn' docs/layout.html && grep -q '>caps<' docs/layout.html && echo ok
```

- [ ] **Step 3: Write `README.md`**

```markdown
# Mano-zmk

My keyboards (ZMK firmware) and my laptop's Karabiner config, in one place.

- **Cheat sheet:** open [docs/layout.html](docs/layout.html). It has every layer and the Mac setup steps.
- **Change a key:** edit `config/layout.dtsi`. The Corne and the Lily58 share it, so they always match. Then run `python3 scripts/layout_html.py` to refresh the cheat sheet, and push. GitHub Actions builds the firmware; download the `firmware` artifact from the run.
- **Keyboards:** Corne (`config/corne.*`), Lily58 (`config/lily58.*`), mano (`config/boards/shields/mano/`; not built, its build has failed since Aug 2026).
- **Laptop:** `karabiner/` is the live `~/.config/karabiner` folder (symlinked). See `karabiner/README.md`.
- **Design notes:** `docs/superpowers/`.
```

- [ ] **Step 4: Commit**

```bash
git add scripts/layout_html.py docs/layout.html README.md && git commit -m "docs: layout cheat sheet (generated from layout.dtsi) and README"
```

### Task 5: Karabiner config in the repo, real Fn for the ZMK keyboards

**Files:** Create `karabiner/karabiner.json` (via script below), `karabiner/assets/complex_modifications/*.json` (copied), `karabiner/README.md`. Symlink `~/.config/karabiner` → `~/projects/Mano-zmk/karabiner`.

- [ ] **Step 1: The update script** (`/tmp/kbviz/karabiner_update.py`)

```python
#!/usr/bin/env python3
"""Update karabiner.json for the ZMK keyboards (Corne, Lily58). Run once.

Usage: python3 karabiner_update.py <in karabiner.json> <out karabiner.json>
1. Every existing rule gets a device_if condition: built-in keyboard only, so the laptop's
   Space layer and combos can never run on top of the ZMK keyboards.
2. New first rule: F18 from the ZMK keyboards -> the real Mac Fn key.
3. New device entry for the ZMK keyboards (all ZMK boards share vendor 7504 / product 24926):
   "ignore": false (Karabiner ignores them by default because they are also pointing devices),
   and F1-F12 mapped to themselves so they stay F-keys instead of turning into media keys.
The script refuses to run twice on the same file.
"""
import json
import sys

ZMK = {"vendor_id": 7504, "product_id": 24926}
BUILT_IN = {"type": "device_if", "identifiers": [{"is_built_in_keyboard": True}]}
FN_RULE_DESC = "ZMK keyboards (Corne, Lily58): F18 = the real Mac Fn / Globe key (hold C or , on the keyboard)"

src, dst = sys.argv[1], sys.argv[2]
cfg = json.load(open(src))
profile = next(p for p in cfg["profiles"] if p.get("selected"))
rules = profile["complex_modifications"]["rules"]
if any(r["description"] == FN_RULE_DESC for r in rules):
    sys.exit("already updated: the Fn rule is present")

for rule in rules:
    for m in rule["manipulators"]:
        m.setdefault("conditions", []).append(BUILT_IN)

rules.insert(0, {
    "description": FN_RULE_DESC,
    "manipulators": [{
        "type": "basic",
        "from": {"key_code": "f18", "modifiers": {"optional": ["any"]}},
        "to": [{"key_code": "fn"}],
        "conditions": [{"type": "device_if", "identifiers": [ZMK]}],
    }],
})

profile.setdefault("devices", []).append({
    "identifiers": {"is_keyboard": True, "is_pointing_device": True, **ZMK},
    "ignore": False,
    "fn_function_keys": [{"from": {"key_code": f"f{i}"}, "to": [{"key_code": f"f{i}"}]} for i in range(1, 13)],
})

with open(dst, "w") as f:
    json.dump(cfg, f, indent=4, ensure_ascii=False)
    f.write("\n")
print(f"wrote {dst}: {len(rules)} rules, {len(profile['devices'])} device entries")
```

- [ ] **Step 2: Build the repo copy and check it**

```bash
mkdir -p karabiner/assets/complex_modifications
cp ~/.config/karabiner/assets/complex_modifications/*.json karabiner/assets/complex_modifications/
python3 /tmp/kbviz/karabiner_update.py ~/.config/karabiner/karabiner.json karabiner/karabiner.json
python3 -m json.tool karabiner/karabiner.json > /dev/null && echo valid
```

Expected: `wrote karabiner/karabiner.json: 5 rules, 2 device entries`, `valid`. A second run must print `already updated`.

- [ ] **Step 3: `karabiner/README.md`**

```markdown
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
```

- [ ] **Step 4: Link it and restart Karabiner** (backup already at `/tmp/kbviz/karabiner-backup-2026-09-26`)

```bash
mv ~/.config/karabiner ~/.config/karabiner.before-repo-2026-09-26
ln -s ~/projects/Mano-zmk/karabiner ~/.config/karabiner
launchctl kickstart -k gui/$(id -u)/org.pqrs.service.agent.Karabiner-Console-User-Server
sleep 3; ls -la ~/.config/karabiner   # expect a symlink to the repo folder
```

- [ ] **Step 5: Verify Karabiner loaded it without errors**

Check the newest Karabiner log lines for `karabiner.json` load messages and no `error`; confirm `karabiner_cli --list-connected-devices` still lists the Corne. Ask the user to test the laptop: hold Space + J/K/L/I (arrows), F+J (Esc).

- [ ] **Step 6: Commit**

```bash
git add karabiner && git commit -m "feat(karabiner): config lives in the repo; F18 from ZMK keyboards = real Mac Fn"
```

### Task 6: Independent review before anything leaves the Mac

- [ ] **Step 1:** Run a review workflow: a ZMK-correctness reviewer (devicetree syntax, behaviors, conditional layers, Studio), a layout reviewer (keymaps vs spec table, both boards), and a Karabiner reviewer (JSON semantics vs Karabiner 16.3 docs). Fix confirmed findings, re-run `verify_keymaps.py`, commit fixes.

### Task 7: Push main and watch the build (ask the user first)

- [ ] **Step 1:** Ask the user. Then `git push origin main`.
- [ ] **Step 2:** `gh run watch` on the new run. Expected: 5 build jobs green (corne_left, corne_right, lily58_left, lily58_right, settings_reset) and a `firmware` artifact.
- [ ] **Step 3:** If a job fails: read its log (`gh run view --log-failed`), fix, re-run Task 3's test, commit, push.

### Task 8: Point the gist to the repo (ask the user first)

- [ ] **Step 1:** Replace the gist README and remove its karabiner.json:

```bash
gh gist edit df54f1a2df275be634aa51a45f142a12 --filename README.md /tmp/kbviz/gist_README.md
gh gist edit df54f1a2df275be634aa51a45f142a12 --remove karabiner.json
```

Gist README content (`/tmp/kbviz/gist_README.md`):

```markdown
# Moved

This Karabiner-Elements config now lives in my keyboard repo, next to the ZMK keyboards it goes with:

**https://github.com/emmanuelgr/Mano-zmk/tree/main/karabiner**

(It is also a working setup: the repo's `karabiner/` folder is linked as `~/.config/karabiner`. See its README.)
```

### Task 9: Delete the old branches (ask the user first)

- [ ] **Step 1:** `git branch --merged main` must list corne, lily58 and mano. Then:

```bash
git branch -d corne lily58 mano
git push origin --delete corne lily58 mano
```

### Task 10: Hand-over

- [ ] **Step 1:** Tell the user: download `firmware`, flash all four halves, "Restore Stock Settings" in ZMK Studio if they ever saved there, test Fn (hold C + F = full screen), and open `docs/layout.html`.
