import os
import sys
import time
import socket
import threading
import traceback
import keyboard
import eel
import eel.browsers

from core.config import HOTKEY, get_base_dir
from core.state import state, add_log, broadcast_state, ui_pump, write_file_log
from core.vision import capture_screen, match_template, load_all_templates
from core.snip import SnipTool
from core.worker import worker_loop, w_space_worker

_last_hotkey_time = 0.0

@eel.expose
def ping():
    return "ok"

@eel.expose
def start_macro():
    try:
        with state.lock:
            if state.running:
                return {"status": "already_running"}
            for t in (state.worker_thread, state.w_space_thread):
                if t is not None and t.is_alive():
                    state.stop_event.set()
                    t.join(timeout=2.0)
            state.running = True
            state.stop_event.clear()
            if state.start_time is None:
                state.start_time = time.time()
            state.worker_thread = threading.Thread(target=worker_loop, daemon=True)
            state.worker_thread.start()
            state.w_space_thread = threading.Thread(target=w_space_worker, daemon=True)
            state.w_space_thread.start()
        broadcast_state(force=True)
        return {"status": "started"}
    except Exception as e:
        write_file_log(f"start_macro error: {e}")
        return {"status": "error", "message": str(e)}

@eel.expose
def stop_macro():
    try:
        with state.lock:
            if not state.running:
                return {"status": "not_running"}
            state.running = False
            state.stop_event.set()
            state.status = "IDLE"
        broadcast_state(force=True)
        return {"status": "stopped"}
    except Exception as e:
        write_file_log(f"stop_macro error: {e}")
        return {"status": "error", "message": str(e)}

@eel.expose
def toggle_macro():
    try:
        if state.running:
            return stop_macro()
        return start_macro()
    except Exception as e:
        write_file_log(f"toggle_macro error: {e}")
        return {"status": "error", "message": str(e)}

@eel.expose
def get_initial_data():
    uptime = 0
    if state.running and state.start_time:
        uptime = int(time.time() - state.start_time)
    match_dur = 0
    if state.running and state.match_start_time:
        match_dur = int(time.time() - state.match_start_time)
    with state.lock:
        logs_copy = list(state.logs)
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
        "logs": logs_copy
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
    gf, ox, oy, fw, fh = capture_screen(1, as_gray=True)
    if gf is None:
        add_log("Test match scan: Screen capture unavailable", "warn")
        return {"status": "error", "details": []}
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
    with state.lock:
        state.logs.clear()
    return {"status": "ok"}

@eel.expose
def reset_counters():
    state.matches = 0
    state.access_found = 0
    state.start_time = time.time() if state.running else None
    state.match_start_time = time.time() if state.running else None
    add_log("Session statistics reset.", "info")
    broadcast_state(force=True)
    return {"status": "ok"}

def setup_hotkeys():
    def on_hotkey():
        global _last_hotkey_time
        now = time.time()
        if now - _last_hotkey_time < 0.35:
            return
        _last_hotkey_time = now
        threading.Thread(target=toggle_macro, daemon=True).start()
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

def _install_crash_hooks():
    def _sys_hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            return
        write_file_log("UNHANDLED SYS EXCEPTION:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

    def _thread_hook(args):
        write_file_log(
            f"UNHANDLED THREAD EXCEPTION ({args.thread.name}):\n"
            + "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        )

    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook

def _on_ws_close(page, remaining_sockets):
    write_file_log(f"WebSocket closed on '{page}' (remaining={len(remaining_sockets)}, running={state.running})")

def run_app():
    _install_crash_hooks()
    write_file_log("Application started.")
    setup_hotkeys()
    web_dir = os.path.join(get_base_dir(), "web")
    eel.init(web_dir)
    eel.spawn(ui_pump)
    browser = find_browser()
    port = get_free_port()
    cmdline_args = ["--disable-http-cache"]
    if browser in ("edge", "chrome"):
        cmdline_args.extend([
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows"
        ])
    try:
        eel.start(
            "index.html",
            mode=browser,
            host="127.0.0.1",
            port=port,
            cmdline_args=cmdline_args,
            shutdown_delay=5.0,
            close_callback=_on_ws_close,
            size=(980, 720)
        )
    except (SystemExit, MemoryError, KeyboardInterrupt) as e:
        write_file_log(f"App exited via {type(e).__name__}: {e} (running={state.running})")
        state.stop_event.set()
        return 0
    except Exception as e:
        write_file_log(f"Primary eel.start failed: {e}\n{traceback.format_exc()}")
        try:
            port = get_free_port()
            eel.start(
                "index.html",
                mode="default",
                host="127.0.0.1",
                port=port,
                shutdown_delay=5.0,
                close_callback=_on_ws_close,
                size=(980, 720)
            )
        except Exception as e2:
            write_file_log(f"Fallback eel.start failed: {e2}\n{traceback.format_exc()}")
            state.stop_event.set()
            return 1
    write_file_log("App exited normally.")
    return 0

