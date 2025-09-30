# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

class SampleWidget(QtWidgets.QWidget):

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
        self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # マスターレイアウト
        layout = QtWidgets.QVBoxLayout(self)

        """
        ここに、ウィジェットのUI要素を追加。
        """ 
        self.label = QtWidgets.QLabel("SAMPLE_TEXT")
        self.label.setStyleSheet("color: black; font-size: 10px;")
        layout.addWidget(self.label)

        self.button = QtWidgets.QPushButton("Click Me")
        layout.addWidget(self.button)
        layout.stretch(1)


        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """
        self.button.clicked.connect(self.on_button_clicked)

    """
    ここに、各種ロジックを記述。
    """
    def on_button_clicked(self):
        self.label.setText("Button Clicked!")
        
        """
        Unityのキャラクターを制御するAPI
        """
        self.ctrl.smile(500)  # Unityコントローラーのメソッドを呼び出す例
        """
        ボイスをしゃべらせるAPI
        口パクはボイスに合わせて自動で行われます。
        今後キャラクターが増えた場合でも、自動でキャラクターごとのボイスを再生します。
        """
        self.voice_service.play_async("サンプル")  # 音声サービスを使用する例

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
