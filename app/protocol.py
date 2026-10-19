from collections import OrderedDict

APP_NAME = "Standalone Keypad Studio"
APP_VERSION = "1.0.0"
FW_TAG = "STANDALONE_KEYPAD"
PROTOCOL_VER = 2

PRESS_FX = [("Instant", 0), ("Smooth", 1), ("Ultra Smooth", 2), ("Bouncy", 3)]
IDLE_FX = [("Off", 0), ("Static", 1), ("Breathing", 2), ("Rainbow", 3), ("Wave", 4), ("Sparkle", 5)]


def fx_label(table, value):
    for label, v in table:
        if v == value:
            return label
    return str(value)


_keycodes = []


def _add(code, name, label, group):
    _keycodes.append({"code": code, "name": name, "label": label, "group": group})


for _c in "abcdefghijklmnopqrstuvwxyz":
    _add(ord(_c), _c.upper(), _c.upper(), "Letters")
for _c in "0123456789":
    _add(ord(_c), _c, _c, "Digits")
for _c, _lbl in [("-", "-"), ("=", "="), ("[", "["), ("]", "]"), ("\\", "\\"), (";", ";"), ("'", "'"), ("`", "`"), (",", ","), (".", "."), ("/", "/"), (" ", "Space")]:
    _add(ord(_c), _lbl, _lbl, "Symbols")
for _c, _lbl in [("!", "!"), ("@", "@"), ("#", "#"), ("$", "$"), ("%", "%"), ("^", "^"), ("&", "&"), ("*", "*"), ("(", "("), (")", ")"), ("_", "_"), ("+", "+"), ("{", "{"), ("}", "}"), ("|", "|"), (":", ":"), ('"', '"'), ("<", "<"), (">", ">"), ("?", "?"), ("~", "~")]:
    _add(ord(_c), _lbl, _lbl, "Symbols")
for _code, _n, _l in [(0x80, "LCtrl", "L CTRL"), (0x81, "LShift", "L SHIFT"), (0x82, "LAlt", "L ALT"), (0x83, "LWin", "L WIN"), (0x84, "RCtrl", "R CTRL"), (0x85, "RShift", "R SHIFT"), (0x86, "RAlt", "R ALT"), (0x87, "RWin", "R WIN")]:
    _add(_code, _n, _l, "Modifiers")
for _code, _n, _l in [(0xD7, "Right", "→"), (0xD8, "Left", "←"), (0xD9, "Down", "↓"), (0xDA, "Up", "↑"), (0xD2, "Home", "Home"), (0xD5, "End", "End"), (0xD3, "PgUp", "PgUp"), (0xD6, "PgDn", "PgDn"), (0xD1, "Insert", "Ins"), (0xD4, "Delete", "Del")]:
    _add(_code, _n, _l, "Navigation")
for _code, _n, _l in [(0xB0, "Enter", "Enter"), (0xB1, "Esc", "Esc"), (0xB2, "Backspace", "Bksp"), (0xB3, "Tab", "Tab"), (0xC1, "CapsLock", "Caps"), (0xED, "Menu", "Menu"), (0xCE, "PrintScreen", "PrtSc"), (0xCF, "ScrollLock", "ScrLk"), (0xD0, "Pause", "Pause"), (0xDB, "NumLock", "NumLk")]:
    _add(_code, _n, _l, "Special")
for _i in range(1, 13):
    _add(0xC1 + _i, "F%d" % _i, "F%d" % _i, "Function")

CODE_TO_LABEL = {k["code"]: k["label"] for k in _keycodes}
NAME_TO_CODE = {k["name"]: k["code"] for k in _keycodes}
GROUPS = OrderedDict()
for _k in _keycodes:
    GROUPS.setdefault(_k["group"], []).append(_k)


def label_for(code):
    if code in CODE_TO_LABEL:
        return CODE_TO_LABEL[code]
    if 32 <= int(code) < 127:
        return chr(int(code))
    return "0x%02X" % int(code)


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])


def hex_to_rgb(value):
    v = value.lstrip("#")
    return [int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)]


