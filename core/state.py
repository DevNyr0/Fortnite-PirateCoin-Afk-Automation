import time
import threading
import eel
from core.config import DEFAULT_CHECK_INTERVAL, DEFAULT_CONFIDENCE, DEFAULT_AFK_INTERVAL

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

state = MacroState()

def add_log(msg, level="info"):
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "text": msg, "level": level}
    state.logs.append(entry)
    if len(state.logs) > 300:
        state.logs.pop(0)
    try:
        eel.js_add_log(entry)()
    except Exception:
        pass

def broadcast_state():
    uptime = 0
    if state.running and state.start_time:
        uptime = int(time.time() - state.start_time)
    match_dur = 0
    if state.running and state.match_start_time:
        match_dur = int(time.time() - state.match_start_time)
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
    try:
        eel.js_update_state(data)()
    except Exception:
        pass

