import os
import sys
import time
import socket
import random
import threading
import cv2
import keyboard
import eel
import eel.browsers

from core import (
    HOTKEY,
    W_SPACE_INTERVAL,
    SHOP_ACCESS_COOLDOWN,
    get_base_dir,
    is_safe_click_area,
    capture_screen,
    match_template,
    load_all_templates,
    safe_click,
    press_key,
    press_w_space,
    ensure_fortnite_foreground,
    SnipTool,
    state,
    add_log,
    broadcast_state
)

def w_space_worker():
    while not state.stop_event.is_set():
        if state.running and state.w_space and state.status not in ("MATCHMAKING", "IDLE"):
            press_w_space()
            if random.random() < 0.35:
                add_log("Action: Jump-Walk (W + Space) active", "action")
        state.stop_event.wait(W_SPACE_INTERVAL)

def worker_loop():
    templates = load_all_templates()
    state.status = "IN MATCH"
    state.match_start_time = time.time()
    state.last_afk_time = time.time()
    last_skip_time = 0.0
    broadcast_state()
    add_log("Macro engine active. Watching for team elimination and Play Again...", "action")

    while not state.stop_event.is_set():
        try:
            now = time.time()
            if state.anti_afk and (now - state.last_afk_time >= state.afk_interval):
                if ensure_fortnite_foreground():
                    k = random.choice(["w", "a", "s", "d"])
                    press_key(k)
                    state.last_afk_time = now

            frame, ox, oy, fw, fh = capture_screen(1)
            if frame is None:
                state.stop_event.wait(state.check_interval)
                continue

            gf = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame

            if now - state.last_access_time >= SHOP_ACCESS_COOLDOWN:
                roi_shop = (0, int(fh * 0.70), int(fw * 0.15), int(fw * 0.85))
                for name, tpl in templates.get("shop_access", []):
                    pos, score = match_template(gf, tpl, threshold=min(state.confidence, 0.68), roi=roi_shop, fw=fw)
                    if pos:
                        state.access_found += 1
                        state.last_access_time = now
                        add_log(f"PIRATE SHOP ACCESS DETECTED! (Total Drops: {state.access_found})", "success")
                        broadcast_state()
                        break

            roi_back = (int(fh * 0.60), int(fh * 0.95), int(fw * 0.10), int(fw * 0.50))
            for name, tpl in templates.get("back", []):
                pos, score = match_template(gf, tpl, threshold=0.75, roi=roi_back, fw=fw)
                if pos:
                    add_log("Report dialog detected. Dismissing...", "warn")
                    press_key("esc")
                    safe_click(ox + pos[0], oy + pos[1])
                    time.sleep(1.2)
                    break

            clicked_play = False
            roi_play_again = (int(fh * 0.20), int(fh * 0.85), int(fw * 0.45), fw)
            for name, tpl in templates.get("play_again", []):
                pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_play_again, fw=fw)
                if pos:
                    if not is_safe_click_area(pos[0], pos[1], fw, fh):
                        continue
                    state.status = "CLICKING PLAY AGAIN"
                    broadcast_state()
                    add_log(f"Target '{name}' found (Score: {score:.2f}). Starting next match...", "success")
                    safe_click(ox + pos[0], oy + pos[1])
                    clicked_play = True
                    state.matches += 1
                    state.match_start_time = time.time()
                    add_log(f"Match #{state.matches} queued!", "success")
                    state.status = "MATCHMAKING"
                    broadcast_state()
                    for _ in range(25):
                        if state.stop_event.is_set():
                            break
                        time.sleep(1.0)
                    state.status = "IN MATCH"
                    broadcast_state()
                    break

            if clicked_play:
                state.stop_event.wait(state.check_interval)
                broadcast_state()
                continue

            clicked_lobby = False
            roi_lobby = (int(fh * 0.55), fh, 0, int(fw * 0.50))
            for name, tpl in templates.get("lobby_play", []):
                pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_lobby, fw=fw)
                if pos:
                    if not is_safe_click_area(pos[0], pos[1], fw, fh):
                        continue
                    add_log(f"Lobby Play button ({name}) detected. Starting match...", "success")
                    safe_click(ox + pos[0], oy + pos[1])
                    clicked_lobby = True
                    state.matches += 1
                    state.match_start_time = time.time()
                    add_log(f"Match #{state.matches} queued from lobby!", "success")
                    state.status = "MATCHMAKING"
                    broadcast_state()
                    for _ in range(20):
                        if state.stop_event.is_set():
                            break
                        time.sleep(1.0)
                    state.status = "IN MATCH"
                    broadcast_state()
                    break

            if clicked_lobby:
                state.stop_event.wait(state.check_interval)
                broadcast_state()
                continue

            found_action = False
            roi_continue = (int(fh * 0.55), int(fh * 0.95), int(fw * 0.45), fw)
            for name, tpl in templates.get("continue", []):
                pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_continue, fw=fw)
                if pos and is_safe_click_area(pos[0], pos[1], fw, fh):
                    add_log(f"Continue button ({name}) detected. Clicking...", "info")
                    safe_click(ox + pos[0], oy + pos[1])
                    found_action = True
                    time.sleep(1.0)
                    break

            if found_action:
                state.stop_event.wait(state.check_interval)
                broadcast_state()
                continue

            if now - last_skip_time > 3.0:
                roi_skip = (int(fh * 0.55), int(fh * 0.95), int(fw * 0.45), fw)
                for name, tpl in templates.get("skip", []):
                    pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_skip, fw=fw)
                    if pos and is_safe_click_area(pos[0], pos[1], fw, fh):
                        add_log(f"Skip prompt ({name}) detected. Clicking...", "info")
                        safe_click(ox + pos[0], oy + pos[1])
                        last_skip_time = now
                        found_action = True
                        time.sleep(1.0)
                        break

            if found_action:
                state.stop_event.wait(state.check_interval)
                broadcast_state()
                continue

            for name, tpl in templates.get("nvidia", []):
                pos, score = match_template(gf, tpl, threshold=state.confidence, fw=fw)
                if pos:
                    state.status = "ELIMINATED"
                    add_log(f"Team elimination confirmed via screen cue ({name})", "warn")
                    broadcast_state()
                    break

            if state.status == "ELIMINATED":
                roi_ret = (int(fh * 0.20), int(fh * 0.85), int(fw * 0.45), fw)
                for name, tpl in templates.get("return_lobby", []):
                    pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_ret, fw=fw)
                    if pos and is_safe_click_area(pos[0], pos[1], fw, fh):
                        add_log(f"Returning to lobby ({name})...", "info")
                        safe_click(ox + pos[0], oy + pos[1])
                        time.sleep(3.0)
                        break

        except Exception as e:
            add_log(f"Engine iteration notice: {str(e)}", "warn")

        broadcast_state()
        state.stop_event.wait(state.check_interval)

    state.status = "IDLE"
    broadcast_state()
    add_log("Macro stopped.", "info")

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

if __name__ == "__main__":
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
        sys.exit(0)
    except Exception:
        try:
            port = get_free_port()
            eel.start("index.html", mode="default", host="127.0.0.1", port=port, size=(980, 720))
        except Exception:
            state.stop_event.set()
            sys.exit(0)
