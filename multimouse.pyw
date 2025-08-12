# -*- coding: utf-8 -*-
"""
multimouse.pyw - MultiMouse hoofdmenu + AutoSnap + AutoMouse (gereviseerd)

Wijzigingen (aug 2025):
- Sampler op 10 ms (0.01s).
- Start/stop opname met globale Insert (ESC stopt ook), ongeacht focus/andere toetsen.
- Hoofdmenu verbergen wanneer AutoMouse/AutoSnap open is; terug na sluiten.
- Tekstaanpassingen: 'playing' -> 'play', geen '...', 'Bezig - druk op ESC om te stoppen',
  'After-Send' -> 'Send to', 'Verzend' -> 'Send'.
- Iconen via ./icons (PNG). Meldingen via statuslabel.
- Donker/licht-modus toggle met ttkbootstrap (darkly/flatly) of eenvoudige Tk fallback.
"""

import os
import sys
import json
import time
import threading
import ctypes
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

# Probeer ttkbootstrap (mooi dark theme); val terug op Tk/ttk als niet aanwezig
try:
    import ttkbootstrap as tb
except ImportError:
    tb = None

import pyautogui
from pynput import keyboard, mouse
from pynput.keyboard import Key

pyautogui.FAILSAFE = False

# ---------------------------
# Windows: taakbalk-icoon fix
# ---------------------------
def set_app_user_model_id(id_str="com.overweel.multimouse"):
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(id_str)
        except Exception:
            pass

set_app_user_model_id("com.overweel.multimouse")

# ---------------------------
# Bestandslocaties (OneDrive)
# ---------------------------
def one_drive_documents_dir() -> Path:
    od = os.environ.get("OneDrive") or os.environ.get("ONE_DRIVE") or ""
    if od:
        p = Path(od) / "Documents"
        if p.exists():
            return p
    up = os.environ.get("UserProfile") or os.path.expanduser("~")
    p2 = Path(up) / "OneDrive" / "Documents"
    if p2.exists():
        return p2
    return Path(os.path.expanduser("~/Documents"))

