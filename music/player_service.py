import pygame
from pathlib import Path
from tinytag import TinyTag
import time


class PlayerService:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.playlist = []
        self.current_index = 0
        self.volume = 0.5
        self._loaded = False
        self._length = 0
        self.track_finished = False
        # position tracking helpers
        self._base_pos_ms = 0  # seek origin (start offset inside track)
        self._is_paused = False
        self._current_path = None
        self._meta = {"title": None, "artist": None, "album": None}

        # 自動で次曲に行く処理のためにエンドイベントを設定
        self.MUSIC_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END)

    def load(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(self.volume)
        self._loaded = True
        print(f"Loaded: {path}")
        # length & metadata via TinyTag
        self._current_path = path
        self._length = 0
        self._meta = {"title": None, "artist": None, "album": None}
        tag = None
        try:
            tag = TinyTag.get(str(path))
        except Exception as exc:
            print(f"TinyTag metadata read failed: {exc}")
            tag = None

        if tag and tag.duration:
            try:
                self._length = int(float(tag.duration) * 1000)
            except Exception:
                self._length = 0

        if tag:
            self._meta = {
                "title": getattr(tag, "title", None) or None,
                "artist": getattr(tag, "artist", None) or None,
                "album": getattr(tag, "album", None) or None,
            }
        # fallback title
        if not self._meta.get("title"):
            self._meta["title"] = path.stem
        self._base_pos_ms = 0
        self._is_paused = False

    def load_playlist(self, paths: list[Path]):
        self.playlist = paths
        self.current_index = 0
        if self.playlist:
            self.load(self.playlist[0])

    def play(self):
        if not self._loaded:
            print("No track loaded.")
            return
        # 既に一時停止中なら再開
        if self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            print("Resumed")
            return
        
        if self.playlist and self.current_index < len(self.playlist):
            track_path = str(self.playlist[self.current_index])
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            self.track_finished = False

        # 新規再生（現在のベース位置から）
        if self._base_pos_ms > 0:
            pygame.mixer.music.play(start=self._base_pos_ms / 1000.0)
        else:
            pygame.mixer.music.play()
        print("Playback started")

    def pause(self):
        if not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            print("Paused")

    def unpause(self):
        if self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            print("Resumed")

    def stop(self):
        pygame.mixer.music.stop()
        print("Stopped")
        self._is_paused = False
        self._base_pos_ms = 0

    def get_length(self):
        """曲の長さを ms 単位で返す"""
        return self._length

    def get_position(self):
        # get_pos returns ms since last play()/play(start=..) or unpause
        delta = pygame.mixer.music.get_pos()
        if delta < 0:
            delta = 0
        pos = self._base_pos_ms + delta
        if pos > self._length:
            pos = self._length
        return pos

    def set_position(self, milliseconds: int):
        milliseconds = max(0, min(self._length, int(milliseconds)))
        self._base_pos_ms = milliseconds
        self._is_paused = False
        pygame.mixer.music.play(start=milliseconds / 1000.0)
        print(f"Seeked to {milliseconds} ms")

    def get_volume(self):
        return self.volume

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        print(f"Volume set to {self.volume * 100:.0f}%")

    def is_playing(self):
        return pygame.mixer.music.get_busy()

    def get_metadata(self) -> dict:
        """現在のトラックのメタデータ（title, artist, album）を返す"""
        return dict(self._meta)

    def get_current_path(self) -> Path | None:
        return self._current_path

    def next_track(self):
        self.current_index += 1
        if self.current_index >= len(self.playlist):
            print("End of playlist. Reset to first track and stop.")
            # reset to first track and load it (do not auto play)
            self.current_index = 0
            if self.playlist:
                self.load(self.playlist[0])
            self.play()
            return
        self.load(self.playlist[self.current_index])
        self.play()

    def prev_track(self):
        """前のトラックへ。現在位置が3秒より進んでいれば同じトラックの頭へ。"""
        current_pos = self.get_position()
        if current_pos > 3000:  # 3秒以上進んでいれば頭出しのみ
            self.set_position(0)
            return
        if self.current_index <= 0:
            # 先頭でさらに前 => 先頭頭出し
            self.set_position(0)
            return
        self.current_index -= 1
        self.load(self.playlist[self.current_index])
        self.play()

    def play_track(self, index: int):
        """
        指定インデックスのトラックに切り替えて再生する
        """
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.load(self.playlist[index])
            self.play()
            print(f"Switched to track {index + 1}: {self.playlist[index].name}")
        else:
            print(f"Invalid track index: {index}")


    def update(self):
        """pygameイベントを処理して、自動で次の曲へ移動"""
        for event in pygame.event.get():
            if event.type == self.MUSIC_END:
                self.next_track()

    


# =========================
# テスト用コード（コマンド操作）
# =========================
if __name__ == "__main__":
    import sys

    player = PlayerService()

    # あなたの環境に合わせて変更してください
    base = Path(__file__).parent.parent.parent / "bgm" 
    playlist = sorted(base.glob("*.mp3" ))  # .mp3 も可（pygameで再生できるもの）

    if not playlist:
        print("No music files found.")
        sys.exit(1)

    player.load_playlist(playlist)
    player.play()

    print("\n--- COMMANDS ---")
    print("  p : pause")
    print("  r : resume")
    print("  s : stop")
    print("  v : set volume (0.0 - 1.0)")
    print("  t : seek to position (ms)")
    print("  i : info (position/volume)")
    print("  n : next track")
    print("  j : jump to track index")
    print("  q : quit")
    print("----------------\n")

    while True:
        player.update()  # 自動で次へ行くか監視

        try:
            cmd = input("Enter command: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == "p":
            player.pause()
        elif cmd == "r":
            player.unpause()
        elif cmd == "s":
            player.stop()
        elif cmd == "v":
            vol = float(input("Volume (0.0 - 1.0): "))
            player.set_volume(vol)
        elif cmd == "t":
            ms = int(input("Seek to (ms): "))
            player.set_position(ms)
        elif cmd == "i":
            player.get_position()
            print(f"Volume: {player.get_volume() * 100:.0f}%")
        elif cmd == "n":
            player.next_track()
        elif cmd == "j":
            idx = int(input(f"Track index (0 - {len(playlist)-1}): "))
            player.play_track(idx)
        elif cmd == "q":
            player.stop()
            break
        else:
            print("Unknown command.")
        
        time.sleep(0.1)
