# unity_embed.py
# Windows限定: Unityビルドexeを -parentHWND でこのウィジェット内に表示
import os, ctypes, subprocess
from typing import Optional, List
if os.name != "nt":
    raise OSError("unity_embed_fixed.py は Windows 専用です。")

from PySide6 import QtWidgets, QtCore
QT_API_VERSION = 6

UNITY_WIDTH, UNITY_HEIGHT = 500, 768

def _enable_dpi_aware():
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

class UnityEmbedConfig:
    def __init__(self, unity_exe: str, extra_args: Optional[List[str]] = None,
                 force_d3d11=True, popupwindow=True, fullscreen=False, wait_ms_after_launch=200, port=5000):
        self.unity_exe = unity_exe
        self.extra_args = extra_args or []
        self.force_d3d11 = force_d3d11
        self.popupwindow = popupwindow
        self.fullscreen = fullscreen
        self.wait_ms_after_launch = wait_ms_after_launch
        self.port = port

class UnityEmbed(QtWidgets.QWidget):
    processExited = QtCore.Signal(int)

    def __init__(self, parent=None, dpi_aware=True):
        super().__init__(parent)
        if dpi_aware: _enable_dpi_aware()
        self.setObjectName("UnityEmbed")
        self.setFixedSize(UNITY_WIDTH, UNITY_HEIGHT)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow, True)
        self._proc: Optional[subprocess.Popen] = None
        self._watch = QtCore.QTimer(self); self._watch.setInterval(400)
        self._watch.timeout.connect(self._poll)

    def start(self, cfg: UnityEmbedConfig):
        self.stop()
        exe = os.path.abspath(cfg.unity_exe)
        if not os.path.isfile(exe):
            raise FileNotFoundError(f"Unity exe not found: {exe}")
        hwnd_parent = int(self.winId())
        args = [exe, "-parentHWND", str(hwnd_parent)]
        args += ["-screen-fullscreen", "0"] if not cfg.fullscreen else []
        if cfg.popupwindow: args += ["-popupwindow"]
        args += ["-screen-width", str(UNITY_WIDTH), "-screen-height", str(UNITY_HEIGHT)]
        if cfg.force_d3d11: args += ["-force-d3d11"]
        if cfg.port: 
            args += ["-ipcPort", str(cfg.port)]
        args += cfg.extra_args
        self._proc = subprocess.Popen(args)
        if cfg.wait_ms_after_launch > 0:
            QtCore.QTimer.singleShot(cfg.wait_ms_after_launch, lambda: None)
        self._watch.start()

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def stop(self, kill=False):
        self._watch.stop()
        if self._proc and self._proc.poll() is None:
            try: self._proc.kill() if kill else self._proc.terminate()
            except Exception: pass
        self._proc = None

    def _poll(self):
        if not self._proc: return
        code = self._proc.poll()
        if code is not None:
            self._watch.stop(); self.processExited.emit(int(code)); self._proc = None

    def resizeEvent(self, e):
        self.setFixedSize(UNITY_WIDTH, UNITY_HEIGHT)
        super().resizeEvent(e)

    def closeEvent(self, e):
        self.stop(kill=False)
        super().closeEvent(e)
