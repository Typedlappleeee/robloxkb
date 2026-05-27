import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

# ─── State partagé ─────────────────────────────────────────────────────────────────

mouse_ctrl = MouseController()
kb_ctrl    = KeyboardController()
app_ref    = None

MACROS_DIR = os.path.join(os.path.dirname(__file__), "macros")
os.makedirs(MACROS_DIR, exist_ok=True)

# ─── Macro state ───────────────────────────────────────────────────────────────

mac_events     = []
mac_recording  = False
mac_playing    = False
mac_start_t    = None
mac_play_thread= None
mac_stop       = threading.Event()

# ─── Autoclicker state ──────────────────────────────────────────────────────────

ac_running     = False
ac_stop        = threading.Event()
ac_thread      = None
ac_click_count = 0

# ─── Hotkeys ───────────────────────────────────────────────────────────────────

hotkeys = {
    "rec_start":  Key.f9,
    "rec_stop":   Key.f10,
    "play_start": Key.f5,
    "play_stop":  Key.f6,
    "ac_toggle":  Key.f7,
}
listening_for = None

def _key_name(key):
    if key is None:
        return "-"
    try:
        return key.name.upper()
    except AttributeError:
        return getattr(key, "char", None) or str(key)

def _keq(a, b):
    return a == b

# ─── Listeners souris ─────────────────────────────────────────────────────────────

def _ts():
    return time.time() - mac_start_t

def on_mouse_move(x, y):
    if mac_recording:
        mac_events.append({"type": "move", "x": x, "y": y, "t": _ts()})

def on_mouse_click(x, y, button, pressed):
    if mac_recording:
        mac_events.append({"type": "click", "x": x, "y": y,
                           "button": button.name, "pressed": pressed, "t": _ts()})

def on_mouse_scroll(x, y, dx, dy):
    if mac_recording:
        mac_events.append({"type": "scroll", "x": x, "y": y,
                           "dx": dx, "dy": dy, "t": _ts()})

# ─── Listeners clavier ────────────────────────────────────────────────────────────

def on_key_press(key):
    global listening_for

    if listening_for is not None:
        slot = listening_for
        hotkeys[slot] = key
        listening_for = None
        if app_ref:
            app_ref.after(0, lambda s=slot, k=key: app_ref._hotkey_set(s, k))
        return

    if _keq(key, hotkeys["rec_start"]) and not mac_recording and not mac_playing:
        if app_ref: app_ref.after(0, app_ref._mac_start_rec)
        return
    if _keq(key, hotkeys["rec_stop"]) and mac_recording:
        if app_ref: app_ref.after(0, app_ref._mac_stop_rec)
        return
    if _keq(key, hotkeys["play_start"]) and not mac_playing and not mac_recording:
        if app_ref: app_ref.after(0, app_ref._mac_start_play)
        return
    if _keq(key, hotkeys["play_stop"]) and mac_playing:
        if app_ref: app_ref.after(0, app_ref._mac_stop_play)
        return
    if _keq(key, hotkeys["ac_toggle"]):
        if app_ref: app_ref.after(0, app_ref._ac_toggle)
        return

    if mac_recording:
        try:
            mac_events.append({"type": "keydown", "key": key.char, "t": _ts()})
        except AttributeError:
            mac_events.append({"type": "keydown", "key": f"__special__{key.name}", "t": _ts()})

def on_key_release(key):
    if listening_for is not None:
        return
    for hk in hotkeys.values():
        if _keq(key, hk):
            return
    if mac_recording:
        try:
            mac_events.append({"type": "keyup", "key": key.char, "t": _ts()})
        except AttributeError:
            mac_events.append({"type": "keyup", "key": f"__special__{key.name}", "t": _ts()})

mouse_listener = mouse.Listener(
    on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll)
kb_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
mouse_listener.start()
kb_listener.start()

# ─── Macro playback ──────────────────────────────────────────────────────────────

def _parse_key(raw):
    if raw.startswith("__special__"):
        return getattr(Key, raw[len("__special__"):], None)
    return raw

def _replay_once(ev_list, speed):
    if not ev_list:
        return
    prev_t = ev_list[0]["t"]
    for ev in ev_list:
        if mac_stop.is_set():
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
            if k: kb_ctrl.press(k)
        elif t == "keyup":
            k = _parse_key(ev["key"])
            if k: kb_ctrl.release(k)

