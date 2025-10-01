# timer_tool/timer_widget.py

from .sleep_detector import SleepDetector

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton
from PySide6.QtCore import QTimer, QDateTime
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

from tools.event_bus import EventBus
from sound_effects import VoiceService
from user_data_manager.config_data import ConfigData
class SleepCheckerWidget(QtWidgets.QWidget):

    def __init__(self, controller, voice_service: VoiceService, event_bus: EventBus, config: ConfigData, parent=None):
        super().__init__(parent)
        self.debug = config.get("debug_mode")
        self.ctrl = controller
        self.voice_service: VoiceService = voice_service
        self.event_bus = event_bus
        self.config = config

        self.continuous_sleep_detection_count = 0

        # --- UI ---
        #レイアウト背景のデザイン
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/sleep_checker/bg.png")  # ウィジェットの背景画像パス
        self._bg_mode = "stretch_xy"   # "stretch_xy" | "contain" | "cover"
        self._bg_scale_x = 1.0         # 横の倍率（stretch_xy 用）
        self._bg_scale_y = 1.0         # 縦の倍率（stretch_xy 用）
        self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        if  self.debug:
            self.resize(120, 200)
        else:
            self.resize(120, 80)

        self.status_label = QLabel("\n睡眠監視停止中...\n")
        self.status_label.setStyleSheet("color: black; font-size: 8pt; font-weight: bold;")
        self.start_btn = QPushButton("開始")
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)

        main_layout.addWidget(self.status_label)
        if self.debug:
            btn_row = QtWidgets.QHBoxLayout()
            btn_row.addWidget(self.start_btn)
            btn_row.addWidget(self.stop_btn)
            main_layout.addLayout(btn_row)

        self.detector: SleepDetector | None = None
        self.timer: QTimer | None = None

        # ---- シグナル接続 ----
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.event_bus.on("timer.started", self._event_timer_start)
        self.event_bus.on("timer.paused", self._event_timer_stop)
        self.event_bus.on("timer.resumed", self._event_timer_start)
        self.event_bus.on("timer.finished", self._event_timer_stop)
        self.event_bus.on("timer.give_up", self.stop_detection)

        print("[SleepCheckerWidget] init complete")

    def _resolve_interval_seconds(self) -> int:
        raw = self.config.get("sleep_checker_interval")
        if isinstance(raw, dict):
            raw = raw.get("value")
        try:
            v = int(raw)
            if v <= 0:
                return 30
            return v
        except Exception:
            return 30

    def start_detection(self):
        if self.detector is None:
            self.detector = SleepDetector(
                device=self.config.get("sleep_checker_device") or 0,
                view=self.debug
            )
        if self.timer:
            self.timer.stop()
        self.timer = QTimer(self)
        interval_sec = self._resolve_interval_seconds()
        self.timer.setInterval(interval_sec * 1000)
        self.timer.timeout.connect(self.check_sleep)
        self.timer.start()

        self.status_label.setText("睡眠監視有効\nカメラ使用中⏺️...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        print(f"[SleepCheckerWidget] start_detection interval={interval_sec}s")
        self.check_sleep()

    def stop_detection(self):
        self.status_label.setText("\n睡眠監視停止中...\n")
        if self.detector:
            self.detector.release()
            self.detector = None
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("[SleepCheckerWidget] stop_detection")

    def check_sleep(self):
        if not self.detector:
            return
        now = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        detected, info = self.detector.detect()
        if detected:
            self.status_label.setText(f"睡眠監視有効\nカメラ使用中⏺️...\n[{info}]\n睡眠検出！")
            self.continuous_sleep_detection_count += 1
            self.event_bus.emit(
                "sleep_checker.sleep_detected",
                payload= self.continuous_sleep_detection_count
            )
            if self.continuous_sleep_detection_count == 1:
                self.voice_service.play_async("オキテ1")
            elif self.continuous_sleep_detection_count == 2:
                self.voice_service.play_async("オキテ2")
            elif self.continuous_sleep_detection_count >= 3:
                self.voice_service.play_async("オキテ3")

        else:
            self.status_label.setText(f"睡眠監視有効\nカメラ使用中⏺️...\n[{info}]\n")
            if self.continuous_sleep_detection_count >= 3:
                self.event_bus.emit(
                    "sleep_checker.woke_up",
                    payload= self.continuous_sleep_detection_count
                )
                self.voice_service.play_async("オハヨウ")
            self.continuous_sleep_detection_count = 0

    def _event_timer_start(self,payload = None):
        print("[SleepCheckerWidget] timer.start event → start_detection()")
        self.start_detection()

    def _event_timer_stop(self,payload = None):
        print("[SleepCheckerWidget] timer.stop event → stop_detection()")
        self.stop_detection()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._bg_pix.isNull():
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = self.rect()
        pix = self._bg_pix
        pw, ph = pix.width(), pix.height()
        if pw == 0 or ph == 0:
            return
        if self._bg_mode == "stretch_xy":
            tw = int(rect.width() * self._bg_scale_x)
            th = int(rect.height() * self._bg_scale_y)
            scaled = pix.scaled(tw, th, QtIgnore, QtSmooth)
        elif self._bg_mode == "contain":
            s = min(rect.width() / pw, rect.height() / ph) * self._bg_uniform
            scaled = pix.scaled(int(pw * s), int(ph * s), QtKeep, QtSmooth)
        elif self._bg_mode == "cover":
            s = max(rect.width() / pw, rect.height() / ph) * self._bg_uniform
            scaled = pix.scaled(int(pw * s), int(ph * s), QtKeep, QtSmooth)
        else:
            s = min(rect.width() / pw, rect.height() / ph)
            scaled = pix.scaled(int(pw * s), int(ph * s), QtKeep, QtSmooth)
        target = QtCore.QRect(0, 0, scaled.width(), scaled.height())
        target.moveCenter(rect.center())
        painter.drawPixmap(target, scaled)
