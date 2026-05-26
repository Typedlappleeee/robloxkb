import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

# ─── State ───────────────────────────────────────────────────────────────────

events = []
recording = False
playing = False
record_start = None
play_thread = None
stop_event = threading.Event()

mouse_ctrl = MouseController()
kb_ctrl = KeyboardController()

MACROS_DIR = os.path.join(os.path.dirname(__file__), "macros")
os.makedirs(MACROS_DIR, exist_ok=True)

# ─── Recording ───────────────────────────────────────────────────────────────

def _ts():
    return time.time() - record_start

def on_mouse_move(x, y):
    if recording:
        events.append({"type": "move", "x": x, "y": y, "t": _ts()})

def on_mouse_click(x, y, button, pressed):
    if recording:
        events.append({"type": "click", "x": x, "y": y,
                       "button": button.name, "pressed": pressed, "t": _ts()})

def on_mouse_scroll(x, y, dx, dy):
    if recording:
        events.append({"type": "scroll", "x": x, "y": y,
                       "dx": dx, "dy": dy, "t": _ts()})

def on_key_press(key):
    if recording:
        try:
            events.append({"type": "keydown", "key": key.char, "t": _ts()})
        except AttributeError:
            events.append({"type": "keydown", "key": f"__special__{key.name}", "t": _ts()})

def on_key_release(key):
    if recording:
        try:
            events.append({"type": "keyup", "key": key.char, "t": _ts()})
        except AttributeError:
            events.append({"type": "keyup", "key": f"__special__{key.name}", "t": _ts()})

mouse_listener = mouse.Listener(
    on_move=on_mouse_move,
    on_click=on_mouse_click,
    on_scroll=on_mouse_scroll,
)
kb_listener = keyboard.Listener(
    on_press=on_key_press,
    on_release=on_key_release,
)
mouse_listener.start()
kb_listener.start()

# ─── Playback ────────────────────────────────────────────────────────────────

def _parse_key(raw):
    if raw.startswith("__special__"):
        name = raw[len("__special__"):]
        return getattr(Key, name, None)
    return raw

def _replay_once(ev_list, speed):
    if not ev_list:
        return
    prev_t = ev_list[0]["t"]
    for ev in ev_list:
        if stop_event.is_set():
            return
        delay = (ev["t"] - prev_t) / speed
        if delay > 0:
            time.sleep(delay)
        prev_t = ev["t"]
        t = ev["type"]
        if t == "move":
            mouse_ctrl.position = (ev["x"], ev["y"])
        elif t == "click":
            btn = Button.left if ev["button"] == "left" else (
                  Button.right if ev["button"] == "right" else Button.middle)
            mouse_ctrl.position = (ev["x"], ev["y"])
            if ev["pressed"]:
                mouse_ctrl.press(btn)
            else:
                mouse_ctrl.release(btn)
        elif t == "scroll":
            mouse_ctrl.position = (ev["x"], ev["y"])
            mouse_ctrl.scroll(ev["dx"], ev["dy"])
        elif t == "keydown":
            k = _parse_key(ev["key"])
            if k:
                kb_ctrl.press(k)
        elif t == "keyup":
            k = _parse_key(ev["key"])
            if k:
                kb_ctrl.release(k)

def _play_loop(ev_list, loops, speed, delay_between, status_var):
    infinite = (loops == 0)
    count = 0
    while not stop_event.is_set():
        count += 1
        lbl = "∞" if infinite else loops
        status_var.set(f"Lecture… ({count}/{lbl})")
        _replay_once(ev_list, speed)
        if not infinite and count >= loops:
            break
        if not stop_event.is_set():
            time.sleep(delay_between)
    status_var.set("Prêt")
    global playing
    playing = False

