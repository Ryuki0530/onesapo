import os
import json
import shutil
from tools import event_bus as event

class ConfigData:
    def __init__(self, config_file: str = None, event_bus: event.EventBus = None):
        # 設定ファイルのパスを決定
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(assets_dir, exist_ok=True)
        self.config_file = config_file or os.path.join(assets_dir, "config.json")
        self.event_bus = event_bus

        # 設定ファイルがなければデフォルトからコピー
        if not os.path.exists(self.config_file):
            default_path = os.path.join(os.path.dirname(__file__), "default_config.json")
            shutil.copy(default_path, self.config_file)

        # 設定データをロード
        with open(self.config_file, "r", encoding="utf-8") as f:
            self._config_data = json.load(f)

    def get(self, key):
        """設定項目名を指定して値を取得"""
        try:
            item = self._config_data.get(key)
            if item is not None:
                return item.get("value")
            return None
        except Exception as e:
            print(f"Error getting '{key}': {e}")
            return None

    def set(self, updates: dict):
        """
        updates: { 設定項目名: 新しい値, ... }
        設定値を更新し、ファイルに保存し、イベントを発火
        """
        changed = False
        for key, value in updates.items():
            if key in self._config_data:
                self._config_data[key]["value"] = value
                changed = True
        try:
            if changed:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self._config_data, f, indent=4, ensure_ascii=False)
                if self.event_bus:
                    self.event_bus.emit("config.changed")
        except Exception as e:
            print(f"Error setting values: {e}")


    def get_all(self):
        """全設定データを返す（デバッグ用など）"""
        return self._config_data

    def get_editable_items(self):
        """
        editable=True の全設定項目について、
        設定項目名、表示名、属性、型、値をリストで返す。
        [
            {
                "key": 設定項目名,
                "display_name": 表示名,
                "attributes": 属性,
                "type": 型,
                "value": 値
            },
            ...
        ]
        """
        result = []
        try:
            for key, item in self._config_data.items():
                if item.get("editable", False):
                    result.append({
                        "key": key,
                        "display_name": item.get("display_name"),
                        "attributes": item.get("attributes"),
                        "type": item.get("type"),
                        "value": item.get("value")
                    })
        except Exception as e:
            print(f"Error getting editable items: {e}")
        return result