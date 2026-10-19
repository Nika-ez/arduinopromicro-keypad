from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QColorDialog, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton,
    QSlider, QStackedWidget, QVBoxLayout, QWidget,
)

import theme


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(14, 12, 14, 12)
        self.body.setSpacing(8)

    def add_title(self, text):
        lbl = QLabel(text.upper())
        lbl.setObjectName("title")
        self.body.addWidget(lbl)
        return lbl


def dim(text, wrap=False):
    lbl = QLabel(text)
    lbl.setObjectName("dim")
    lbl.setWordWrap(wrap)
    return lbl


def hsep():
    f = QFrame()
    f.setObjectName("hsep")
    f.setFixedHeight(1)
    return f


class FadeStack(QStackedWidget):
    def fade_to(self, index, duration=180):
        if index == self.currentIndex():
            return
        self.setCurrentIndex(index)
        w = self.currentWidget()
        if w is None:
            return
        eff = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: w.setGraphicsEffect(None))
        self._anim = anim
        anim.start(QPropertyAnimation.DeleteWhenStopped)


class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._on = False
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self.setFixedSize(16, 16)

    def set_on(self, on):
        self._on = on
        if on:
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tick(self):
        import math
        self._phase = (self._phase + 0.09) % 1.0
        self.update()

    def paintEvent(self, event):
        import math
        c = theme.active_colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        col = QColor(c["ok"] if self._on else c["err"])
        if self._on:
            halo = QColor(col)
            halo.setAlphaF(0.30 + 0.30 * (0.5 + 0.5 * math.sin(self._phase * 6.2832)))
            p.setPen(Qt.NoPen)
            p.setBrush(halo)
            p.drawEllipse(1, 1, 14, 14)
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawEllipse(4, 4, 8, 8)


class SliderRow(QWidget):
    valueChanged = Signal(int)

    def __init__(self, label, maximum=255, fmt=None, parent=None):
        super().__init__(parent)
        self._fmt = fmt or (lambda v: str(v))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self._lbl = QLabel(label)
        self._lbl.setMinimumWidth(96)
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, maximum)
        self._val = QLabel("")
        self._val.setObjectName("mono")
        self._val.setMinimumWidth(72)
        self._val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl)
        lay.addWidget(self._slider, 1)
        lay.addWidget(self._val)
        self._slider.valueChanged.connect(self._on_change)
        self.set_value(0)

    def _on_change(self, v):
        self._val.setText(self._fmt(v))
        self.valueChanged.emit(v)

    def set_value(self, v):
        v = int(v)
        self._slider.blockSignals(True)
        self._slider.setValue(v)
        self._slider.blockSignals(False)
        self._val.setText(self._fmt(v))

    def value(self):
        return self._slider.value()


class ColorSwatch(QPushButton):
    colorChanged = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rgb = (255, 255, 255)
        self.setFixedSize(64, 34)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick)
        self._restyle()

    def _restyle(self):
        c = theme.active_colors()
        hexc = "#%02x%02x%02x" % self._rgb
        self.setStyleSheet(
            "background: %s; border: 1px solid %s; border-radius: 8px;" % (hexc, c["border"])
        )
        self.setToolTip("Click to change color (%s)" % hexc.upper())

    def _pick(self):
        c = QColorDialog.getColor(QColor(*self._rgb), self, "Pick LED color")
        if c.isValid():
            self.set_color((c.red(), c.green(), c.blue()))

    def set_color(self, rgb, emit=True):
        self._rgb = tuple(int(x) for x in rgb)
        self._restyle()
        if emit:
            self.colorChanged.emit(self._rgb)

    def color(self):
        return list(self._rgb)


class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWordWrap(True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

    def show_message(self, text, kind="ok"):
        c = theme.active_colors()
        col = c["ok"] if kind == "ok" else c["err"]
        self.setStyleSheet(
            "background: %s; color: %s; border: 1px solid %s; border-radius: 10px; "
            "padding: 8px 12px; font-size: 11px;" % (c["panel"], c["text"], col)
        )
        self.setText(text)
        self.adjustSize()
        self._reposition()
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(160)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        self._anim = anim
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self.show()
        self.raise_()
        self._timer.start(2400)

    def _reposition(self):
        p = self.parentWidget()
        if p is None:
            return
        x = (p.width() - self.width()) // 2
        y = p.height() - self.height() - int(96 * theme.ui_scale())
        self.move(max(8, x), max(8, y))

    def _fade_out(self):
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(260)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self.hide)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        self._anim = anim
        anim.start(QPropertyAnimation.DeleteWhenStopped)
