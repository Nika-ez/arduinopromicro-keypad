import queue
import time

from PySide6.QtCore import QObject, QThread, QTimer, Signal

import protocol

try:
    import serial
    import serial.tools.list_ports
    HAVE_SERIAL = True
except ImportError:
    HAVE_SERIAL = False

BAUD = 115200


def list_ports():
    if not HAVE_SERIAL:
        return []
    ports = []
    for p in serial.tools.list_ports.comports():
        ports.append({
            "port": p.device,
            "desc": (p.description or "").strip(),
            "vid": p.vid,
            "pid": p.pid,
        })
    ports.sort(key=lambda x: x["port"])
    return ports


def port_detail(info):
    d = info.get("desc") or ""
    if not d or d.lower().startswith("usb serial device"):
        if info.get("vid") is not None:
            d = "USB device %04X:%04X" % (info["vid"], info["pid"])
        else:
            d = "Unknown device"
    return d


class SerialWorker(QThread):
    lineReady = Signal(str)
    opened = Signal(str)
    openFailed = Signal(str)
    died = Signal(str)

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.port_name = port
        self._out = queue.Queue()
        self._stop = False

    def send(self, line):
        self._out.put(line)

    def stop(self):
        self._stop = True

    def run(self):
        try:
            ser = serial.Serial(self.port_name, BAUD, timeout=0.05)
            try:
                ser.dtr = True
                ser.rts = True
            except Exception:
                pass
        except Exception as e:
            self.openFailed.emit(str(e))
            return
        self.opened.emit(self.port_name)
        buf = ""
        try:
            while not self._stop:
                batch = []
                try:
                    while True:
                        batch.append(self._out.get_nowait())
                except queue.Empty:
                    pass
                if batch:
                    ser.write(("\n".join(batch) + "\n").encode("ascii", "ignore"))
                data = ser.read(256)
                if data:
                    buf += data.decode("utf-8", "replace")
                    while "\n" in buf:
                        ln, buf = buf.split("\n", 1)
                        ln = ln.strip("\r \t")
                        if ln:
                            self.lineReady.emit(ln)
                else:
                    time.sleep(0.004)
        except Exception as e:
            if not self._stop:
                self.died.emit(str(e))
        finally:
            try:
                ser.close()
            except Exception:
                pass


class SerialLink(QObject):
    opened = Signal(str)
    verified = Signal()
    handshake_failed = Signal(str)
    failed = Signal(str)
    died = Signal(str)
    lineReady = Signal(str)
    evt = Signal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.port = None
        self.is_verified = False
        self._awaiting = False
        self._collect = None
        self._collect_cb = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._handshake_timeout)
        self._ctimer = QTimer(self)
        self._ctimer.setSingleShot(True)
        self._ctimer.timeout.connect(self._collect_finish)

    def connect_port(self, port):
        self.disconnect_port()
        self.port = port
        self.is_verified = False
        self._awaiting = True
        self.worker = SerialWorker(port)
        self.worker.lineReady.connect(self._on_line)
        self.worker.died.connect(self._on_died)
        self.worker.openFailed.connect(self._on_open_failed)
        self.worker.opened.connect(self._on_opened)
        self.worker.start()

    def _on_opened(self, port):
        self.opened.emit(port)
        self.send("ID")
        self._timer.start(1600)

    def _on_open_failed(self, msg):
        self.worker = None
        self.port = None
        self._awaiting = False
        self.failed.emit(msg)

    def _on_line(self, line):
        if self._awaiting and line.startswith("ID:"):
            if protocol.FW_TAG in line:
                self._awaiting = False
                self.is_verified = True
                self._timer.stop()
                self.verified.emit()
                return
        if self._collect is not None:
            if line == "END":
                self._collect.append(line)
                self._collect_finish()
                return
            if line.split(":")[0] in ("LED", "PRESS", "BRIGHT", "FX", "KEY"):
                self._collect.append(line)
                return
        if line.startswith("EVT:"):
            p = line.split(":")
            if len(p) == 3:
                try:
                    self.evt.emit(int(p[1]), p[2].strip() == "1")
                    return
                except ValueError:
                    pass
        self.lineReady.emit(line)

    def _handshake_timeout(self):
        if self._awaiting:
            self._awaiting = False
            self.handshake_failed.emit(self.port or "")

    def _on_died(self, msg):
        port = self.port
        self.worker = None
        self.port = None
        self.is_verified = False
        self._awaiting = False
        self.died.emit(port or msg)

    def accept_unverified(self):
        self._awaiting = False
        self._timer.stop()

    def disconnect_port(self):
        self._timer.stop()
        self._ctimer.stop()
        if self.worker is not None:
            w = self.worker
            self.worker = None
            w.stop()
            w.wait(700)
        self.port = None
        self.is_verified = False
        self._awaiting = False
        self._collect = None
        self._collect_cb = None

    def send(self, line):
        if self.worker is not None:
            self.worker.send(line)

    def get_config(self, cb, timeout_ms=1500):
        self._collect = []
        self._collect_cb = cb
        self.send("GET")
        self._ctimer.start(timeout_ms)

    def _collect_finish(self):
        self._ctimer.stop()
        lines = self._collect or []
        cb = self._collect_cb
        self._collect = None
        self._collect_cb = None
        if cb:
            cb(protocol.parse_get(lines))


class MockLink(QObject):
    opened = Signal(str)
    verified = Signal()
    handshake_failed = Signal(str)
    failed = Signal(str)
    died = Signal(str)
    lineReady = Signal(str)
    evt = Signal(int, bool)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.port = None
        self.is_verified = False
        self.config = config
        self.sent = []

    def connect_port(self, port):
        self.port = port
        QTimer.singleShot(120, lambda: self.opened.emit(port))
        QTimer.singleShot(300, self._ok)

    def _ok(self):
        self.is_verified = True
        self.verified.emit()

    def accept_unverified(self):
        pass

    def disconnect_port(self):
        self.port = None
        self.is_verified = False

    def send(self, line):
        self.sent.append(line)

    def get_config(self, cb, timeout_ms=1500):
        base = dict(protocol.default_config())
        if self.config:
            base.update(self.config)
        QTimer.singleShot(150, lambda: cb(base))