def _play_loop(ev_list, loops, speed, delay_between, status_var):
    global mac_playing
    infinite = (loops == 0)
    count = 0
    while not mac_stop.is_set():
        count += 1
        status_var.set(f"Lecture... ({count}/{'inf' if infinite else loops})")
        _replay_once(ev_list, speed)
        if not infinite and count >= loops:
            break
        if not mac_stop.is_set():
            time.sleep(delay_between)
    status_var.set("Pret")
    mac_playing = False

# ─── Autoclicker loop ─────────────────────────────────────────────────────────────

def _ac_loop(btn_name, double, interval_ms, count_var, status_var):
    global ac_running, ac_click_count
    btn = {"gauche": Button.left, "droit": Button.right, "milieu": Button.middle}[btn_name]
    ac_click_count = 0
    while not ac_stop.is_set():
        mouse_ctrl.click(btn, 2 if double else 1)
        ac_click_count += 1
        if app_ref:
            app_ref.after(0, lambda c=ac_click_count: count_var.set(f"Clics : {c}"))
        time.sleep(interval_ms / 1000)
    status_var.set("Autoclicker arrete")
    ac_running = False

# ─── GUI ─────────────────────────────────────────────────────────────────────

BG     = "#1e1e2e"
FG     = "#cdd6f4"
BG2    = "#181825"
PURPLE = "#cba6f7"
GREEN  = "#a6e3a1"
RED_C  = "#f38ba8"
BLUE_C = "#89b4fa"
YELLOW = "#f9e2af"
MUTED  = "#6c7086"
PANEL  = "#313244"
HOVER  = "#45475a"

BTN_BASE = {"relief": "flat", "bd": 0, "cursor": "hand2",
            "font": ("Segoe UI", 10, "bold"), "bg": PANEL, "fg": FG,
            "activebackground": HOVER, "activeforeground": FG,
            "width": 18, "height": 2}

