import time
import random
import ctypes
import pydirectinput
import win32gui
import win32con
from core.config import GAME_CLASS, GAME_TITLE

def find_fortnite_hwnd():
    results = []
    def enum_cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h).lower()
            c = win32gui.GetClassName(h)
            if GAME_TITLE in t or c == GAME_CLASS:
                results.append(h)
        return True
    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception:
        pass
    return results[0] if results else None

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
        pyautogui.moveTo(jx, jy)
        time.sleep(0.08)
        pyautogui.click()

def press_key(key):
    ensure_fortnite_foreground()
    pydirectinput.FAILSAFE = False
    pydirectinput.PAUSE = 0.0
    pydirectinput.keyDown(key)
    time.sleep(random.uniform(0.06, 0.12))
    pydirectinput.keyUp(key)

def press_w_space():
    ensure_fortnite_foreground()
    pydirectinput.FAILSAFE = False
    pydirectinput.PAUSE = 0.0
    try:
        pydirectinput.keyDown("w")
        time.sleep(random.uniform(0.08, 0.12))
        pydirectinput.keyDown("space")
        time.sleep(random.uniform(0.14, 0.18))
        pydirectinput.keyUp("space")
        time.sleep(random.uniform(0.22, 0.32))
        pydirectinput.keyUp("w")
    except Exception:
        import pyautogui
        pyautogui.keyDown("w")
        time.sleep(0.08)
        pyautogui.keyDown("space")
        time.sleep(0.15)
        pyautogui.keyUp("space")
        time.sleep(0.25)
        pyautogui.keyUp("w")

