import os
import sys
import time
import socket
import threading
import cv2
import keyboard
import eel
import eel.browsers

from core.config import HOTKEY, get_base_dir
from core.state import state, add_log, broadcast_state
from core.vision import capture_screen, match_template, load_all_templates
from core.snip import SnipTool
from core.worker import worker_loop, w_space_worker

@eel.expose
def start_macro():
    if state.running:
        return {"status": "already_running"}
    state.running = True
    state.stop_event.clear()
    if state.start_time is None:
        state.start_time = time.time()
    state.worker_thread = threading.Thread(target=worker_loop, daemon=True)
    state.worker_thread.start()
    state.w_space_thread = threading.Thread(target=w_space_worker, daemon=True)
    state.w_space_thread.start()
    broadcast_state()
    return {"status": "started"}

@eel.expose
def stop_macro():
    if not state.running:
        return {"status": "not_running"}
    state.running = False
    state.stop_event.set()
    state.status = "IDLE"
    broadcast_state()
    return {"status": "stopped"}

@eel.expose
def toggle_macro():
    if state.running:
        return stop_macro()
    return start_macro()

@eel.expose
def get_initial_data():
    uptime = 0
    if state.running and state.start_time:
        uptime = int(time.time() - state.start_time)
    match_dur = 0
    if state.running and state.match_start_time:
        match_dur = int(time.time() - state.match_start_time)
    return {
        "running": state.running,
        "status": state.status,
        "matches": state.matches,
        "access_found": state.access_found,
        "uptime": uptime,
        "match_duration": match_dur,
        "check_interval": state.check_interval,
        "confidence": state.confidence,
        "anti_afk": state.anti_afk,
        "w_space": state.w_space,
        "logs": state.logs
    }

@eel.expose
def update_settings(interval, conf, afk, w_space=False):
    try:
        state.check_interval = max(0.5, float(interval))
        state.confidence = min(0.99, max(0.50, float(conf)))
        state.anti_afk = bool(afk)
        state.w_space = bool(w_space)
        add_log(f"Settings saved: Interval={state.check_interval}s, Confidence={state.confidence}, Anti-AFK={state.anti_afk}, W+Space (3s)={state.w_space}", "info")
        broadcast_state()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@eel.expose
def test_screen_detection():
    templates = load_all_templates()
    frame, ox, oy, fw, fh = capture_screen(1)
    if frame is None:
        add_log("Test match scan: Screen capture unavailable", "warn")
        return {"status": "error", "details": []}
    gf = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    results = []
    for grp, list_tpl in templates.items():
        for name, tpl in list_tpl:
            pos, score = match_template(gf, tpl, threshold=state.confidence, fw=fw)
            if pos:
                results.append(f"{name}: FOUND at ({pos[0]}, {pos[1]}) score={score:.2f}")
    if results:
        res_str = " | ".join(results)
        add_log(f"Test match scan: {res_str}", "success")
        return {"status": "found", "details": results}
    add_log("Test match scan: No matching buttons found on current screen", "warn")
    return {"status": "not_found", "details": []}

@eel.expose
def trigger_snip():
    def on_done(success, info):
        if success:
            add_log("Custom Play Again button captured and saved successfully!", "success")
        else:
            add_log(f"Snip cancelled or invalid: {info}", "warn")
    threading.Thread(target=lambda: SnipTool(on_done).start(), daemon=True).start()
    return {"status": "initiated"}

@eel.expose
def clear_logs():
    state.logs.clear()
    return {"status": "ok"}

@eel.expose
def reset_counters():
    state.matches = 0
    state.access_found = 0
    state.start_time = time.time() if state.running else None
    state.match_start_time = time.time() if state.running else None
    add_log("Session statistics reset.", "info")
    broadcast_state()
    return {"status": "ok"}

def setup_hotkeys():
    def on_hotkey():
        toggle_macro()
    try:
        keyboard.add_hotkey(HOTKEY, on_hotkey)
    except Exception:
        pass

def get_free_port():
    for p in (28540, 28541, 28542, 28543):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except Exception:
            pass
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p

def find_browser():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for p in edge_paths:
        if os.path.exists(p):
            eel.browsers.set_path("edge", p)
            return "edge"
    for p in chrome_paths:
        if os.path.exists(p):
            eel.browsers.set_path("chrome", p)
            return "chrome"
    return "default"

def run_app():
    setup_hotkeys()
    web_dir = os.path.join(get_base_dir(), "web")
    eel.init(web_dir)
    browser = find_browser()
    port = get_free_port()
    try:
        eel.start(
            "index.html",
            mode=browser,
            host="127.0.0.1",
            port=port,
            size=(980, 720)
        )
    except (SystemExit, MemoryError, KeyboardInterrupt):
        state.stop_event.set()
        return 0
    except Exception:
        try:
            port = get_free_port()
            eel.start("index.html", mode="default", host="127.0.0.1", port=port, size=(980, 720))
        except Exception:
            state.stop_event.set()
            return 1
    return 0

