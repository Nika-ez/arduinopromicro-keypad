from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from serial_link import list_ports, port_detail
from settings_store import load
from widgets.common import Card, dim


class ConnectionPage(QWidget):
    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.win = win
        self._attempted = set()
        self._first_scan = True
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 14)
        lay.setSpacing(12)

        title = QLabel("CONNECT YOUR KEYPAD")
        title.setObjectName("h1")
        lay.addWidget(title)
        lay.addWidget(dim("Plug the device in with a USB cable. It will be detected and verified automatically.", wrap=True))

        card = Card()
        card.add_title("USB devices")
        self.list = QListWidget()
        self.list.setObjectName("ports")
        self.list.setMinimumHeight(150)
        card.body.addWidget(self.list)
        self.status = QLabel("Scanning for devices…")
        self.status.setObjectName("dim")
        self.status.setWordWrap(True)
        card.body.addWidget(self.status)
        self.continue_lbl = QLabel("")
        self.continue_lbl.setTextFormat(Qt.RichText)
        self.continue_lbl.setCursor(Qt.PointingHandCursor)
        self.continue_lbl.setVisible(False)
        self.continue_lbl.linkActivated.connect(lambda _a: self.win.continue_anyway())
        card.body.addWidget(self.continue_lbl)
        lay.addWidget(card)

        row = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("primary")
        self.connect_btn.clicked.connect(self._connect_selected)
        row.addWidget(self.connect_btn, 1)
        ref = QPushButton("Refresh")
        ref.setObjectName("ghost")
        ref.clicked.connect(self.scan)
        row.addWidget(ref)
        lay.addLayout(row)

        self.saved_lbl = dim("")
        lay.addWidget(self.saved_lbl)
        lay.addStretch(1)

        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self.scan)
        self._timer.start()

    def set_status(self, text, kind="dim"):
        self.status.setText(text)
        self.status.setObjectName(kind if kind in ("dim", "ok", "err", "accent") else "dim")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def show_continue(self, port):
        self.continue_lbl.setText(
            '<span style="color:#ff4d5e; font-weight:600; text-decoration:underline;">'
            "Handshake failed on %s — unrecognized device. Connect anyway →</span>" % port
        )
        self.continue_lbl.setVisible(True)

    def hide_continue(self):
        self.continue_lbl.setVisible(False)

    def scan(self):
        if self.win.is_connected or self.win.attempting:
            return
        infos = list_ports()
        ports = [i["port"] for i in infos]
        saved = load().get("port", "")
        self.saved_lbl.setText(
            "Saved port: %s — connects automatically." % saved if saved else "No saved port yet."
        )
        current = None
        if self.list.currentItem() is not None:
            current = self.list.currentItem().data(Qt.UserRole)
        self.list.clear()
        for info in infos:
            item = QListWidgetItem("%s   ·   %s" % (info["port"], port_detail(info)))
            item.setData(Qt.UserRole, info["port"])
            self.list.addItem(item)
            if info["port"] == current:
                self.list.setCurrentItem(item)
        if self.list.currentItem() is None and self.list.count() > 0:
            self.list.setCurrentRow(0)

        if self._first_scan:
            self._first_scan = False
            self._attempted.update(ports)
            if saved and saved in ports:
                self.set_status("Saved port %s found — connecting…" % saved, "accent")
                self.win.try_connect(saved, auto=True)
            elif ports:
                self.set_status("Devices found. Select one and press Connect.")
            else:
                self.set_status("No devices found. Plug in the keypad…")
            return

        new_ports = [p for p in ports if p not in self._attempted]
        for port in new_ports:
            self._attempted.add(port)
        if new_ports:
            self.set_status("New device detected on %s — verifying…" % new_ports[0], "accent")
            self.win.try_connect(new_ports[0], auto=True)

    def _connect_selected(self):
        item = self.list.currentItem()
        if item is None:
            self.set_status("No device selected.", "err")
            return
        port = item.data(Qt.UserRole)
        self.hide_continue()
        self.set_status("Connecting to %s…" % port, "accent")
        self.win.try_connect(port, auto=False)