def default_config():
    return {
        "led": [[255, 255, 255] for _ in range(7)],
        "ena": [1] * 7,
        "press": [255, 255, 255],
        "brightIdle": 0,
        "brightPress": 51,
        "pressFx": 1,
        "idleFx": 0,
        "speed": 5,
        "surround": 0,
        "surroundStrength": 40,
        "keymap": [ord("w"), ord("a"), ord("s"), ord("d"), 0x81, 0x80, 0x20],
    }


def cmd_set_led(i, rgb):
    return "SET LED:%d:%d:%d:%d" % (i, rgb[0], rgb[1], rgb[2])


def cmd_set_ena(i, v):
    return "SET ENA:%d:%d" % (i, 1 if v else 0)


def cmd_set_press(rgb):
    return "SET PRESS:%d:%d:%d" % (rgb[0], rgb[1], rgb[2])


def cmd_set_bright(bi, bp):
    return "SET BRIGHT:%d:%d" % (bi, bp)


def cmd_set_fx(pfx, ifx, spd, sur, ss):
    return "SET FX:%d:%d:%d:%d:%d" % (pfx, ifx, spd, 1 if sur else 0, ss)


def cmd_set_key(i, code):
    return "SET KEY:%d:%d" % (i, code)


def parse_get(lines):
    out = {"led": [None] * 7, "ena": [1] * 7, "keymap": [None] * 7}
    for ln in lines:
        p = ln.split(":")
        try:
            if p[0] == "LED" and len(p) == 6:
                i = int(p[1])
                if 0 <= i < 7:
                    out["led"][i] = [int(p[2]), int(p[3]), int(p[4])]
                    out["ena"][i] = int(p[5])
            elif p[0] == "PRESS" and len(p) == 4:
                out["press"] = [int(p[1]), int(p[2]), int(p[3])]
            elif p[0] == "BRIGHT" and len(p) == 3:
                out["brightIdle"] = int(p[1])
                out["brightPress"] = int(p[2])
            elif p[0] == "FX" and len(p) == 6:
                out["pressFx"] = int(p[1])
                out["idleFx"] = int(p[2])
                out["speed"] = int(p[3])
                out["surround"] = int(p[4])
                out["surroundStrength"] = int(p[5])
            elif p[0] == "KEY" and len(p) == 3:
                i = int(p[1])
                if 0 <= i < 7:
                    out["keymap"][i] = int(p[2])
        except ValueError:
            continue
    return out


def gradient(a, b, n=7):
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append(tuple(round(a[j] + (b[j] - a[j]) * t) for j in range(3)))
    return out


RAINBOW7 = [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (160, 0, 255)]

