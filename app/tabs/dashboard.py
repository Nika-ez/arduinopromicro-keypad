from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

import protocol
from widgets import controls
from widgets.common import Card, dim
from widgets.pad_view import PadView


class DashboardTab(QWidget):
    def __init__(self, state, win, parent=None):
        super().__init__(parent)
        self.state = state
        self.win = win
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

        dev = Card()
        dev.add_title("Device")
        self.port_val = dim("—")
        self.fw_val = dim("—")
        self.state_val = dim("—")
        for label, val in (("Port", self.port_val), ("Firmware", self.fw_val), ("Status", self.state_val)):
            row = QHBoxLayout()
            k = QLabel(label)
            k.setMinimumWidth(80)
            row.addWidget(k)
            row.addWidget(val, 1)
            dev.body.addLayout(row)
        disc = QPushButton("Disconnect")
        disc.setObjectName("ghost")
        disc.clicked.connect(self.win.disconnect_device)
        dev.body.addWidget(disc)
        lay.addWidget(dev)

        pre = Card()
        pre.add_title("Quick presets")
        pre.body.addWidget(dim("Tap to apply instantly to the device."))
        grid, self.preset_btns = controls.presets_grid(protocol.PRESETS[:8], self.apply_preset, columns=2)
        pre.body.addWidget(grid)
        lay.addWidget(pre)

        self.eff = controls.effects_card()
        self.br = controls.brightness_card()
        self.sur = controls.surround_card()
        self._wire_cards()
        lay.addWidget(self.eff)
        lay.addWidget(self.br)
        lay.addWidget(self.sur)

        padc = Card()
        padc.add_title("Live view")
        self.pad = PadView(state, clickable=False)
        self.pad.setMinimumHeight(200)
        padc.body.addWidget(self.pad)
        padc.body.addWidget(dim("Your keypad, mirrored live. Press keys to see them light up."))
        lay.addWidget(padc)
        lay.addStretch(1)

        state.configChanged.connect(self.refresh)
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

    def apply_preset(self, preset):
        self.state.apply_preset(preset)
        self.win.toast("Preset applied: %s" % preset["name"])

    def refresh(self):
        cfg = self.state.cfg
        info = self.state.info
        self.port_val.setText(info.get("port", "—"))
        self.fw_val.setText(info.get("firmware", "—"))
        if self.state.connected:
            if info.get("verified", True):
                self.state_val.setText("Connected — verified")
            else:
                self.state_val.setText("Connected — unverified device")
        else:
            self.state_val.setText("Disconnected")
        controls.refresh_cards(cfg, self.eff, self.br, self.sur)
        for btn, preset in zip(self.preset_btns, protocol.PRESETS[:8]):
            btn.setChecked(protocol.preset_matches(cfg, preset))
