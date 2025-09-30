# timer_tool/timer_logic.py
from PySide6 import QtCore

class TimerLogic(QtCore.QObject):
    """UIから独立したタイマーの純ロジック。"""
    finished = QtCore.Signal()
    tick = QtCore.Signal(int)  # 残りms（必要なら）
    paused = QtCore.Signal()
    resumed = QtCore.Signal()
    stopped = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        #tick用（1秒ごと）
        self._tick = QtCore.QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)

        self._remain_ms = 0
        #経過時間管理と状態
        self._elapsed = QtCore.QElapsedTimer()
        self._duration_ms = 0
        self._is_running = False
        self._is_paused = False

    def start(self, ms: int):
        """タイマーを開始（既存の進行は破棄）"""
        self.stop()
        self._duration_ms = int(ms)
        self._remain_ms = int(ms)
        self._elapsed.start()
        self._timer.start(self._remain_ms)
        self._tick.start()
        self._is_running = True
        self._is_paused = False

    def pause(self):
        """一時停止（残り時間を保持）"""
        if not self._is_running or self._is_paused:
            return
        #　正確な残り時間を計算
        self._remain_ms = max(0, self._duration_ms - self._elapsed.elapsed())
        self._timer.stop()
        self._tick.stop()
        self._is_running = False
        self._is_paused = True
        self.paused.emit()

    def resume(self):
        """一時停止から再開"""
        if not self._is_paused or self._remain_ms <= 0:
            return
        self._duration_ms = int(self._remain_ms)
        self._elapsed.restart()
        self._timer.start(self._remain_ms)
        self._tick.start()
        self._is_running = True
        self._is_paused = False
        self.resumed.emit()

    def stop(self):
        """完全停止（残り時間クリア）"""
        self._timer.stop()
        self._tick.stop()
        self._remain_ms = 0
        self._duration_ms = 0
        self._is_running = False
        self._is_paused = False
        self.stopped.emit()

    def is_running(self) -> bool:
        return self._is_running

    def is_paused(self) -> bool:
        return self._is_paused

    def remaining_ms(self) -> int:
        """現在の残り時間（ms）。稼働中は計算して返す。"""
        if self._is_running:
            return max(0, self._duration_ms - self._elapsed.elapsed())
        return self._remain_ms
    
    def remaining_seconds(self) -> int:
        """現在の残り時間（秒）。稼働中は計算して返す。"""
        return self.remaining_ms() // 1000

    def _on_timeout(self):
        self._tick.stop()
        self._remain_ms = 0
        self._duration_ms = 0
        self._is_running = False
        self._is_paused = False
        self.finished.emit()

    def _on_tick(self):
        # 稼働中は正確な残り時間を計算
        if self._is_running:
            self._remain_ms = max(0, self._duration_ms - self._elapsed.elapsed())
        self.tick.emit(self._remain_ms)
