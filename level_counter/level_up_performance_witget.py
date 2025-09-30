# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

class LevelUpPerformanceWidget(QtWidgets.QWidget):

    def __init__(self, controller, voice_service, event_bus, parent=None):
        super().__init__(parent)
        self.ctrl = controller
        self.voice_service = voice_service
        self.event_bus = event_bus

        # --- UI ---
        #レイアウト背景のデザイン
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/level_counter/bg2.png")  # ウィジェットの背景画像パス
        self._bg_mode = "stretch_xy"   # "stretch_xy" | "contain" | "cover"
        self._bg_scale_x = 1.0         # 横の倍率（stretch_xy 用）
        self._bg_scale_y = 1.0         # 縦の倍率（stretch_xy 用）
        self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.resize(300, 150) # 最小サイズを設定
        self.resize(0, 0)   # 初期状態は非表示

        # マスターレイアウト
        layout = QtWidgets.QVBoxLayout(self)

        """
        ここに、ウィジェットのUI要素を追加。
        """ 
        # タイトルラベル
        self.title_label = QtWidgets.QLabel("Friendship Level Up!")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13pt;
            letter-spacing: 2px;
            font-weight: bold;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 4px 0;
        """)
        layout.addWidget(self.title_label)

        # 日数ラベル（大きく目立たせる）
        self.level_label = QtWidgets.QLabel("0")
        self.level_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.level_label.setStyleSheet("""
            color: #ffeb3b;
            font-size: 40pt;
            font-weight: bold;
        """)
        layout.addWidget(self.level_label)

        # サブラベル
        self.sub_label = QtWidgets.QLabel("信頼度レベルUP！")
        self.sub_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14pt;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
            padding: 2px 0;
        """)
        layout.addWidget(self.sub_label)

        layout.stretch(1)

        # 10秒後に_update_consecutive_daysを呼び出すテスト用タイマー
        # QtCore.QTimer.singleShot(10000, lambda: self._update_consecutive_days({"days": 5}))


        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """
        self.event_bus.on("level_counter.level_up", self._level_up)


    """
    ここに、各種ロジックを記述。
    """

    def _level_up(self, level):
        self.open(level["level"])
        QtCore.QTimer.singleShot(5000, self.close)

    def open(self, level):
        self.level_label.setText(f"Lv.{level}")
        self.resize(300, 150)

    def close(self):
        self.resize(0, 0)

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
