from PySide6 import QtWidgets, QtCore
import sys
from pathlib import Path

from .player_service import PlayerService
from .bgm_data import get_bgm_list


def format_time(ms: int) -> str:
    seconds = int(ms) // 1000
    minutes = seconds // 60
    seconds %= 60
    return f"{minutes:02}:{seconds:02}"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 300, 100)

        self.player = PlayerService()

        # bgm_data.pyからBGMリストを取得
        bgm_paths = get_bgm_list()
        playlist = [Path(path) for path in bgm_paths]  # Path オブジェクトに変換
        
        if playlist:
            self.player.load_playlist(playlist)
            # 最初から再生開始
            self.player.play()
        else:
            print("No music files found in bgm_data.")

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # フォルダ選択UIを削除（bgm直下固定のため）

        # 再生位置スライダー
        pos_layout = QtWidgets.QHBoxLayout()
        self.label_pos = QtWidgets.QLabel("00:00")
        self.slider_pos = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_pos.setRange(0, 100)
        self.label_dur = QtWidgets.QLabel("00:00")
        pos_layout.addWidget(self.label_pos)
        pos_layout.addWidget(self.slider_pos, 1)
        pos_layout.addWidget(self.label_dur)
        layout.addLayout(pos_layout)

        # 曲情報表示
        info_layout = QtWidgets.QVBoxLayout()
        self.label_title = QtWidgets.QLabel("-")
        self.label_artist = QtWidgets.QLabel("-")
        info_layout.addWidget(self.label_title)
        info_layout.addWidget(self.label_artist)
        layout.addLayout(info_layout)

        # コントロールボタン
        controls_layout = QtWidgets.QHBoxLayout()
        self.btn_play = QtWidgets.QPushButton("PLAY")
        self.btn_pause = QtWidgets.QPushButton("PAUSE")
        self.btn_stop = QtWidgets.QPushButton("STOP")
        self.btn_prev = QtWidgets.QPushButton("PREV")
        self.btn_next = QtWidgets.QPushButton("NEXT")
        for b in (self.btn_play, self.btn_pause, self.btn_stop, self.btn_prev, self.btn_next):
            controls_layout.addWidget(b)
        layout.addLayout(controls_layout)

        # 音量スライダー
        vol_layout = QtWidgets.QHBoxLayout()
        vol_label = QtWidgets.QLabel("Volume")
        self.slider_vol = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.label_vol = QtWidgets.QLabel("50%")
        vol_layout.addWidget(vol_label)
        vol_layout.addWidget(self.slider_vol, 1)
        vol_layout.addWidget(self.label_vol)
        layout.addLayout(vol_layout)

        # イベント接続
        self.btn_play.clicked.connect(self.on_play)
        self.btn_pause.clicked.connect(self.on_pause)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_next.clicked.connect(self.on_next)
        self.btn_prev.clicked.connect(self.on_prev)
        self.slider_vol.valueChanged.connect(self.on_volume_changed)
        self.slider_pos.sliderReleased.connect(self.on_position_changed)
        self.slider_pos.sliderPressed.connect(self.on_slider_pressed)
        self.slider_pos.valueChanged.connect(self.on_slider_preview)

        # タイマーを用いて再生位置を更新
        self._user_dragging = False
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(500)

        # 初期表示
        if playlist:
            self.update_track_info()

    def _collect_tracks(self, folder: Path) -> list[Path]:
        if not folder.exists():
            return []
        tracks = []
        tracks.extend(sorted(folder.glob("*.mp3")))
        tracks.extend(sorted(folder.glob("*.wav")))
        return tracks

    def on_play(self):
        self.player.play()

    def on_pause(self):
        self.player.pause()

    def on_stop(self):
        self.player.stop()
        self.slider_pos.setValue(0)
        self.label_pos.setText("00:00")

    def on_next(self):
        self.player.next_track()
        self.after_track_change()

    def on_prev(self):
        self.player.prev_track()
        self.after_track_change()

    def after_track_change(self):
        self.slider_pos.setValue(0)
        self.update_track_info()
        self.label_pos.setText("00:00")

    def update_track_info(self):
        meta = self.player.get_metadata()
        title = meta.get("title") or (self.player.get_current_path().stem if self.player.get_current_path() else "-")
        artist = meta.get("artist") or "Unknown Artist"
        self.label_title.setText(f"Title: {title}")
        self.label_artist.setText(f"Artist: {artist}")
        self.label_dur.setText(format_time(self.player.get_length()))

    def on_volume_changed(self, value: int):
        self.label_vol.setText(f"{value}%")
        self.player.set_volume(value / 100.0)

    def on_slider_pressed(self):
        self._user_dragging = True

    def on_slider_preview(self):
        if self._user_dragging:
            length = self.player.get_length()
            if length > 0:
                preview_ms = int(self.slider_pos.value() / 100 * length)
                self.label_pos.setText(format_time(preview_ms))

    def on_position_changed(self):
        self._user_dragging = False
        length = self.player.get_length()
        if length <= 0:
            return
        seek_ms = int(self.slider_pos.value() / 100 * length)
        self.player.set_position(seek_ms)
        self.label_pos.setText(format_time(seek_ms))

    def update_position(self):
        self.player.update()

        # 曲終了の検知とループ処理を追加
        if hasattr(self.player, 'is_finished') and self.player.is_finished():
            self.on_next()  # 次の曲へ（最後の曲なら最初に戻る）
            return
        
        length = self.player.get_length()
        if length <= 0:
            return
        if self._user_dragging:
            return
        pos = self.player.get_position()
        self.label_pos.setText(format_time(pos))
        self.label_dur.setText(format_time(length))
        self.slider_pos.blockSignals(True)
        self.slider_pos.setValue(int(pos / length * 100))
        self.slider_pos.blockSignals(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())