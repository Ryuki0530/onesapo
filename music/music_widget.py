# timer_tool/timer_widget.py

from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

import sys
import os # クリーンアップのために os をインポート（後述）
from PySide6.QtWidgets import QApplication
from music.mainwindow import MainWindow # mainwindow.py から MainWindowクラスをインポート


class MusicWidget(QtWidgets.QWidget):

    # ...existing code...
    def __init__(self, controller, voice_service, parent=None):
        super().__init__(parent)
        self.ctrl = controller
        self.voice_service = voice_service

        # ...existing code...
        # 350x200サイズに最適化した薄い水色テーマ
        self.setStyleSheet("""
            MusicWidget {
                background-image: url('./assets/timer/btn/bg.png');
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;  /* stretch相当 */
                border-radius: 15px;
                border: 3px solid #F0F8FF;
            }
            
            QLabel {
                color: #2F4F4F;
                font-family: 'Arial', sans-serif;
                font-size: 11px;
                font-weight: bold;
                background: rgba(255, 255, 255, 0.4);
                border-radius: 6px;
                padding: 3px 6px;
                margin: 1px;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E0F6FF, stop:1 #87CEEB);
                color: #2F4F4F;
                border: 2px solid #B0E0E6;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
                min-height: 20px;
                max-height: 25px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F0F8FF, stop:1 #ADD8E6);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #B0E0E6, stop:1 #87CEEB);
            }
            
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.6);
                height: 6px;
                border-radius: 3px;
                border: 1px solid #E0F6FF;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E0F6FF, stop:1 #B0E0E6);
                border: 2px solid white;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            
            QMainWindow {
                background: rgba(224, 246, 255, 0.2);
                border-radius: 10px;
            }
        """)

        # ドロップシャドウ効果を追加
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)
        
        # 角丸効果を強化
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)


        # --- UI ---
        #レイアウト背景のデザイン
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/timer/btn/bg.png")  # ウィジェットの背景画像パス
        self._bg_mode = "stretch_xy"   # "stretch_xy" | "contain" | "cover"
        self._bg_scale_x = 1.0         # 横の倍率（stretch_xy 用）
        self._bg_scale_y = 1.0         # 縦の倍率（stretch_xy 用）
        self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # マスターレイアウト
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)  # 余白を調整
        layout.setSpacing(2)  # アイテム間隔を狭く
        
        
        title = QtWidgets.QLabel("BGM Player")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setMaximumHeight(20)  # 高さ制限
        title.setMaximumWidth(120)  # 幅を120pxに制限
        # タイトルを中央に配置
        layout.addWidget(title, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        

        # mainwindow.pyのMainWindowを組み込み
        self.music_player = MainWindow()
        layout.addWidget(self.music_player)
        
        #ここに、ウィジェットのUI要素を追加。
        


        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """
        #self.button.clicked.connect(self.on_button_clicked)

    """
    ここに、各種ロジックを記述。
    """
    def on_button_clicked(self):
        #self.label.setText("Button Clicked!")
        
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

def main():
    app = QApplication(sys.argv)
    # player.py で定義した MusicPlayer クラスのインスタンスを作成
    window = MainWindow()
    window.show()
    # app.exec() でアプリケーションを実行し、終了コードを受け取る
    exit_code = app.exec()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
