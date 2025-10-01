# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation

class MovieUnlockedReminderWidget(QtWidgets.QWidget):

    def __init__(self, controller, voice_service, event_bus, parent=None):
        super().__init__(parent)
        self.ctrl = controller
        self.voice_service = voice_service
        self.event_bus = event_bus

        # --- UI ---
        self.resize(0, 0)   # 初期状態は非表示

        # マスターレイアウト
        layout = QtWidgets.QVBoxLayout(self)

        """
        ここに、ウィジェットのUI要素を追加。
        """ 
        # タイトルラベル
        self.title_label = QtWidgets.QLabel("新しいムービーが解放されました！→")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13pt;
            font-weight: bold;
            background: rgba(0,0,0,0.5);
            border-radius: 8px;
            padding: 4px 0;
        """)
        layout.addWidget(self.title_label)

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
        is_unlocked = False
        if level["level"] == 2:
            is_unlocked = True
        elif level["level"] == 3:
            is_unlocked = True
        elif level["level"] == 4:
            is_unlocked = False
        elif level["level"] == 5:
            is_unlocked = False
        else :
            is_unlocked = False
        if not is_unlocked:
            return
        
        self.open(level["level"])
        QtCore.QTimer.singleShot(10000, self.close)

    def open(self, level):
        self.resize(290, 50)

    def close(self):
        self.resize(0, 0)

  