# main.py
DEBUG = False

import os, sys
from PySide6 import QtWidgets, QtCore
QEvent = QtCore.QEvent

# グローバル機能インポート
from user_data_manager import ConfigData, SaveData
from tools.event_bus import EventBus
from sound_effects import VoiceService

# Unity関連モジュールインポート
from tools.ports import find_free_port
from unity.unity_ipc import UnityIPC
from unity.unity_embed import UnityEmbed, UnityEmbedConfig
from unity.async_unity_controller import AsyncUnityController
from unity.overlay_for_unity_widget import OverlayOnWidget

# 各種機能モジュールインポート
from setting_menu import SettingMenuOpenButtonWidget
from timer.timer_widget import TimerWidget
from widget_frameWork_sample.sample_widget import SampleWidget
from music.music_widget import MusicWidget  
from sleep_checker.sleep_checker_widget import SleepCheckerWidget
from game_process_checker.game_process_checker_widget import GameProcessCheckerWidget
from level_counter.level_counter_widget import LevelCounterWidget
from level_counter.consecutive_record_performance_witget import ConsecutiveRecordPerformanceWidget
from level_counter.level_up_performance_witget import LevelUpPerformanceWidget
from movie.movie_menu_button import MovieMenuOpenButtonWidget
from movie.movie_menu import MovieMenuWidget
from movie.movie_unlocked_reminder_witget import MovieUnlockedReminderWidget


