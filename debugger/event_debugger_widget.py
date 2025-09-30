# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

class EventDebuggerWidget(QtWidgets.QWidget):

    def __init__(self, controller, voice_service, event_bus, parent=None):
        super().__init__(parent)
        self.ctrl = controller
        self.voice_service = voice_service
        self.event_bus = event_bus

        # --- UI ---
        #レイアウト背景のデザイン
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/ui_bg/sample.png")  # ウィジェットの背景画像パス
        self._bg_mode = "stretch_xy"   # "stretch_xy" | "contain" | "cover"
        self._bg_scale_x = 1.0         # 横の倍率（stretch_xy 用）
        self._bg_scale_y = 1.0         # 縦の倍率（stretch_xy 用）
        # self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # マスターレイアウト
        layout = QtWidgets.QVBoxLayout(self)

        # 対象となる購読するイベントを選択するUI
        self.select_event_layout = QtWidgets.QHBoxLayout()
        self.select_label = QtWidgets.QLabel("Select Event to Debug:")
        self.select_label.setStyleSheet("color: black; font-size: 15px;")
        self.select_event_layout.addWidget(self.select_label)
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems([
            "timer.started",
            "timer.finished",
            "timer.paused",
            "timer.resumed",
            "config.changed",
            "sleep_checker.sleep_detected",
            "sleep_checker.woke_up",
            "game_checker.game_detected",
            "game_checker.game_exit"
        ])
        self.select_event_layout.addWidget(self.combo)
        layout.addLayout(self.select_event_layout)
        self.subscribe_button = QtWidgets.QPushButton("Subscribe")
        self.select_event_layout.addWidget(self.subscribe_button)

        # イベント受信を示す表示ラベル
        self.label = QtWidgets.QLabel("Event Debugger")
        self.label.setStyleSheet("color: black; font-size: 15px;")
        layout.addWidget(self.label)


        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """
        self.subscribe_button.clicked.connect(self.on_subscribe_clicked)
    
    """
    ここに、各種ロジックを記述。
    """
    def on_subscribe_clicked(self):
        selected_event = self.combo.currentText()
        self.event_bus.on(selected_event, self._on_event_received)
        self.label.setText(f"Subscribed to: {selected_event}")

    def _on_event_received(self, payload):
        self.label.setText(f"Event received: {payload}")

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
