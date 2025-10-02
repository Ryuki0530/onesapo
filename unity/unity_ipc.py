# unity_ipc.py
import socket
import os
import subprocess

class UnityIPC:
    """Unityへ1コマンド=1TCP接続で送る"""
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, timeout: float = 2.0, unity_boot: bool = False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._proc = None
        if unity_boot:
            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TRY_IPC.exe")
            if not os.path.exists(exe_path):
                raise FileNotFoundError(f"{exe_path} が見つかりません")
            self._proc = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def close(self):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def _send(self, cmd: str) -> None:
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.sendall((cmd.strip() + "\n").encode("utf-8"))
        except OSError as e:
            # ここで例外を飲み込んでログに回す（UIを止めない）
            raise RuntimeError(f"UnityIPC送信失敗: {e}")

    # --- 公開API ---
    #todo: Unity変更次第、コメントアウト部は解除
    #表情
    def smile(self, ms: int = 1000):   self._send(f"SMILE {ms}")
    def kanashi(self, ms: int = 1000): self._send(f"KANASHI {ms}")
    def oko(self, ms: int = 1000):     self._send(f"OKO {ms}")
    def tere(self, ms: int = 1000):    self._send(f"TERE {ms}")

    #体のアニメーション
    def gattu(self, ms: int = 1000):    self._send(f"GATTU {ms}")
    def ude_gattu(self, ms: int = 1000): self._send(f"UDE_GATTU {ms}")
    def yubifuri(self, ms: int = 1000):  self._send(f"YUBIFURI {ms}")

    # def idleA(self, ms: int = 1000):   self._send(f"IDLE_A {ms}")
    # def idleB(self, ms: int = 1000):   self._send(f"IDLE_B {ms}")
    
    def lip(self, ms: int = 1000):     self._send(f"LIP {ms}")
    def lip_stop(self):                self._send("LIP STOP")


    def send_raw(self, raw: str):      self._send(raw)

    def change_character(self, chara_name: str): self._send(f"CHANGE_CHARACTER {chara_name}")
    