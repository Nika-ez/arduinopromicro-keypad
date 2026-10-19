from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

import protocol
from widgets.common import Card, dim


class SettingsTab(QWidget):
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

        dfl = Card()
        dfl.add_title("Defaults")
        dfl.body.addWidget(
            dim("Restores LED colors, brightness, effects and key mappings on the DEVICE back to "
                "factory settings. This cannot be undone.", wrap=True)
        )
        reset = QPushButton("RESET DEVICE TO DEFAULTS")
        reset.setObjectName("danger")
        reset.clicked.connect(self._confirm_reset)
        dfl.body.addWidget(reset)
        lay.addWidget(dfl)

        app = Card()
        app.add_title("Appearance")
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.currentIndexChanged.connect(
            lambda _i: self.win.set_theme(self.theme_combo.currentData())
        )
        row1.addWidget(self.theme_combo, 1)
        app.body.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Interface scale"))
        self.scale_combo = QComboBox()
        for pct in (85, 90, 100, 110, 120, 130):
            self.scale_combo.addItem("%d%%" % pct, pct)
        self.scale_combo.currentIndexChanged.connect(
            lambda _i: self.win.set_scale(self.scale_combo.currentData())
        )
        row2.addWidget(self.scale_combo, 1)
        app.body.addLayout(row2)
        lay.addWidget(app)

        conn = Card()
        conn.add_title("Connection")
        self.saved_lbl = dim("—")
        conn.body.addWidget(self.saved_lbl)
        rowb = QHBoxLayout()
        forget = QPushButton("Forget saved port")
        forget.setObjectName("ghost")
        forget.clicked.connect(self.win.forget_saved_port)
        rowb.addWidget(forget)
        disc = QPushButton("Disconnect")
        disc.setObjectName("ghost")
        disc.clicked.connect(self.win.disconnect_device)
        rowb.addWidget(disc)
        conn.body.addLayout(rowb)
        conn.body.addWidget(dim("The app reconnects to the saved port automatically at launch and when replugged.", wrap=True))
        lay.addWidget(conn)

        about = Card()
        about.add_title("About")
        about.body.addWidget(QLabel("%s v%s" % (protocol.APP_NAME, protocol.APP_VERSION)))
        about.body.addWidget(dim("Serial protocol v%d · firmware tag %s" % (protocol.PROTOCOL_VER, protocol.FW_TAG)))
        about.body.addWidget(dim("Open-source. MIT License."))
        lay.addWidget(about)
        lay.addStretch(1)

        self.refresh()

    def _confirm_reset(self):
        box = QMessageBox(self)
        box.setWindowTitle("Reset device?")
        box.setText("Reset EVERYTHING on the device to defaults?")
        box.setInformativeText(
            "LED colors, brightness, effects and all key mappings will be wiped and set "
            "back to factory defaults. This cannot be undone."
        )
        box.setIcon(QMessageBox.Warning)
        yes = box.addButton("YES, RESET", QMessageBox.AcceptRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is yes:
            self.state.reset_device()
            self.win.toast("Device reset to defaults")

    def refresh(self):
        from settings_store import load
        saved = load().get("port", "")
        self.saved_lbl.setText("Saved port: %s" % (saved if saved else "(none)"))
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(0 if self.win.theme_name == "dark" else 1)
        self.theme_combo.blockSignals(False)
        pct = int(round(self.win.scale * 100))
        idx = self.scale_combo.findData(pct)
        if idx >= 0:
            self.scale_combo.blockSignals(True)
            self.scale_combo.setCurrentIndex(idx)
            self.scale_combo.blockSignals(False)
