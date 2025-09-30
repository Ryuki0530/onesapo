#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプル動画再生ウィンドウ (ffpyplayer + PyQt6)
- 再生のみ
- 再生終了後は自動でウィンドウを閉じる
"""

from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtGui import QImage, QPixmap

try:
    from ffpyplayer.player import MediaPlayer
    FFPYPLAYER_AVAILABLE = True
except ImportError:
    FFPYPLAYER_AVAILABLE = False


class PlayerWindow(QMainWindow):
    window_closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("onesapo - ムービー")
        self.resize(960, 540)

        # 映像表示ラベル
        self.video_label = QLabel("動画を開いてください")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background:#101010; color:#AAA;")

        # レイアウト
        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.video_label, stretch=1)
        self.setCentralWidget(root)

        # 状態
        self.player: MediaPlayer | None = None
        self.current_frame_bytes: bytes | None = None
        self.pending_timer: QTimer | None = None
        self._closing = False  # EOF/close 処理中フラグ

    def load_and_play_video(self, file_path: str):
        """外部から呼び出して動画再生開始"""
        if not FFPYPLAYER_AVAILABLE:
            QMessageBox.critical(self, "エラー", "ffpyplayer 未インストール: pip install ffpyplayer")
            return
        p = Path(file_path)
        if not p.exists():
            QMessageBox.critical(self, "エラー", f"ファイルが存在しません:\n{file_path}")
            return

        # 既存停止
        self._stop(close=True)

        self.video_label.setText("読み込み中...")
        self.repaint()

        ff_opts = {
            "out_format": "rgb24",   # 変更: bgr24 -> rgb24
            "sync": "audio",
            "paused": False,
        }
        try:
            self.player = MediaPlayer(str(p), ff_opts=ff_opts)
        except Exception:
            # 一部ビルドでキー名違いの場合のフォールバック
            try:
                ff_opts2 = dict(ff_opts)
                ff_opts2["out_fmt"] = ff_opts2.pop("out_format")
                self.player = MediaPlayer(str(p), ff_opts=ff_opts2)
            except Exception as e:
                self.player = None
                QMessageBox.critical(self, "初期化失敗", f"MediaPlayer 生成に失敗:\n{e}")
                return

        # 取得ループ開始
        self._schedule_next_frame(0)

    # ===== 内部ループ =====
    def _schedule_next_frame(self, delay_sec: float):
        if self._closing:
            return
        if self.pending_timer:
            self.pending_timer.stop()
            self.pending_timer.deleteLater()
        self.pending_timer = QTimer(self)
        self.pending_timer.setSingleShot(True)
        msec = max(int(delay_sec * 1000), 1)
        self.pending_timer.timeout.connect(self._fetch_frame)
        self.pending_timer.start(msec)

    def _fetch_frame(self):
        if self._closing or not self.player:
            return
        try:
            frame, val = self.player.get_frame()
        except Exception as e:
            print("get_frame 例外:", e)
            self.video_label.setText("フレーム取得エラー")
            self._finish_and_close()
            return

        # EOF
        if val == 'eof':
            self._finish_and_close()
            return

        if frame is not None:
            img, pts = frame
            w, h = img.get_size()
            raw = img.to_bytearray()[0]
            self.current_frame_bytes = bytes(raw)
            # 変更: Format_RGB888
            qimg = QImage(self.current_frame_bytes, w, h, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qimg).scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(pix)

        # 次フレームまでの遅延
        delay = 0.001
        if isinstance(val, (int, float)) and val > 0:
            delay = val
        self._schedule_next_frame(delay)

    def _finish_and_close(self):
        """再生終了またはエラー時に呼ぶ"""
        if self._closing:
            return
        self._closing = True
        # 後処理して閉じる
        self._stop(close=True)
        # close() で closeEvent -> window_closed シグナル
        self.close()

    def _stop(self, close=False):
        if self.pending_timer:
            self.pending_timer.stop()
            self.pending_timer.deleteLater()
            self.pending_timer = None
        if self.player:
            try:
                self.player.set_pause(True)
            except Exception:
                pass
            if close:
                try:
                    self.player.close_player()
                except Exception:
                    pass
                self.player = None

    # ===== イベント =====
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.video_label.pixmap():
            self.video_label.setPixmap(
                self.video_label.pixmap().scaled(
                    self.video_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def closeEvent(self, event):
        self._closing = True
        self._stop(close=True)
        self.window_closed.emit()
        super().closeEvent(event)