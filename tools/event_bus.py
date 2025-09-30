# tools/event_bus.py
from PySide6 import QtCore

class EventBus(QtCore.QObject):
    """共通の軽量イベントハブ"""
    message = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._routers = []  # ライフサイクル保持

    def emit(self, topic: str, **payload):
        """イベント発行。例: bus.emit('timer.started', seconds=10)"""
        self.message.emit(topic, payload)

    def on(self, topic: str, slot):
        """トピックを絞って購読: bus.on('timer.started', handler)"""
        router = _TopicRouter(topic, slot, self)
        self.message.connect(router._dispatch)
        self._routers.append(router)
        return router  

class _TopicRouter(QtCore.QObject):
    def __init__(self, topic: str, slot, parent=None):
        super().__init__(parent)
        self._topic = topic
        self._slot = slot

    @QtCore.Slot(str, object)
    def _dispatch(self, topic: str, payload: object):
        if topic == self._topic:
            self._slot(payload if isinstance(payload, dict) else {})
