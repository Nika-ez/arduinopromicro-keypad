import os
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget,
)

import protocol
import settings_store
import theme
from connection_page import ConnectionPage
from serial_link import MockLink, SerialLink
from state import AppState
from tabs.dashboard import DashboardTab
from tabs.keyboard_tab import KeyboardTab
from tabs.led_tab import LedTab
from tabs.settings_tab import SettingsTab
from widgets.common import FadeStack, StatusDot, Toast


class MainPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.stack = FadeStack()
        self.tabs = [
            DashboardTab(win.state, win),
            LedTab(win.state, win),
            KeyboardTab(win.state, win),
            SettingsTab(win.state, win),
        ]
        for t in self.tabs:
            self.stack.addWidget(t)
        lay.addWidget(self.stack, 1)
        nav = QFrame()
        nav.setObjectName("navbar")
        nlay = QHBoxLayout(nav)
        nlay.setContentsMargins(6, 0, 6, 0)
        nlay.setSpacing(2)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i, label in enumerate(("MAIN", "LED", "KEYBOARD", "SETTINGS")):
            b = QPushButton(label)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _c=False, idx=i: self.goto(idx))
            nlay.addWidget(b, 1)
            self.group.addButton(b, i)
        self.group.button(0).setChecked(True)
        lay.addWidget(nav)

    def goto(self, idx):
        self.stack.fade_to(idx)
        self.group.button(idx).setChecked(True)


class MainWindow(QMainWindow):
    def __init__(self, mock=False, mock_config=None):
        super().__init__()
        self.app_settings = settings_store.load()
        self.theme_name = self.app_settings.get("theme", "dark")
        try:
            self.scale = float(self.app_settings.get("scale", "1.0"))
        except ValueError:
            self.scale = 1.0
        self.is_connected = False
        self.attempting = False
        self.link = MockLink(mock_config) if mock else SerialLink()
        self.state = AppState(self.link)

        self.setWindowTitle(protocol.APP_NAME)
        self.resize(440, 900)
        self.setMinimumSize(384, 680)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 10, 12, 2)
        hl.setSpacing(8)
        tv = QVBoxLayout()
        tv.setSpacing(0)
        brand = QLabel("STANDALONE KEYPAD STUDIO")
        brand.setObjectName("title")
        sub = QLabel("v%s  ·  serial protocol v%d" % (protocol.APP_VERSION, protocol.PROTOCOL_VER))
        sub.setObjectName("dim")
        tv.addWidget(brand)
        tv.addWidget(sub)
        hl.addLayout(tv)
        hl.addStretch(1)
        self.dot = StatusDot()
        hl.addWidget(self.dot)
        self.theme_btn = QPushButton("☾")
        self.theme_btn.setObjectName("mini")
        self.theme_btn.setFixedWidth(40)
        self.theme_btn.clicked.connect(self.toggle_theme)
        hl.addWidget(self.theme_btn)
        lay.addWidget(header)

        self.stack = FadeStack()
        self.conn_page = ConnectionPage(self)
        self.main_page = MainPage(self)
        self.stack.addWidget(self.conn_page)
        self.stack.addWidget(self.main_page)
        lay.addWidget(self.stack, 1)

        self.toast_lbl = Toast(root)

        self.link.opened.connect(
            lambda p: self.conn_page.set_status("Port %s open — checking device…" % p, "accent")
        )
        self.link.verified.connect(lambda: self._enter_main(verified=True))
        self.link.handshake_failed.connect(self._on_handshake_fail)
        self.link.failed.connect(self._on_failed)
        self.link.died.connect(self._on_died)
        self.state.connectionChanged.connect(lambda on: self.dot.set_on(on))

        self._update_theme_button()
        QTimer.singleShot(50, self.conn_page.scan)

    def toast(self, message, kind="ok"):
        self.toast_lbl.show_message(message, kind)

    def try_connect(self, port, auto=False):
        if self.is_connected:
            return
        self.attempting = True
        self.conn_page.hide_continue()
        self.conn_page.set_status(
            "Verifying %s%s…" % (port, " (auto-detected)" if auto else ""), "accent"
        )
        self.link.connect_port(port)

    def continue_anyway(self):
        self.link.accept_unverified()
        self.attempting = False
        self._enter_main(verified=False)

    def _enter_main(self, verified):
        port = self.link.port or ""
        self.attempting = False
        self.is_connected = True
        settings_store.save(port=port)
        self.state.info = {
            "port": port,
            "firmware": "%s v2" % protocol.FW_TAG if verified else "Unknown device",
            "verified": verified,
        }
        self.state.set_connected(True)
        self.conn_page.hide_continue()
        self.stack.fade_to(1)
        self.main_page.goto(0)
        self.state.refresh_from_device()
        self.main_page.tabs[3].refresh()
        if verified:
            self.toast("Connected to %s" % port)
        else:
            self.toast("Connected to %s (unverified device)" % port, "err")

    def _on_handshake_fail(self, port):
        if self.is_connected:
            return
        self.attempting = False
        self.conn_page.show_continue(port)
        self.conn_page.set_status(
            "Device on %s did not answer the handshake — it may not be a Keypad Studio device." % port,
            "err",
        )

    def _on_failed(self, msg):
        self.attempting = False
        self.conn_page.set_status("Could not open the port: %s" % msg, "err")

    def _on_died(self, port):
        self.attempting = False
        if self.is_connected:
            self.is_connected = False
            self.state.set_connected(False)
            self.stack.fade_to(0)
            self.conn_page.set_status("Connection to %s lost — device unplugged?" % port, "err")
            self.toast("Connection lost — device disconnected", "err")
        else:
            self.conn_page.hide_continue()
            self.conn_page.set_status("Port %s disappeared during the connection attempt." % port, "err")

    def disconnect_device(self):
        if self.link.port is None and not self.is_connected:
            return
        self.link.disconnect_port()
        self.attempting = False
        self.is_connected = False
        self.state.set_connected(False)
        self.stack.fade_to(0)
        self.conn_page.set_status("Disconnected.", "dim")
        self.main_page.tabs[3].refresh()

    def set_theme(self, name):
        self.theme_name = name
        self.apply_appearance()

    def set_scale(self, pct):
        self.scale = float(pct) / 100.0
        self.apply_appearance()

    def toggle_theme(self):
        self.set_theme("light" if self.theme_name == "dark" else "dark")

    def apply_appearance(self):
        app = QApplication.instance()
        theme.apply_theme(app, self.theme_name != "light", self.scale)
        settings_store.save(theme=self.theme_name, scale=self.scale)
        self._update_theme_button()

    def _update_theme_button(self):
        if self.theme_name == "dark":
            self.theme_btn.setText("☀")
            self.theme_btn.setToolTip("Switch to light theme")
        else:
            self.theme_btn.setText("☾")
            self.theme_btn.setToolTip("Switch to dark theme")

    def forget_saved_port(self):
        settings_store.save(port="")
        self.main_page.tabs[3].refresh()
        self.toast("Saved port cleared")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(protocol.APP_NAME)
    app.setOrganizationName("standalone-keypad")
    settings = settings_store.load()
    dark = settings.get("theme", "dark") != "light"
    try:
        scale = float(settings.get("scale", "1.0"))
    except ValueError:
        scale = 1.0
    theme.apply_theme(app, dark, scale)
    mock = os.environ.get("SKS_MOCK") == "1"
    win = MainWindow(mock=mock)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
