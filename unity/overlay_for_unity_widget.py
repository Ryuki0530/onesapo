# overlay_for_unity_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QRect, QObject, QEvent, QPoint

# フラグの列挙（PySide6）
WIN = Qt.WindowType.Window
TOOL = Qt.WindowType.Tool
FRAMELESS = Qt.WindowType.FramelessWindowHint
WA = Qt.WidgetAttribute


class OverlayOnWidget(QWidget):
    def __init__(self, target_widget: QWidget, parent_window: QWidget, *, click_through_bg=False):
        super().__init__(parent_window)

        self._target = target_widget
        self._parent_window = parent_window

        flags = self.windowFlags() | WIN | FRAMELESS | TOOL
        self.setWindowFlags(flags)

        self.setAttribute(WA.WA_TranslucentBackground, True)
        # ※ 子ウィジェットを普通に操作したいので、まずはアクティブ奪取の抑制は外す
        # self.setAttribute(WA.WA_ShowWithoutActivating, True)  # ← 一旦コメントアウト

        # ★ クリック透過は無効（まずは確実に操作できる状態に）
        # if click_through_bg:
        #     self.setAttribute(WA.WA_TransparentForMouseEvents, True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        target_widget.installEventFilter(self)
        parent_window.installEventFilter(self)

        self._anchors = {}
        self.sync_to_target()


    def add_overlay_widget(self, w: QWidget):
        w.setParent(self)
        w.setAttribute(WA.WA_TransparentForMouseEvents, False)
        w.show()

    def set_anchor(self, w: QWidget, rx: float, ry: float, *, ax: float = 0.0, ay: float = 0.0, dx: int = 0, dy: int = 0):
        self._anchors[w] = (rx, ry, ax, ay, dx, dy)
        self._reposition_child(w)

    def eventFilter(self, obj: QObject, ev: QEvent) -> bool:
        t = ev.type()
        if obj in (self._target, self._parent_window):
            if t in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show,
                     QEvent.Type.Hide, QEvent.Type.WindowStateChange, QEvent.Type.ActivationChange):
                self.sync_to_target()
        return super().eventFilter(obj, ev)

    def sync_to_target(self):
        # 親が非表示 or 最小化なら隠す（※ isActiveWindow は見ない）
        if (not self._parent_window.isVisible()
            or self._parent_window.isMinimized()):
            self.hide()
            return

        if not self._target.isVisible():
            self.hide()
            return

        top_left = self._target.mapToGlobal(self._target.rect().topLeft())
        self.setGeometry(QRect(top_left, self._target.size()))
        self.show()
        self.raise_()  # ← Z順を安定させる

        for w in list(self._anchors.keys()):
            if w:
                self._reposition_child(w)

    def _reposition_child(self, w: QWidget):
        rx, ry, ax, ay, dx, dy = self._anchors[w]
        W, H = self.width(), self.height()
        px, py = int(round(rx * W)), int(round(ry * H))
        cw, ch = w.width(), w.height()
        x = px - int(round(ax * cw)) + dx
        y = py - int(round(ay * ch)) + dy
        w.move(max(0, min(W - cw, x)), max(0, min(H - ch, y)))

    def set_children_visible(self, visible: bool):
        """
        アンカー管理している全オーバーレイ子ウィジェットの表示/非表示を一括変更
        """
        for w in list(self._anchors.keys()):
            if w:
                w.setVisible(visible)

    def hide_children(self):
        """内包（アンカー登録）ウィジェットを全て非表示"""
        self.set_children_visible(False)

    def show_children(self):
        """内包（アンカー登録）ウィジェットを全て表示"""
        self.set_children_visible(True)

    def toggle_children(self):
        """
        全子ウィジェットの表示状態をトグル
        （最初に True のものが一つでもあれば全て非表示、なければ表示）
        """
        any_visible = any(w.isVisible() for w in self._anchors.keys() if w)
        self.set_children_visible(not any_visible)
