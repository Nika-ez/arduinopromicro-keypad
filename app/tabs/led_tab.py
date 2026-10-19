from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

import layout
import protocol
from widgets import controls
from widgets.common import Card, ColorSwatch, dim
from widgets.pad_view import PadView


class LedTab(QWidget):
    def __init__(self, state, win, parent=None):
        super().__init__(parent)
        self.state = state
        self.win = win
        self.selected = 0
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(12)

        keysc = Card()
        keysc.add_title("LED editor")
        keysc.body.addWidget(dim("Tap a key to select the LED strip position it maps to."))
        self.pad = PadView(state, clickable=True)
        self.pad.setMinimumHeight(200)
        self.pad.keyClicked.connect(self.select_key)
        keysc.body.addWidget(self.pad)
        lay.addWidget(keysc)

        edit = Card()
        edit.add_title("Selected key")
        self.edit_lbl = QLabel("—")
        self.edit_lbl.setObjectName("h2")
        self.edit_sub = dim("")
        edit.body.addWidget(self.edit_lbl)
        edit.body.addWidget(self.edit_sub)
        row = QHBoxLayout()
        self.swatch = ColorSwatch()
        self.swatch.colorChanged.connect(self._color_changed)
        col = QVBoxLayout()
        col.addWidget(dim("LED color"))
        col.addWidget(self.swatch)
        row.addLayout(col)
        self.apply_all = QPushButton("Apply color to ALL keys")
        self.apply_all.clicked.connect(self._apply_all)
        arow = QVBoxLayout()
        arow.addWidget(dim("Bulk action"))
        arow.addWidget(self.apply_all)
        row.addLayout(arow, 1)
        edit.body.addLayout(row)
        self.ena = controls.styled_checkbox("LED enabled for this key")
        self.ena.toggled.connect(lambda v: self.state.set_ena_key(self.selected, v))
        edit.body.addWidget(self.ena)
        self.press_row = QHBoxLayout()
        press_col = QVBoxLayout()
        press_col.addWidget(dim("Press color (all keys)"))
        self.press_swatch = ColorSwatch()
        self.press_swatch.colorChanged.connect(self.state.set_press_color)
        press_col.addWidget(self.press_swatch)
        self.press_row.addLayout(press_col)
        self.press_row.addStretch(1)
        edit.body.addLayout(self.press_row)
        lay.addWidget(edit)

        self.eff = controls.effects_card()
        self.br = controls.brightness_card()
        self.sur = controls.surround_card()
        self._wire_cards()
        lay.addWidget(self.eff)
        lay.addWidget(self.br)
        lay.addWidget(self.sur)

        presc = Card()
        presc.add_title("Presets")
        presc.body.addWidget(dim("Tap a preset — it applies to the device immediately and overwrites colors, brightness and effects.", wrap=True))
        grid, self.preset_btns = controls.presets_grid(protocol.PRESETS, self.apply_preset, columns=2)
        presc.body.addWidget(grid)
        lay.addWidget(presc)

        infoc = Card()
        infoc.body.addWidget(
            dim("All settings are stored on the Arduino in EEPROM — they survive unplugging and reboots. "
                "Settings > Reset returns everything to defaults.", wrap=True)
        )
        lay.addWidget(infoc)
        lay.addStretch(1)

        state.configChanged.connect(self.refresh)
        self.select_key(0)
        self.refresh()

    def _wire_cards(self):
        e, b, s = self.eff, self.br, self.sur
        e.press_combo.currentIndexChanged.connect(
            lambda _i: self.state.set_fx(press_fx=e.press_combo.currentData())
        )
        e.idle_combo.currentIndexChanged.connect(
            lambda _i: self.state.set_fx(idle_fx=e.idle_combo.currentData())
        )
        e.speed_row.valueChanged.connect(lambda v: self.state.set_fx(speed=v))
        b.idle_row.valueChanged.connect(
            lambda v: self.state.set_brightness(v, b.press_row.value())
        )
        b.press_row.valueChanged.connect(
            lambda v: self.state.set_brightness(b.idle_row.value(), v)
        )
        s.check.toggled.connect(lambda c: self.state.set_fx(surround=c))
        s.strength.valueChanged.connect(lambda v: self.state.set_fx(strength=v))

    def select_key(self, key_i):
        self.selected = key_i
        self.pad.selected_key = key_i
        self.pad.update()
        self.refresh()

    def _color_changed(self, rgb):
        self.state.set_led_key(self.selected, rgb)

    def _apply_all(self):
        self.state.set_led_key(self.selected, self.swatch.color(), all_keys=True)
        self.win.toast("Color applied to all %d LEDs" % 7)

    def apply_preset(self, preset):
        self.state.apply_preset(preset)
        self.win.toast("Preset applied: %s" % preset["name"])

    def refresh(self):
        cfg = self.state.cfg
        key_i = self.selected
        led = layout.LED_OF_KEY[key_i]
        self.edit_lbl.setText("KEY %s   →   LED %d" % (layout.KEY_LABEL[key_i], led))
        self.edit_sub.setText(
            "Position %d in the LED strip (1st = SPACE … 7th = A)." % (led + 1)
        )
        self.swatch.set_color(cfg["led"][led], emit=False)
        self.ena.blockSignals(True)
        self.ena.setChecked(bool(cfg["ena"][led]))
        self.ena.blockSignals(False)
        self.press_swatch.set_color(cfg["press"], emit=False)
        controls.refresh_cards(cfg, self.eff, self.br, self.sur)
        for btn, preset in zip(self.preset_btns, protocol.PRESETS):
            btn.setChecked(protocol.preset_matches(cfg, preset))
