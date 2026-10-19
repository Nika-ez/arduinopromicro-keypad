import os
import tempfile

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF

DARK = {
    "bg": "#05070d", "panel": "#0c1420", "panel2": "#111c30", "chip": "#152340",
    "border": "#1c2b42", "input": "#0a1220", "text": "#dbe6f2", "dim": "#7d8da3",
    "accent": "#29e0ff", "accent2": "#ff3ea5", "ok": "#35f0a0", "err": "#ff4d5e",
    "accent_text": "#03151d", "track": "#16233a",
}
LIGHT = {
    "bg": "#e9edf4", "panel": "#ffffff", "panel2": "#f3f6fb", "chip": "#e3ebf7",
    "border": "#d4dce8", "input": "#f5f8fc", "text": "#182a44", "dim": "#5d6d84",
    "accent": "#0aa2c0", "accent2": "#d1268f", "ok": "#0da06b", "err": "#d92c3f",
    "accent_text": "#ffffff", "track": "#dde5f0",
}

_current = dict(DARK)
_dark = True
_scale = 1.0


def active_colors():
    return _current


def is_dark():
    return _dark


def ui_scale():
    return _scale


def _icon_path(color, name):
    d = os.path.join(tempfile.gettempdir(), "standalone_keypad_studio")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "check_%s_%s.png" % (name, color.lstrip("#")))
    if not os.path.exists(path):
        pm = QPixmap(18, 18)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color))
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPolyline(QPolygonF([QPointF(4, 9.5), QPointF(7.5, 13), QPointF(14, 5)]))
        p.end()
        pm.save(path)
    return path.replace("\\", "/")


