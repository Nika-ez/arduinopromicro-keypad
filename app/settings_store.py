import os
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "standalone_keypad_studio")
_FILE = os.path.join(_DIR, "settings.txt")


def load():
    out = {}
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def save(**kwargs):
    data = load()
    data.update({k: str(v) for k, v in kwargs.items()})
    try:
        os.makedirs(_DIR, exist_ok=True)
        with open(_FILE, "w", encoding="utf-8") as f:
            for k, v in data.items():
                f.write(f"{k}={v}\n")
    except OSError:
        pass
