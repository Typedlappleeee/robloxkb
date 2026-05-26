import tkinter as tk
from tkinter import messagebox, filedialog
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
app_ref = None

MACROS_DIR = os.path.join(os.path.dirname(__file__), "macros")
os.makedirs(MACROS_DIR, exist_ok=True)

# ─── Hotkeys (globaux, modifiables) ──────────────────────────────────────────

hotkeys = {
    "rec_start":  Key.f9,
    "rec_stop":   Key.f10,
    "play_start": Key.f5,
    "play_stop":  Key.f6,
}
listening_for = None   # slot en attente d'une touche

def _key_name(key):
    if key is None:
        return "—"
    try:
        return key.name.upper()
    except AttributeError:
        return getattr(key, "char", None) or str(key)

def _keys_eq(a, b):
    return a == b

# ─── Listeners souris ────────────────────────────────────────────────────────

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

# ─── Listeners clavier ───────────────────────────────────────────────────────

def on_key_press(key):
    global listening_for

    # Mode configuration d'un hotkey
    if listening_for is not None:
        slot = listening_for
        hotkeys[slot] = key
        listening_for = None
        if app_ref:
            app_ref.after(0, lambda s=slot, k=key: app_ref._hotkey_set(s, k))
        return

    # Hotkeys globaux
    if _keys_eq(key, hotkeys["rec_start"]) and not recording and not playing:
        if app_ref:
            app_ref.after(0, app_ref._start_rec)
        return
    if _keys_eq(key, hotkeys["rec_stop"]) and recording:
        if app_ref:
            app_ref.after(0, app_ref._stop_rec)
        return
    if _keys_eq(key, hotkeys["play_start"]) and not playing and not recording:
        if app_ref:
            app_ref.after(0, app_ref._start_play)
        return
    if _keys_eq(key, hotkeys["play_stop"]) and playing:
        if app_ref:
            app_ref.after(0, app_ref._stop_play)
        return

    # Enregistrement
    if recording:
        try:
            events.append({"type": "keydown", "key": key.char, "t": _ts()})
        except AttributeError:
            events.append({"type": "keydown", "key": f"__special__{key.name}", "t": _ts()})

def on_key_release(key):
    # Ignorer les touches hotkey et le mode config
    if listening_for is not None:
        return
    for hk in hotkeys.values():
        if _keys_eq(key, hk):
            return

    if recording:
        try:
            events.append({"type": "keyup", "key": key.char, "t": _ts()})
        except AttributeError:
            events.append({"type": "keyup", "key": f"__special__{key.name}", "t": _ts()})

mouse_listener = mouse.Listener(
    on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll)
kb_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
mouse_listener.start()
kb_listener.start()

# ─── Playback ────────────────────────────────────────────────────────────────

def _parse_key(raw):
    if raw.startswith("__special__"):
        return getattr(Key, raw[len("__special__"):], None)
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
            (mouse_ctrl.press if ev["pressed"] else mouse_ctrl.release)(btn)
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
        status_var.set(f"Lecture... ({count}/{'inf' if infinite else loops})")
        _replay_once(ev_list, speed)
        if not infinite and count >= loops:
            break
        if not stop_event.is_set():
            time.sleep(delay_between)
    status_var.set("Pret")
    global playing
    playing = False

