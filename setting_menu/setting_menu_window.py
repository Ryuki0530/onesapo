import os
import sys

from PySide6 import QtWidgets, QtCore

from user_data_manager import ConfigData


class SettingMenuWindow(QtWidgets.QDialog):
    def __init__(self, config: ConfigData | None = None, event_bus=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.resize(320, 240)

        self._config = config or ConfigData()
        self._editors = {}   # key -> (widget, type_str)

        root = QtWidgets.QVBoxLayout(self)

        # スクロール領域（項目が増えても対応）
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        root.addWidget(scroll)

        body = QtWidgets.QWidget(scroll)
        form = QtWidgets.QFormLayout(body)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight if hasattr(QtCore.Qt, "AlignmentFlag") else QtCore.Qt.AlignRight)
        scroll.setWidget(body)

        # editable=True の項目を自動生成
        for item in self._config.get_editable_items():
            key = item.get("key")
            disp = item.get("display_name") or key
            type_str = (item.get("type") or "string").lower()
            value = item.get("value")
            attrs = item.get("attributes")

            w = self._create_editor(type_str, value, key)
            # 属性などはヒントとして表示
            hint_parts = []
            if attrs:
                hint_parts.append(f"属性: {attrs}")
            hint_parts.append(f"型: {type_str}")
            w.setToolTip(" / ".join(hint_parts))

            form.addRow(QtWidgets.QLabel(disp, body), w)
            self._editors[key] = (w, type_str)

        # ボタン
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        root.addWidget(btn_box)

    def _create_editor(self, type_str: str, value, key: str):
        # boolean: チェックボックス
        if type_str == "boolean":
            cb = QtWidgets.QCheckBox(self)
            cb.setChecked(bool(value))
            return cb

        # int / float: SpinBox 系
        if type_str == "int":
            sb = QtWidgets.QSpinBox(self)
            sb.setRange(-1_000_000_000, 1_000_000_000)
            try:
                sb.setValue(int(value) if value is not None else 0)
            except Exception:
                sb.setValue(0)
            return sb

        if type_str == "float":
            dsb = QtWidgets.QDoubleSpinBox(self)
            dsb.setDecimals(4)
            dsb.setRange(-1e12, 1e12)
            try:
                dsb.setValue(float(value) if value is not None else 0.0)
            except Exception:
                dsb.setValue(0.0)
            return dsb

        # path: 行編集 + 参照ボタン
        if type_str == "path":
            line = QtWidgets.QLineEdit(self)
            line.setText(str(value) if value is not None else "")
            btn = QtWidgets.QPushButton("参照...", self)

            # フォルダ/ファイルの簡易推定（key名や現状の値から）
            def browse():
                current = line.text().strip()
                choose_dir = ("folder" in key.lower()) or (current and os.path.isdir(current))
                if choose_dir:
                    d = QtWidgets.QFileDialog.getExistingDirectory(self, "フォルダを選択", current or os.getcwd())
                    if d:
                        line.setText(d)
                else:
                    fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, "ファイルを選択", current or os.getcwd(), "すべてのファイル (*)")
                    if fn:
                        line.setText(fn)

            btn.clicked.connect(browse)

            cont = QtWidgets.QWidget(self)
            lay = QtWidgets.QHBoxLayout(cont); lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(line, 1)
            lay.addWidget(btn, 0)
            # 値アクセス時に line を返すように cont に属性を持たせる
            cont._line_edit = line
            return cont

        # string(既定)
        line = QtWidgets.QLineEdit(self)
        line.setText("" if value is None else str(value))
        return line

    def _collect_updates(self) -> dict:
        updates = {}
        for key, (w, type_str) in self._editors.items():
            if type_str == "boolean":
                updates[key] = bool(w.isChecked())
            elif type_str == "int":
                updates[key] = int(w.value())
            elif type_str == "float":
                updates[key] = float(w.value())
            elif type_str == "path":
                # _line_edit を持つコンテナ
                line = getattr(w, "_line_edit", None)
                updates[key] = line.text().strip() if line else ""
            else:
                # string 既定
                updates[key] = w.text().strip() if hasattr(w, "text") else str(w)
        return updates

    def _on_save(self):
        updates = self._collect_updates()
        # ConfigData.set は既存キーのみ更新する仕様
        self._config.set(updates)
        self.accept()


# 動作確認用（単体起動時）
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dlg = SettingMenuWindow()
    dlg.exec()