DOCS_BASE = one_drive_documents_dir()
MULTIMOUSE_DIR = DOCS_BASE / "Multimouse"
AUTOSNAP_DIR = MULTIMOUSE_DIR / "AutoSnap"
AUTOMOUSE_DIR = MULTIMOUSE_DIR / "AutoMouse"
for d in (MULTIMOUSE_DIR, AUTOSNAP_DIR, AUTOMOUSE_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------
# App iconen (.ico) per venster (naast script plaatsen)
# ---------------------------
APP_ICON_MM = "inputmouse_92614.ico"                   # hoofdmenu + AutoMouse
APP_ICON_SNAP = "snapchat_black_logo_icon_147080.ico"  # AutoSnap

# ---------------------------
# Button iconen (PNG) map  —> vervangingen
# ---------------------------
ICONS_DIR = Path(__file__).parent / "icons"
ICON_FILES = {
    "record": "button.png",
    "open": "folder.png",
    "mouse": "mouse.png",
    "camera": "photo-camera-interface-symbol-for-button.png",
    "play": "play-button-arrowhead.png",
    "send": "send.png",
    "stop": "stop-button.png",
    "users": "user.png",
}

# ---------------------------
# i18n (EN default)
# ---------------------------
LANGS = {
    "en": {
        "app_title": "MultiMouse",
        "autosnap": "AutoSnap",
        "automouse": "AutoMouse",
        "open_autosnap": "Open AutoSnap",
        "open_automouse": "Open AutoMouse",
        "settings": "Settings",
        "people": "Select people",
        "recalibrate": "Recalibrate",
        "count": "Play count",
        "until_closed": "Until program closed",
        "delay": "Delay between runs (seconds)",
        "start": "Start Automation",
        "back": "Back",
        "record_new": "New recording",
        "open_record": "Open recording",
        "status_busy": "Busy - press ESC to stop",
        "status_done": "Done",
        "status_stopped": "Stopped",
        "status_saved": "Saved",
        "recording": "Recording",
        "recording_stopped": "Recording stopped",
        "playback": "Play",
        "playback_done": "Play finished",
        "error_calib": "You must calibrate first.",
        "saved": "Saved",
        "calib_title": "Calibration",
        "move_mouse_to": "Move your mouse to:\n{target}",
        "stop_hint": "Press INSERT (or ESC) to stop recording",
        "start_hint": "Press INSERT to start recording",
        "dark_mode": "Dark mode",
        "language": "Language",
        "english": "English",
        "dutch": "Dutch",
        "play_delay": "Delay between repeats (seconds)",
        "press_insert_to_start": "Press INSERT to start (ESC to cancel)",
        "press_insert_or_esc_to_stop": "Recording - press INSERT or ESC to stop",
        "waiting_for_insert": "Waiting for INSERT",
        "send_to": "Send to",
        "send": "Send",
    },
    "nl": {
        "app_title": "MultiMouse",
        "autosnap": "AutoSnap",
        "automouse": "AutoMouse",
        "open_autosnap": "Open AutoSnap",
        "open_automouse": "Open AutoMouse",
        "settings": "Instellingen",
        "people": "Kies personen",
        "recalibrate": "Recalibreren",
        "count": "Aantal keer afspelen",
        "until_closed": "Tot programma sluiten",
        "delay": "Delay tussen herhalingen (seconden)",
        "start": "Start automatisering",
        "back": "Terug",
        "record_new": "Nieuwe opname",
        "open_record": "Open opname",
        "status_busy": "Bezig - druk op ESC om te stoppen",
        "status_done": "Klaar",
        "status_stopped": "Gestopt",
        "status_saved": "Opgeslagen",
        "recording": "Opnemen",
        "recording_stopped": "Opname gestopt",
        "playback": "Play",
        "playback_done": "Play voltooid",
        "error_calib": "Je moet eerst kalibreren.",
        "saved": "Opgeslagen",
        "calib_title": "Kalibratie",
        "move_mouse_to": "Beweeg je muis naar:\n{target}",
        "stop_hint": "Druk op INSERT (of ESC) om opname te stoppen",
        "start_hint": "Druk op INSERT om opname te starten",
        "dark_mode": "Donkere modus",
        "language": "Taal",
        "english": "Engels",
        "dutch": "Nederlands",
        "play_delay": "Delay tussen herhalingen (seconden)",
        "press_insert_to_start": "Druk op INSERT om te starten (ESC annuleert)",
        "press_insert_or_esc_to_stop": "Opnemen - druk INSERT of ESC om te stoppen",
        "waiting_for_insert": "Wachten op INSERT",
        "send_to": "Send to",
        "send": "Send",
    }
}
CURRENT_LANG = "en"

def tr(key, **kwargs):
    txt = LANGS.get(CURRENT_LANG, LANGS["en"]).get(key, key)
    return txt.format(**kwargs) if kwargs else txt

# ---------------------------
# Toast (alleen gebruikt door AutoSnap; AutoMouse gebruikt statuslabel)
# ---------------------------
def toast(parent, title, message, timeout=2000):
    top = tk.Toplevel(parent)
    top.title(title)
    top.attributes("-topmost", True)
    top.resizable(False, False)
    frm = ttk.Frame(top, padding=12)
    frm.pack(fill="both", expand=True)
    ttk.Label(frm, text=message, font=("Segoe UI", 10)).pack()
    top.update_idletasks()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    tw, th = top.winfo_width(), top.winfo_height()
    top.geometry(f"+{px + (pw - tw)//2}+{py + (ph - th)//2}")
    top.after(timeout, top.destroy)
    return top

# ---------------------------
# AutoSnap config
# ---------------------------
AUTOSNAP_CONFIG_FILE = AUTOSNAP_DIR / "muis_config.json"
DEFAULT_SNAP_CONFIG = {
    "foto1": None,
    "foto2": None,
    "verstuur_na_foto": None,
    "personen": [None] * 8,
    "verzend": None
}

def load_snap_config():
    if AUTOSNAP_CONFIG_FILE.exists():
        try:
            return json.loads(AUTOSNAP_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_SNAP_CONFIG.copy()

def save_snap_config(cfg):
    AUTOSNAP_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# ---------------------------
# Recorder / Player
# ---------------------------
class Recorder:
    """
    Legt vast:
    - muispositie elke 10 ms (type: pos)
    - muisklikken/scroll (down/up/scroll) met tijdstempel
    - toetsen (key_down / key_up) met tijdstempel
    """
    SAMPLE_INTERVAL = 0.01  # 10 ms

    def __init__(self):
        self.events = []
        self.start_time = None
        self.running = False
        self._lock = threading.Lock()
        self._kl = None
        self._ml = None
        self._sampler = None

    def _t(self):
        return time.perf_counter() - self.start_time

    # keyboard
    def _on_key_press(self, key):
        if not self.running: return
        key_name, special = self._key_to_name(key)
        with self._lock:
            self.events.append({"t": self._t(), "type": "key_down", "key": key_name, "special": special})

    def _on_key_release(self, key):
        if not self.running: return
        key_name, special = self._key_to_name(key)
        with self._lock:
            self.events.append({"t": self._t(), "type": "key_up", "key": key_name, "special": special})

    # mouse
    def _on_click(self, x, y, button, pressed):
        if not self.running: return
        btn = getattr(button, "name", str(button)).replace("Button.", "")
        with self._lock:
            self.events.append({"t": self._t(), "type": "mouse_down" if pressed else "mouse_up", "button": btn})

    def _on_scroll(self, x, y, dx, dy):
        if not self.running: return
        with self._lock:
            self.events.append({"t": self._t(), "type": "scroll", "dx": dx, "dy": dy})

    def _sample_positions(self):
        import pyautogui
        next_time = time.perf_counter()
        while self.running:
            try:
                x, y = pyautogui.position()
                with self._lock:
                    self.events.append({"t": self._t(), "type": "pos", "x": int(x), "y": int(y)})
            except Exception:
                pass
            # strakke 10ms timing
            next_time += self.SAMPLE_INTERVAL
            delay = next_time - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            else:
                # ingehaald: reset referentie
                next_time = time.perf_counter()

    @staticmethod
    def _key_to_name(key):
        if hasattr(key, "char") and key.char is not None:
            return key.char, False
        name = getattr(key, "name", str(key))
        if name.startswith("Key."):
            name = name.split(".", 1)[1]
        return name, True

    def start(self):
        if self.running: return
        self.events = []
        self.start_time = time.perf_counter()
        self.running = True
        self._kl = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        self._ml = mouse.Listener(on_click=self._on_click, on_scroll=self._on_scroll)
        self._kl.start(); self._ml.start()
        self._sampler = threading.Thread(target=self._sample_positions, daemon=True)
        self._sampler.start()

    def stop(self):
        if not self.running: return
        self.running = False
        try:
            if self._kl: self._kl.stop()
            if self._ml: self._ml.stop()
        except Exception:
            pass
        self._kl = None
        self._ml = None

    def save(self, filepath: Path):
        self.events.sort(key=lambda e: e.get("t", 0.0))
        filepath.write_text(json.dumps(self.events, indent=2), encoding="utf-8")


class Player:
    """
    Speelt events exact op tijd af (geen speed-up).
    ESC tijdens afspelen stopt meteen (geen false positives bij afgespeelde ESC).
    """
    def __init__(self, events):
        self.events = sorted(events or [], key=lambda e: e.get("t", 0.0))
        self._stop = threading.Event()
        self._esc_listener = None
        self._ignore_esc = False

    def stop(self):
        self._stop.set()

    @staticmethod
    def _key_from_name(name, special):
        if special:
            try:
                return getattr(Key, name)
            except Exception:
                return None
        return name

    def _on_esc_press(self, key):
        if key == Key.esc:
            if self._ignore_esc:
                return None
            self._stop.set()
            return False
        return None

    def play(self):
        if not self.events:
            return
        import pyautogui
        self._esc_listener = keyboard.Listener(on_press=self._on_esc_press)
        self._esc_listener.start()

        last_t = 0.0
        try:
            for ev in self.events:
                if self._stop.is_set():
                    break
                t = ev.get("t", 0.0)
                wait_for = t - last_t
                if wait_for > 0:
                    if self._stop.wait(wait_for):
                        break

                et = ev["type"]
                if et == "pos":
                    try: pyautogui.moveTo(ev["x"], ev["y"])
                    except Exception: pass
                elif et == "mouse_down":
                    btn = ev.get("button", "left")
                    try: pyautogui.mouseDown(button=btn)
                    except Exception: pass
                elif et == "mouse_up":
                    btn = ev.get("button", "left")
                    try: pyautogui.mouseUp(button=btn)
                    except Exception: pass
                elif et == "scroll":
                    dy = int(ev.get("dy", 0)); dx = int(ev.get("dx", 0))
                    try:
                        if dy: pyautogui.scroll(dy)
                        if dx:
                            try: pyautogui.hscroll(dx)
                            except Exception: pass
                    except Exception: pass
                elif et in ("key_down", "key_up"):
                    keyname = ev.get("key"); special = ev.get("special", False)
                    keyobj = self._key_from_name(keyname, special)
                    try:
                        if et == "key_down":
                            if special and keyobj == Key.esc:
                                self._ignore_esc = True
                            if isinstance(keyobj, str): pyautogui.keyDown(keyobj)
                            else: keyboard.Controller().press(keyobj)
                        else:
                            if isinstance(keyobj, str): pyautogui.keyUp(keyobj)
                            else: keyboard.Controller().release(keyobj)
                            if special and keyobj == Key.esc:
                                time.sleep(0.05); self._ignore_esc = False
                    except Exception:
                        if et == "key_down" and isinstance(keyobj, str) and len(keyobj) == 1:
                            try: pyautogui.typewrite(keyobj)
                            except Exception: pass
                last_t = t
        finally:
            try:
                if self._esc_listener: self._esc_listener.stop()
            except Exception:
                pass

# ---------------------------
# Icon helpers (PNG)
# ---------------------------
def set_window_icon(win: tk.Tk, ico_path: str):
    try:
        if ico_path and Path(ico_path).exists() and ico_path.lower().endswith((".png", ".gif")):
            img = Image.open(ico_path)
            tkimg = ImageTk.PhotoImage(img)
            win.iconphoto(True, tkimg)
            win._icon_ref = tkimg
            return
    except Exception:
        pass
    try:
        if ico_path and Path(ico_path).exists():
            win.iconbitmap(ico_path)
    except Exception:
        pass

def load_png_by_key(key: str, size: int = 18):
    fname = ICON_FILES.get(key)
    if not fname:
        return None
    p = ICONS_DIR / fname
    if not p.exists():
        return None
    img = Image.open(p).convert("RGBA")
    if size:
        img = img.resize((size, size), Image.LANCZOS)
    return ImageTk.PhotoImage(img)

# ---------------------------
# Kalibratie dialoog (AutoSnap)
# ---------------------------
def calibrate_position(root: tk.Tk, target_label: str):
    top = tk.Toplevel(root)
    top.title(tr("calib_title"))
    top.attributes("-topmost", True)
    top.resizable(False, False)
    set_window_icon(top, APP_ICON_SNAP)

    frm = ttk.Frame(top, padding=16)
    frm.pack(fill="both", expand=True)

    lbl = ttk.Label(frm, text=tr("move_mouse_to", target=target_label), font=("Segoe UI", 12))
    lbl.pack(pady=(0, 8))

    timer_lbl = ttk.Label(frm, text="", font=("Segoe UI", 28, "bold"))
    timer_lbl.pack()

    result = {"pos": None}

    def countdown(n=3):
        if n <= 0:
            x, y = pyautogui.position()
            result["pos"] = (int(x), int(y))
            top.destroy()
        else:
            timer_lbl.config(text=str(n))
            top.after(1000, lambda: countdown(n - 1))

    top.after(100, countdown)
    top.grab_set()
    root.wait_window(top)
    return result["pos"]

# ---------------------------
# Vensters
# ---------------------------
class AutoSnapWindow(tk.Toplevel):
    def __init__(self, master, get_lang, set_lang):
        super().__init__(master)
        self.get_lang = get_lang
        self.set_lang = set_lang
        self.title(tr("autosnap"))
        set_window_icon(self, APP_ICON_SNAP)
        self.geometry("680x720")
        self.resizable(True, True)
        self.attributes("-topmost", True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.cfg = load_snap_config()

        self.person_vars = [tk.BooleanVar(value=True) for _ in range(8)]
        self.status_var = tk.StringVar(value="")
        self.count_var = tk.IntVar(value=1)
        self.until_var = tk.BooleanVar(value=False)
        self.delay_var = tk.DoubleVar(value=1.0)

        self._build_ui()

    def _build_ui(self):
        wrap = ttk.Frame(self, padding=20)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.columnconfigure(0, weight=1)

        header = ttk.Label(wrap, text=tr("autosnap"), font=("Segoe UI", 20, "bold"))
        header.grid(row=0, column=0, pady=(0, 16))

        # calibration group
        calib = ttk.LabelFrame(wrap, text=tr("recalibrate"), padding=12)
        calib.grid(row=1, column=0, sticky="ew", pady=8)
        calib.columnconfigure(0, weight=1)

        cam_ic = load_png_by_key("camera", 18)
        users_ic = load_png_by_key("users", 18)
        send_ic = load_png_by_key("send", 18)

        row = ttk.Frame(calib)
        row.grid(row=0, column=0, sticky="ew", pady=6)
        for i in range(3):
            row.columnconfigure(i, weight=1)
        ttk.Button(row, text=" Foto 1", image=cam_ic, compound="left",
                   command=lambda: self._calib_key("foto1", "Foto knop 1")).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(row, text=" Foto 2", image=cam_ic, compound="left",
                   command=lambda: self._calib_key("foto2", "Foto knop 2")).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(row, text=" " + tr("send_to"), image=send_ic, compound="left",
                   command=lambda: self._calib_key("verstuur_na_foto", tr("send_to"))).grid(row=0, column=2, padx=6, sticky="ew")

        row2 = ttk.Frame(calib)
        row2.grid(row=1, column=0, sticky="ew", pady=6)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)
        ttk.Button(row2, text=" Personen", image=users_ic, compound="left",
                   command=self._calib_people).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(row2, text=" " + tr("send"), image=send_ic, compound="left",
                   command=lambda: self._calib_key("verzend", tr("send"))).grid(row=0, column=1, padx=6, sticky="ew")

        # people selection
        pf = ttk.LabelFrame(wrap, text=tr("people"), padding=12)
        pf.grid(row=2, column=0, sticky="ew", pady=8)
        for c in range(4): pf.columnconfigure(c, weight=1)
        for i in range(8):
            ttk.Checkbutton(pf, text=f"Person {i+1}", variable=self.person_vars[i]) \
                .grid(row=i // 4, column=i % 4, padx=8, pady=6, sticky="w")

        # settings
        sf = ttk.LabelFrame(wrap, text=tr("settings"), padding=12)
        sf.grid(row=3, column=0, sticky="ew", pady=8)
        for c in range(4): sf.columnconfigure(c, weight=1)

        ttk.Label(sf, text=tr("count")).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.count_var, width=10).grid(row=0, column=1, padx=8, pady=6, sticky="ew")

        ttk.Checkbutton(sf, text=tr("until_closed"), variable=self.until_var)\
            .grid(row=0, column=2, columnspan=2, sticky="w", padx=8, pady=6)

        ttk.Label(sf, text=tr("delay")).grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.delay_var, width=10).grid(row=1, column=1, padx=8, pady=6, sticky="ew")

        # start
        play_ic = load_png_by_key("play", 18)
        ttk.Button(wrap, text=" " + tr("start"), image=play_ic, compound="left", command=self._start) \
            .grid(row=4, column=0, pady=12, sticky="ew")

        # status
        self.status_lbl = ttk.Label(wrap, textvariable=self.status_var, font=("Segoe UI", 10, "italic"))
        self.status_lbl.grid(row=5, column=0, sticky="w")

        self._img_refs = [cam_ic, users_ic, send_ic, play_ic]

    def _calib_key(self, key, label_text):
        pos = calibrate_position(self, label_text)
        if pos:
            self.cfg[key] = pos
            save_snap_config(self.cfg)
            toast(self, tr("saved"), f"{label_text} -> {pos}", timeout=2000)

    def _calib_people(self):
        for i in range(8):
            pos = calibrate_position(self, f"Persoon {i+1}")
            if not pos:
                break
            self.cfg["personen"][i] = pos
            save_snap_config(self.cfg)
        toast(self, tr("saved"), "Personenposities opgeslagen", timeout=2000)

    def _start(self):
        if not all([self.cfg.get("foto1"), self.cfg.get("foto2"), self.cfg.get("verstuur_na_foto"), self.cfg.get("verzend")]):
            messagebox.showerror(tr("error_calib"), tr("error_calib"))
            return
        persons = [i for i, v in enumerate(self.person_vars) if v.get()]
        count = self.count_var.get()
        endless = self.until_var.get()
        delay = self.delay_var.get()
        threading.Thread(target=self._run, args=(persons, count, endless, delay), daemon=True).start()

    def _run(self, persons, count, endless, delay):
        def click(pos):
            x, y = pos
            pyautogui.moveTo(x, y)
            pyautogui.click()
        self.status_var.set(tr("status_busy"))
        try:
            while endless or count > 0:
                click(tuple(self.cfg["foto1"]))
                time.sleep(5.0)
                click(tuple(self.cfg["foto2"]))
                time.sleep(0.5)
                click(tuple(self.cfg["verstuur_na_foto"]))
                time.sleep(0.5)
                for idx in persons:
                    p = self.cfg["personen"][idx]
                    if p:
                        click(tuple(p)); time.sleep(0.5)
                click(tuple(self.cfg["verzend"]))
                if not endless:
                    count -= 1
                time.sleep(delay)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.status_var.set(tr("status_done"))

class AutoMouseWindow(tk.Toplevel):
    def __init__(self, master, get_lang, set_lang):
        super().__init__(master)
        self.get_lang = get_lang
        self.set_lang = set_lang
        self.title(tr("automouse"))
        set_window_icon(self, APP_ICON_MM)
        self.geometry("720x520")
        self.resizable(True, True)
        self.attributes("-topmost", True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.recorder = Recorder()
        self.player = None

        # UI state
        self.status_var = tk.StringVar(value=tr("status_done"))
        self.count_var = tk.IntVar(value=1)
        self.until_var = tk.BooleanVar(value=False)
        self.play_delay_var = tk.DoubleVar(value=0.0)

        self._build_ui()

    def _set_status(self, kind: str):
        mapping = {
            "busy": tr("status_busy"),
            "done": tr("status_done"),
            "stopped": tr("status_stopped"),
            "saved": tr("status_saved"),
        }
        self.status_var.set(mapping.get(kind, kind))

    # -------- globale key-wacht helper ----------
    @staticmethod
    def _wait_for_global_key(target_keys=(Key.insert,), allow_esc=True, tick_ui=None):
        """
        Wacht blokkerend tot een van de target_keys is ingedrukt (globaal, via pynput).
        Keert terug met de Key of string 'esc' indien ESC en allow_esc=True.
        tick_ui: optionele callable die in de wachtlus aangeroepen wordt om UI responsief te houden.
        """
        evt = threading.Event()
        result = {"val": None}

        def on_press(k):
            try:
                if isinstance(k, Key):
                    if k in target_keys:
                        result["val"] = k
                        evt.set()
                        return False
                    if allow_esc and k == Key.esc:
                        result["val"] = "esc"
                        evt.set()
                        return False
            except Exception:
                pass
            return None

        lis = keyboard.Listener(on_press=on_press)
        lis.start()
        try:
            while not evt.is_set():
                if tick_ui:
                    tick_ui()
                time.sleep(0.01)
        finally:
            try:
                lis.stop()
            except Exception:
                pass
        return result["val"]

    def _build_ui(self):
        wrap = ttk.Frame(self, padding=20)
        wrap.grid(row=0, column=0, sticky="nsew")
        for r in range(6):
            wrap.rowconfigure(r, weight=0)
        wrap.columnconfigure(0, weight=1)
        wrap.columnconfigure(1, weight=1)

        header = ttk.Label(wrap, text=tr("automouse"), font=("Segoe UI", 20, "bold"))
        header.grid(row=0, column=0, columnspan=2, pady=(0, 16), sticky="w")

        rec_ic = load_png_by_key("record", 18)
        play_ic = load_png_by_key("play", 18)
        open_ic = load_png_by_key("open", 18)
        stop_ic = load_png_by_key("stop", 18)
        save_ic = load_png_by_key("send", 18)

        row = ttk.Frame(wrap)
        row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=6)
        for c in range(5):
            row.columnconfigure(c, weight=1)

        ttk.Button(row, text=" " + tr("record_new"), image=rec_ic, compound="left",
                   command=self._record).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(row, text=" " + tr("open_record"), image=open_ic, compound="left",
                   command=self._open).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.play_btn = ttk.Button(row, text=" " + tr("playback"), image=play_ic, compound="left",
                                   command=self._play, state="disabled")
        self.play_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        self.stop_btn = ttk.Button(row, text=" Stop", image=stop_ic, compound="left",
                                   command=self._stop_play, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        self.save_btn = ttk.Button(row, text=" " + tr("saved"), image=save_ic, compound="left",
                                   command=self._save, state="disabled")
        self.save_btn.grid(row=0, column=4, padx=6, pady=6, sticky="ew")

        # settings
        sf = ttk.LabelFrame(wrap, text=tr("settings"), padding=12)
        sf.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        for c in range(6):
            sf.columnconfigure(c, weight=1)

        ttk.Label(sf, text=tr("count")).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.count_var, width=10).grid(row=0, column=1, padx=8, pady=6, sticky="ew")

        ttk.Checkbutton(sf, text=tr("until_closed"), variable=self.until_var) \
            .grid(row=0, column=2, columnspan=2, sticky="w", padx=8, pady=6)

        ttk.Label(sf, text=tr("play_delay")).grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.play_delay_var, width=10).grid(row=1, column=1, padx=8, pady=6, sticky="ew")

        # status
        self.status_lbl = ttk.Label(wrap, textvariable=self.status_var, font=("Segoe UI", 11, "bold"))
        self.status_lbl.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self._img_refs = [rec_ic, play_ic, open_ic, stop_ic, save_ic]

    # ---- AutoMouse acties ----
    def _record(self):
        # bestandsnaam voorstellen
        fname = time.strftime("record_%Y%m%d_%H%M%S.json")
        path = filedialog.asksaveasfilename(
            initialdir=str(AUTOMOUSE_DIR),
            defaultextension=".json",
            initialfile=fname,
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return

        # 1) Wachten op INSERT om te starten (globaal)
        self._set_status("busy")
        self.status_var.set(tr("waiting_for_insert"))
        key = self._wait_for_global_key(target_keys=(Key.insert,), allow_esc=True, tick_ui=self.update)
        if key == "esc":
            self._set_status("done")
            return

        # 2) Start Recorder
        try:
            self.recorder.start()
        except Exception as e:
            messagebox.showerror("Recorder error", str(e))
            self._set_status("done")
            return

        self.status_var.set(tr("press_insert_or_esc_to_stop"))

        # 3) Wachten op INSERT of ESC om te stoppen (globaal)
        _ = self._wait_for_global_key(target_keys=(Key.insert,), allow_esc=True, tick_ui=self.update)

        # 4) Stop & Save
        self.recorder.stop()
        try:
            self.recorder.save(Path(path))
            self._set_status("saved")
        except Exception:
            self._set_status("done")

        # enable knoppen
        self.play_btn.config(state="normal")
        self.save_btn.config(state="normal")

    def _open(self):
        path = filedialog.askopenfilename(initialdir=str(AUTOMOUSE_DIR), filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            events = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(events, list):
                raise ValueError("Invalid file")
            self.recorder.events = events
            self._set_status("done")
            self.play_btn.config(state="normal")
            self.save_btn.config(state="normal")
        except Exception:
            self.recorder.events = []
            self._set_status("done")

    def _save(self):
        if not self.recorder.events:
            return
        path = filedialog.asksaveasfilename(initialdir=str(AUTOMOUSE_DIR),
                                            defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.recorder.events, indent=2), encoding="utf-8")
            self._set_status("saved")
        except Exception:
            self._set_status("done")

    def _play(self):
        if not self.recorder.events:
            return
        count = self.count_var.get()
        endless = self.until_var.get()
        play_delay = self.play_delay_var.get()

        self._set_status("busy")
        self.play_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        def loop():
            nonlocal count
            try:
                while endless or count > 0:
                    self.player = Player(self.recorder.events)
                    self.player.play()
                    if self.player._stop.is_set():
                        break
                    if play_delay > 0:
                        wait_flag = threading.Event()
                        if wait_flag.wait(play_delay):
                            break
                    if not endless:
                        count -= 1
            finally:
                self.stop_btn.config(state="disabled")
                self.play_btn.config(state="normal")
                if self.player and self.player._stop.is_set():
                    self._set_status("stopped")
                else:
                    self._set_status("done")

        threading.Thread(target=loop, daemon=True).start()

    def _stop_play(self):
        if self.player:
            self.player.stop()

# ---------------------------
# Hoofdmenu
# ---------------------------
class MultiMouseApp:
    def __init__(self):
        self.root = None
        self.style = None
        self.using_tb = tb is not None
        if self.using_tb:
            self.root = tb.Window(themename="darkly")
            self.style = tb.Style()
        else:
            self.root = tk.Tk()
            self.style = ttk.Style()
            try:
                self.style.theme_use("clam")
            except Exception:
                pass

        self.root.title(tr("app_title"))
        self.root.geometry("720x420")
        self.root.resizable(True, True)
        self.root.attributes("-topmost", True)
        set_window_icon(self.root, APP_ICON_MM)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.lang_var = tk.StringVar(value=CURRENT_LANG)
        self.dark_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._apply_theme(initial=True)

    def _build_ui(self):
        wrap = ttk.Frame(self.root, padding=16)
        wrap.grid(row=0, column=0, sticky="nsew")
        for c in range(2):
            wrap.columnconfigure(c, weight=1)

        logo_png = load_png_by_key("mouse", 64)
        if logo_png:
            logo = ttk.Label(wrap, image=logo_png)
            logo.image = logo_png
            logo.grid(row=0, column=0, columnspan=2, pady=(8, 6))

        title = ttk.Label(wrap, text=tr("app_title"), font=("Segoe UI", 22, "bold"))
        title.grid(row=1, column=0, columnspan=2, pady=(0, 14))

        cam_ic = load_png_by_key("camera", 24)
        mice_ic = load_png_by_key("mouse", 24)

        btn_autosnap = ttk.Button(wrap, text=" " + tr("open_autosnap"), image=cam_ic, compound="left",
                                  command=self.open_autosnap)
        btn_automouse = ttk.Button(wrap, text=" " + tr("open_automouse"), image=mice_ic, compound="left",
                                   command=self.open_automouse)

        btn_autosnap.grid(row=2, column=0, padx=10, pady=8, sticky="ew")
        btn_automouse.grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        bar = ttk.Frame(wrap, padding=(6, 4))
        bar.grid(row=3, column=0, columnspan=2, pady=(8, 4), sticky="ew")
        for c in range(4):
            bar.columnconfigure(c, weight=1)

        small_font = ("Segoe UI", 8)

        ttk.Label(bar, text=tr("language"), font=small_font).grid(row=0, column=0, padx=4, sticky="e")
        lang = ttk.OptionMenu(bar, self.lang_var, self.lang_var.get(), "en", "nl", command=self._switch_lang)
        lang.grid(row=0, column=1, padx=4, sticky="w")
        try:
            lang["menu"].configure(font=small_font)
        except Exception:
            pass

        ttk.Label(bar, text=tr("dark_mode"), font=small_font).grid(row=0, column=2, padx=4, sticky="e")
        chk = ttk.Checkbutton(bar, variable=self.dark_var, command=self._apply_theme)
        chk.grid(row=0, column=3, padx=4, sticky="w")

        self._img_refs = [logo_png, cam_ic, mice_ic]

    def _switch_lang(self, val):
        global CURRENT_LANG
        CURRENT_LANG = val
        for w in list(self.root.children.values()):
            w.destroy()
        self._build_ui()
        self._apply_theme()

    def _apply_theme(self, initial=False):
        is_dark = bool(self.dark_var.get())
        if self.using_tb:
            target = "darkly" if is_dark else "flatly"
            try:
                self.style.theme_use(target)
            except Exception:
                pass
        else:
            bg = "#1e1e1e" if is_dark else "#f0f0f0"
            fg = "#f5f5f5" if is_dark else "#111111"
            try:
                self.root.configure(bg=bg)
            except Exception:
                pass
            try:
                self.style.configure(".", background=bg, foreground=fg)
                self.style.configure("TLabel", background=bg, foreground=fg)
                self.style.configure("TFrame", background=bg)
                self.style.configure("TButton", background=bg, foreground=fg)
                self.style.configure("TCheckbutton", background=bg, foreground=fg)
                self.style.configure("TLabelframe", background=bg, foreground=fg)
                self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
                self.style.map("TButton", foreground=[("disabled", "#888888")])
            except Exception:
                pass

    # --- helper om child venster modaal te tonen terwijl hoofdmenu verborgen is ---
    def _show_child_modal(self, child_window: tk.Toplevel):
        self.root.withdraw()
        def on_close():
            try:
                child_window.destroy()
            finally:
                self.root.deiconify()
        child_window.protocol("WM_DELETE_WINDOW", on_close)
        # wacht tot child sluit
        child_window.wait_window()
        # veiligheid: zorg dat hoofdmenu zichtbaar is
        self.root.deiconify()

    def open_autosnap(self):
        w = AutoSnapWindow(self.root, lambda: self.lang_var.get(), self._switch_lang)
        self._show_child_modal(w)

    def open_automouse(self):
        w = AutoMouseWindow(self.root, lambda: self.lang_var.get(), self._switch_lang)
        self._show_child_modal(w)

    def run(self):
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
        except Exception:
            pass
        self.root.mainloop()

# ---------------------------
# main
# ---------------------------
if __name__ == "__main__":
    try:
        app = MultiMouseApp()
        app.run()
    except KeyboardInterrupt:
        pass