# ─── GUI ─────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        global app_ref
        super().__init__()
        app_ref = self
        self.title("Macro Recorder")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self._hk_btn_vars = {}   # slot -> StringVar pour afficher la touche
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        PAD = {"padx": 10, "pady": 5}
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        BTN = {"bg": "#313244", "fg": FG, "activebackground": "#45475a",
               "activeforeground": FG, "relief": "flat", "bd": 0,
               "font": ("Segoe UI", 10, "bold"), "cursor": "hand2",
               "width": 18, "height": 2}
        ACCENT = {"bg": "#a6e3a1", "fg": "#1e1e2e"}
        RED    = {"bg": "#f38ba8", "fg": "#1e1e2e"}
        BLUE   = {"bg": "#89b4fa", "fg": "#1e1e2e"}

        tk.Label(self, text="Macro Recorder", bg=BG, fg="#cba6f7",
                 font=("Segoe UI", 16, "bold")).pack(pady=(14, 2))
        tk.Label(self, text="Enregistre tes actions et rejoue-les en boucle",
                 bg=BG, fg="#6c7086", font=("Segoe UI", 9)).pack(pady=(0, 8))

        self.status_var = tk.StringVar(value="Pret")
        tk.Label(self, textvariable=self.status_var, bg="#181825", fg="#a6adc8",
                 font=("Segoe UI", 9), width=52, anchor="w",
                 padx=10, pady=4).pack(fill="x", padx=14)

        self.count_var = tk.StringVar(value="Actions enregistrees : 0")
        tk.Label(self, textvariable=self.count_var, bg=BG, fg="#6c7086",
                 font=("Segoe UI", 9)).pack(pady=(4, 0))

        # ── Enregistrement ──
        frm1 = tk.Frame(self, bg=BG)
        frm1.pack(**PAD)
        self.btn_rec = tk.Button(frm1, text="Demarrer enregistrement",
                                 command=self._start_rec, **{**BTN, **ACCENT})
        self.btn_rec.pack(side="left", padx=4)
        self.btn_stop_rec = tk.Button(frm1, text="Arreter enregistrement",
                                      command=self._stop_rec, **{**BTN, **RED},
                                      state="disabled")
        self.btn_stop_rec.pack(side="left", padx=4)

        # ── Options lecture ──
        opts = tk.LabelFrame(self, text="Options de lecture", bg=BG, fg=FG,
                             font=("Segoe UI", 9), bd=1, relief="solid",
                             padx=10, pady=6)
        opts.pack(fill="x", padx=14, pady=4)

        tk.Label(opts, text="Boucles (0=inf) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.loops_var = tk.IntVar(value=0)
        tk.Spinbox(opts, from_=0, to=9999, textvariable=self.loops_var,
                   width=6, bg="#313244", fg=FG, buttonbackground="#45475a",
                   relief="flat").grid(row=0, column=1, sticky="w", padx=8)

        tk.Label(opts, text="Vitesse :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.speed_var = tk.DoubleVar(value=1.0)
        sf = tk.Frame(opts, bg=BG)
        sf.grid(row=1, column=1, sticky="w", padx=8)
        tk.Scale(sf, from_=0.1, to=5.0, resolution=0.1, orient="horizontal",
                 variable=self.speed_var, bg=BG, fg=FG, highlightthickness=0,
                 troughcolor="#313244", length=120).pack(side="left")
        tk.Label(sf, textvariable=self.speed_var, bg=BG, fg=FG,
                 font=("Segoe UI", 9), width=4).pack(side="left")

        tk.Label(opts, text="Delai entre boucles (s) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.delay_var = tk.DoubleVar(value=0.5)
        tk.Spinbox(opts, from_=0.0, to=60.0, increment=0.5,
                   textvariable=self.delay_var, width=6,
                   bg="#313244", fg=FG, buttonbackground="#45475a",
                   relief="flat").grid(row=2, column=1, sticky="w", padx=8)

        # ── Lecture ──
        frm2 = tk.Frame(self, bg=BG)
        frm2.pack(**PAD)
        self.btn_play = tk.Button(frm2, text="Lancer la macro",
                                  command=self._start_play, **{**BTN, **BLUE})
        self.btn_play.pack(side="left", padx=4)
        self.btn_stop_play = tk.Button(frm2, text="Stopper la lecture",
                                       command=self._stop_play, **{**BTN, **RED},
                                       state="disabled")
        self.btn_stop_play.pack(side="left", padx=4)

        # ── Raccourcis globaux ──
        hk_frame = tk.LabelFrame(self, text="Raccourcis globaux (fonctionnent meme dans Roblox)",
                                 bg=BG, fg="#cba6f7", font=("Segoe UI", 9),
                                 bd=1, relief="solid", padx=10, pady=6)
        hk_frame.pack(fill="x", padx=14, pady=4)

        rows = [
            ("rec_start",  "Demarrer enregistrement"),
            ("rec_stop",   "Arreter enregistrement"),
            ("play_start", "Lancer la macro"),
            ("play_stop",  "Stopper la macro"),
        ]
        self._listen_btns = {}
        for i, (slot, label) in enumerate(rows):
            tk.Label(hk_frame, text=label, bg=BG, fg=FG,
                     font=("Segoe UI", 9), width=26, anchor="w").grid(
                row=i, column=0, sticky="w", pady=2)

            var = tk.StringVar(value=_key_name(hotkeys[slot]))
            self._hk_btn_vars[slot] = var

            tk.Label(hk_frame, textvariable=var, bg="#313244", fg="#f9e2af",
                     font=("Segoe UI", 9, "bold"), width=8,
                     relief="flat", padx=4).grid(row=i, column=1, padx=6)

            btn = tk.Button(hk_frame, text="Changer",
                            command=lambda s=slot: self._listen_hotkey(s),
                            bg="#45475a", fg=FG, relief="flat", bd=0,
                            font=("Segoe UI", 9), cursor="hand2", padx=6)
            btn.grid(row=i, column=2, padx=2)
            self._listen_btns[slot] = btn

        # ── Sauvegarde / Chargement ──
        frm3 = tk.Frame(self, bg=BG)
        frm3.pack(**PAD)
        small = dict(BTN, width=10, height=1)
        tk.Button(frm3, text="Sauvegarder", command=self._save, **small).pack(side="left", padx=3)
        tk.Button(frm3, text="Charger",     command=self._load, **small).pack(side="left", padx=3)
        tk.Button(frm3, text="Effacer",     command=self._clear,
                  **{**small, "bg": "#f38ba8", "fg": "#1e1e2e"}).pack(side="left", padx=3)

        tk.Label(self, text="Les raccourcis marchent meme si cette fenetre est en arriere-plan.",
                 bg=BG, fg="#45475a", font=("Segoe UI", 8)).pack(pady=(4, 10))

    # ── Hotkey config ─────────────────────────────────────────────────────────

    def _listen_hotkey(self, slot):
        global listening_for
        listening_for = slot
        self._hk_btn_vars[slot].set("...")
        self._listen_btns[slot].config(text="Appuie sur une touche", state="disabled")
        self.status_var.set(f"En attente d'une touche pour : {slot}")

    def _hotkey_set(self, slot, key):
        self._hk_btn_vars[slot].set(_key_name(key))
        self._listen_btns[slot].config(text="Changer", state="normal")
        self.status_var.set(f"Raccourci mis a jour : {_key_name(key)}")

    # ── Enregistrement ───────────────────────────────────────────────────────

    def _start_rec(self):
        global recording, events, record_start
        if recording or playing:
            return
        events = []
        record_start = time.time()
        recording = True
        self.status_var.set("Enregistrement en cours...")
        self.btn_rec.config(state="disabled")
        self.btn_stop_rec.config(state="normal")
        self._poll_count()

    def _poll_count(self):
        if recording:
            self.count_var.set(f"Actions enregistrees : {len(events)}")
            self.after(200, self._poll_count)

    def _stop_rec(self):
        global recording
        recording = False
        self.btn_rec.config(state="normal")
        self.btn_stop_rec.config(state="disabled")
        self.count_var.set(f"Actions enregistrees : {len(events)}")
        self.status_var.set(f"Enregistrement termine - {len(events)} actions")

    # ── Lecture ──────────────────────────────────────────────────────────────

    def _start_play(self):
        global playing, play_thread
        if playing or recording:
            return
        if not events:
            messagebox.showwarning("Vide", "Aucune macro enregistree.\nFais un enregistrement d'abord.")
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
        self.after(400, self._check_play_done)

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
        self.status_var.set("Lecture arretee")

    # ── Fichiers ─────────────────────────────────────────────────────────────

    def _save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Macro JSON", "*.json")],
            initialdir=MACROS_DIR, title="Sauvegarder la macro")
        if path:
            with open(path, "w") as f:
                json.dump(events, f, indent=2)
            self.status_var.set(f"Sauvegarde : {os.path.basename(path)}")

    def _load(self):
        global events
        path = filedialog.askopenfilename(
            filetypes=[("Macro JSON", "*.json")],
            initialdir=MACROS_DIR, title="Charger une macro")
        if path:
            with open(path) as f:
                events = json.load(f)
            self.count_var.set(f"Actions enregistrees : {len(events)}")
            self.status_var.set(f"Charge : {os.path.basename(path)} ({len(events)} actions)")

    def _clear(self):
        global events
        if messagebox.askyesno("Effacer", "Effacer la macro actuelle ?"):
            events = []
            self.count_var.set("Actions enregistrees : 0")
            self.status_var.set("Macro effacee")

    def _on_close(self):
        stop_event.set()
        mouse_listener.stop()
        kb_listener.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
