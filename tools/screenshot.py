import os
import sys
import time

os.environ["SKS_MOCK"] = "1"

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(HERE, "..", "app"))
OUT = os.path.abspath(os.path.join(HERE, "..", "shots"))
sys.path.insert(0, APP)

import settings_store
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import protocol
import theme
from main import MainWindow

SHOWCASE = {
    "led": [[0, 170, 255]] * 7,
    "ena": [1] * 7,
    "press": [140, 240, 255],
    "brightIdle": 96,
    "brightPress": 210,
    "pressFx": 1,
    "idleFx": 2,
    "speed": 5,
    "surround": 1,
    "surroundStrength": 35,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    settings_store.save(port="", theme="dark", scale="1.0")

    app = QApplication(sys.argv)
    theme.apply_theme(app, True, 1.0)
    win = MainWindow(mock=True, mock_config=dict(SHOWCASE))
    win.setAttribute(Qt.WA_DontShowOnScreen, True)
    win.resize(440, 900)
    win.show()

    def spin(ms=350):
        end = time.time() + ms / 1000.0
        while time.time() < end:
            app.processEvents()
            time.sleep(0.01)

    spin(500)
    win.grab().save(os.path.join(OUT, "01_connection_dark.png"))

    win.try_connect("COM11")
    deadline = time.time() + 4
    while not win.is_connected and time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)
    spin(600)
    win.state._on_evt(2, True)
    win.state._on_evt(6, True)
    spin(400)
    win.grab().save(os.path.join(OUT, "02_dashboard_dark.png"))

    win.main_page.goto(1)
    spin(400)
    win.main_page.tabs[1].select_key(3)
    spin(300)
    win.grab().save(os.path.join(OUT, "03_led_dark.png"))

    win.main_page.goto(2)
    spin(400)
    win.grab().save(os.path.join(OUT, "04_keyboard_dark.png"))

    win.main_page.goto(3)
    spin(400)
    win.grab().save(os.path.join(OUT, "05_settings_dark.png"))

    win.set_theme("light")
    win.main_page.goto(0)
    spin(400)
    win.grab().save(os.path.join(OUT, "06_dashboard_light.png"))

    win.main_page.goto(1)
    spin(400)
    win.grab().save(os.path.join(OUT, "07_led_light.png"))

    win.set_scale(120)
    win.resize(520, 1040)
    spin(500)
    win.grab().save(os.path.join(OUT, "08_led_scaled.png"))

    print("screenshots saved to", OUT)
    settings_store.save(port="")
    app.quit()


if __name__ == "__main__":
    main()
