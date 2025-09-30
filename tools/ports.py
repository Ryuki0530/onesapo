# tools/ports.py
import socket
import time
import contextlib

def is_port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    """
    そのポートに「誰かがLISTENしているか」を確認（クライアント接続の試行で判断）
    True: 接続成功＝誰かが開けている / False: 接続不可＝誰もいない or FWなどで拒否
    """
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0

def find_free_port(start: int = 5000, tries: int = 200, host: str = "127.0.0.1") -> int:
    """
    指定開始番号から「bindできる=未使用」なポートを探して返す。
    ※ bindしてすぐcloseするので、理論上レースは残るがハッカソン用途では十分実用。
    """
    for p in range(start, start + max(1, tries)):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            # Windowsでの挙動安定のためREUSEはオフのまま
            try:
                s.bind((host, p))
            except OSError:
                continue
        return p
    raise RuntimeError(f"No free port found in [{start}, {start+tries-1}]")

def wait_for_port(host: str, port: int, timeout: float = 5.0, poll_interval: float = 0.1) -> bool:
    """
    指定ポートで“LISTENが立つ”のを待つ。Unity起動直後の準備待ちに使える。
    True: 開いた / False: タイムアウト
    """
    deadline = time.time() + max(0.0, timeout)
    while time.time() < deadline:
        if is_port_open(host, port, timeout=poll_interval):
            return True
        time.sleep(poll_interval)
    return False

if __name__ == "__main__":
    # 便利CLI: python -m tools.ports 127.0.0.1 5000
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    print(f"{host}:{port} -> {'OPEN' if is_port_open(host, port) else 'CLOSED'}")
