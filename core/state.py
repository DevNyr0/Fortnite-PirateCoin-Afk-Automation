import time
import threading
import eel
from core.config import DEFAULT_CHECK_INTERVAL, DEFAULT_CONFIDENCE, DEFAULT_AFK_INTERVAL

_MAX_LOGS = 200
_HEARTBEAT_INTERVAL = 30.0

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
        self.eel_lock = threading.Lock()
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
    with state.eel_lock:
        try:
            eel.js_add_log(entry)()
        except Exception:
            pass

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
    with state.eel_lock:
        try:
            eel.js_update_state(data)()
        except Exception:
            pass

