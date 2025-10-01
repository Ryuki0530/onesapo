# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation
from movie.movie_player import PlayerWindow

class MovieMenuWidget(QtWidgets.QWidget):

    def __init__(self, controller, voice_service, event_bus, config, save_data, parent=None):
        self.widget_size = [400, 150]  # メニューの初期サイズ
        super().__init__(parent)
        self.resize(self.widget_size[0], self.widget_size[1])
        self.ctrl = controller
        self.voice_service = voice_service
        self.event_bus = event_bus
        self.config = config
        self.save_data = save_data
        self.current_level : int = self.save_data.get("relationship")

        self.menu_opened = False

        # --- UI ---
        #レイアウト背景のデザイン
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/ui_bg/bg.png")  # ウィジェットの背景画像パス
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
        self.header_layout = QtWidgets.QHBoxLayout()
        self.title = QtWidgets.QLabel("親密度ムービーメニュー")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: black;")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.header_layout.addWidget(self.title)
        self.close_button = QtWidgets.QPushButton("✖")
        self.close_button.setStyleSheet("font-size: 18px; color: red;")
        self.close_button.setFixedSize(30, 30)
        self.header_layout.addWidget(self.close_button)

        self.movie_menu_layout = QtWidgets.QGridLayout()
        self.movie1 = MovieButtonWidget("assets/movies/movie1.mp4", "ムービー1")
        self.movie2 = MovieButtonWidget("assets/movies/movie2.mp4", "ムービー2")
        self.movie3 = MovieButtonWidget("assets/movies/movie3.mp4", "ムービー3")
        self.movie_menu_layout.addWidget(self.movie1, 0, 0)
        self.movie_menu_layout.addWidget(self.movie2, 0, 1)
        self.movie_menu_layout.addWidget(self.movie3, 0, 2)
        self.movie_unlock_check()
        self.event_bus.on("level_counter.level_up", self.movie_unlock_check_wrapper_for_event)

        layout.addLayout(self.header_layout)
        layout.addLayout(self.movie_menu_layout)
        layout.stretch(1)


        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """
        self.close_button.clicked.connect(self.close_menu)
    """
    ここに、各種ロジックを記述。
    """
    def movie_unlock_check_wrapper_for_event(self, event_data):
        self.current_level = event_data["level"]
        self.movie_unlock_check()

    def movie_unlock_check(self):
        if self.current_level >= 2:
            print("[MovieMenu] Unlocking movie 1")
            self.movie1.unlock_movie()
        if self.current_level >= 3:
            print("[MovieMenu] Unlocking movie 2")
            self.movie2.unlock_movie()
        # if self.current_level >= 4:
        #     print("[MovieMenu] Unlocking movie 3")
        #     self.movie3.unlock_movie()

    def open_menu(self):
        self.resize(self.widget_size[0], self.widget_size[1])
        self.menu_opened = True

    def close_menu(self):
        self.resize(0, 0)
        self.menu_opened = False

    def clicked_open_button(self):
        if self.menu_opened:
            self.close_menu()
        else:
            self.open_menu()
            
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


class MovieButtonWidget(QtWidgets.QWidget):

    def __init__(self, movie_path, movie_title, parent=None):
        super().__init__(parent)
        self.movie_path = movie_path
        self.movie_title = movie_title

        # マスターレイアウト
        layout = QtWidgets.QVBoxLayout(self)

        # 設定画面を開くボタン
        self.open_button = QtWidgets.QPushButton(self.movie_title)
        self.open_button.setStyleSheet("font-size: 20pt; ")
        self.open_button.setVisible(False)
        layout.addWidget(self.open_button)

        self.lock_label = QtWidgets.QLabel(f"{self.movie_title}\n未開放")
        self.lock_label.setStyleSheet("font-size: 20pt; color: gray;")
        layout.addWidget(self.lock_label)
        layout.addStretch(1)

        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """
        self.open_button.clicked.connect(self.play_movie)
    
    def unlock_movie(self):
        self.lock_label.setVisible(False)
        self.open_button.setVisible(True)

    def play_movie(self):
        self.player_window = PlayerWindow()
        self.player_window.show()
        self.player_window.activateWindow()
        self.player_window.load_and_play_video(self.movie_path)