class NullUnityController(QtCore.QObject):
    """Unityが利用できない状況で各ウィジェットを動作させるための no-op コントローラー"""

    error = QtCore.Signal(str)

    def __init__(self, reason: str = "Unity is not available"):
        super().__init__()
        self._reason = reason
        self._warned_methods: set[str] = set()

    def stop(self):
        """AsyncUnityController とインターフェイスを合わせる"""
        return None

    def __getattr__(self, item: str):
        def _noop(*args, **kwargs):
            if item not in self._warned_methods:
                print(f"[UnityDisabled] '{item}' call ignored. {self._reason}")
                self._warned_methods.add(item)
            return None

        return _noop


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):

        # --- 共通機能初期化 ---
        # イベントバスの初期化
        self.bus = EventBus()
        # 設定データ・セーブデータ読み込み
        self.config = ConfigData(event_bus=self.bus)
        self.save_data = SaveData(event_bus=self.bus)

        DEBUG = self.config.get("debug_mode")
        if DEBUG:
            from debugger.unity_debbugger_widget import UnityDebuggerWidget
            from debugger.event_debugger_widget import EventDebuggerWidget 

        self.current_character = "Milltina"

        super().__init__()
        self.setWindowTitle("おねサポ - OneSapo")

        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)

        # 左: Unity埋め込みとIPCコントローラー作成

        unity_exe_path = os.path.abspath(self.config.get("external_rendering_system_path"))
        
        port_number = find_free_port()
        print(f"Using port {port_number} for Unity IPC")
        self.unity = UnityEmbed(self)
        h.addWidget(self.unity)

        self._unity_ready = False
        unity_start_error_msg = ""
        try:
            self.unity.start(UnityEmbedConfig(unity_exe=unity_exe_path, port=port_number))
            ipc = UnityIPC(host="127.0.0.1", port=port_number, timeout=2.0, unity_boot=False)
            self.controller = AsyncUnityController(ipc)
            self._unity_ready = True
        except Exception as exc:
            unity_start_error_msg = str(exc) if exc else "Unknown error"
            print(f"外部レンダリングモジュールの起動に失敗しました: {unity_start_error_msg}")
            self.controller = NullUnityController(unity_start_error_msg)

        self.overlay = OverlayOnWidget(self.unity, parent_window=self, click_through_bg=False)
        self.installEventFilter(self)

        if not self._unity_ready:
            message_body = "外部レンダリングモジュールの起動に失敗しました。\n" + (unity_start_error_msg or "詳細情報はありません。")
            QtCore.QTimer.singleShot(0, lambda m=message_body: QtWidgets.QMessageBox.warning(self, "外部レンダリングモジュールの起動失敗", m))

        # キャラクターボイス再生サービス起動
        assets_voice_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "voice"))
        self.voice_service = VoiceService(self.controller,event_bus= self.bus, config=self.config, assets_root=assets_voice_root)
        self.voice_service.set_current_character(self.current_character)

        # 右: 仮のツール置き場
        if DEBUG:
            right = QtWidgets.QWidget(); v = QtWidgets.QVBoxLayout(right)
            h.addWidget(right)

        # 設定メニューを開くボタン
        self.setting_menu_button = SettingMenuOpenButtonWidget(self.controller, self.voice_service, self.bus, self.config)
        self.overlay.add_overlay_widget(self.setting_menu_button)
        self.overlay.set_anchor(self.setting_menu_button, rx=0.995, ry=0.12, ax=1.0, ay=0.0)

        #タイマーウィジェット(Unityウィンドウ上にGUIウィジェットを表示したい場合の実装例)
        self.timer = TimerWidget(self.controller, self.voice_service, self.bus)
        self.overlay.add_overlay_widget(self.timer)
        self.overlay.set_anchor(self.timer, rx=0.01, ry=0.775, ax=0.0, ay=0.0)

        #BGMプレイヤーウィジェット
        self.music_widget = MusicWidget(self.controller, self.voice_service)
        self.overlay.add_overlay_widget(self.music_widget)
        self.music_widget.resize(350, 200)  # 最小サイズを設定
        self.overlay.set_anchor(self.music_widget, rx=1.0, ry=0.775, ax=0.0, ay=0.0)

        # 睡眠チェッカーウィジェット
        self.sleep_checker_widget = SleepCheckerWidget(self.controller, self.voice_service, self.bus, self.config)
        self.overlay.add_overlay_widget(self.sleep_checker_widget)
        self.overlay.set_anchor(self.sleep_checker_widget, rx=0.01, ry=0.01, ax=0.0, ay=0.0)

        # ゲームプロセスチェッカーウィジェット
        self.game_process_checker_widget = GameProcessCheckerWidget(self.controller, self.voice_service, self.bus, self.config)
        self.overlay.add_overlay_widget(self.game_process_checker_widget)
        if not DEBUG:
            self.overlay.set_anchor(self.game_process_checker_widget, rx=0.01, ry=0.12, ax=0.0, ay=0.0)
        else:
            self.overlay.set_anchor(self.game_process_checker_widget, rx=0.01, ry=0.24, ax=0.0, ay=0.0)

        # レベルカウンターウィジェット
        self.level_counter_widget = LevelCounterWidget(self.controller, self.voice_service, self.bus, self.config, self.save_data)
        self.overlay.add_overlay_widget(self.level_counter_widget)
        self.overlay.set_anchor(self.level_counter_widget,rx=0.99, ry=0.01, ax=1.0, ay=0.0)

        # ムービーメニューウィジェット
        self.movie_menu_widget = MovieMenuWidget(self.controller, self.voice_service, self.bus,self.config,self.save_data)
        self.overlay.add_overlay_widget(self.movie_menu_widget)
        self.overlay.set_anchor(self.movie_menu_widget, rx=0.1, ry=0.3, ax=0.0, ay=0.0)
        self.movie_menu_widget.resize(0, 0)  # 最小サイズを設定

        # ムービーメニューを開くボタン
        self.movie_menu_open_button = MovieMenuOpenButtonWidget(self.controller, self.voice_service, self.movie_menu_widget, self.bus, self.config)
        self.overlay.add_overlay_widget(self.movie_menu_open_button)
        self.overlay.set_anchor(self.movie_menu_open_button,  rx=0.9, ry=0.12, ax=1.0, ay=0.0)

        # 連続記録パフォーマンスウィジェット
        self.consecutive_record_performance_widget = ConsecutiveRecordPerformanceWidget(self.controller, self.voice_service, self.bus)
        self.overlay.add_overlay_widget(self.consecutive_record_performance_widget)
        self.overlay.set_anchor(self.consecutive_record_performance_widget, rx=0.2, ry=0.7, ax=0.0, ay=0.0)

        # レベルアップパフォーマンスウィジェット
        self.level_up_performance_widget = LevelUpPerformanceWidget(self.controller, self.voice_service, self.bus)
        self.overlay.add_overlay_widget(self.level_up_performance_widget)
        self.overlay.set_anchor(self.level_up_performance_widget, rx=0.2, ry=0.7, ax=0.0, ay=0.0)

        # ムービーアンロックリマインダーウィジェット
        self.movie_unlocked_reminder_widget = MovieUnlockedReminderWidget(self.controller, self.voice_service, self.bus)
        self.overlay.add_overlay_widget(self.movie_unlocked_reminder_widget)
        self.overlay.set_anchor(self.movie_unlocked_reminder_widget, rx=0.24, ry=0.125, ax=0.0, ay=0.0)

        # # サンプルウィジェットの実装例1
        # self.sample_widget = SampleWidget(self.controller, self.voice_service, self.bus)
        # self.overlay.add_overlay_widget(self.sample_widget)
        # self.sample_widget.resize(160, 80)  # 最小サイズを設定
        # # Unity領域の左上を原点、右下をrx = 1.0, ry = 1.0の正規化座標
        # self.overlay.set_anchor(self.sample_widget, rx=0.5, ry=0.5, ax=0.0, ay=0.0)

        # # サンプルウィジェットの実装例2
        # self.sample_widget2 = SampleWidget(self.controller, self.voice_service, self.bus)
        # v.addWidget(self.sample_widget2)

        # Unity制御のテスト用UI
        if DEBUG:
            self.debugger = UnityDebuggerWidget(self.controller); v.addWidget(self.debugger)
            self.event_debugger = EventDebuggerWidget(self.controller, self.voice_service, self.bus); v.addWidget(self.event_debugger)
            self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True); v.addWidget(self.log)
            self.controller.error.connect(self.log.appendPlainText)
        if DEBUG:
            v.addStretch(1)

    def closeEvent(self, e):
        try: self.controller.stop()
        except Exception: pass
        try: self.unity.stop()
        except Exception: pass
        super().closeEvent(e)

    def eventFilter(self, obj, ev):
        # このウィンドウ自体が Move / Resize されたら
        if obj is self and ev.type() in (QEvent.Type.Move, QEvent.Type.Resize):
            if hasattr(self, "overlay"):
                self.overlay.sync_to_target()
        return super().eventFilter(obj, ev)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show()
    w.overlay.set_children_visible(False)
    QtCore.QTimer.singleShot(1000 * 3, lambda: w.overlay.set_children_visible(True))
    sys.exit(app.exec())
