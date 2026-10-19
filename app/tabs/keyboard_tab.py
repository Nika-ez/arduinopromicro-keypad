from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

import layout
import protocol
from widgets.common import Card, dim, hsep

QT_KEYMAP = {
    Qt.Key_Left: 0xD8, Qt.Key_Right: 0xD7, Qt.Key_Up: 0xDA, Qt.Key_Down: 0xD9,
    Qt.Key_Home: 0xD2, Qt.Key_End: 0xD5, Qt.Key_PageUp: 0xD3, Qt.Key_PageDown: 0xD6,
    Qt.Key_Insert: 0xD1, Qt.Key_Delete: 0xD4, Qt.Key_Backspace: 0xB2, Qt.Key_Tab: 0xB3,
    Qt.Key_Backtab: 0xB3, Qt.Key_Return: 0xB0, Qt.Key_Enter: 0xB0, Qt.Key_CapsLock: 0xC1,
    Qt.Key_Menu: 0xED, Qt.Key_Print: 0xCE, Qt.Key_ScrollLock: 0xCF, Qt.Key_Pause: 0xD0,
    Qt.Key_NumLock: 0xDB, Qt.Key_Control: 0x80, Qt.Key_Shift: 0x81, Qt.Key_Alt: 0x82,
    Qt.Key_Meta: 0x83,
}
for _i in range(1, 13):
    QT_KEYMAP[getattr(Qt, "Key_F%d" % _i)] = 0xC1 + _i


def resolve_qt_key(event):
    text = event.text()
    if text and len(text) == 1 and ord(text) < 128 and text.isprintable():
        return ord(text)
    return QT_KEYMAP.get(event.key())


class CaptureDialog(QDialog):
    def __init__(self, key_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remap key")
        self.setModal(True)
        self.code = None
        self.setMinimumWidth(320)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(10)
        head = QLabel("PRESS THE KEY YOU WANT")
        head.setObjectName("dim")
        lay.addWidget(head)
        name = QLabel('"%s" TO SEND' % key_label)
        name.setObjectName("h2")
        lay.addWidget(name)
        hint = dim("Just press any key now. Esc cancels.")
        lay.addWidget(hint)
        lay.addWidget(hsep())
        lay.addWidget(dim("…or pick one from the list:"))
        self.combo = QComboBox()
        for group, items in protocol.GROUPS.items():
            for item in items:
                self.combo.addItem("%s  —  %s" % (item["label"], group), item["code"])
        lay.addWidget(self.combo)
        use = QPushButton("Use this key")
        use.setObjectName("primary")
        use.clicked.connect(self._pick)
        lay.addWidget(use)

    def _pick(self):
        self.code = self.combo.currentData()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        code = resolve_qt_key(event)
        if code is not None:
            self.code = code
            self.accept()


class KeyboardTab(QWidget):
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

        intro = Card()
        intro.add_title("Remap keys")
        intro.body.addWidget(
            dim("Every physical key can send any keyboard key you want. Changes apply immediately "
                "and are stored on the device's EEPROM.", wrap=True)
        )
        lay.addWidget(intro)

        mapc = Card()
        mapc.add_title("Key mapping")
        self.map_buttons = {}
        self.clear_buttons = {}
        for idx, key in enumerate(layout.KEYS):
            if idx > 0:
                mapc.body.addWidget(hsep())
            row = QHBoxLayout()
            left = QVBoxLayout()
            big = QLabel(key["label"])
            big.setObjectName("h2")
            orig = dim("originally %s" % protocol.label_for(layout.ORIGINAL_CODES[idx]))
            left.addWidget(big)
            left.addWidget(orig)
            row.addLayout(left, 0)
            arrow = QLabel("→")
            arrow.setObjectName("dim")
            row.addWidget(arrow)
            btn = QPushButton("—")
            btn.setObjectName("mini")
            btn.clicked.connect(lambda _c=False, i=idx: self._capture(i))
            row.addWidget(btn, 1)
            clear = QPushButton("✕")
            clear.setObjectName("mini")
            clear.setFixedWidth(40)
            clear.setToolTip("Reset this key to its original mapping")
            clear.clicked.connect(lambda _c=False, i=idx: self._clear(i))
            row.addWidget(clear)
            mapc.body.addLayout(row)
            self.map_buttons[idx] = btn
            self.clear_buttons[idx] = clear
        lay.addWidget(mapc)

        lay.addStretch(1)
        state.configChanged.connect(self.refresh)
        self.refresh()

    def _capture(self, key_i):
        dlg = CaptureDialog(layout.KEY_LABEL[key_i], self)
        if dlg.exec() == QDialog.Accepted and dlg.code is not None:
            self.state.set_key(key_i, dlg.code)
            self.win.toast("%s now sends %s" % (layout.KEY_LABEL[key_i], protocol.label_for(dlg.code)))

    def _clear(self, key_i):
        orig = layout.ORIGINAL_CODES[key_i]
        if self.state.cfg["keymap"][key_i] != orig:
            self.state.set_key(key_i, orig)
            self.win.toast("%s reset to original" % layout.KEY_LABEL[key_i])

    def refresh(self):
        for idx in range(len(layout.KEYS)):
            code = self.state.cfg["keymap"][idx]
            self.map_buttons[idx].setText(protocol.label_for(code))
            self.clear_buttons[idx].setEnabled(code != layout.ORIGINAL_CODES[idx])
