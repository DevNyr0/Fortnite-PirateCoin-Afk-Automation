import os
import cv2
import tkinter as tk
from core.config import get_templates_dir, get_images_dir
from core.vision import capture_screen

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
            _, buf = cv2.imencode(".png", cropped)
            save_dirs = [get_templates_dir(), get_images_dir()]
            target_path = None
            for d in save_dirs:
                if d and os.path.exists(d):
                    sp = os.path.join(d, "custom_button.png")
                    with open(sp, "wb") as f:
                        f.write(buf)
                    if target_path is None:
                        target_path = sp
            if self.on_complete:
                self.on_complete(True, target_path or "custom_button.png")
        else:
            if self.on_complete:
                self.on_complete(False, "Selection too small")

