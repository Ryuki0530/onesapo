# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

from .timer_logic import TimerLogic
from sound_effects.voice_service import VoiceService
from unity.async_unity_controller import AsyncUnityController
from user_data_manager.config_data import ConfigData
class TimerWidget(QtWidgets.QWidget):
    """
    見た目と配線だけ担当。
    満了時に controller.smile() → controller.lip() を呼ぶ。
    タイマーの純ロジックは別スレッド実行のため、整理のために TimerLogic に分離。
    """
    def __init__(self, controller: AsyncUnityController, voice_service: VoiceService, event_bus,config: ConfigData, parent=None):


        # MTGで30分って聞いた気がするからとりあえずデフォで30分
        self.DEFAULT_TIME = 60 * 30
        super().__init__(parent)
        self.ctrl : AsyncUnityController = controller
        self.cheering_frequency_minutes = 100
        self.cheering_enabled = True
        self.next_cheering_second_countdown = None
        self.ctrl = controller
        self.voice_service = voice_service
        self.event_bus = event_bus
        self.config: ConfigData = config
        self.logic = TimerLogic(self)
        self.paused_counter = 0
        

        # --- UI ---
        #レイアウト背景のデザイン
        layout = QtWidgets.QVBoxLayout(self)
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/timer/bg.png")  # 画像パス
        self._bg_mode = "stretch_xy"   # "stretch_xy" | "contain" | "cover"
        self._bg_scale_x = 1.0         # 横の倍率（stretch_xy 用）
        self._bg_scale_y = 1.0         # 縦の倍率（stretch_xy 用）
        self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)


        self.resize(120, 170) # 最小サイズを設定

        # self.spin = QtWidgets.QSpinBox()
        # self.spin.setRange(1, 3600)
        # self.spin.setSuffix(" sec")
        # layout.addWidget(self.spin)

        self.btn_start = QtWidgets.QPushButton()
        start_icon = QtGui.QIcon("./assets/timer/btn/start.png")
        self.btn_start.setIcon(start_icon)
        self.btn_start.setFlat(True)
        self.btn_start.setStyleSheet("background: transparent; border: none;")
        self.btn_start.setIconSize(QtCore.QSize(140, 160))
        self.btn_start.setEnabled(True)
        self.btn_start.setVisible(True)

        self.btn_pause = QtWidgets.QPushButton()
        pause_icon = QtGui.QIcon("./assets/timer/btn/pause.png")
        self.btn_pause.setIcon(pause_icon)
        self.btn_pause.setFlat(True)
        self.btn_pause.setStyleSheet("background: transparent; border: none;")
        self.btn_pause.setIconSize(QtCore.QSize(110, 110))
        self.btn_pause.setEnabled(False)
        self.btn_pause.setVisible(False)
        self.btn_pause.setEnabled(False)

        self.btn_giveup = QtWidgets.QPushButton()
        self.btn_giveup.setText("あきらめる")
        self.btn_giveup.setVisible(False)
        self.btn_giveup.setEnabled(False)


        self.btn_resume = QtWidgets.QPushButton()
        resume_icon = QtGui.QIcon("./assets/timer/btn/resume.png")
        self.btn_resume.setIcon(resume_icon)
        self.btn_resume.setFlat(True)
        self.btn_resume.setStyleSheet("background: transparent; border: none;")
        self.btn_resume.setIconSize(QtCore.QSize(100, 100))
        self.btn_resume.setVisible(False)
        self.btn_resume.setEnabled(False)

        btns = QtWidgets.QVBoxLayout(self)
        btns.addWidget(self.btn_start)
        btns.addWidget(self.btn_pause)
        btns.addWidget(self.btn_giveup)
        btns.addWidget(self.btn_resume)
        layout.addLayout(btns)

        self.label = QtWidgets.QLabel("START")
        self.label.setStyleSheet("color: black; font-size: 33px; font-weight: bold;")
        layout.addWidget(self.label)
        self.label.setVisible(False)
        layout.stretch(1)

        # --- 配線 ---
        self.btn_start.clicked.connect(self._start)
        self.btn_pause.clicked.connect(self._pause)
        self.btn_resume.clicked.connect(self._resume)
        self.btn_giveup.clicked.connect(self._give_up)
        self.logic.finished.connect(self._on_finished)
        self.logic.tick.connect(self._on_tick)

    def _start(self):
        # self.logic.start(self.spin.value() * 1000)
        self.logic.start(self.DEFAULT_TIME * 1000)
        self.cheering_enabled = self.config.get("cheering_enabled")
        self.cheering_frequency_minutes = self.config.get("cheering_frequency")
        self.next_cheering_second_countdown = self.cheering_frequency_minutes * 60
        self.btn_start.setVisible(False)
        self.btn_start.setEnabled(False)
        self.btn_pause.setVisible(True)
        self.btn_pause.setEnabled(True)
        self.event_bus.emit("timer.started", seconds = self.DEFAULT_TIME)
        self.ctrl.smile(10000)
        self.ctrl.gattu(10000)
        self.voice_service.play_async_random("スタート", 1, 3)
        self.label.setVisible(True)

    def _pause(self):
        self.logic.pause()
        self.btn_giveup.setVisible(True)
        self.btn_giveup.setEnabled(True)
        self.btn_resume.setVisible(True)
        self.btn_resume.setEnabled(True)
        self.btn_pause.setVisible(False)
        self.btn_pause.setEnabled(False)
        self.paused_counter += 1
        self.event_bus.emit("timer.paused" , count = self.paused_counter,seconds = self.logic.remaining_seconds())

    def _give_up(self):
        self.logic.stop()
        self.btn_start.setEnabled(True)
        self.btn_start.setVisible(True)
        self.btn_pause.setVisible(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setVisible(False)
        self.btn_resume.setEnabled(False)
        self.btn_giveup.setVisible(False)
        self.btn_giveup.setEnabled(False)
        self.event_bus.emit("timer.give_up")
        self.label.setVisible(False)
        self.paused_counter = 0

    def _resume(self):
        self.logic.resume()
        self.btn_resume.setVisible(False)
        self.btn_resume.setEnabled(False)
        self.btn_pause.setVisible(True)
        self.btn_pause.setEnabled(True)
        self.btn_giveup.setVisible(False)
        self.btn_giveup.setEnabled(False)
        self.event_bus.emit("timer.resumed")
        self.ctrl.smile(5000)

    def _on_tick(self, remain_ms: int):
        minutes = remain_ms // 60000
        seconds = (remain_ms % 60000) // 1000
        self.next_cheering_second_countdown -= 1
        self.label.setText(f" {minutes:02d}:{seconds:02d}")
        if minutes == 0 and seconds == 9:
            self.voice_service.play_async(f"カウントダウン")
        if self.cheering_enabled and self.next_cheering_second_countdown <= 0 and (minutes > 0 or seconds > 10):
            self._cheering()
            self.next_cheering_second_countdown = self.cheering_frequency_minutes * 60

    def _on_finished(self):
        # UIは止めずにUnityへ指令
        self.btn_start.setEnabled(True)
        self.btn_start.setVisible(True)
        self.btn_pause.setVisible(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setVisible(False)
        self.btn_resume.setEnabled(False)
        self.ctrl.smile(1000)
        self.event_bus.emit("timer.finished")
        self.label.setVisible(False)
        self.paused_counter = 0

    def _cheering(self):
        self.voice_service.play_async_random(f"エール", 1, 5)

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

        # ターゲットサイズ計算
        if self._bg_mode == "stretch_xy":
            # 縦横を独立にスケール（比率を自由に調整したいとき）
            tw = int(rect.width()  * self._bg_scale_x)
            th = int(rect.height() * self._bg_scale_y)
            scaled = pix.scaled(tw, th, QtIgnore, QtSmooth)

        elif self._bg_mode == "contain":
            # 画像全体が収まるように等倍スケール（黒帯が出る可能性）
            s = min(rect.width() / pw, rect.height() / ph) * self._bg_uniform
            tw, th = max(1, int(pw * s)), max(1, int(ph * s))
            scaled = pix.scaled(tw, th, QtKeep, QtSmooth)

        elif self._bg_mode == "cover":
            # 埋め尽くす（はみ出し切り抜きあり）
            s = max(rect.width() / pw, rect.height() / ph) * self._bg_uniform
            tw, th = max(1, int(pw * s)), max(1, int(ph * s))
            scaled = pix.scaled(tw, th, QtKeep, QtSmooth)

        else:
            # 想定外の指定は等倍contain扱い
            s = min(rect.width() / pw, rect.height() / ph)
            tw, th = max(1, int(pw * s)), max(1, int(ph * s))
            scaled = pix.scaled(tw, th, QtKeep, QtSmooth)

        # 中央配置
        target = QtCore.QRect(0, 0, scaled.width(), scaled.height())
        target.moveCenter(rect.center())

        painter.drawPixmap(target, scaled)
