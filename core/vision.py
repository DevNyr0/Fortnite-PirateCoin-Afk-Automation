import os
import cv2
import mss
import numpy as np
from core.config import get_templates_dir

def load_cv_image(path):
    if not os.path.exists(path):
        return None
    try:
        data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None

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

def load_all_templates():
    td = get_templates_dir()
    candidates = {
        "play_again": ["play_again.png", "play_again_text.png", "recap_play_again.png", "custom_button.png"],
        "lobby_play": ["play_btn_en.png", "play_btn.png", "ready.png", "custom_button.png"],
        "shop_access": ["shop_access_text.png", "shop_access_coin.png", "shop_access_full.png", "shop_access_you_found.png"],
        "return_lobby": ["return_lobby_exact.png", "return_lobby_btn_en.png"],
        "continue": ["continue_btn.png"],
        "skip": ["skip_btn.png"],
        "back": ["back_btn.png"],
        "nvidia": ["nvidia.png"],
        "failsafe": ["failsafe.png"]
    }
    loaded = {}
    for group, names in candidates.items():
        loaded[group] = []
        for name in names:
            p = os.path.join(td, name)
            img = load_cv_image(p)
            if img is not None:
                if img.ndim == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                loaded[group].append((name, img))
    return loaded