PRESETS = [
    {"name": "Stealth Default", "led": (255, 255, 255), "press": (255, 255, 255), "brightIdle": 0, "brightPress": 51, "pressFx": 1, "idleFx": 0, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "Cyan Pulse", "led": (0, 170, 255), "press": (140, 240, 255), "brightIdle": 40, "brightPress": 210, "pressFx": 1, "idleFx": 2, "speed": 5, "surround": 1, "surroundStrength": 35},
    {"name": "Cyberpunk", "led": (255, 180, 0), "press": (255, 0, 160), "brightIdle": 35, "brightPress": 220, "pressFx": 0, "idleFx": 4, "speed": 6, "surround": 1, "surroundStrength": 40},
    {"name": "Matrix", "led": (0, 255, 80), "press": (170, 255, 170), "brightIdle": 30, "brightPress": 200, "pressFx": 1, "idleFx": 5, "speed": 7, "surround": 0, "surroundStrength": 40},
    {"name": "Synthwave", "led": (255, 50, 170), "press": (90, 230, 255), "brightIdle": 40, "brightPress": 230, "pressFx": 2, "idleFx": 2, "speed": 4, "surround": 1, "surroundStrength": 35},
    {"name": "Ice", "led": (110, 190, 255), "press": (235, 250, 255), "brightIdle": 35, "brightPress": 230, "pressFx": 1, "idleFx": 1, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "Inferno", "led": (255, 70, 0), "press": (255, 210, 110), "brightIdle": 35, "brightPress": 230, "pressFx": 3, "idleFx": 2, "speed": 6, "surround": 1, "surroundStrength": 45},
    {"name": "Toxic", "led": (140, 255, 0), "press": (255, 0, 240), "brightIdle": 35, "brightPress": 220, "pressFx": 3, "idleFx": 4, "speed": 6, "surround": 0, "surroundStrength": 40},
    {"name": "Vaporwave", "led": gradient((255, 110, 200), (110, 220, 255)), "press": (255, 255, 255), "brightIdle": 35, "brightPress": 220, "pressFx": 1, "idleFx": 2, "speed": 4, "surround": 1, "surroundStrength": 30},
    {"name": "Blood Moon", "led": (130, 0, 0), "press": (255, 60, 60), "brightIdle": 30, "brightPress": 230, "pressFx": 3, "idleFx": 2, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "Deep Ocean", "led": (0, 50, 130), "press": (90, 210, 255), "brightIdle": 30, "brightPress": 210, "pressFx": 1, "idleFx": 4, "speed": 5, "surround": 1, "surroundStrength": 35},
    {"name": "Sunset Drive", "led": gradient((255, 120, 0), (255, 0, 110)), "press": (255, 255, 255), "brightIdle": 35, "brightPress": 220, "pressFx": 1, "idleFx": 1, "speed": 4, "surround": 0, "surroundStrength": 40},
    {"name": "Aurora", "led": gradient((0, 255, 170), (150, 80, 255)), "press": (210, 255, 235), "brightIdle": 35, "brightPress": 220, "pressFx": 2, "idleFx": 2, "speed": 3, "surround": 1, "surroundStrength": 40},
    {"name": "Mono Chrome", "led": (255, 255, 255), "press": (255, 255, 255), "brightIdle": 25, "brightPress": 200, "pressFx": 1, "idleFx": 1, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "Retro Amber", "led": (255, 140, 10), "press": (255, 225, 140), "brightIdle": 35, "brightPress": 220, "pressFx": 1, "idleFx": 2, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "RGB Gamer", "led": RAINBOW7, "press": (255, 255, 255), "brightIdle": 40, "brightPress": 230, "pressFx": 1, "idleFx": 1, "speed": 5, "surround": 1, "surroundStrength": 30},
    {"name": "Neon Pink", "led": (255, 0, 130), "press": (255, 140, 220), "brightIdle": 35, "brightPress": 230, "pressFx": 2, "idleFx": 2, "speed": 5, "surround": 1, "surroundStrength": 40},
    {"name": "Emerald", "led": (0, 210, 110), "press": (150, 255, 200), "brightIdle": 30, "brightPress": 220, "pressFx": 1, "idleFx": 2, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "Royal Purple", "led": (120, 0, 255), "press": (210, 160, 255), "brightIdle": 35, "brightPress": 225, "pressFx": 2, "idleFx": 1, "speed": 5, "surround": 1, "surroundStrength": 35},
    {"name": "Hacker", "led": (0, 255, 60), "press": (255, 255, 255), "brightIdle": 25, "brightPress": 220, "pressFx": 0, "idleFx": 5, "speed": 9, "surround": 0, "surroundStrength": 40},
    {"name": "Lovebug", "led": (255, 40, 90), "press": (255, 180, 200), "brightIdle": 35, "brightPress": 225, "pressFx": 3, "idleFx": 2, "speed": 4, "surround": 1, "surroundStrength": 45},
    {"name": "Cold Steel", "led": (150, 170, 190), "press": (255, 255, 255), "brightIdle": 30, "brightPress": 210, "pressFx": 0, "idleFx": 1, "speed": 5, "surround": 0, "surroundStrength": 40},
    {"name": "Disco", "led": RAINBOW7, "press": (255, 255, 255), "brightIdle": 45, "brightPress": 235, "pressFx": 0, "idleFx": 5, "speed": 8, "surround": 1, "surroundStrength": 40},
    {"name": "Zen", "led": (90, 255, 220), "press": (200, 255, 245), "brightIdle": 30, "brightPress": 200, "pressFx": 1, "idleFx": 2, "speed": 3, "surround": 0, "surroundStrength": 40},
]


def preset_matches(cfg, preset):
    for key in ("press", "brightIdle", "brightPress", "pressFx", "idleFx", "speed", "surround", "surroundStrength"):
        if key in preset and cfg.get(key) != preset[key]:
            return False
    p_led = preset.get("led")
    if p_led is not None:
        if isinstance(p_led[0], int):
            want = [list(p_led)] * 7
        else:
            want = [list(c) for c in p_led]
        if [list(c) for c in cfg["led"]] != want:
            return False
    return True
