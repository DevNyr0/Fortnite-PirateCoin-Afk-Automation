import time
import random
import ctypes
import pydirectinput
import win32gui
import win32con
from core.config import GAME_CLASS, GAME_TITLE

_cached_hwnd = None

def _is_game_window(h):
    if not h or not win32gui.IsWindow(h) or not win32gui.IsWindowVisible(h):
        return False
    t = win32gui.GetWindowText(h).lower()
    c = win32gui.GetClassName(h)
    return GAME_TITLE in t or c == GAME_CLASS

def find_fortnite_hwnd():
    global _cached_hwnd
    try:
        if _is_game_window(_cached_hwnd):
            return _cached_hwnd
    except Exception:
        _cached_hwnd = None

    results = []
    def enum_cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h).lower()
            c = win32gui.GetClassName(h)
            if GAME_TITLE in t or c == GAME_CLASS:
                results.append(h)
                return False
        return True
    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception:
        pass
    _cached_hwnd = results[0] if results else None
    return _cached_hwnd

def ensure_fortnite_foreground():
    h = find_fortnite_hwnd()
    if not h or win32gui.IsIconic(h):
        return False
    fg = win32gui.GetForegroundWindow()
    if fg == h:
        return True
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        cur_tid = kernel32.GetCurrentThreadId()
        fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
        attached = False
        if fg_tid and fg_tid != cur_tid:
            attached = bool(user32.AttachThreadInput(cur_tid, fg_tid, True))
        try:
            win32gui.ShowWindow(h, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(h)
            time.sleep(0.12)
        finally:
            if attached:
                user32.AttachThreadInput(cur_tid, fg_tid, False)
        return win32gui.GetForegroundWindow() == h
    except Exception:
        return False

def safe_click(x, y, jitter=4):
    ensure_fortnite_foreground()
    pydirectinput.FAILSAFE = False
    pydirectinput.PAUSE = 0.0
    jx = int(x + random.randint(-jitter, jitter))
    jy = int(y + random.randint(-jitter, jitter))
    try:
        pydirectinput.moveTo(jx, jy)
        time.sleep(random.uniform(0.08, 0.12))
        pydirectinput.mouseDown(button="left")
        time.sleep(random.uniform(0.12, 0.18))
        pydirectinput.mouseUp(button="left")
        time.sleep(0.15)
        pydirectinput.mouseDown(button="left")
        time.sleep(random.uniform(0.08, 0.14))
        pydirectinput.mouseUp(button="left")
    except Exception:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(jx, jy)
        time.sleep(0.08)
        pyautogui.click()

def press_key(key):
    ensure_fortnite_foreground()
    pydirectinput.FAILSAFE = False
    pydirectinput.PAUSE = 0.0
    try:
        pydirectinput.keyDown(key)
        time.sleep(random.uniform(0.06, 0.12))
    finally:
        try:
            pydirectinput.keyUp(key)
        except Exception:
            pass

def press_w_space():
    ensure_fortnite_foreground()
    pydirectinput.FAILSAFE = False
    pydirectinput.PAUSE = 0.0
    try:
        try:
            pydirectinput.keyDown("w")
            time.sleep(random.uniform(0.08, 0.12))
            pydirectinput.keyDown("space")
            time.sleep(random.uniform(0.14, 0.18))
        finally:
            try:
                pydirectinput.keyUp("space")
            except Exception:
                pass
            time.sleep(random.uniform(0.22, 0.32))
            try:
                pydirectinput.keyUp("w")
            except Exception:
                pass
    except Exception:
        import pyautogui
        pyautogui.FAILSAFE = False
        try:
            pyautogui.keyDown("w")
            time.sleep(0.08)
            pyautogui.keyDown("space")
            time.sleep(0.15)
        finally:
            try:
                pyautogui.keyUp("space")
            except Exception:
                pass
            time.sleep(0.25)
            try:
                pyautogui.keyUp("w")
            except Exception:
                pass

