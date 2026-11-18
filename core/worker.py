import gc
import time
import random
import ctypes
from core.config import (
    W_SPACE_INTERVAL,
    SHOP_ACCESS_COOLDOWN,
    is_safe_click_area
)
from core.input_handler import (
    press_w_space,
    press_key,
    safe_click,
    ensure_fortnite_foreground
)
from core.vision import (
    capture_screen,
    match_template,
    load_all_templates
)
from core.state import (
    state,
    add_log,
    broadcast_state
)

_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

def _set_keep_awake(enable):
    try:
        flags = (_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED) if enable else _ES_CONTINUOUS
        ctypes.windll.kernel32.SetThreadExecutionState(flags)
    except Exception:
        pass

def w_space_worker():
    while not state.stop_event.is_set():
        try:
            if state.running and state.w_space and state.status not in ("MATCHMAKING", "IDLE"):
                press_w_space()
                if random.random() < 0.15:
                    add_log("Action: Jump-Walk (W + Space) active", "action")
        except Exception as e:
            add_log(f"Jump-Walk notice: {str(e)}", "warn")
        state.stop_event.wait(W_SPACE_INTERVAL)

def worker_loop():
    _set_keep_awake(True)
    templates = load_all_templates()
    state.status = "IN MATCH"
    state.match_start_time = time.time()
    state.last_afk_time = time.time()
    last_skip_time = 0.0
    capture_failures = 0
    iteration = 0
    broadcast_state(force=True)
    add_log("Macro engine active. Watching for team elimination and Play Again...", "action")

    try:
        while not state.stop_event.is_set():
            gf = None
            try:
                iteration += 1
                now = time.time()
                if state.anti_afk and (now - state.last_afk_time >= state.afk_interval):
                    if ensure_fortnite_foreground():
                        k = random.choice(["w", "a", "s", "d"])
                        press_key(k)
                        state.last_afk_time = now

                gf, ox, oy, fw, fh = capture_screen(1, as_gray=True)
                if gf is None:
                    capture_failures += 1
                    if capture_failures == 5:
                        add_log("Screen capture unavailable, waiting for display recovery...", "warn")
                    state.stop_event.wait(min(10.0, state.check_interval * 2))
                    continue
                capture_failures = 0

                if now - state.last_access_time >= SHOP_ACCESS_COOLDOWN:
                    roi_shop = (0, int(fh * 0.70), int(fw * 0.15), int(fw * 0.85))
                    for name, tpl in templates.get("shop_access", []):
                        pos, score = match_template(gf, tpl, threshold=min(state.confidence, 0.68), roi=roi_shop, fw=fw)
                        if pos:
                            state.access_found += 1
                            state.last_access_time = now
                            add_log(f"PIRATE SHOP ACCESS DETECTED! (Total Drops: {state.access_found})", "success")
                            broadcast_state(force=True)
                            break

                roi_back = (int(fh * 0.60), int(fh * 0.95), int(fw * 0.10), int(fw * 0.50))
                for name, tpl in templates.get("back", []):
                    pos, score = match_template(gf, tpl, threshold=0.75, roi=roi_back, fw=fw)
                    if pos:
                        add_log("Report dialog detected. Dismissing...", "warn")
                        press_key("esc")
                        safe_click(ox + pos[0], oy + pos[1])
                        state.stop_event.wait(1.2)
                        break

                clicked_play = False
                roi_play_again = (int(fh * 0.20), int(fh * 0.85), int(fw * 0.45), fw)
                for name, tpl in templates.get("play_again", []):
                    pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_play_again, fw=fw)
                    if pos:
                        if not is_safe_click_area(pos[0], pos[1], fw, fh):
                            continue
                        state.status = "CLICKING PLAY AGAIN"
                        broadcast_state(force=True)
                        add_log(f"Target '{name}' found (Score: {score:.2f}). Starting next match...", "success")
                        safe_click(ox + pos[0], oy + pos[1])
                        clicked_play = True
                        state.matches += 1
                        state.match_start_time = time.time()
                        add_log(f"Match #{state.matches} queued!", "success")
                        state.status = "MATCHMAKING"
                        broadcast_state(force=True)
                        state.stop_event.wait(25.0)
                        if not state.stop_event.is_set():
                            state.status = "IN MATCH"
                            broadcast_state(force=True)
                        break

                if clicked_play:
                    state.stop_event.wait(state.check_interval)
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
                        broadcast_state(force=True)
                        state.stop_event.wait(20.0)
                        if not state.stop_event.is_set():
                            state.status = "IN MATCH"
                            broadcast_state(force=True)
                        break

                if clicked_lobby:
                    state.stop_event.wait(state.check_interval)
                    continue

                found_action = False
                roi_continue = (int(fh * 0.55), int(fh * 0.95), int(fw * 0.45), fw)
                for name, tpl in templates.get("continue", []):
                    pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_continue, fw=fw)
                    if pos and is_safe_click_area(pos[0], pos[1], fw, fh):
                        add_log(f"Continue button ({name}) detected. Clicking...", "info")
                        safe_click(ox + pos[0], oy + pos[1])
                        found_action = True
                        state.stop_event.wait(1.0)
                        break

                if found_action:
                    state.stop_event.wait(state.check_interval)
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
                            state.stop_event.wait(1.0)
                            break

                if found_action:
                    state.stop_event.wait(state.check_interval)
                    continue

                for name, tpl in templates.get("nvidia", []):
                    pos, score = match_template(gf, tpl, threshold=state.confidence, fw=fw)
                    if pos:
                        state.status = "ELIMINATED"
                        add_log(f"Team elimination confirmed via screen cue ({name})", "warn")
                        broadcast_state(force=True)
                        break

                if state.status == "ELIMINATED":
                    roi_ret = (int(fh * 0.20), int(fh * 0.85), int(fw * 0.45), fw)
                    for name, tpl in templates.get("return_lobby", []):
                        pos, score = match_template(gf, tpl, threshold=state.confidence, roi=roi_ret, fw=fw)
                        if pos and is_safe_click_area(pos[0], pos[1], fw, fh):
                            add_log(f"Returning to lobby ({name})...", "info")
                            safe_click(ox + pos[0], oy + pos[1])
                            state.stop_event.wait(3.0)
                            break

            except Exception as e:
                add_log(f"Engine iteration notice: {str(e)}", "warn")
            finally:
                gf = None
                if iteration % 200 == 0:
                    gc.collect()

            broadcast_state()
            state.stop_event.wait(state.check_interval)
    finally:
        _set_keep_awake(False)
        state.status = "IDLE"
        broadcast_state(force=True)
        add_log("Macro stopped.", "info")