class App(tk.Tk):
    def __init__(self):
        global app_ref
        super().__init__()
        app_ref = self
        self.title("Macro Recorder")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._hk_vars  = {}
        self._hk_btns  = {}
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        tk.Label(self, text="Macro Recorder", bg=BG, fg=PURPLE,
                 font=("Segoe UI", 16, "bold")).pack(pady=(14, 2))
        tk.Label(self, text="Automatise tes actions Roblox",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(0, 8))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=FG,
                        font=("Segoe UI", 10, "bold"), padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", PURPLE)],
                  foreground=[("selected", BG)])

        tab_mac = tk.Frame(nb, bg=BG)
        tab_ac  = tk.Frame(nb, bg=BG)
        nb.add(tab_mac, text="  Macro  ")
        nb.add(tab_ac,  text="  Autoclicker  ")

        self._build_macro(tab_mac)
        self._build_ac(tab_ac)

        tk.Label(self, text="Raccourcis globaux actifs meme quand Roblox est en avant-plan",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(0, 10))

    def _build_macro(self, parent):
        PAD = {"padx": 10, "pady": 5}

        self.mac_status = tk.StringVar(value="Pret")
        tk.Label(parent, textvariable=self.mac_status, bg=BG2, fg="#a6adc8",
                 font=("Segoe UI", 9), width=52, anchor="w",
                 padx=10, pady=4).pack(fill="x", padx=0, pady=(8, 2))

        self.mac_count = tk.StringVar(value="Actions enregistrees : 0")
        tk.Label(parent, textvariable=self.mac_count, bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(pady=(2, 4))

        frm1 = tk.Frame(parent, bg=BG)
        frm1.pack(**PAD)
        self.btn_rec = tk.Button(frm1, text="Demarrer enreg.",
                                 command=self._mac_start_rec,
                                 **{**BTN_BASE, "bg": GREEN, "fg": BG, "activebackground": "#7ec77e"})
        self.btn_rec.pack(side="left", padx=4)
        self.btn_stop_rec = tk.Button(frm1, text="Arreter enreg.",
                                      command=self._mac_stop_rec,
                                      **{**BTN_BASE, "bg": RED_C, "fg": BG, "activebackground": "#c96e86"},
                                      state="disabled")
        self.btn_stop_rec.pack(side="left", padx=4)

        opts = tk.LabelFrame(parent, text="Options de lecture", bg=BG, fg=FG,
                             font=("Segoe UI", 9), bd=1, relief="solid", padx=10, pady=6)
        opts.pack(fill="x", padx=10, pady=4)

        tk.Label(opts, text="Boucles (0=inf) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.mac_loops = tk.IntVar(value=0)
        tk.Spinbox(opts, from_=0, to=9999, textvariable=self.mac_loops,
                   width=6, bg=PANEL, fg=FG, buttonbackground=HOVER,
                   relief="flat").grid(row=0, column=1, sticky="w", padx=8)

        tk.Label(opts, text="Vitesse :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.mac_speed = tk.DoubleVar(value=1.0)
        sf = tk.Frame(opts, bg=BG)
        sf.grid(row=1, column=1, sticky="w", padx=8)
        tk.Scale(sf, from_=0.1, to=5.0, resolution=0.1, orient="horizontal",
                 variable=self.mac_speed, bg=BG, fg=FG, highlightthickness=0,
                 troughcolor=PANEL, length=120).pack(side="left")
        tk.Label(sf, textvariable=self.mac_speed, bg=BG, fg=FG,
                 font=("Segoe UI", 9), width=4).pack(side="left")

        tk.Label(opts, text="Delai boucles (s) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.mac_delay = tk.DoubleVar(value=0.5)
        tk.Spinbox(opts, from_=0.0, to=60.0, increment=0.5,
                   textvariable=self.mac_delay, width=6,
                   bg=PANEL, fg=FG, buttonbackground=HOVER,
                   relief="flat").grid(row=2, column=1, sticky="w", padx=8)

        frm2 = tk.Frame(parent, bg=BG)
        frm2.pack(**PAD)
        self.btn_play = tk.Button(frm2, text="Lancer la macro",
                                  command=self._mac_start_play,
                                  **{**BTN_BASE, "bg": BLUE_C, "fg": BG, "activebackground": "#6a9fd8"})
        self.btn_play.pack(side="left", padx=4)
        self.btn_stop_play = tk.Button(frm2, text="Stopper la macro",
                                       command=self._mac_stop_play,
                                       **{**BTN_BASE, "bg": RED_C, "fg": BG, "activebackground": "#c96e86"},
                                       state="disabled")
        self.btn_stop_play.pack(side="left", padx=4)

        frm3 = tk.Frame(parent, bg=BG)
        frm3.pack(**PAD)
        sm = dict(BTN_BASE, width=10, height=1)
        tk.Button(frm3, text="Sauvegarder", command=self._mac_save, **sm).pack(side="left", padx=3)
        tk.Button(frm3, text="Charger",     command=self._mac_load, **sm).pack(side="left", padx=3)
        tk.Button(frm3, text="Effacer",     command=self._mac_clear,
                  **{**sm, "bg": RED_C, "fg": BG}).pack(side="left", padx=3)

        hk = tk.LabelFrame(parent, text="Raccourcis macro", bg=BG, fg=PURPLE,
                            font=("Segoe UI", 9), bd=1, relief="solid", padx=8, pady=4)
        hk.pack(fill="x", padx=10, pady=(4, 8))
        self._hk_row(hk, 0, "rec_start",  "Demarrer enreg.")
        self._hk_row(hk, 1, "rec_stop",   "Arreter enreg.")
        self._hk_row(hk, 2, "play_start", "Lancer macro")
        self._hk_row(hk, 3, "play_stop",  "Stopper macro")

    def _build_ac(self, parent):
        PAD = {"padx": 10, "pady": 6}

        self.ac_status = tk.StringVar(value="Autoclicker arrete")
        tk.Label(parent, textvariable=self.ac_status, bg=BG2, fg="#a6adc8",
                 font=("Segoe UI", 9), width=52, anchor="w",
                 padx=10, pady=4).pack(fill="x", padx=0, pady=(8, 2))

        self.ac_count_var = tk.StringVar(value="Clics : 0")
        tk.Label(parent, textvariable=self.ac_count_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(pady=(2, 4))

        opts = tk.LabelFrame(parent, text="Parametres", bg=BG, fg=FG,
                             font=("Segoe UI", 9), bd=1, relief="solid", padx=14, pady=8)
        opts.pack(fill="x", padx=10, pady=4)

        tk.Label(opts, text="Intervalle (ms) :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=4)
        self.ac_interval = tk.IntVar(value=100)
        interval_frame = tk.Frame(opts, bg=BG)
        interval_frame.grid(row=0, column=1, sticky="w", padx=8)
        tk.Scale(interval_frame, from_=10, to=2000, resolution=10,
                 orient="horizontal", variable=self.ac_interval,
                 bg=BG, fg=FG, highlightthickness=0, troughcolor=PANEL, length=160,
                 command=lambda v: self._ac_update_cps()).pack(side="left")
        self.ac_cps_label = tk.StringVar(value="10.0 CPS")
        tk.Label(interval_frame, textvariable=self.ac_cps_label,
                 bg=BG, fg=YELLOW, font=("Segoe UI", 9, "bold"),
                 width=9).pack(side="left", padx=4)

        tk.Label(opts, text="Ou CPS direct :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        cps_f = tk.Frame(opts, bg=BG)
        cps_f.grid(row=1, column=1, sticky="w", padx=8)
        self.ac_cps_entry = tk.Spinbox(cps_f, from_=0.5, to=100, increment=0.5,
                                       width=6, bg=PANEL, fg=FG,
                                       buttonbackground=HOVER, relief="flat",
                                       command=self._ac_cps_to_interval)
        self.ac_cps_entry.delete(0, "end")
        self.ac_cps_entry.insert(0, "10")
        self.ac_cps_entry.pack(side="left")
        tk.Button(cps_f, text="Appliquer", command=self._ac_cps_to_interval,
                  bg=PANEL, fg=FG, relief="flat", font=("Segoe UI", 9),
                  cursor="hand2", padx=6).pack(side="left", padx=6)

        tk.Label(opts, text="Bouton :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self.ac_btn = tk.StringVar(value="gauche")
        btn_f = tk.Frame(opts, bg=BG)
        btn_f.grid(row=2, column=1, sticky="w", padx=8)
        for val, lbl in [("gauche", "Gauche"), ("droit", "Droit"), ("milieu", "Milieu")]:
            tk.Radiobutton(btn_f, text=lbl, variable=self.ac_btn, value=val,
                           bg=BG, fg=FG, selectcolor=PANEL,
                           activebackground=BG, activeforeground=FG,
                           font=("Segoe UI", 9)).pack(side="left", padx=4)

        tk.Label(opts, text="Type :", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=4)
        self.ac_double = tk.BooleanVar(value=False)
        type_f = tk.Frame(opts, bg=BG)
        type_f.grid(row=3, column=1, sticky="w", padx=8)
        tk.Radiobutton(type_f, text="Simple", variable=self.ac_double, value=False,
                       bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG,
                       font=("Segoe UI", 9)).pack(side="left", padx=4)
        tk.Radiobutton(type_f, text="Double", variable=self.ac_double, value=True,
                       bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG,
                       font=("Segoe UI", 9)).pack(side="left", padx=4)

        frm = tk.Frame(parent, bg=BG)
        frm.pack(**PAD)
        self.btn_ac_start = tk.Button(frm, text="Demarrer autoclicker",
                                      command=self._ac_start,
                                      **{**BTN_BASE, "bg": GREEN, "fg": BG, "activebackground": "#7ec77e"})
        self.btn_ac_start.pack(side="left", padx=4)
        self.btn_ac_stop = tk.Button(frm, text="Stopper autoclicker",
                                     command=self._ac_stop,
                                     **{**BTN_BASE, "bg": RED_C, "fg": BG, "activebackground": "#c96e86"},
                                     state="disabled")
        self.btn_ac_stop.pack(side="left", padx=4)

        hk = tk.LabelFrame(parent, text="Raccourci autoclicker", bg=BG, fg=PURPLE,
                            font=("Segoe UI", 9), bd=1, relief="solid", padx=8, pady=4)
        hk.pack(fill="x", padx=10, pady=(4, 8))
        self._hk_row(hk, 0, "ac_toggle", "Toggle (marche/arrete)")

    def _hk_row(self, parent, row, slot, label):
        tk.Label(parent, text=label, bg=BG, fg=FG,
                 font=("Segoe UI", 9), width=22, anchor="w").grid(
            row=row, column=0, sticky="w", pady=2)
        var = tk.StringVar(value=_key_name(hotkeys[slot]))
        self._hk_vars[slot] = var
        tk.Label(parent, textvariable=var, bg=PANEL, fg=YELLOW,
                 font=("Segoe UI", 9, "bold"), width=8,
                 relief="flat", padx=4).grid(row=row, column=1, padx=6)
        btn = tk.Button(parent, text="Changer",
                        command=lambda s=slot: self._listen_hotkey(s),
                        bg=HOVER, fg=FG, relief="flat", bd=0,
                        font=("Segoe UI", 9), cursor="hand2", padx=6)
        btn.grid(row=row, column=2, padx=2)
        self._hk_btns[slot] = btn

    def _listen_hotkey(self, slot):
        global listening_for
        listening_for = slot
        self._hk_vars[slot].set("...")
        self._hk_btns[slot].config(text="Appuie...", state="disabled")

    def _hotkey_set(self, slot, key):
        self._hk_vars[slot].set(_key_name(key))
        self._hk_btns[slot].config(text="Changer", state="normal")

    def _ac_update_cps(self):
        ms = self.ac_interval.get()
        cps = 1000 / ms if ms > 0 else 0
        self.ac_cps_label.set(f"{cps:.1f} CPS")

    def _ac_cps_to_interval(self):
        try:
            cps = float(self.ac_cps_entry.get())
            if cps > 0:
                ms = int(1000 / cps)
                self.ac_interval.set(max(10, ms))
                self._ac_update_cps()
        except ValueError:
            pass

    def _ac_toggle(self):
        if ac_running:
            self._ac_stop()
        else:
            self._ac_start()

    def _ac_start(self):
        global ac_running, ac_thread, ac_click_count
        if ac_running:
            return
        ac_stop.clear()
        ac_running = True
        ac_click_count = 0
        self.btn_ac_start.config(state="disabled")
        self.btn_ac_stop.config(state="normal")
        self.ac_status.set("Autoclicker actif...")
        ac_thread = threading.Thread(
            target=_ac_loop,
            args=(self.ac_btn.get(), self.ac_double.get(),
                  self.ac_interval.get(), self.ac_count_var, self.ac_status),
            daemon=True,
        )
        ac_thread.start()
        self.after(300, self._ac_check_done)

    def _ac_stop(self):
        ac_stop.set()
        self.btn_ac_start.config(state="normal")
        self.btn_ac_stop.config(state="disabled")

    def _ac_check_done(self):
        if ac_running:
            self.after(300, self._ac_check_done)
        else:
            self.btn_ac_start.config(state="normal")
            self.btn_ac_stop.config(state="disabled")

    def _mac_start_rec(self):
        global mac_recording, mac_events, mac_start_t
        if mac_recording or mac_playing:
            return
        mac_events = []
        mac_start_t = time.time()
        mac_recording = True
        self.mac_status.set("Enregistrement en cours...")
        self.btn_rec.config(state="disabled")
        self.btn_stop_rec.config(state="normal")
        self._mac_poll()

    def _mac_poll(self):
        if mac_recording:
            self.mac_count.set(f"Actions enregistrees : {len(mac_events)}")
            self.after(200, self._mac_poll)

    def _mac_stop_rec(self):
        global mac_recording
        mac_recording = False
        self.btn_rec.config(state="normal")
        self.btn_stop_rec.config(state="disabled")
        self.mac_count.set(f"Actions enregistrees : {len(mac_events)}")
        self.mac_status.set(f"Enregistrement termine - {len(mac_events)} actions")

    def _mac_start_play(self):
        global mac_playing, mac_play_thread
        if mac_playing or mac_recording:
            return
        if not mac_events:
            messagebox.showwarning("Vide", "Aucune macro.\nFais un enregistrement d'abord.")
            return
        mac_stop.clear()
        mac_playing = True
        self.btn_play.config(state="disabled")
        self.btn_stop_play.config(state="normal")
        mac_play_thread = threading.Thread(
            target=_play_loop,
            args=(list(mac_events), self.mac_loops.get(),
                  self.mac_speed.get(), self.mac_delay.get(), self.mac_status),
            daemon=True,
        )
        mac_play_thread.start()
        self.after(400, self._mac_check_done)

    def _mac_check_done(self):
        if mac_playing:
            self.after(300, self._mac_check_done)
        else:
            self.btn_play.config(state="normal")
            self.btn_stop_play.config(state="disabled")

    def _mac_stop_play(self):
        mac_stop.set()
        self.btn_play.config(state="normal")
        self.btn_stop_play.config(state="disabled")
        self.mac_status.set("Lecture arretee")

    def _mac_save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Macro JSON", "*.json")],
            initialdir=MACROS_DIR, title="Sauvegarder")
        if path:
            with open(path, "w") as f:
                json.dump(mac_events, f, indent=2)
            self.mac_status.set(f"Sauvegarde : {os.path.basename(path)}")

    def _mac_load(self):
        global mac_events
        path = filedialog.askopenfilename(
            filetypes=[("Macro JSON", "*.json")], initialdir=MACROS_DIR, title="Charger")
        if path:
            with open(path) as f:
                mac_events = json.load(f)
            self.mac_count.set(f"Actions enregistrees : {len(mac_events)}")
            self.mac_status.set(f"Charge : {os.path.basename(path)}")

    def _mac_clear(self):
        global mac_events
        if messagebox.askyesno("Effacer", "Effacer la macro ?"):
            mac_events = []
            self.mac_count.set("Actions enregistrees : 0")
            self.mac_status.set("Macro effacee")

    def _on_close(self):
        mac_stop.set()
        ac_stop.set()
        mouse_listener.stop()
        kb_listener.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
