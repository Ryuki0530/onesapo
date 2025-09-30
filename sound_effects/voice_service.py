# sound_effects/voice_service.py
"""
assets/voice/<character>/<voice_name>.wav を解決して再生。
再生中は Unity に LIP(既定60秒) → 再生終了後に LIP STOP。
UIを止めないため内部でスレッド起動（非同期API）。
"""

import os
import threading
import traceback
import winsound  # Windows標準（WAVのみ）
from user_data_manager import ConfigData
from tools.event_bus import EventBus
import tempfile
from pydub import AudioSegment
import random

class VoiceService:
    def __init__(self, controller, event_bus: EventBus, config: ConfigData, assets_root: str, default_lip_ms: int = 60_000):
        """
        controller: AsyncUnityController（lip(int), lip_stop() を持つ）
        assets_root: assets/voice への絶対パス
        """
        self._config = config
        self.voice_volume = self._read_voice_volume()
        print(f"VoiceService: voice_volume_setting = {self.voice_volume}")

        self._controller = controller
        self._assets_root = os.path.abspath(assets_root)
        self._default_lip_ms = int(default_lip_ms)
        self._current_character = None  # main.py がマスタ。set_current_character()で同期

        # EventBus を保持し、設定変更を購読
        self._bus = event_bus
        if self._bus and hasattr(self._bus, "on"):
            self._bus.on("config.changed", self._on_config_changed)

    # --- キャラ（mainがマスタ） ---
    def set_current_character(self, name: str):
        self._current_character = name

    def get_current_character(self) -> str | None:
        return self._current_character

    # --- 公開API ---
    def play_async(self, voice_name: str, lip_ms: int | None = None) -> threading.Thread:
        """
        voice_name: 拡張子なし/あり（.wav）どちらでもOK
        """
        th = threading.Thread(
            target=self._play_sync_worker,
            args=(voice_name, lip_ms),
            name=f"VoiceService:{voice_name}",
            daemon=True,
        )
        th.start()
        return th

    def play_async_random(self, voice_name: str, min_num: int, max_num: int, lip_ms: int | None = None) -> threading.Thread:
        """
        voice_name: 拡張子なし/あり（.wav）どちらでもOK
        """
        num = random.randint(min_num, max_num)
        if not voice_name.lower().endswith(".wav"):
            voice_name = f"{voice_name}{num}.wav"
        else:
            voice_name = f"{voice_name[:-4]}{num}.wav"
        th = threading.Thread(
            target=self._play_sync_worker,
            args=(voice_name, lip_ms),
            name=f"VoiceService:{voice_name}",
            daemon=True,
        )
        th.start()
        return th

    # --- 内部 ---
    def _resolve(self, character: str, voice_name: str) -> str | None:
        base = os.path.join(self._assets_root, character)
        if not os.path.isdir(base): return None
        stem, ext = os.path.splitext(voice_name)
        cand = os.path.join(base, voice_name) if ext.lower() == ".wav" else os.path.join(base, stem + ".wav")
        return cand if os.path.isfile(cand) else None

    def _play_sync_worker(self, voice_name: str, lip_ms: int | None):
        char = self._current_character
        if not char:
            return
        path = self._resolve(char, voice_name)
        if not path:
            return

        lip_dur = int(lip_ms if lip_ms is not None else self._default_lip_ms)

        try:
            self._controller.lip(lip_dur)
            # 音量加工
            sound = AudioSegment.from_wav(path)
            volume_change = (self.voice_volume or 100) - 100  # 100基準
            sound = sound + volume_change
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sound.export(tmp.name, format="wav")
                tmp_path = tmp.name
            winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
            os.remove(tmp_path)
        except Exception:
            traceback.print_exc()
        finally:
            try:
                self._controller.lip_stop()
            except Exception:
                traceback.print_exc()

    def _read_voice_volume(self) -> int:
        """ConfigData から voice_volume を読み直す（不正値は 100 にフォールバック）"""
        try:
            v = self._config.get("voice_volume")
            return int(v) if v is not None else 100
        except Exception:
            return 100

    def _on_config_changed(self, *_args, **_kwargs):
        """
        ペイロードには依存せず、常に ConfigData から読み直す
        """
        old = getattr(self, "voice_volume", None)
        self.voice_volume = self._read_voice_volume()
        if old != self.voice_volume:
            print(f"VoiceService: voice_volume updated -> {self.voice_volume}")