# ─── GUI ─────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Macro Recorder — Roblox")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        PAD = {"padx": 10, "pady": 6}
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        BTN = {"bg": "#313244", "fg": FG, "activebackground": "#45475a",
               "activeforeground": FG, "relief": "flat", "bd": 0,
               "font": ("Segoe UI", 10, "bold"), "cursor": "hand2",
               "width": 18, "height": 2}
        ACCENT = {"bg": "#a6e3a1", "fg": "#1e1e2e"}
        RED    = {"bg": "#f38ba8", "fg": "#1e1e2e"}
        BLUE   = {"bg": "#89b4fa", "fg": "#1e1e2e"}

        # Title
        tk.Label(self, text="🎮  Macro Recorder", bg=BG, fg="#cba6f7",
                 font=("Segoe UI", 16, "bold")).pack(pady=(16, 4))
        tk.Label(self, text="Enregistre tes actions et rejoue-les en boucle",
                 bg=BG, fg="#6c7086", font=("Segoe UI", 9)).pack(pady=(0, 12))

        # Status bar
        self.status_var = tk.StringVar(value="Prêt")
        tk.Label(self, textvariable=self.status_var, bg="#181825", fg="#a6adc8",
                 font=("Segoe UI", 9), width=48, anchor="w",
                 padx=10, pady=4).pack(fill="x", padx=14)

        # Event count
        self.count_var = tk.StringVar(value="Actions enregistrées : 0")
        tk.Label(self, textvariable=self.count_var, bg=BG, fg="#6c7086",
                 font=("Segoe UI", 9)).pack(pady=(4, 0))

        # ── Record / Stop record ──
        frm1 = tk.Frame(self, bg=BG)
        frm1.pack(**PAD)
        self.btn_rec = tk.Button(frm1, text="⏺  Démarrer l'enregistrement",
                                 command=self._start_rec, **{**BTN, **ACCENT})
        self.btn_rec.pack(side="left", padx=4)
        self.btn_stop_rec = tk.Button(frm1, text="⏹  Arrêter l'enregistrement",
                                      command=self._stop_rec, **{**BTN, **RED},
                                      state="disabled")
        self.btn_stop_rec.pack(side="left", padx=4)

        # ── Play options ──
        opts = tk.LabelFrame(self, text="Options de lecture", bg=BG, fg=FG,
                             font=("Segoe UI", 9), bd=1, relief="solid",
                             padx=10, pady=8)
        opts.pack(fill="x", padx=14, pady=6)

        # Loops
        tk.Label(opts, text="Boucles (0 = infini) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=3)
        self.loops_var = tk.IntVar(value=0)
        tk.Spinbox(opts, from_=0, to=9999, textvariable=self.loops_var,
                   width=6, bg="#313244", fg=FG, buttonbackground="#45475a",
                   relief="flat").grid(row=0, column=1, sticky="w", padx=8)

        # Speed
        tk.Label(opts, text="Vitesse :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=3)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_frame = tk.Frame(opts, bg=BG)
        speed_frame.grid(row=1, column=1, sticky="w", padx=8)
        tk.Scale(speed_frame, from_=0.1, to=5.0, resolution=0.1,
                 orient="horizontal", variable=self.speed_var,
                 bg=BG, fg=FG, highlightthickness=0,
                 troughcolor="#313244", length=120).pack(side="left")
        tk.Label(speed_frame, textvariable=self.speed_var, bg=BG, fg=FG,
                 font=("Segoe UI", 9), width=4).pack(side="left")

        # Delay between loops
        tk.Label(opts, text="Délai entre boucles (s) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=3)
        self.delay_var = tk.DoubleVar(value=0.5)
        tk.Spinbox(opts, from_=0.0, to=60.0, increment=0.5,
                   textvariable=self.delay_var, width=6,
                   bg="#313244", fg=FG, buttonbackground="#45475a",
                   relief="flat").grid(row=2, column=1, sticky="w", padx=8)

        # ── Play / Stop play ──
        frm2 = tk.Frame(self, bg=BG)
        frm2.pack(**PAD)
        self.btn_play = tk.Button(frm2, text="▶  Lancer la macro",
                                  command=self._start_play, **{**BTN, **BLUE})
        self.btn_play.pack(side="left", padx=4)
        self.btn_stop_play = tk.Button(frm2, text="⏹  Stopper la lecture",
                                       command=self._stop_play, **{**BTN, **RED},
                                       state="disabled")
        self.btn_stop_play.pack(side="left", padx=4)

        # ── Save / Load / Clear ──
        frm3 = tk.Frame(self, bg=BG)
        frm3.pack(**PAD)
        small = dict(BTN, width=10, height=1)
        tk.Button(frm3, text="💾 Sauvegarder", command=self._save, **small).pack(side="left", padx=3)
        tk.Button(frm3, text="📂 Charger",     command=self._load, **small).pack(side="left", padx=3)
        tk.Button(frm3, text="🗑 Effacer",      command=self._clear,
                  **{**small, "bg": "#f38ba8", "fg": "#1e1e2e"}).pack(side="left", padx=3)

        tk.Label(self, text="F5 = Lancer  |  F6 = Stopper  |  F9 = Enregistrer  |  F10 = Stop enreg.",
                 bg=BG, fg="#45475a", font=("Segoe UI", 8)).pack(pady=(6, 12))

        # Hotkeys
        self.bind_all("<F9>",  lambda e: self._start_rec())
        self.bind_all("<F10>", lambda e: self._stop_rec())
        self.bind_all("<F5>",  lambda e: self._start_play())
        self.bind_all("<F6>",  lambda e: self._stop_play())

    # ── Actions ──────────────────────────────────────────────────────────────

    def _start_rec(self):
        global recording, events, record_start
        if recording or playing:
            return
        events = []
        record_start = time.time()
        recording = True
        self.status_var.set("⏺ Enregistrement en cours…")
        self.btn_rec.config(state="disabled")
        self.btn_stop_rec.config(state="normal")
        self._poll_count()

    def _poll_count(self):
        if recording:
            self.count_var.set(f"Actions enregistrées : {len(events)}")
            self.after(200, self._poll_count)

    def _stop_rec(self):
        global recording
        recording = False
        self.btn_rec.config(state="normal")
        self.btn_stop_rec.config(state="disabled")
        self.count_var.set(f"Actions enregistrées : {len(events)}")
        self.status_var.set(f"Enregistrement terminé — {len(events)} actions")

    def _start_play(self):
        global playing, play_thread
        if playing or recording or not events:
            if not events:
                messagebox.showwarning("Vide", "Aucune macro enregistrée.\nFais un enregistrement d'abord.")
            return
        stop_event.clear()
        playing = True
        self.btn_play.config(state="disabled")
        self.btn_stop_play.config(state="normal")
        play_thread = threading.Thread(
            target=_play_loop,
            args=(list(events), self.loops_var.get(),
                  self.speed_var.get(), self.delay_var.get(),
                  self.status_var),
            daemon=True,
        )
        play_thread.start()
        self.after(500, self._check_play_done)

    def _check_play_done(self):
        if playing:
            self.after(300, self._check_play_done)
        else:
            self.btn_play.config(state="normal")
            self.btn_stop_play.config(state="disabled")

    def _stop_play(self):
        stop_event.set()
        self.btn_play.config(state="normal")
        self.btn_stop_play.config(state="disabled")
        self.status_var.set("Lecture arrêtée")

    def _save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Macro JSON", "*.json")],
            initialdir=MACROS_DIR,
            title="Sauvegarder la macro",
        )
        if path:
            with open(path, "w") as f:
                json.dump(events, f, indent=2)
            self.status_var.set(f"Sauvegardé : {os.path.basename(path)}")

    def _load(self):
        global events
        path = filedialog.askopenfilename(
            filetypes=[("Macro JSON", "*.json")],
            initialdir=MACROS_DIR,
            title="Charger une macro",
        )
        if path:
            with open(path) as f:
                events = json.load(f)
            self.count_var.set(f"Actions enregistrées : {len(events)}")
            self.status_var.set(f"Chargé : {os.path.basename(path)} ({len(events)} actions)")

    def _clear(self):
        global events
        if messagebox.askyesno("Effacer", "Effacer la macro actuelle ?"):
            events = []
            self.count_var.set("Actions enregistrées : 0")
            self.status_var.set("Macro effacée")

    def _on_close(self):
        stop_event.set()
        mouse_listener.stop()
        kb_listener.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
