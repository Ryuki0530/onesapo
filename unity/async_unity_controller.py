# async_unity_controller.py
from PySide6.QtCore import QObject, QThread, Signal, Slot
from collections import deque
import time, traceback

class AsyncUnityController(QObject):
    """
    unity_ipcクラスのインスタンスを使用し、非同期でUnityのアニメーションコントロールを行う。
    """
    error = Signal(str)
    def __init__(self, unity_ipc, rate_hz=60):
        super().__init__()
        self._ipc = unity_ipc
        self._q = deque()
        self._alive = True
        self._interval = 1.0 / max(1, rate_hz)
        self._th = QThread()
        self.moveToThread(self._th)
        self._th.started.connect(self._loop)
        self._th.start()

    # 公開API（UnityIPCと同名）
    # 表情
    @Slot(int)
    def smile(self, ms=1000):
        self._q.append(("SMILE", ms))

    @Slot(int)
    def kanashi(self, ms=1000):
        self._q.append(("KANASHI", ms))

    @Slot(int)
    def oko(self, ms=1000):
        self._q.append(("OKO", ms))

    @Slot(int)
    def tere(self, ms=1000):
        self._q.append(("TERE", ms))

    # 体のアニメーション
    @Slot(int)
    def gattu(self, ms=1000):
        self._q.append(("GATTU", ms))

    @Slot(int)
    def ude_gattu(self, ms=1000):
        self._q.append(("UDE_GATTU", ms))

    @Slot(int)
    def yubifuri(self, ms=1000):
        self._q.append(("YUBIFURI", ms))

    @Slot(int)
    def idleA(self, ms=1000):
        self._q.append(("IDLE_A", ms))

    @Slot(int)
    def idleB(self, ms=1000):
        self._q.append(("IDLE_B", ms))

    @Slot(int)
    def lip(self, ms=1000):
        self._q.append(("LIP", ms))

    @Slot()
    def lip_stop(self):
        self._q.append(("LIP_STOP", None))

    @Slot(str)
    def send_raw(self, raw):
        self._q.append(("RAW", raw))

    @Slot(str)
    def change_character(self, chara_name):
        self._q.append(("CHANGE_CHARACTER", chara_name))

    @Slot()
    def stop(self):
        self._alive = False
        self._th.quit(); self._th.wait()

    def _loop(self):
        while self._alive:
            try:
                if self._q:
                    kind, param = self._q.popleft()
                    # 表情
                    if   kind == "SMILE":    self._ipc.smile(param)
                    elif kind == "KANASHI":  self._ipc.kanashi(param)
                    elif kind == "OKO":      self._ipc.oko(param)
                    elif kind == "TERE":     self._ipc.tere(param)
                    # 体のアニメーション
                    elif kind == "GATTU":    self._ipc.gattu(param)
                    elif kind == "UDE_GATTU": self._ipc.ude_gattu(param)
                    elif kind == "YUBIFURI": self._ipc.yubifuri(param)
                    elif kind == "IDLE_A":   self._ipc.idleA(param)
                    elif kind == "IDLE_B":   self._ipc.idleB(param)
                    elif kind == "LIP":      self._ipc.lip(param)
                    elif kind == "LIP_STOP": self._ipc.lip_stop()
                    elif kind == "RAW":      self._ipc.send_raw(param)
                    # キャラクター変更
                    elif kind == "CHANGE_CHARACTER": self._ipc.change_character(param)
                time.sleep(self._interval)
            except Exception as e:
                self.error.emit(f"[UnityIPC] {e}\n{traceback.format_exc()}")
