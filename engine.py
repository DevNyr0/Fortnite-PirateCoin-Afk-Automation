import os
import sys
import time
import random
import ctypes
import threading
import cv2
import mss
import numpy as np
import pydirectinput
import win32gui
import win32con
from PIL import Image, ImageTk
import tkinter as tk

GAME_CLASS = "UnrealWindow"
GAME_TITLE = "fortnite"

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def get_images_dir():
    return os.path.join(get_base_dir(), "images")

def load_cv_image(path):
    if not os.path.exists(path):
        return None
    try:
        data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None

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

def capture_screen(monitor_index=1):
    try:
        with mss.mss() as sct:
            idx = min(monitor_index, len(sct.monitors) - 1)
            mon = sct.monitors[idx]
            raw = np.array(sct.grab(mon))
            bgr = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
            return bgr, mon["left"], mon["top"], mon["width"], mon["height"]
    except Exception:
        try:
            from PIL import ImageGrab
            shot = ImageGrab.grab()
            raw = np.array(shot)
            bgr = cv2.cvtColor(raw, cv2.COLOR_RGB2BGR)
            return bgr, 0, 0, bgr.shape[1], bgr.shape[0]
        except Exception:
            return None, 0, 0, 1920, 1080

def match_template(frame, template, threshold=0.78, roi=None, fw=None):
    if frame is None or template is None:
        return None, 0.0
    gf = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    gt = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if template.ndim == 3 else template
    ox, oy = 0, 0
    if roi:
        y0, y1, x0, x1 = roi
        y0 = max(0, min(y0, gf.shape[0]))
        y1 = max(y0, min(y1, gf.shape[0]))
        x0 = max(0, min(x0, gf.shape[1]))
        x1 = max(x0, min(x1, gf.shape[1]))
        if (y1 - y0) < 10 or (x1 - x0) < 10:
            return None, 0.0
        gf = gf[y0:y1, x0:x1]
        ox, oy = x0, y0
    ref_w = fw if fw is not None else gf.shape[1]
    base_scale = max(0.4, min(1.5, ref_w / 1920.0))
    scales = (
        round(base_scale * 0.82, 3),
        round(base_scale * 0.91, 3),
        round(base_scale * 1.00, 3),
        round(base_scale * 1.09, 3),
        round(base_scale * 1.18, 3)
    )
    best_score = -1.0
    best_loc = None
    best_wh = None
    for sc in scales:
        th = int(gt.shape[0] * sc)
        tw = int(gt.shape[1] * sc)
        if th < 6 or tw < 6 or th >= gf.shape[0] or tw >= gf.shape[1]:
            continue
        interp = cv2.INTER_AREA if sc < 1.0 else cv2.INTER_LINEAR
        resized = cv2.resize(gt, (tw, th), interpolation=interp)
        res = cv2.matchTemplate(gf, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_score:
            best_score = max_val
            best_loc = max_loc
            best_wh = (tw, th)
    if best_score >= threshold and best_loc and best_wh:
        cx = ox + best_loc[0] + best_wh[0] // 2
        cy = oy + best_loc[1] + best_wh[1] // 2
        return (cx, cy), float(best_score)
    return None, float(max(0.0, best_score))

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

class SnipTool:
    def __init__(self, on_complete=None):
        self.on_complete = on_complete
        self.root = None
        self.canvas = None
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.rect_id = None
        self.screenshot = None

    def start(self):
        frame, ox, oy, w, h = capture_screen(1)
        if frame is None:
            if self.on_complete:
                self.on_complete(False, "Screen capture unavailable")
            return
        self.screenshot = frame
        self.ox = ox
        self.oy = oy

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0.35)
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{w}x{h}+{ox}+{oy}")
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Escape>", lambda e: self.root.destroy())

        self.root.mainloop()

    def on_press(self, event):
        self.x0 = event.x
        self.y0 = event.y
        self.rect_id = self.canvas.create_rectangle(self.x0, self.y0, self.x0, self.y0, outline="#00ffcc", width=2)

    def on_drag(self, event):
        self.x1 = event.x
        self.y1 = event.y
        self.canvas.coords(self.rect_id, self.x0, self.y0, self.x1, self.y1)

    def on_release(self, event):
        self.x1 = event.x
        self.y1 = event.y
        self.root.destroy()
        min_x = max(0, min(self.x0, self.x1))
        max_x = min(self.screenshot.shape[1], max(self.x0, self.x1))
        min_y = max(0, min(self.y0, self.y1))
        max_y = min(self.screenshot.shape[0], max(self.y0, self.y1))
        if max_x - min_x > 15 and max_y - min_y > 15:
            cropped = self.screenshot[min_y:max_y, min_x:max_x]
            save_path = os.path.join(get_images_dir(), "custom_button.png")
            _, buf = cv2.imencode(".png", cropped)
            with open(save_path, "wb") as f:
                f.write(buf)
            if self.on_complete:
                self.on_complete(True, save_path)
        else:
            if self.on_complete:
                self.on_complete(False, "Selection too small")
