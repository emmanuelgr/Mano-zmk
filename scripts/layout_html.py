#!/usr/bin/env python3
"""Make docs/layout.html (the cheat sheet) from config/layout.dtsi.

Run from the repo root after changing config/layout.dtsi:
    python3 scripts/layout_html.py
Standard library only. The page shows a shortcut list (every way to get
backspace, arrows, mods, media keys ... worked out from the layers), every
layer (the keys both keyboards share, plus the Lily58's number row) and the
one-time Mac setup steps.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "config" / "layout.dtsi"
POS = ROOT / "config" / "corne.keymap"   # combo key numbers (POS_K ...) use the Corne's 42-key numbering
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
        if k == "F18":   # Karabiner turns F18 into the Mac's real Fn
            return "🌐", "fn", ""
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


def key_html(b, base_b, cls_extra, held=False, alt=False):
    if held:
        return f'<div class="k held {cls_extra}"><span class="m">HELD</span></div>'
    if alt:   # the other thumb pair that opens the same two-thumb layer
        return f'<div class="k held alt {cls_extra}"><span class="m">or</span></div>'
    if b == "&trans":
        main, small, cls = label(base_b)
        cls = "pass"
    else:
        main, small, cls = label(b)
    inner = f'<span class="m">{html.escape(main)}</span>'
    if small:
        inner += f'<span class="s">{html.escape(small)}</span>'
    return f'<div class="k {cls} {cls_extra}">{inner}</div>'


def board_html(layer, base, held, alts=()):
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
                     f'{key_html(layer["core"][p], base[p], "thumb", held=p in held, alt=p in alts)}'
                     f'<span class="tn">{THUMBS[i]}</span></div>')
    return f'<div class="kb">{"".join(cells)}</div>'


def parse_combos(text):
    """-> [(key positions, binding)] for every combo in layout.dtsi."""
    pos = {m.group(1): int(m.group(2)) for m in re.finditer(r"#define\s+(POS_\w+)\s+(\d+)", POS.read_text())}
    combos = []
    for m in re.finditer(r"combo_\w+\s*\{([^}]*)\}", text):
        body = m.group(1)
        keys = re.search(r"key-positions\s*=\s*<([^>]*)>", body).group(1).split()
        binding = " ".join(re.search(r"bindings\s*=\s*<([^>]*)>", body).group(1).split())
        combos.append(([pos[k] if k in pos else int(k) for k in keys], binding))
    return combos


def key_name(base, p):
    """What is printed on key p of the base layer (thumbs by their name)."""
    return THUMBS[p - 36] if p >= 36 else label(base[p])[0]


def kbd(s):
    return f"<kbd>{html.escape(s)}</kbd>"


def tap_target(b):
    """The binding a plain tap of b produces."""
    beh, *a = b[1:].split()
    return f"&kp {a[1]}" if beh in ("lt", "fnh") else b


# The shortcut list: (group, [(what you want, [bindings that give it])]). "ALT+&kp BSPC" means: a layer
# where an Alt key and backspace are both under your fingers while one thumb is held.
SHORTCUTS = [
    ("Editing", [
        ("⌫ backspace", ["&kp BSPC"]),
        ("⌦ forward delete", ["&kp DELETE"]),
        ("⌥⌫ delete the word before", ["ALT+&kp BSPC"]),
        ("⌘⌫ delete to the start of the line", ["GUI+&kp BSPC"]),
        ("⌥⌦ delete the word after", ["ALT+&kp DELETE"]),
        ("⏎ enter", ["&kp RETURN"]),
        ("esc", ["&kp ESC"]),
        ("tab", ["&kp TAB"]),
        ("caps lock", ["&kp CAPS"]),
    ]),
    ("Moving around", [
        ("← ↓ ↑ → arrows", ["&kp LEFT", "&kp DOWN", "&kp UP", "&kp RIGHT"]),
        ("Home / End", ["&kp HOME", "&kp END"]),
        ("Page up / down", ["&kp PG_UP", "&kp PG_DN"]),
        ("Print screen", ["&kp PRINTSCREEN"]),
    ]),
    ("Modifiers", [
        ("⌘ command", ["&kp LGUI", "&kp RGUI"]),
        ("⌥ option", ["&kp LALT", "&kp RALT"]),
        ("⇧ shift", ["&kp LSHFT", "&kp RSHFT"]),
        ("⌃ control", ["&kp LCTRL", "&kp RCTRL"]),
        ("🌐 Fn (needs Karabiner, see below)", ["&kp F18"]),
    ]),
    ("Numbers, F-keys, symbols", [
        ("1 2 3 4 5", [f"&kp N{i}" for i in range(1, 6)]),
        ("6 7 8 9 0", [f"&kp N{i}" for i in (6, 7, 8, 9, 0)]),
        ("F1 … F6", [f"&kp F{i}" for i in range(1, 7)]),
        ("F7 … F12", [f"&kp F{i}" for i in range(7, 13)]),
        ("- =", ["&kp MINUS", "&kp EQUAL"]),
        ("\\ |", ["&kp BSLH", "&kp PIPE"]),
        ("` ~", ["&kp GRAVE", "&kp TILDE"]),
    ]),
    ("Mouse", [
        ("move ← ↓ ↑ →", ["&mmv MOVE_LEFT", "&mmv MOVE_DOWN", "&mmv MOVE_UP", "&mmv MOVE_RIGHT"]),
        ("scroll ← → ↑ ↓", ["&msc SCRL_LEFT", "&msc SCRL_RIGHT", "&msc SCRL_UP", "&msc SCRL_DOWN"]),
        ("click left / right / middle", ["&mkp LCLK", "&mkp RCLK", "&mkp MCLK"]),
    ]),
    ("Media", [
        ("🔅 🔆 brightness", ["&kp C_BRI_DN", "&kp C_BRI_UP"]),
        ("Mission Control / Spotlight", ["&kp LC(UP)", "&kp LG(SPACE)"]),
        ("⏮ ⏯ ⏭", ["&kp C_PREV", "&kp C_PP", "&kp C_NEXT"]),
        ("🔇 🔉 🔊", ["&kp C_MUTE", "&kp C_VOL_DN", "&kp C_VOL_UP"]),
    ]),
    ("The keyboard itself", [
        ("Bluetooth: device 1 / 2 / 3", ["&bt BT_SEL 0", "&bt BT_SEL 1", "&bt BT_SEL 2"]),
        ("Bluetooth: forget the current device", ["&bt BT_CLR"]),
        ("unlock ZMK Studio", ["&studio_unlock"]),
        ("bootloader (to flash)", ["&bootloader"]),
        ("restart", ["&sys_reset"]),
    ]),
]


def collect_ways(layers, layer_index, rules, combos):
    """binding -> [(kind, holds, press)]: every way the layout produces that binding.
    kind: tap (a plain key), combo (two keys together), holdkey (hold a letter), layer (hold thumb(s) + key).
    holds: thumb names to hold, alternatives as a tuple. press: HTML for the key(s) to press."""
    base = layers[0]["core"]
    ways = {}

    def add(target, *way):
        ways.setdefault(target, []).append(way)

    for p, b in enumerate(base):
        beh = b[1:].split()[0]
        if beh in ("mo", "none", "trans"):
            continue
        add(tap_target(b), "tap", (), kbd(key_name(base, p)))
        if beh == "fnh":
            add(f"&kp {b.split()[1]}", "holdkey", (), kbd(key_name(base, p)))
    for keys, b in combos:
        add(b, "combo", (), "+".join(kbd(key_name(base, k)) for k in keys))
    for layer in layers[1:]:
        held, alts = held_thumbs(layer, layer_index, rules, base)
        holds = tuple("+".join(THUMBS[p - 36] for p in g) for g in [held] + alts)
        core = layer["core"]
        for p, b in enumerate(core):
            if b not in ("&trans", "&none"):
                add(b, "layer", holds, kbd(key_name(base, p)))
        for mod, names in (("ALT", ("&kp LALT", "&kp RALT")), ("GUI", ("&kp LGUI", "&kp RGUI"))):
            for mp in [p for p, b in enumerate(core) if b in names][:1]:
                for target in ("&kp BSPC", "&kp DELETE"):
                    for tp in [p for p, b in enumerate(core) if b == target][:1]:
                        add(f"{mod}+{target}", "layer", holds,
                            f"{kbd(key_name(base, mp))} + {kbd(key_name(base, tp))}")
    return ways


def row_html(ways, targets):
    singles, by_holds = [], {}
    for t in targets:
        for kind, holds, press in ways.get(t, []):
            if kind == "layer":
                presses = by_holds.setdefault(holds, [])
                if press not in presses:
                    presses.append(press)
            else:
                singles.append({"tap": f"tap {press}", "combo": f"{press} <small>together</small>",
                                "holdkey": f"hold {press}"}[kind])
    by_press = {}   # the same key(s) under several thumbs -> one entry
    for holds, presses in by_holds.items():
        by_press.setdefault(" ".join(presses), []).extend(holds)
    return " &nbsp;·&nbsp; ".join(singles + [f"hold {' / '.join(kbd(h) for h in holds)} + {press}"
                                            for press, holds in by_press.items()])


def shortcuts_html(ways):
    groups = []
    for group, rows in SHORTCUTS:
        trs = []
        for what, targets in rows:
            how = row_html(ways, targets)
            if not how:
                print(f"warning: no key gives {what!r} ({targets}); check SHORTCUTS", file=sys.stderr)
                how = "—"
            trs.append(f"<tr><td>{html.escape(what)}</td><td>{how}</td></tr>")
        groups.append(f'<div><h3>{html.escape(group)}</h3><table>{"".join(trs)}</table></div>')
    return f'<h2>Shortcuts</h2><div class="card sc">{"".join(groups)}</div>'


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
.k.held.alt { background: transparent; color: var(--accent); border: 2px dashed var(--accent); }
.thumbcell { display: flex; flex-direction: column; align-items: stretch; }
.thumbcell .k { height: var(--k); }
.thumbcell .tn { font-size: 10px; color: var(--accent); text-align: center; font-weight: 600; }
.legend span { display: inline-block; padding: 1px 8px; border-radius: 6px; margin-right: 8px; font-size: 13px; }
code { background: var(--soft); padding: 1px 5px; border-radius: 5px; font-size: 13px; }
kbd { display: inline-block; border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 5px; padding: 0 6px;
      background: var(--card); font: 600 12px/1.6 inherit; margin: 1px 0; white-space: nowrap; }
.sc { display: flex; flex-wrap: wrap; gap: 18px 40px; max-width: 1400px; }
.sc h3 { margin-bottom: 6px; } .sc table { font-size: 14px; } .sc td { padding: 3px 14px 3px 0; line-height: 1.7; }
.sc td:first-child { font-weight: 500; } .sc small { color: var(--dim); font-size: 12px; }
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
screen), 🌐+E (emoji), Fn+← (Home) and window tiling (🌐⌃ + arrows) work. On the arrows layer (hold L2), C is Fn too,
so the order you press them in doesn't matter. ZMK can't send a real Fn by itself: a Mac only accepts Fn from
Apple-made keyboards.</p>
<ol>
  <li>Install <a href="https://karabiner-elements.pqrs.org/">Karabiner-Elements</a>, open it once and allow what it asks
      for (driver extension, Input Monitoring).</li>
  <li>The <code>karabiner/</code> folder in this repo <i>is</i> Karabiner's settings folder. Link it once (Karabiner's docs
      require the restart at the end):<br>
      <code>mkdir -p ~/.config; mv ~/.config/karabiner ~/.config/karabiner.old; ln -s ~/projects/Mano-zmk/karabiner ~/.config/karabiner;
      launchctl kickstart -k gui/$(id -u)/org.pqrs.service.agent.Karabiner-Console-User-Server</code></li>
  <li>Karabiner-Elements → Settings → <b>Devices</b>: the keyboard shown as <b>Corne</b> or <b>Lily58</b>
      (maker "ZMK Project") must have <b>Modify events</b> switched on. The repo's config switches it on; check it once.</li>
  <li>Test: open <b>Karabiner-EventViewer</b>, hold C and press ←. You should see <code>fn</code> with
      <code>left_arrow</code>. Holding C on its own shows nothing: the keyboards' Fn only works together with another
      key, so a long press of C never switches your input source by accident.</li>
  <li>F1–F12 on the keyboards stay real F-keys (the config says so for these keyboards). For media keys, hold L1+L2 or R1+R2.</li>
  <li>On a Mac without this Karabiner config, holding C or , does nothing extra; tapping still types c and ,.</li>
</ol>
<p>A single tap of the laptop's own 🌐 key still does what System Settings → Keyboard → <b>Press 🌐 key to</b> says
(on this Mac: <i>Change Input Source</i>).</p>
</div>

<h2>Change keys in the browser (ZMK Studio)</h2>
<div class="steps card">
<ol>
  <li>Plug the keyboard's <b>left</b> half in by USB. Only the left half runs Studio, and a browser can reach it over
      USB only (the ZMK Studio desktop app can also use Bluetooth).</li>
  <li>Open <a href="https://zmk.studio/">zmk.studio</a> in <b>Chrome</b> or <b>Edge</b> (not Safari or Firefox),
      choose USB and pick the keyboard.</li>
  <li><b>Unlock</b> it on the keyboard: hold <b>L1 + L2</b> (or R1 + R2) for a moment, then press <b>G</b>
      ("studio unlock"). On the Lily58, holding R2 and pressing the number-row key above Q also works. It locks
      again after 10 minutes without Studio activity, or when you close the tab or unplug.</li>
  <li>Click a key, choose what it should do, then <b>Save</b>.</li>
</ol>
<p><b>Good to know:</b> Studio changes are stored only on that one keyboard. They don't reach the other keyboard,
<code>config/layout.dtsi</code> or this page, and firmware you flash later keeps the Studio version until you click
<b>Restore Stock Settings</b>. To make a change permanent on both keyboards, put it in <code>config/layout.dtsi</code>.
Studio also can't change the combos, the two-thumb Media rule, hold timings, or the Fn hold on C and , (current ZMK
Studio refuses F13–F24).</p>
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
    combos = parse_combos(text)
    combo_text = " · ".join(f"{'+'.join(key_name(base, k) for k in keys)} {label(b)[0]}" for keys, b in combos)
    shortcuts = shortcuts_html(collect_ways(layers, layer_index, rules, combos))
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
                     f'<p>{html.escape(layer["about"])}</p>{board_html(layer, base, held, sum(alts, []))}</div>')
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
Combos (plain typing, after a short pause): {html.escape(combo_text)}</p></div>
{shortcuts}
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
