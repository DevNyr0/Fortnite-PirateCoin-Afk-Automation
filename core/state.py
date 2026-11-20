import os
import time
import threading
from collections import deque
import eel
from core.config import DEFAULT_CHECK_INTERVAL, DEFAULT_CONFIDENCE, DEFAULT_AFK_INTERVAL, get_base_dir

_MAX_LOGS = 200
_HEARTBEAT_INTERVAL = 30.0
_MAX_LOG_BYTES = 512 * 1024

def write_file_log(msg):
    try:
        log_path = os.path.join(get_base_dir(), "macro.log")
        if os.path.exists(log_path) and os.path.getsize(log_path) > _MAX_LOG_BYTES:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                tail = f.readlines()[-500:]
            with open(log_path, "w", encoding="utf-8") as f:
                f.writelines(tail)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

class MacroState:
    def __init__(self):
        self.running = False
        self.status = "IDLE"
        self.matches = 0
        self.access_found = 0
        self.start_time = None
        self.match_start_time = None
        self.logs = []
        self.check_interval = DEFAULT_CHECK_INTERVAL
        self.confidence = DEFAULT_CONFIDENCE
        self.anti_afk = True
        self.afk_interval = DEFAULT_AFK_INTERVAL
        self.w_space = False
        self.last_w_space_time = 0.0
        self.last_access_time = 0.0
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.w_space_thread = None
        self.last_afk_time = 0.0
        self.lock = threading.Lock()
        self._ui_queue = deque(maxlen=250)
        self._last_snapshot = None
        self._last_broadcast_time = 0.0

state = MacroState()

def add_log(msg, level="info"):
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "text": msg, "level": level}
    with state.lock:
        state.logs.append(entry)
        if len(state.logs) > _MAX_LOGS:
            del state.logs[:len(state.logs) - _MAX_LOGS]
        state._ui_queue.append(("log", entry))
    if level in ("warn", "error"):
        write_file_log(f"[{level.upper()}] {msg}")

def broadcast_state(force=False):
    now = time.time()
    uptime = 0
    if state.running and state.start_time:
        uptime = int(now - state.start_time)
    match_dur = 0
    if state.running and state.match_start_time:
        match_dur = int(now - state.match_start_time)

    snapshot = (
        state.running,
        state.status,
        state.matches,
        state.access_found,
        state.check_interval,
        state.confidence,
        state.anti_afk,
        state.w_space,
    )
    if not force and snapshot == state._last_snapshot and (now - state._last_broadcast_time) < _HEARTBEAT_INTERVAL:
        return

    state._last_snapshot = snapshot
    state._last_broadcast_time = now

    data = {
        "running": state.running,
        "status": state.status,
        "matches": state.matches,
        "access_found": state.access_found,
        "uptime": uptime,
        "match_duration": match_dur,
        "check_interval": state.check_interval,
        "confidence": state.confidence,
        "anti_afk": state.anti_afk,
        "w_space": state.w_space
    }
    with state.lock:
        state._ui_queue.append(("state", data))

def ui_pump():
    while True:
        batch = []
        with state.lock:
            while state._ui_queue:
                batch.append(state._ui_queue.popleft())
        for kind, payload in batch:
            try:
                if kind == "log":
                    eel.js_add_log(payload)()
                elif kind == "state":
                    eel.js_update_state(payload)()
            except Exception:
                pass
        eel.sleep(0.2)

