from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

import protocol
from widgets.common import Card, SliderRow, dim


def presets_grid(presets, on_click, columns=2):
    grid = QWidget()
    lay = QVBoxLayout(grid)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    buttons = []
    row = None
    for idx, preset in enumerate(presets):
        if idx % columns == 0:
            row = QHBoxLayout()
            row.setSpacing(8)
            lay.addLayout(row)
        btn = _preset_button(preset)
        btn.clicked.connect(lambda checked=False, p=preset: on_click(p))
        row.addWidget(btn, 1)
        buttons.append(btn)
    last_row_count = len(presets) % columns
    if last_row_count:
        for _ in range(columns - last_row_count):
            spacer = QWidget()
            row.addWidget(spacer, 1)
    return grid, buttons


def _preset_button(preset):
    btn = QPushButton(preset["name"])
    btn.setObjectName("preset")
    btn.setCheckable(True)
    btn.setCursor(Qt.PointingHandCursor)
    led = preset.get("led")
    if led:
        first = led[0] if not isinstance(led[0], int) else led
        col = "#%02x%02x%02x" % (first[0], first[1], first[2])
        btn.setStyleSheet("border-left: 4px solid %s;" % col)
    btn.setMinimumHeight(34)
    return btn


def styled_checkbox(text):
    cb = QCheckBox(text)
    cb.setCursor(Qt.PointingHandCursor)
    return cb


def effects_card():
    card = Card()
    card.add_title("Effects")
    card.body.addWidget(dim("How the LEDs react when you press, and what they do at idle."))
    row = QHBoxLayout()
    row.setSpacing(10)
    left = QVBoxLayout()
    left.addWidget(dim("On press"))
    card.press_combo = QComboBox()
    for label, val in protocol.PRESS_FX:
        card.press_combo.addItem(label, val)
    left.addWidget(card.press_combo)
    right = QVBoxLayout()
    right.addWidget(dim("At idle"))
    card.idle_combo = QComboBox()
    for label, val in protocol.IDLE_FX:
        card.idle_combo.addItem(label, val)
    right.addWidget(card.idle_combo)
    row.addLayout(left, 1)
    row.addLayout(right, 1)
    card.body.addLayout(row)
    card.speed_row = SliderRow("Effect speed", 10, fmt=lambda v: "%d / 10" % v)
    card.body.addWidget(card.speed_row)
    return card


def brightness_card():
    card = Card()
    card.add_title("Brightness")
    card.idle_row = SliderRow(
        "Idle brightness", 255, fmt=lambda v: "%d  (%d%%)" % (v, round(v / 255 * 100))
    )
    card.press_row = SliderRow(
        "Press brightness", 255, fmt=lambda v: "%d  (%d%%)" % (v, round(v / 255 * 100))
    )
    card.body.addWidget(card.idle_row)
    card.body.addWidget(card.press_row)
    return card


def surround_card():
    card = Card()
    card.add_title("Surround glow")
    card.check = styled_checkbox("Light up neighboring keys when one is pressed")
    card.body.addWidget(card.check)
    card.strength = SliderRow("Glow strength", 100, fmt=lambda v: "%d%%" % v)
    card.body.addWidget(card.strength)
    return card


def refresh_cards(cfg, eff, br, sur):
    eff.press_combo.blockSignals(True)
    idx = eff.press_combo.findData(cfg.get("pressFx", 1))
    if idx >= 0:
        eff.press_combo.setCurrentIndex(idx)
    eff.press_combo.blockSignals(False)
    eff.idle_combo.blockSignals(True)
    idx = eff.idle_combo.findData(cfg.get("idleFx", 0))
    if idx >= 0:
        eff.idle_combo.setCurrentIndex(idx)
    eff.idle_combo.blockSignals(False)
    eff.speed_row.set_value(cfg.get("speed", 5))
    br.idle_row.set_value(cfg.get("brightIdle", 0))
    br.press_row.set_value(cfg.get("brightPress", 51))
    on = cfg.get("surround", 0) == 1
    sur.check.blockSignals(True)
    sur.check.setChecked(on)
    sur.check.blockSignals(False)
    sur.strength.set_value(cfg.get("surroundStrength", 40))
    sur.strength.setEnabled(on)
