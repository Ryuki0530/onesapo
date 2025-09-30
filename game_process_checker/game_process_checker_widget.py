# timer_tool/timer_widget.py

from .winenum import WinEnumService, WindowInfo
import unicodedata

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton
from PySide6.QtCore import QTimer, QDateTime
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

from tools.event_bus import EventBus
from sound_effects import VoiceService
from user_data_manager.config_data import ConfigData
class GameProcessCheckerWidget(QtWidgets.QWidget):

    def __init__(self, controller, voice_service: VoiceService, event_bus: EventBus, config: ConfigData, parent=None):
        super().__init__(parent)
        self.debug = config.get("debug_mode")
        self.ctrl = controller
        self.voice_service: VoiceService = voice_service
        self.event_bus = event_bus
        self.config = config

        self.game_list = []
        self.game_word_path = "./data/game_words.txt"
        self.game_words = self._game_word_load(self.game_word_path)
        # print(self.game_words)

        self.continuous_game_detection_count = 0

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

        self.status_label = QLabel("\nゲーム監視停止中...\n")
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

        self.winenum: WinEnumService = WinEnumService()
        self.timer: QTimer | None = None

        # ---- シグナル接続 ----
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.event_bus.on("timer.started", self._event_timer_start)
        self.event_bus.on("timer.paused", self._event_timer_stop)
        self.event_bus.on("timer.resumed", self._event_timer_start)
        self.event_bus.on("timer.finished", self._event_timer_stop)

        print("[GameCheckerWidget] init complete")

    def _resolve_interval_seconds(self) -> int:
        raw = self.config.get("window_monitor_interval")
        if isinstance(raw, dict):
            raw = raw.get("value")
        try:
            v = int(raw)
            if v <= 0:
                return 30
            return v
        except Exception:
            return 30
        
    def _check_windows(self):
        windows = self.winenum.enumerate(include_empty = False, all_styles=False, include_exe=False)
        print(f"[GameProcessCheckerWidget] check_windows found {len(windows)} windows")
        if self.debug == False:
            return windows
        
        for win in windows:
            print(f"{win.title}")
        print("----")
        return windows

    def _game_word_load(self,path = None):
        if path is None:
            path = "./assets/game_process_checker/game_words.txt"

        words = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                line = unicodedata.normalize("NFKC", line)
                words.append(line)
        return words

    def _is_game(self, title: str) -> bool:
        for keyword in self.game_words:
            if keyword in title:
                return True
        return False

    def start_detection(self):
        if self.timer:
            self.timer.stop()
        self.timer = QTimer(self)
        interval_sec = self._resolve_interval_seconds()
        self.timer.setInterval(interval_sec * 1000)
        self.timer.timeout.connect(self.check_games)
        self.timer.start()

        self.status_label.setText("ゲーム監視有効\nタスク情報収集中...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        print(f"[GameCheckerWidget] start_detection interval={interval_sec}s")
        self.check_games()

    def stop_detection(self):
        self.status_label.setText("\nゲーム監視停止中...\n")
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("[GameCheckerWidget] stop_detection")

    def check_games(self):
        now = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        windows = self._check_windows()
        
        found_game = None
        for win in windows:
            if self._is_game(win.title):
                self.status_label.setText(f"ゲーム検出！\n[{now}]\n{win.title}")
                print(f"[GameProcessCheckerWidget] game detected: '{win.title}'")
                found_game = win
                break

        

        if found_game is not None:
            self.continuous_game_detection_count += 1
            self.event_bus.emit(
                    "game_checker.game_detected",
                    payload= found_game.title
            )
            if self.continuous_game_detection_count == 1:
                self.voice_service.play_async("ゲーム1")
            elif self.continuous_game_detection_count == 2:
                self.voice_service.play_async("ゲーム2")
            elif self.continuous_game_detection_count >= 3:
                self.voice_service.play_async("ゲーム3")
        else:
            self.status_label.setText(f"ゲーム監視有効\nタスク情報収集中...\n[{now}]")
            if self.continuous_game_detection_count >= 3:
                self.event_bus.emit(
                    "game_checker.game_exit",
                    payload= self.continuous_game_detection_count
                )

            self.continuous_game_detection_count = 0

    def _event_timer_start(self,payload = None):
        print("[GameCheckerWidget] timer.start event → start_detection()")
        self.start_detection()

    def _event_timer_stop(self,payload = None):
        print("[GameCheckerWidget] timer.stop event → stop_detection()")
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