def build_qss(c, scale=1.0):
    def s(px):
        return max(1, int(round(px * scale)))

    check = _icon_path(c["accent_text"], "d" if _dark else "l")
    return """
* { font-family: 'Segoe UI', sans-serif; }
QWidget { color: %(text)s; font-size: %(f12)dpx; background: transparent; }
QMainWindow, QDialog, #root { background: %(bg)s; }
QLabel { background: transparent; }
QLabel#h1 { font-family: 'Bahnschrift SemiBold','Segoe UI'; font-size: %(f22)dpx; font-weight: 600; letter-spacing: 1px; color: %(text)s; }
QLabel#h2 { font-family: 'Bahnschrift SemiBold','Segoe UI'; font-size: %(f15)dpx; font-weight: 600; letter-spacing: 1px; }
QLabel#title { font-size: %(f13)dpx; font-weight: 600; letter-spacing: 1px; }
QLabel#dim { color: %(dim)s; font-size: %(f11)dpx; }
QLabel#mono { font-family: 'Consolas','Courier New'; color: %(dim)s; font-size: %(f11)dpx; }
QLabel#ok { color: %(ok)s; font-size: %(f11)dpx; }
QLabel#err { color: %(err)s; font-size: %(f11)dpx; }
QLabel#accent { color: %(accent)s; font-size: %(f11)dpx; font-weight: 600; }
QFrame#card { background: %(panel)s; border: 1px solid %(border)s; border-radius: %(r14)dpx; }
QFrame#navbar { background: %(panel)s; border-top: 1px solid %(border)s; }
QFrame#hsep { background: %(border)s; max-height: 1px; min-height: 1px; border: none; }
QPushButton {
  background: %(chip)s; color: %(text)s; border: 1px solid %(border)s;
  border-radius: %(r10)dpx; padding: %(p8)dpx %(p12)dpx; font-size: %(f12)dpx;
}
QPushButton:hover { border: 1px solid %(accent)s; }
QPushButton:pressed { background: %(panel2)s; }
QPushButton:disabled { color: %(dim)s; border: 1px solid %(border)s; background: %(panel2)s; }
QPushButton#primary { background: %(accent)s; color: %(accent_text)s; border: 1px solid %(accent)s; font-weight: 600; }
QPushButton#primary:hover { background: %(accent2)s; border-color: %(accent2)s; }
QPushButton#ghost { background: transparent; }
QPushButton#danger { background: %(err)s; color: #ffffff; border: 1px solid %(err)s; font-weight: 600; }
QPushButton#danger:hover { background: #ff6172; border-color: #ff6172; }
QPushButton#nav { background: transparent; border: none; border-top: 2px solid transparent; border-radius: 0px; padding: %(p6)dpx 0px %(p8)dpx 0px; color: %(dim)s; font-size: %(f11)dpx; font-weight: 600; letter-spacing: 1px; }
QPushButton#nav:hover { color: %(text)s; }
QPushButton#nav:checked { color: %(accent)s; border-top: 2px solid %(accent)s; }
QPushButton#preset { background: %(panel2)s; border: 1px solid %(border)s; border-radius: %(r10)dpx; padding: %(p6)dpx; font-size: %(f11)dpx; }
QPushButton#preset:hover { border: 1px solid %(accent)s; }
QPushButton#preset:checked { border: 2px solid %(accent)s; }
QPushButton#mini { padding: %(p4)dpx %(p8)dpx; font-size: %(f11)dpx; border-radius: %(r8)dpx; }
QListWidget { background: %(input)s; border: 1px solid %(border)s; border-radius: %(r10)dpx; outline: none; font-size: %(f12)dpx; }
QListWidget::item { padding: %(p8)dpx %(p10)dpx; border-bottom: 1px solid %(border)s; }
QListWidget::item:selected { background: %(chip)s; color: %(text)s; border-left: 3px solid %(accent)s; }
QListWidget::item:hover { background: %(panel2)s; }
QComboBox { background: %(input)s; border: 1px solid %(border)s; border-radius: %(r8)dpx; padding: %(p6)dpx %(p10)dpx; font-size: %(f12)dpx; }
QComboBox:hover { border: 1px solid %(accent)s; }
QComboBox::drop-down { border: none; width: %(p18)dpx; }
QComboBox QAbstractItemView { background: %(panel)s; border: 1px solid %(border)s; selection-background-color: %(chip)s; outline: none; }
QSlider::groove:horizontal { height: %(p4)dpx; background: %(track)s; border-radius: %(p2)dpx; }
QSlider::sub-page:horizontal { background: %(accent)s; border-radius: %(p2)dpx; }
QSlider::handle:horizontal { width: %(p14)dpx; height: %(p14)dpx; margin: -%(p5)dpx 0; border-radius: %(p7)dpx; background: %(accent)s; border: 2px solid %(bg)s; }
QSlider::handle:horizontal:hover { background: %(accent2)s; }
QCheckBox { spacing: %(p8)dpx; font-size: %(f12)dpx; }
QCheckBox::indicator { width: %(p18)dpx; height: %(p18)dpx; border: 1px solid %(border)s; border-radius: %(r5)dpx; background: %(input)s; }
QCheckBox::indicator:checked { background: %(accent)s; border: 1px solid %(accent)s; image: url("%(check)s"); }
QScrollArea { border: none; }
QScrollBar:vertical { background: transparent; width: %(p8)dpx; margin: 0px; }
QScrollBar::handle:vertical { background: %(border)s; border-radius: %(p4)dpx; min-height: %(p30)dpx; }
QScrollBar::handle:vertical:hover { background: %(dim)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background: transparent; height: %(p8)dpx; }
QScrollBar::handle:horizontal { background: %(border)s; border-radius: %(p4)dpx; min-width: %(p30)dpx; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QLineEdit { background: %(input)s; border: 1px solid %(border)s; border-radius: %(r8)dpx; padding: %(p6)dpx %(p10)dpx; selection-background-color: %(accent)s; }
QToolTip { background: %(panel)s; color: %(text)s; border: 1px solid %(accent)s; padding: %(p4)dpx %(p6)dpx; font-size: %(f11)dpx; }
QMessageBox { background: %(panel)s; }
""" % {
        "bg": c["bg"], "panel": c["panel"], "panel2": c["panel2"], "chip": c["chip"],
        "border": c["border"], "input": c["input"], "text": c["text"], "dim": c["dim"],
        "accent": c["accent"], "accent2": c["accent2"], "ok": c["ok"], "err": c["err"],
        "accent_text": c["accent_text"], "track": c["track"], "check": check,
        "f22": s(22), "f15": s(15), "f13": s(13), "f12": s(12), "f11": s(11),
        "r14": s(14), "r10": s(10), "r8": s(8), "r5": s(5),
        "p2": s(2), "p4": s(4), "p5": s(5), "p6": s(6), "p7": s(7), "p8": s(8),
        "p10": s(10), "p12": s(12), "p14": s(14), "p18": s(18), "p30": s(30),
    }


def apply_theme(app, dark=True, scale=1.0):
    global _current, _dark, _scale
    _dark = dark
    _scale = scale
    _current = dict(DARK if dark else LIGHT)
    app.setStyleSheet(build_qss(_current, scale))
