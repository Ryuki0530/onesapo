# winenum.py
"""
Win32 のトップレベルウィンドウ列挙＆操作を提供する純ロジック層。
外部ライブラリは使わず ctypes のみで実装。

推奨の使い方（ui_main などから）:
    service = WinEnumService()
    items = service.enumerate(include_empty=False, all_styles=False, include_exe=False)
    # items は WindowModel.replace(items) にそのまま渡せる想定の list[WindowInfo]

必要に応じて、ダブルクリック等で:
    service.activate(hwnd)

Copyright: Public Domain
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import ctypes
from ctypes import wintypes


# =========================
# Dataclass for UI binding
# =========================

@dataclass(frozen=True)
class WindowInfo:
    """列挙結果 1 件分の情報."""
    hwnd: int
    title: str
    pid: int
    class_name: str
    is_foreground: bool
    exe_path: Optional[str] = None  # include_exe=True のときのみ解決


# =========================
# Win32 API setup (ctypes)
# =========================

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_psapi = ctypes.WinDLL("psapi", use_last_error=True)

# 基本ウィンドウ列挙
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL

_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL

_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL

_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.GetWindowTextLengthW.restype = ctypes.c_int

_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int

_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetClassNameW.restype = ctypes.c_int

_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD

_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND

_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL

_user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindowAsync.restype = wintypes.BOOL

# プロセス系
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE

_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL

# QueryFullProcessImageNameW (推奨)
try:
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    _kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    _HAS_QFPI = True
except AttributeError:
    _HAS_QFPI = False

# GetModuleFileNameExW (フォールバック)
_psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD]
_psapi.GetModuleFileNameExW.restype = wintypes.DWORD

# 定数
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000  # Vista 以降
SW_RESTORE = 9
MAX_PATH_FRIENDLY = 32768  # 長いパス対策


# =========================
# Service implementation
# =========================

class WinEnumService:
    """
    Windows のトップレベルウィンドウを列挙・操作するサービス。
    Qt に依存しない純ロジック。UIスレッドから同期呼び出しして OK。
    """

    def enumerate(
        self,
        include_empty: bool = False,
        all_styles: bool = False,
        include_exe: bool = False,
    ) -> List[WindowInfo]:
        """
        トップレベルウィンドウを列挙して WindowInfo のリストを返す。

        :param include_empty: タイトルが空のウィンドウも含める。
        :param all_styles: 可視判定を無視（IsWindowVisible を無視して全列挙）。
        :param include_exe: 実行ファイルパスを解決して含める（やや重い）。
        """
        hwnd_list: list[int] = []

        @WNDENUMPROC
        def _cb(hwnd: int, lparam: int) -> bool:
            # トップレベルのみ（EnumWindows は基本トップレベル）
            if not _user32.IsWindow(hwnd):
                return True  # continue
            if not all_styles and not _user32.IsWindowVisible(hwnd):
                return True  # continue
            hwnd_list.append(hwnd)
            return True

        # 列挙
        if not _user32.EnumWindows(_cb, 0):
            # 失敗時でも空リスト返す（落とさない）
            return []

        # フォアグラウンド判定用
        fg_hwnd = _user32.GetForegroundWindow()

        items: list[WindowInfo] = []
        for hwnd in hwnd_list:
            try:
                title = self._get_window_text(hwnd)
                if not include_empty:
                    # GetWindowTextLengthW が 0 でも、稀にアイコン名等で値が返るケースに備え実測で判定
                    if len(title.strip()) == 0:
                        continue

                class_name = self._get_class_name(hwnd)
                pid = self._get_pid(hwnd)
                is_fg = (hwnd == fg_hwnd)

                exe_path: Optional[str] = None
                if include_exe and pid:
                    exe_path = self._get_exe_path(pid) or None

                items.append(
                    WindowInfo(
                        hwnd=int(hwnd),
                        title=title,
                        pid=int(pid),
                        class_name=class_name,
                        is_foreground=bool(is_fg),
                        exe_path=exe_path,
                    )
                )
            except Exception:
                # 個別ウィンドウで失敗しても全体は続行
                continue

        return items

    def activate(self, hwnd: int) -> bool:
        """
        指定ウィンドウを前面に出す試行。成功すれば True。
        OS のフォアグラウンド制御ポリシで失敗することがある点に注意。

        実装:
          - 最小化されていれば ShowWindowAsync(hwnd, SW_RESTORE)
          - SetForegroundWindow(hwnd)
        """
        h = wintypes.HWND(hwnd)
        if not _user32.IsWindow(h):
            return False
        # まずリストア（最小化対策）
        _user32.ShowWindowAsync(h, SW_RESTORE)
        ok = _user32.SetForegroundWindow(h)
        return bool(ok)

    # -------------------------
    # Internal helper methods
    # -------------------------

    @staticmethod
    def _get_window_text(hwnd: int) -> str:
        length = _user32.GetWindowTextLengthW(hwnd)
        # 長さ 0 の場合も、念のため 1 文字バッファで呼んで再確認
        buf = ctypes.create_unicode_buffer(max(1, length + 1))
        _user32.GetWindowTextW(hwnd, buf, len(buf))
        return buf.value

    @staticmethod
    def _get_class_name(hwnd: int) -> str:
        buf = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(hwnd, buf, len(buf))
        return buf.value

    @staticmethod
    def _get_pid(hwnd: int) -> int:
        pid = wintypes.DWORD(0)
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value)

    @staticmethod
    def _get_exe_path(pid: int) -> str:
        """
        プロセスの実行ファイルフルパスを取得。
        まず QueryFullProcessImageNameW、なければ GetModuleFileNameExW を試す。
        取得失敗時は空文字。
        """
        handle = wintypes.HANDLE(0)
        try:
            access = PROCESS_QUERY_LIMITED_INFORMATION
            handle = _kernel32.OpenProcess(access, False, pid)
            if not handle:
                # 古い環境向けに権限広めで再試行
                access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
                handle = _kernel32.OpenProcess(access, False, pid)
            if not handle:
                return ""

            # まずは QFPI を試す
            if _HAS_QFPI:
                size = wintypes.DWORD(MAX_PATH_FRIENDLY)
                buf = ctypes.create_unicode_buffer(size.value)
                ok = _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
                if ok:
                    # size は実際の文字数（終端含まず）
                    return buf.value

            # フォールバック: GetModuleFileNameExW（psapi）
            buf2 = ctypes.create_unicode_buffer(MAX_PATH_FRIENDLY)
            got = _psapi.GetModuleFileNameExW(handle, None, buf2, MAX_PATH_FRIENDLY)
            if got:
                return buf2.value

            return ""
        except Exception:
            return ""
        finally:
            if handle:
                _kernel32.CloseHandle(handle)


__all__ = ["WinEnumService", "WindowInfo"]
