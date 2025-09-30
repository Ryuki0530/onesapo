# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore

class UnityDebuggerWidget(QtWidgets.QWidget):
    """
    Unityデバッガー用ウィジェット
    """
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.ctrl = controller

        # --- UI ---
        smile_layout = QtWidgets.QHBoxLayout()
        self.smile_sec_edit = QtWidgets.QSpinBox()
        self.smile_sec_edit.setRange(1, 60)
        self.smile_sec_edit.setValue(2)
        smile_sec_label = QtWidgets.QLabel("秒")
        btn_smile = QtWidgets.QPushButton("スマイルモーション")
        smile_layout.addWidget(QtWidgets.QLabel("時間:"))
        smile_layout.addWidget(self.smile_sec_edit)
        smile_layout.addWidget(smile_sec_label)
        smile_layout.addWidget(btn_smile)

        # ジト目アニメーション
        jitome_layout = QtWidgets.QHBoxLayout()
        self.jitome_sec_edit = QtWidgets.QSpinBox()
        self.jitome_sec_edit.setRange(1, 60)
        self.jitome_sec_edit.setValue(2)
        jitome_sec_label = QtWidgets.QLabel("秒")
        btn_jitome = QtWidgets.QPushButton("ジト目モーション")
        jitome_layout.addWidget(QtWidgets.QLabel("時間:"))
        jitome_layout.addWidget(self.jitome_sec_edit)
        jitome_layout.addWidget(jitome_sec_label)
        jitome_layout.addWidget(btn_jitome)

        # リップアニメーション
        lip_layout = QtWidgets.QHBoxLayout()
        self.lip_sec_edit = QtWidgets.QSpinBox()
        self.lip_sec_edit.setRange(1, 60)
        self.lip_sec_edit.setValue(2)
        lip_sec_label = QtWidgets.QLabel("秒")
        btn_lip = QtWidgets.QPushButton("リップモーション")
        btn_lip_stop = QtWidgets.QPushButton("停止")
        lip_layout.addWidget(QtWidgets.QLabel("時間:"))
        lip_layout.addWidget(self.lip_sec_edit)
        lip_layout.addWidget(lip_sec_label)
        lip_layout.addWidget(btn_lip)
        lip_layout.addWidget(btn_lip_stop)

        # 待機Bアニメーション
        idleB_layout = QtWidgets.QHBoxLayout()
        self.idleB_sec_edit = QtWidgets.QSpinBox()
        self.idleB_sec_edit.setRange(1, 60)
        self.idleB_sec_edit.setValue(2)
        idleB_sec_label = QtWidgets.QLabel("秒")
        btn_idleB = QtWidgets.QPushButton("待機Bモーション")
        idleB_layout.addWidget(QtWidgets.QLabel("時間:"))
        idleB_layout.addWidget(self.idleB_sec_edit)
        idleB_layout.addWidget(idleB_sec_label)
        idleB_layout.addWidget(btn_idleB)

        lay = QtWidgets.QVBoxLayout(self)
        for w in (smile_layout, jitome_layout, lip_layout, idleB_layout):
            lay.addLayout(w)
        lay.addStretch(1)

        # --- 配線 ---
        btn_smile.clicked.connect(self._smile)
        btn_jitome.clicked.connect(self._jitome)
        btn_lip.clicked.connect(self._lip)
        btn_lip_stop.clicked.connect(self._lip_stop)
        btn_idleB.clicked.connect(self._idleB)

    def _smile(self):
        try:
            sec = float(self.smile_sec_edit.text())
            ms = int(sec * 1000)
            self.ctrl.smile(ms)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "入力エラー", "秒数を正しく入力してください。")

    def _jitome(self):
        try:
            sec = float(self.jitome_sec_edit.text())
            ms = int(sec * 1000)
            self.ctrl.jitome(ms)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "入力エラー", "秒数を正しく入力してください。")

    def _lip(self):
        try:
            sec = float(self.lip_sec_edit.text())
            ms = int(sec * 1000)
            self.ctrl.lip(ms)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "入力エラー", "秒数を正しく入力してください。")

    def _lip_stop(self):
        self.ctrl.lip_stop()

    def _idleB(self):
        try:
            sec = float(self.idleB_sec_edit.text())
            ms = int(sec * 1000)
            self.ctrl.idleB(ms)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "入力エラー", "秒数を正しく入力してください。")
