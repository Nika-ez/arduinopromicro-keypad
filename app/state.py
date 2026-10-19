from PySide6.QtCore import QObject, Signal

import layout
import protocol


class AppState(QObject):
    configChanged = Signal()
    pressChanged = Signal(set)
    connectionChanged = Signal(bool)

    def __init__(self, link, parent=None):
        super().__init__(parent)
        self.link = link
        self.cfg = protocol.default_config()
        self.pressed = set()
        self.connected = False
        self.info = {}
        self.link.evt.connect(self._on_evt)

    def _on_evt(self, i, down):
        if down:
            self.pressed.add(i)
        else:
            self.pressed.discard(i)
        self.pressChanged.emit(set(self.pressed))

    def set_connected(self, connected):
        self.connected = connected
        if not connected:
            self.pressed.clear()
            self.pressChanged.emit(set())
        self.connectionChanged.emit(connected)

    def refresh_from_device(self):
        self.link.get_config(self._apply_config)

    def _apply_config(self, cfg):
        for k, v in cfg.items():
            if v is not None and not (isinstance(v, list) and all(x is None for x in v)):
                self.cfg[k] = v
        self.configChanged.emit()

    def set_led_key(self, key_i, rgb, all_keys=False):
        rgb = [int(x) for x in rgb]
        if all_keys:
            self.cfg["led"] = [list(rgb) for _ in range(7)]
            self.link.send(protocol.cmd_set_led(255, rgb))
        else:
            led = layout.LED_OF_KEY[key_i]
            self.cfg["led"][led] = list(rgb)
            self.link.send(protocol.cmd_set_led(led, rgb))
        self.configChanged.emit()

    def set_ena_key(self, key_i, enabled):
        led = layout.LED_OF_KEY[key_i]
        self.cfg["ena"][led] = 1 if enabled else 0
        self.link.send(protocol.cmd_set_ena(led, enabled))
        self.configChanged.emit()

    def set_press_color(self, rgb):
        self.cfg["press"] = [int(x) for x in rgb]
        self.link.send(protocol.cmd_set_press(rgb))
        self.configChanged.emit()

    def set_brightness(self, idle, press):
        self.cfg["brightIdle"] = int(idle)
        self.cfg["brightPress"] = int(press)
        self.link.send(protocol.cmd_set_bright(idle, press))
        self.configChanged.emit()

    def set_fx(self, press_fx=None, idle_fx=None, speed=None, surround=None, strength=None):
        if press_fx is not None:
            self.cfg["pressFx"] = int(press_fx)
        if idle_fx is not None:
            self.cfg["idleFx"] = int(idle_fx)
        if speed is not None:
            self.cfg["speed"] = int(speed)
        if surround is not None:
            self.cfg["surround"] = 1 if surround else 0
        if strength is not None:
            self.cfg["surroundStrength"] = int(strength)
        self.link.send(
            protocol.cmd_set_fx(
                self.cfg["pressFx"], self.cfg["idleFx"], self.cfg["speed"],
                self.cfg["surround"], self.cfg["surroundStrength"],
            )
        )
        self.configChanged.emit()

    def set_key(self, key_i, code):
        self.cfg["keymap"][key_i] = int(code)
        self.link.send(protocol.cmd_set_key(key_i, code))
        self.configChanged.emit()

    def apply_preset(self, preset):
        led = preset.get("led")
        if led is not None:
            if isinstance(led[0], int):
                self.cfg["led"] = [list(led) for _ in range(7)]
                self.link.send(protocol.cmd_set_led(255, led))
            else:
                self.cfg["led"] = [list(c) for c in led]
                for led_i, col in enumerate(led):
                    self.link.send(protocol.cmd_set_led(led_i, col))
            self.cfg["ena"] = [1] * 7
            for led_i in range(7):
                self.link.send(protocol.cmd_set_ena(led_i, 1))
        if "press" in preset:
            self.cfg["press"] = list(preset["press"])
            self.link.send(protocol.cmd_set_press(preset["press"]))
        for key in ("brightIdle", "brightPress", "pressFx", "idleFx", "speed", "surround", "surroundStrength"):
            if key in preset:
                self.cfg[key] = preset[key]
        self.link.send(
            protocol.cmd_set_bright(self.cfg["brightIdle"], self.cfg["brightPress"])
        )
        self.link.send(
            protocol.cmd_set_fx(
                self.cfg["pressFx"], self.cfg["idleFx"], self.cfg["speed"],
                self.cfg["surround"], self.cfg["surroundStrength"],
            )
        )
        self.configChanged.emit()

    def reset_device(self):
        self.link.send("RESET")
        self.cfg = protocol.default_config()
        self.configChanged.emit()
