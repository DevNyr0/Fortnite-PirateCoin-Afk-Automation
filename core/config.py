import os
import sys

GAME_CLASS = "UnrealWindow"
GAME_TITLE = "fortnite"
HOTKEY = "f8"

DEFAULT_CHECK_INTERVAL = 1.5
DEFAULT_CONFIDENCE = 0.78
DEFAULT_AFK_INTERVAL = 25.0
W_SPACE_INTERVAL = 3.0
SHOP_ACCESS_COOLDOWN = 12.0

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_assets_dir():
    return os.path.join(get_base_dir(), "assets")

def get_templates_dir():
    return os.path.join(get_assets_dir(), "templates")

def get_icons_dir():
    return os.path.join(get_assets_dir(), "icons")

def is_safe_click_area(x, y, fw, fh):
    rx = x / float(fw)
    ry = y / float(fh)
    if rx >= 0.45 and ry >= 0.88:
        return False
    return True
