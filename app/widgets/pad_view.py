import colorsys
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

import layout
import protocol
import theme


class PadView(QWidget):
    keyClicked = Signal(int)

    def __init__(self, state=None, clickable=False, parent=None):
        super().__init__(parent)
        self.state = state
        self.clickable = clickable
        self.selected_key = -1
        self._glow = {}
        self._last = set()
        self._t0 = time.time()
        self.setMinimumHeight(180)
        self.setCursor(Qt.PointingHandCursor if clickable else Qt.ArrowCursor)
        if state is not None:
            state.configChanged.connect(self.update)
            state.pressChanged.connect(self._on_press)
        self._timer = QTimer(self)
        self._timer.setInterval(45)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _on_press(self, keys):
        for k in keys:
            self._glow[k] = 1.0
        self._last = set(keys)
        self.update()

    def _tick(self):
        for k in list(self._glow.keys()):
            if k not in self._last:
                self._glow[k] = max(0.0, self._glow[k] - 0.12)
                if self._glow[k] <= 0.0:
                    del self._glow[k]
        self.update()

    def _cfg(self):
        if self.state is not None:
            return self.state.cfg
        return protocol.default_config()

    def _metrics(self):
        m = max(18, int(24 * theme.ui_scale()))
        w = self.width() - 2 * m
        h = self.height() - 2 * m
        return m, w / layout.GRID_W, h / layout.GRID_H

    def _key_rect(self, key):
        m, cw, ch = self._metrics()
        gap = cw * 0.16
        x = m + key["x"] * cw + gap / 2
        y = m + key["y"] * ch + gap / 2
        return QRectF(x, y, key["w"] * cw - gap, ch - gap)

    def key_at(self, pos):
        for k in layout.KEYS:
            if self._key_rect(k).contains(QPointF(pos)):
                return k["i"]
        return -1

    def mousePressEvent(self, event):
        if not self.clickable:
            return
        k = self.key_at(event.position())
        if k >= 0:
            self.selected_key = k
            self.keyClicked.emit(k)
            self.update()

    def _idle_level(self, led, tnow, fx, spd):
        if fx == 0:
            return 0.0
        if fx == 1:
            return 1.0
        if fx == 2:
            return 0.55 + 0.45 * math.sin(tnow * 1.6 * spd + led * 0.9)
        if fx == 3:
            return 1.0
        if fx == 4:
            return 0.35 + 0.65 * (0.5 + 0.5 * math.sin(led * 1.05 - tnow * 3.2 * spd))
        if fx == 5:
            bucket = int(tnow * 3.0 * spd)
            r = random.Random(led * 977 + bucket)
            if r.random() < 0.5:
                return r.uniform(0.65, 1.0)
            return 0.12
        return 1.0

    def _key_color(self, key_i, tnow):
        cfg = self._cfg()
        led = layout.LED_OF_KEY[key_i]
        base = cfg["led"][led]
        if not cfg["ena"][led]:
            return QColor(70, 76, 88), False, True
        fx = cfg.get("idleFx", 0)
        spd = max(1, cfg.get("speed", 5)) / 5.0
        idle_b = cfg.get("brightIdle", 0) / 255.0
        press_b = cfg.get("brightPress", 51) / 255.0
        level = max(0.0, self._idle_level(led, tnow, fx, spd))
        if fx == 3:
            hue = ((tnow * 0.22 * spd) + led / 7.0) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            col = [r * 255.0, g * 255.0, b * 255.0]
        else:
            col = [float(x) for x in base]
        col = [x * level * idle_b for x in col]
        if cfg.get("surround", 0):
            ss = cfg.get("surroundStrength", 40) / 100.0
            boost = 0.0
            for n in layout.NEIGHBORS[key_i]:
                boost += self._glow.get(n, 0.0)
            boost = min(1.0, boost) * ss * 0.9
            if boost > 0:
                press = cfg.get("press", [255, 255, 255])
                col = [min(255.0, col[j] + press[j] * press_b * boost) for j in range(3)]
        glow = self._glow.get(key_i, 0.0)
        if glow > 0:
            press = cfg.get("press", [255, 255, 255])
            pcol = [x * press_b for x in press]
            col = [col[j] * (1.0 - glow) + pcol[j] * glow for j in range(3)]
        qc = QColor(min(255, int(col[0])), min(255, int(col[1])), min(255, int(col[2])))
        lit = max(col) > 90
        return qc, lit, False

    def paintEvent(self, event):
        c = theme.active_colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        tnow = time.time() - self._t0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c["input"]))
        p.drawRoundedRect(QRectF(self.rect()), 12, 12)
        inner = QRectF(self.rect()).adjusted(5, 5, -5, -5)
        p.setBrush(QColor(c["bg"]))
        p.drawRoundedRect(inner, 10, 10)

        base_font = QFont("Bahnschrift SemiBold")
        base_font.setPointSizeF(max(7.0, 9.0 * theme.ui_scale()))
        small_font = QFont("Segoe UI")
        small_font.setPointSizeF(max(5.5, 6.5 * theme.ui_scale()))

        for key in layout.KEYS:
            r = self._key_rect(key)
            i = key["i"]
            col, lit, disabled = self._key_color(i, tnow)
            radius = min(r.width(), r.height()) * 0.16
            glow = self._glow.get(i, 0.0)
            if glow > 0.02 and not disabled:
                halo = QColor(*self._cfg().get("press", [255, 255, 255]))
                halo.setAlphaF(min(0.8, glow * 0.7))
                p.setPen(Qt.NoPen)
                p.setBrush(halo)
                infl = r.adjusted(-4, -4, 4, 4)
                p.drawRoundedRect(infl, radius + 4, radius + 4)
            p.setBrush(col)
            if i == self.selected_key and self.clickable:
                p.setPen(QPen(QColor(c["accent"]), 2.6))
            else:
                pen = QPen(QColor(c["border"]), 1.6)
                if lit and not disabled:
                    light = QColor(col)
                    light = light.lighter(150)
                    light.setAlphaF(0.9)
                    pen = QPen(light, 1.8)
                p.setPen(pen)
            p.drawRoundedRect(r, radius, radius)
            if disabled:
                p.setPen(QPen(QColor(120, 126, 140), 1.6))
                p.drawLine(
                    QPointF(r.left() + r.width() * 0.22, r.bottom() - r.height() * 0.22),
                    QPointF(r.right() - r.width() * 0.22, r.top() + r.height() * 0.22),
                )
            label = key["label"]
            p.setFont(base_font)
            lum = 0.2126 * col.red() + 0.7152 * col.green() + 0.0722 * col.blue()
            fg = QColor("#0a0d12") if lum > 140 else QColor("#dbe6f2")
            if disabled:
                fg = QColor(c["dim"])
            p.setPen(fg)
            p.drawText(r, Qt.AlignCenter, label)
            led = layout.LED_OF_KEY[i]
            p.setFont(small_font)
            p.setPen(QColor(c["dim"]))
            p.drawText(
                QRectF(r.left() + 6, r.top() + 3, r.width() - 12, 12),
                Qt.AlignLeft | Qt.AlignTop,
                "LED %d" % led,
            )
