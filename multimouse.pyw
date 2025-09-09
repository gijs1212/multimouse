# -*- coding: utf-8 -*-
"""
MultiMouse - single file .pyw

Modules:
- AutoSnap (Sender, Responder, Combi redesigned)
- AutoMouse (record/play with ESC stop)
- AutoTikTok (upload flow)
"""

import os, sys, json, time, ctypes, threading, shutil, importlib
from pathlib import Path
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# search additional roaming site-packages on Windows (incl. Windows PE)
if sys.platform == "win32":
    candidates = []
    appdata = os.getenv("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Python" / "Python313" / "site-packages")
    for drive in ("C:", "X:"):
        for user in ("user", "Default"):
            candidates.append(Path(drive) / "Users" / user / "AppData" / "Roaming" / "Python" / "Python313" / "site-packages")
    for c in candidates:
        if c.exists() and str(c) not in sys.path:
            sys.path.insert(0, str(c))


def _fatal(msg: str):
    """Show a blocking error message and exit."""
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("MultiMouse", msg)
        root.destroy()
    except Exception:
        pass
    sys.exit(1)


def _require_module(name: str, pip_hint: str):
    """Import a module and show its location; exit if missing."""
    try:
        mod = importlib.import_module(name)
        path = getattr(mod, "__file__", "builtin")
        print(f"{name} -> {path}")
        return mod
    except ModuleNotFoundError as e:
        _fatal(f"{pip_hint} ontbreekt: {e}\nInstalleer met: pip install {pip_hint}")
    except Exception as e:
        _fatal(f"Fout bij importeren van {name}: {e}")

ctk = _require_module("customtkinter", "customtkinter")  # type: ignore
pyautogui = _require_module("pyautogui", "pyautogui pillow")  # type: ignore
try:
    from PIL import Image, ImageTk  # type: ignore
    print(f"Pillow -> {Image.__file__}")
except Exception as e:
    Image = ImageTk = None  # icon fallback wanneer Pillow ontbreekt
    print(f"Pillow ontbreekt: {e}")

pynput = _require_module("pynput", "pynput")  # type: ignore
from pynput import keyboard, mouse  # type: ignore
from pynput.keyboard import Key  # type: ignore

# -----------------------------------------------------------------------------
# Windows AUMID (taskbar grouping)
# -----------------------------------------------------------------------------
def set_app_user_model_id(id_str="com.gijs.multimouse"):
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(id_str)
        except Exception:
            pass
set_app_user_model_id("com.gijs.multimouse")

pyautogui.FAILSAFE = False
try:
    pyautogui.PAUSE = 0.5
    pyautogui.MINIMUM_DURATION = 0
    pyautogui.MINIMUM_SLEEP = 0
except Exception:
    pass

# -----------------------------------------------------------------------------
# Paths & icons
# -----------------------------------------------------------------------------
def BASE_PATH() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    try:
        return Path(__file__).parent
    except Exception:
        return Path(os.getcwd())

def res_path(*parts) -> str:
    return str(BASE_PATH().joinpath(*parts))

def one_drive_documents_dir() -> Path:
    od = os.environ.get("OneDrive") or os.environ.get("ONE_DRIVE") or ""
    if od:
        p = Path(od) / "Documents"
        if p.exists(): return p
    up = os.environ.get("UserProfile") or os.path.expanduser("~")
    p2 = Path(up) / "OneDrive" / "Documents"
    if p2.exists(): return p2
    return Path(os.path.expanduser("~/Documents"))

DOCS_BASE = one_drive_documents_dir()
BASE_DIR = DOCS_BASE / "Multimouse"
AUTOSNAP_DIR = BASE_DIR / "AutoSnap"
AUTOMOUSE_DIR = BASE_DIR / "AutoMouse"
AUTOTIKTOK_DIR = BASE_DIR / "AutoTikTok"
for d in (BASE_DIR, AUTOSNAP_DIR, AUTOMOUSE_DIR, AUTOTIKTOK_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Extra opslaglocatie voor gecombineerde instellingen
EXTRA_SAVE_DIR = Path("bestanden/multimouse/kalibratie")
EXTRA_SAVE_DIR.mkdir(parents=True, exist_ok=True)
EXTRA_SAVE_FILE = EXTRA_SAVE_DIR / "instellingen.txt"

# .ico bestanden naast dit .pyw
APP_ICON_MM = res_path("inputmouse_92614.ico")                  # muis icoon (hoofdmenu)
APP_ICON_SNAP = res_path("snapchat_black_logo_icon_147080.ico") # snapchat icoon
APP_ICON_TT  = res_path("tiktok_logo_icon_144802.ico")          # tiktok icoon

# Windows startup helper
def windows_startup_dir():
    if sys.platform != "win32":
        return None
    p = Path(os.getenv("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return p if p.exists() else None

def update_autosnap_startup(enable: bool):
    start_dir = windows_startup_dir()
    if not start_dir:
        return
    src = BASE_PATH() / "autosnap_startup.py"
    dst = start_dir / "autosnap_startup.py"
    try:
        if enable:
            shutil.copy(src, dst)
        else:
            if dst.exists():
                dst.unlink()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# i18n
# -----------------------------------------------------------------------------
LANGS = {
    "nl": {
        "app_title": "MultiMouse",
        "autosnap": "AutoSnap",
        "automouse": "AutoMouse",
        "autotiktok": "AutoTikTok",
        "open_autosnap": "Open AutoSnap",
        "open_automouse": "Open AutoMouse",
        "open_autotiktok": "Open AutoTikTok",
        "settings": "Instellingen",
        "people": "Kies personen",
        "recalibrate": "Kalibreren",
        "full_calibration": "Volledige kalibratie",
        "count": "Aantal keer afspelen",
        "until_closed": "Tot programma sluiten",
        "delay": "Delay tussen herhalingen (seconden)",
        "start": "Start automatisering",
        "record_new": "Nieuwe opname",
        "open_record": "Open opname",
        "status_busy": "Bezig - druk op ESC om te stoppen",
        "status_done": "Klaar",
        "status_stopped": "Gestopt",
        "status_saved": "Opgeslagen",
        "playback": "Afspelen",
        "error_calib": "Je moet eerst alle benodigde punten kalibreren.",
        "saved": "Opgeslagen",
        "calib_title": "Kalibratie",
        "move_mouse_to": "Beweeg je muis naar:\n{target}",
        "dark_mode": "Donkere modus",
        "language": "Taal",
        "save_settings": "Instellingen opslaan",
        "load_settings": "Instellingen laden",
        "loaded": "Ingeladen",
        "play_delay": "Delay tussen herhalingen (seconden)",
        "waiting_for_insert": "Wachten op INSERT",
        "press_insert_to_start": "Druk op INSERT om te starten (ESC annuleert)",
        "press_insert_or_esc_to_stop": "Opnemen - druk INSERT of ESC om te stoppen",
        "waiting_until": "Wachten tot {time}",
        "send_to": "Versturen 1 (Send To)",
        "send": "Versturen 2 (Verzend)",
        "schedule_enable": "Op tijden uitvoeren (dagelijks)",
        "schedule_time": "Tijd (UU:MM)",
        "add_time": "Toevoegen",
        "remove_time": "Verwijderen",
        "times": "Tijden",
        "times_people": "Tijden & personen",
        "mode": "Modus",
        "sender": "Sender",
        "responder": "Responder",
        "combi": "Combi",
        "badge_points": "Rode blokjes (1..8)",
        "recent_second": "Recent #2 (Send To)",
        "speed": "Snelheid",
        "start_responder": "Start Responder",
        "stop_responder": "Stop Responder",
        "start_combi": "Start Combi",
        "stop_combi": "Stop Combi",
        "send_reply": "Versturen reply",
        "close_snap": "Snap sluiten (X in viewer)",
        "close_before_reply": "Snap sluiten voor reactie",
        "restart_after_snaps": "Herstart na snaps",
        "restart_after_minutes": "Herstart na minuten",
        "searchbar": "Zoekbalk",
        "restart_close": "App sluiten (X rechtsboven)",
        "restart_search": "Zoekbalk (app starten)",
        "mini_msg": "Bezig — druk op ESC om te stoppen of wacht tot afgelopen",
        "combi_send_count": "Aantal verzenden (dagelijkse snaps)",
        "hourly_restart": "Elk uur app herstarten",
        "windows_startup": "Start bij Windows",
        "autoload_settings": "Instellingen automatisch laden bij start",
        "startup_settings_file": "Instellingenbestand bij start",
    },
    "en": {  # (not used now, but kept for completeness)
        "app_title": "MultiMouse",
        "autosnap": "AutoSnap",
        "automouse": "AutoMouse",
        "autotiktok": "AutoTikTok",
        "open_autosnap": "Open AutoSnap",
        "open_automouse": "Open AutoMouse",
        "open_autotiktok": "Open AutoTikTok",
        "settings": "Settings",
        "people": "Select people",
        "recalibrate": "Recalibrate",
        "full_calibration": "Full calibration",
        "count": "Play count",
        "until_closed": "Until program closed",
        "delay": "Delay between runs (seconds)",
        "start": "Start Automation",
        "record_new": "New recording",
        "open_record": "Open recording",
        "status_busy": "Busy - press ESC to stop",
        "status_done": "Done",
        "status_stopped": "Stopped",
        "status_saved": "Saved",
        "playback": "Play",
        "error_calib": "You must calibrate required points first.",
        "saved": "Saved",
        "calib_title": "Calibration",
        "move_mouse_to": "Move your mouse to:\n{target}",
        "dark_mode": "Dark mode",
        "language": "Language",
        "save_settings": "Save settings",
        "load_settings": "Load settings",
        "loaded": "Loaded",
        "play_delay": "Delay between repeats (seconds)",
        "waiting_for_insert": "Waiting for INSERT",
        "press_insert_to_start": "Press INSERT to start (ESC to cancel)",
        "press_insert_or_esc_to_stop": "Recording - press INSERT or ESC to stop",
        "waiting_until": "Waiting until {time}",
        "send_to": "Send To (step 1)",
        "send": "Send (final)",
        "schedule_enable": "Run at times (daily)",
        "schedule_time": "Time (HH:MM)",
        "add_time": "Add",
        "remove_time": "Remove",
        "times": "Times",
        "times_people": "Times & people",
        "mode": "Mode",
        "sender": "Sender",
        "responder": "Responder",
        "combi": "Combi",
        "badge_points": "Badge points (1..8)",
        "recent_second": "Recent #2 (Send To)",
        "speed": "Speed",
        "start_responder": "Start Responder",
        "stop_responder": "Stop Responder",
        "start_combi": "Start Combi",
        "stop_combi": "Stop Combi",
        "send_reply": "Send reply",
        "close_snap": "Close Snap (X)",
        "close_before_reply": "Close snap before reply",
        "restart_after_snaps": "Restart after snaps",
        "restart_after_minutes": "Restart after minutes",
        "searchbar": "Search bar",
        "restart_close": "Close app (X)",
        "restart_search": "Search bar (start app)",
        "mini_msg": "Busy — press ESC to stop or wait until finished",
        "combi_send_count": "Send count (daily snaps)",
        "hourly_restart": "Restart app every hour",
        "windows_startup": "Start with Windows",
        "autoload_settings": "Auto-load settings at startup",
        "startup_settings_file": "Startup settings file",
    }
}
CURRENT_LANG = "nl"
def tr(key, **kwargs):
    txt = LANGS.get(CURRENT_LANG, LANGS["nl"]).get(key, key)
    return txt.format(**kwargs) if kwargs else txt

# -----------------------------------------------------------------------------
# UI helpers & mini-mode
# -----------------------------------------------------------------------------
def set_window_icon(win: tk.Tk, ico_path: str):
    try:
        if ico_path and Path(ico_path).exists() and ico_path.lower().endswith(".ico"):
            win.iconbitmap(ico_path); return
        if ico_path and Path(ico_path).exists():
            img = Image.open(ico_path)
            tkimg = ImageTk.PhotoImage(img)
            win.iconphoto(True, tkimg)
            win._icon_ref = tkimg
    except Exception:
        pass

def toast(parent, title, message, timeout=2000):
    top = ctk.CTkToplevel(parent)
    top.title(title); top.attributes("-topmost", True); top.resizable(False, False)
    frm = ttk.Frame(top, padding=12); frm.pack(fill="both", expand=True)
    ttk.Label(frm, text=message, font=("Segoe UI", 10)).pack()
    top.update_idletasks()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    tw, th = top.winfo_width(), top.winfo_height()
    top.geometry(f"+{px + (pw - tw)//2}+{py + (ph - th)//2}")
    top.after(timeout, top.destroy)
    return top

def position_bottom_right(win: tk.Misc, w=460, h=130, margin=10):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x = max(0, sw - w - margin)
    y = max(0, sh - h - margin)
    win.geometry(f"{w}x{h}+{x}+{y}")

class EscListener:
    def __init__(self, on_esc):
        self._cb = on_esc
        self._lis = keyboard.Listener(on_press=self._on_press)
        self._lis.start()
    def _on_press(self, key):
        if key == Key.esc:
            try: self._cb()
            except Exception: pass
            return False
        return None
    def stop(self):
        try: self._lis.stop()
        except Exception: pass

class MiniMixin:
    def __init__(self):
        self._mini_prev_geom = None
        self._mini_prev_topmost = None
        self._esc_listener = None
        self._mini_banner = None
    def _enter_mini(self, stop_callback, banner_text=None):
        try:
            if self._esc_listener: self._esc_listener.stop()
        except Exception: pass
        self._mini_prev_geom = self.geometry()
        try: self._mini_prev_topmost = bool(self.attributes("-topmost"))
        except Exception: self._mini_prev_topmost = True
        position_bottom_right(self)
        try: self.attributes("-topmost", True)
        except Exception: pass
        if banner_text is None: banner_text = tr("mini_msg")
        if self._mini_banner is None or not self._mini_banner.winfo_exists():
            bar = ttk.Frame(self, padding=10)
            bar.place(relx=0, rely=0, relwidth=1, relheight=1)
            ttk.Label(bar, text=banner_text, font=("Segoe UI", 10, "bold"),
                      anchor="center", justify="center").pack(expand=True, fill="both")
            self._mini_banner = bar
        else:
            for w in self._mini_banner.winfo_children():
                if isinstance(w, ttk.Label): w.config(text=banner_text)
        self._esc_listener = EscListener(stop_callback)
    def _exit_mini(self):
        try:
            if self._mini_banner and self._mini_banner.winfo_exists():
                self._mini_banner.place_forget(); self._mini_banner.destroy()
        except Exception: pass
        self._mini_banner = None
        try:
            if self._mini_prev_geom: self.geometry(self._mini_prev_geom)
            if self._mini_prev_topmost is not None: self.attributes("-topmost", self._mini_prev_topmost)
        except Exception: pass
        try:
            if self._esc_listener: self._esc_listener.stop()
        except Exception: pass
        self._esc_listener = None

# --- kalibratie-mini helpers: bij afronden/onderbreken venster weer GROOT ---
def _enter_calibration_mini(win: tk.Tk, w=460, h=130, margin=10):
    prev = {"geom": None, "topmost": None, "state": None}
    try:
        prev["geom"] = win.geometry()
        prev["topmost"] = bool(win.attributes("-topmost"))
        prev["state"] = win.state()
    except Exception:
        pass
    try:
        if win.state() == "iconic": win.deiconify()
        win.state("normal")
        position_bottom_right(win, w=w, h=h, margin=margin)
        win.attributes("-topmost", True)
        win.update_idletasks()
    except Exception:
        pass
    return prev

def _exit_calibration_mini(win: tk.Tk, prev: dict | None):
    try:
        if prev and prev.get("topmost") is not None:
            win.attributes("-topmost", prev["topmost"])
        else:
            win.attributes("-topmost", False)
        if prev:
            if prev.get("state") == "zoomed":
                win.state("zoomed")
            elif prev.get("geom"):
                win.state("normal")
                win.geometry(prev["geom"])
            else:
                win.state("normal")
                sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
                ww, wh = min(1200, sw - 80), min(900, sh - 80)
                win.geometry(f"{ww}x{wh}+40+40")
        else:
            win.state("normal")
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            ww, wh = min(1200, sw - 80), min(900, sh - 80)
            win.geometry(f"{ww}x{wh}+40+40")
        win.deiconify()
        try:
            win.lift(); win.focus_force()
        except Exception:
            pass
        win.update_idletasks()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Time helpers
# -----------------------------------------------------------------------------
def parse_hhmm(s: str):
    s = (s or "").strip()
    if not s: return None
    try:
        hh, mm = s.split(":")
        hh = int(hh); mm = int(mm)
        if not (0 <= hh <= 23 and 0 <= mm <= 59): return None
        return f"{hh:02d}:{mm:02d}"
    except Exception:
        return None

def next_occurrence(hhmm: str) -> datetime:
    now = datetime.now()
    hh, mm = map(int, hhmm.split(":"))
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= now: target += timedelta(days=1)
    return target

def wait_until(dt: datetime, tick=lambda: None, cancel_evt=None):
    while True:
        if cancel_evt is not None and cancel_evt.is_set(): break
        if datetime.now() >= dt: break
        try: tick()
        except Exception: pass
        time.sleep(0.2)

# -----------------------------------------------------------------------------
# Color helpers (radius 20)
# -----------------------------------------------------------------------------
RADIUS_DEFAULT = 20

def _is_white(rgb, tol=25):
    if rgb is None: return False
    r,g,b = rgb; return r>255-tol and g>255-tol and b>255-tol

def _is_gray(rgb, tol=18):
    if rgb is None: return False
    r,g,b = rgb; return abs(r-g)<tol and abs(r-b)<tol and abs(g-b)<tol and 60<=r<=210

def _is_red(rgb, r_min=170, rg_diff=60, rb_diff=60):
    if rgb is None: return False
    r,g,b = rgb; return (r>=r_min) and (r-g>=rg_diff) and (r-b>=rb_diff)

def screenshot_region_center(x,y,radius):
    try:
        return pyautogui.screenshot(region=(max(0,x-radius), max(0,y-radius), radius*2+1, radius*2+1))
    except Exception:
        return None

def any_match_in_radius(x, y, predicate, radius=RADIUS_DEFAULT):
    img = screenshot_region_center(x,y,radius)
    if img is None: return False
    w, h = img.width, img.height
    for i in range(w):
        for j in range(h):
            if predicate(img.getpixel((i,j))): return True
    return False

def red_in_radius(x,y,radius=RADIUS_DEFAULT):   return any_match_in_radius(x,y,_is_red,radius)
def gray_in_radius(x,y,radius=RADIUS_DEFAULT):  return any_match_in_radius(x,y,_is_gray,radius)
def white_in_radius(x,y,radius=RADIUS_DEFAULT): return any_match_in_radius(x,y,_is_white,radius)

# -----------------------------------------------------------------------------
# AutoSnap (Sender/Responder/Combi)
# -----------------------------------------------------------------------------
AUTOSNAP_CONFIG_FILE = AUTOSNAP_DIR / "autosnap_config.json"
DEFAULT_SNAP_CONFIG = {
    # Sender
    "foto1": None, "foto2": None, "verstuur_na_foto": None, "personen": [None]*8, "verzend": None,
    # Responder/Combi
    "foto_reply": None,                   # Foto knop voor replies
    "verzend_reply": None,               # Verzendknop voor replies
    "responder_badges": [None]*8,         # rode blokjes
    "responder_close_snap": None,         # X in viewer
    "restart_close_app": None,            # App X (rechtsboven)
    "restart_searchbar": None,            # Zoekbalk
    "close_before_reply": False,
    "restart_after_snaps": 0,
    "restart_after_minutes": 0,
    "combi_times": [],                    # ["08:00","21:30",...]
    "combi_time_people": {},              # map tijd -> [bool x 8]
    "startup_enabled": False,
    "startup_send_snap": False,
    "boot_searchbar": None,
    "snapchat_shortcut": None,
    "action_delay": 0.5,
    "auto_load_settings": False,
    "auto_settings_file": None,
}

def load_snap_config():
    if AUTOSNAP_CONFIG_FILE.exists():
        try: return json.loads(AUTOSNAP_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return DEFAULT_SNAP_CONFIG.copy()

def save_snap_config(cfg):
    AUTOSNAP_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        path = None
        if cfg.get("auto_load_settings"):
            path = cfg.get("auto_settings_file")
        if not path and EXTRA_SAVE_FILE.exists():
            path = EXTRA_SAVE_FILE
        if path:
            p = Path(path)
            data = {}
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            data["autosnap"] = cfg
            p.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(data, indent=2)
            p.write_text(text, encoding="utf-8")
            if p != EXTRA_SAVE_FILE:
                EXTRA_SAVE_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass

# --- kalibratie dialoog (countdown 3->1) + mini-mode en restore groot ---
def calibrate_position_snap(root: ctk.CTk, target_label: str):
    prev_state = _enter_calibration_mini(root, w=460, h=130, margin=10)
    top = ctk.CTkToplevel(root)
    result = {"pos": None}
    def _close_interrupt():
        try: top.destroy()
        except Exception: pass
    try:
        top.title(tr("calib_title")); set_window_icon(top, APP_ICON_SNAP)
        top.attributes("-topmost", True); top.resizable(False, False)

        frm = ttk.Frame(top, padding=16); frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=tr("move_mouse_to", target=target_label), font=("Segoe UI", 12)).pack(pady=(0,8))
        timer_lbl = ttk.Label(frm, text="", font=("Segoe UI", 28, "bold")); timer_lbl.pack()

        # ESC of sluitkruis = onderbreken
        top.protocol("WM_DELETE_WINDOW", _close_interrupt)
        top.bind("<Escape>", lambda e: _close_interrupt())

        def countdown(n=3):
            if not top.winfo_exists(): return
            if n <= 0:
                x, y = pyautogui.position()
                result["pos"] = (int(x), int(y))
                try: top.destroy()
                except Exception: pass
            else:
                timer_lbl.config(text=str(n))
                top.after(1000, lambda: countdown(n-1))

        # centreer tov (nu kleine) hoofdvenster
        top.update_idletasks()
        pw, ph = root.winfo_width(), root.winfo_height()
        px, py = root.winfo_rootx(), root.winfo_rooty()
        tw, th = 380, 180
        x = px + max(0, (pw - tw)//2)
        y = py + max(0, (ph - th)//2)
        top.geometry(f"{tw}x{th}+{x}+{y}")

        top.after(100, countdown)
        top.grab_set()
        root.wait_window(top)
        return result["pos"]
    finally:
        _exit_calibration_mini(root, prev_state)

class AutoSnapWindow(ctk.CTkToplevel, MiniMixin):
    def __init__(self, master, get_lang, set_lang, save_combined, load_combined):
        ctk.CTkToplevel.__init__(self, master)
        MiniMixin.__init__(self)
        self.get_lang = get_lang; self.set_lang = set_lang
        self.save_combined = save_combined; self.load_combined = load_combined
        self.title(tr("autosnap")); set_window_icon(self, APP_ICON_SNAP)
        self.geometry("900x1040"); self.resizable(True, True); self.attributes("-topmost", True)

        self.cfg = load_snap_config()
        self.status_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="sender")
        self.startup_enabled = tk.BooleanVar(value=bool(self.cfg.get("startup_enabled")))
        self.startup_send_snap = tk.BooleanVar(value=bool(self.cfg.get("startup_send_snap")))
        self.action_delay_var = tk.DoubleVar(value=self.cfg.get("action_delay", 0.5))
        self.autoload_var = tk.BooleanVar(value=bool(self.cfg.get("auto_load_settings")))
        self.autoload_file_var = tk.StringVar(value=self.cfg.get("auto_settings_file", ""))
        self.autoload_file_var.trace_add("write", lambda *_: self._autoload_file_changed())
        self.snap_shortcut_var = tk.StringVar(value=self.cfg.get("snapchat_shortcut", ""))
        self.snap_shortcut_var.trace_add("write", lambda *_: self._snap_shortcut_changed())
        pyautogui.PAUSE = self.action_delay_var.get()
        self.action_delay_var.trace_add("write", lambda *_: self._apply_action_delay())
        self.settings_win = None

        # Sender state
        self.person_vars = [tk.BooleanVar(value=True) for _ in range(8)]
        self.count_var = tk.IntVar(value=1)
        self.until_var = tk.BooleanVar(value=False)
        self.delay_var = tk.DoubleVar(value=1.0)
        self.schedule_enabled = tk.BooleanVar(value=False)
        self.new_time_var = tk.StringVar(value="")
        self.times = self.cfg.get("combi_times", []).copy()  # hergebruik opslag
        self.time_people = self.cfg.get("combi_time_people", {}).copy()
        self.sender_running = threading.Event()
        self.sender_cancel_evt = threading.Event()
        self._sender_scheduler_thread = None

        # Responder/Combi state
        self.responder_running = threading.Event()
        self.combi_running = threading.Event()
        self.combi_schedule_enabled = tk.BooleanVar(value=True)
        self.combi_new_time_var = tk.StringVar(value="")
        self.combi_times = self.cfg.get("combi_times", []).copy()
        self.combi_time_people = self.cfg.get("combi_time_people", {}).copy()
        self.hourly_restart = tk.BooleanVar(value=False)  # kan aan/uit
        self.close_before_reply = tk.BooleanVar(value=bool(self.cfg.get("close_before_reply")))
        self.restart_after_snaps = tk.IntVar(value=int(self.cfg.get("restart_after_snaps", 0)))
        self.restart_after_minutes = tk.IntVar(value=int(self.cfg.get("restart_after_minutes", 0)))
        self._color_cooldown_until = 0.0
        self.ui_lock = threading.Lock()

        self._build_ui()
        update_autosnap_startup(self.startup_enabled.get())

    # ---------- helpers ----------
    def move_then_click(self, pos):
        """Beweeg naar positie, klik en wacht"""
        if not pos:
            return
        delay = self.action_delay_var.get()
        x, y = pos
        pyautogui.moveTo(x, y)
        pyautogui.click()
        if delay > 0:
            time.sleep(delay)

    def _ensure_calibrated(self, items):
        missing = []
        for key, label in items:
            val = self.cfg.get(key)
            if key == "responder_badges":
                if not any(val or []):
                    missing.append(label)
            elif not val:
                missing.append(label)
        if missing:
            messagebox.showerror(tr("error_calib"), "Kalibratie incompleet: " + ", ".join(missing))
            return False
        return True

    # ---------- UI ----------
    def _build_ui(self):
        wrap = ctk.CTkScrollableFrame(self)
        wrap.pack(fill="both", expand=True, padx=20, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        top = ttk.Frame(wrap)
        top.grid(row=0, column=0, sticky="ew", pady=(0,10))
        top.columnconfigure(0, weight=1)
        mode_frame = ttk.LabelFrame(top, text=tr("mode"), padding=12)
        mode_frame.grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text=tr("sender"), variable=self.mode_var, value="sender",
                        command=self._refresh_mode).grid(row=0, column=0, padx=8, sticky="w")
        ttk.Radiobutton(mode_frame, text=tr("responder"), variable=self.mode_var, value="responder",
                        command=self._refresh_mode).grid(row=0, column=1, padx=8, sticky="w")
        ttk.Radiobutton(mode_frame, text=tr("combi"), variable=self.mode_var, value="combi",
                        command=self._refresh_mode).grid(row=0, column=2, padx=8, sticky="w")
        ttk.Button(top, text="⚙", width=3, command=self._open_settings).grid(row=0, column=1, sticky="e", padx=(6,0))

        self.sender_frame = ttk.Frame(wrap, padding=4); self.sender_frame.grid(row=1, column=0, sticky="nsew")
        self.responder_frame = ttk.Frame(wrap, padding=4); self.responder_frame.grid(row=1, column=0, sticky="nsew")
        self.combi_frame = ttk.Frame(wrap, padding=4); self.combi_frame.grid(row=1, column=0, sticky="nsew")

        self._build_sender(self.sender_frame)
        self._build_responder(self.responder_frame)
        self._build_combi(self.combi_frame)

        btn_row = ttk.Frame(wrap)
        btn_row.grid(row=2, column=0, sticky="e", pady=(0,5))
        ttk.Button(btn_row, text=tr("load_settings"), command=self._load_settings).pack(side="left", padx=(0,6))
        ttk.Button(btn_row, text=tr("save_settings"), command=self.save_combined).pack(side="left")
        self.status_lbl = ttk.Label(wrap, textvariable=self.status_var, font=("Segoe UI", 10, "italic"))
        self.status_lbl.grid(row=3, column=0, sticky="w")

        self._refresh_mode()

    def _load_settings(self):
        self.load_combined()
        self.cfg = load_snap_config()
        self.startup_enabled.set(bool(self.cfg.get("startup_enabled")))
        self.startup_send_snap.set(bool(self.cfg.get("startup_send_snap")))
        self.action_delay_var.set(self.cfg.get("action_delay", 0.5))
        self.autoload_var.set(bool(self.cfg.get("auto_load_settings")))
        self.autoload_file_var.set(self.cfg.get("auto_settings_file", ""))
        self.snap_shortcut_var.set(self.cfg.get("snapchat_shortcut", ""))
        self.times = self.cfg.get("combi_times", []).copy()
        self.time_people = self.cfg.get("combi_time_people", {}).copy()
        self.combi_times = self.cfg.get("combi_times", []).copy()
        self.combi_time_people = self.cfg.get("combi_time_people", {}).copy()
        try:
            self._refresh_times()
            self._combi_refresh_times()
        except Exception:
            pass

    def _refresh_mode(self):
        m = self.mode_var.get()
        if m == "sender": self.sender_frame.lift()
        elif m == "responder": self.responder_frame.lift()
        else: self.combi_frame.lift()

    def _toggle_startup(self):
        enabled = bool(self.startup_enabled.get())
        self.cfg["startup_enabled"] = enabled
        save_snap_config(self.cfg)
        update_autosnap_startup(enabled)
        if enabled:
            messagebox.showinfo("Startup", "Script toegevoegd aan Windows Startup. Uitschakelen: vink deze optie uit.")
        else:
            messagebox.showinfo("Startup", "Startup-script verwijderd uit Windows Startup.")

    def _toggle_startup_send_snap(self):
        self.cfg["startup_send_snap"] = bool(self.startup_send_snap.get())
        save_snap_config(self.cfg)

    def _snap_shortcut_changed(self):
        self.cfg["snapchat_shortcut"] = self.snap_shortcut_var.get()
        save_snap_config(self.cfg)

    def _choose_snap_shortcut(self):
        path = filedialog.askopenfilename(
            title="Kies Snapchat-snelkoppeling",
            filetypes=[("Snelkoppeling", "*.lnk"), ("Alle bestanden", "*.*")],
        )
        if path:
            self.snap_shortcut_var.set(path)

    def _autoload_file_changed(self):
        self.cfg["auto_settings_file"] = self.autoload_file_var.get()
        save_snap_config(self.cfg)

    def _choose_autoload_file(self):
        path = filedialog.askopenfilename(
            title="Kies instellingenbestand",
            filetypes=[("JSON", "*.json"), ("Alle bestanden", "*.*")],
        )
        if path:
            self.autoload_file_var.set(path)

    def _toggle_autoload(self):
        self.cfg["auto_load_settings"] = bool(self.autoload_var.get())
        save_snap_config(self.cfg)

    def _apply_action_delay(self):
        try:
            val = float(self.action_delay_var.get())
        except Exception:
            val = 0.5
            self.action_delay_var.set(val)
        self.cfg["action_delay"] = val
        save_snap_config(self.cfg)
        try:
            pyautogui.PAUSE = val
        except Exception:
            pass

    def _open_settings(self):
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.lift(); return
        win = ctk.CTkToplevel(self)
        win.title(tr("settings"))
        set_window_icon(win, APP_ICON_SNAP)
        win.geometry("360x240")
        win.attributes("-topmost", True)
        self.settings_win = win
        win.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "settings_win", None), win.destroy()))

        tabs = ctk.CTkTabview(win)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        tab_gen = tabs.add("Algemeen")
        ctk.CTkLabel(tab_gen, text="Actie-delay (s)").pack(anchor="w", padx=10, pady=(10,0))
        ctk.CTkEntry(tab_gen, textvariable=self.action_delay_var, width=80).pack(anchor="w", padx=10, pady=(0,10))
        ctk.CTkCheckBox(tab_gen, text=tr("autoload_settings"),
                        variable=self.autoload_var,
                        command=self._toggle_autoload).pack(anchor="w", padx=10, pady=8)
        ctk.CTkButton(tab_gen, text=tr("full_calibration"), command=self._calibrate_from_settings).pack(fill="x", padx=10, pady=8)

        tab_start = tabs.add("Startup")
        ctk.CTkCheckBox(tab_start, text=tr("windows_startup"), variable=self.startup_enabled,
                        command=self._toggle_startup).pack(anchor="w", padx=10, pady=8)
        ctk.CTkLabel(tab_start, text="Snapchat-snelkoppeling").pack(anchor="w", padx=10, pady=(0,0))
        row = ctk.CTkFrame(tab_start)
        row.pack(fill="x", padx=10, pady=4)
        ctk.CTkEntry(row, textvariable=self.snap_shortcut_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="Kies...", width=80, command=self._choose_snap_shortcut).pack(side="left", padx=(6,0))
        ctk.CTkLabel(tab_start, text=tr("startup_settings_file")).pack(anchor="w", padx=10, pady=(10,0))
        row2 = ctk.CTkFrame(tab_start)
        row2.pack(fill="x", padx=10, pady=4)
        ctk.CTkEntry(row2, textvariable=self.autoload_file_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row2, text="Kies...", width=80, command=self._choose_autoload_file).pack(side="left", padx=(6,0))
        ctk.CTkButton(tab_start, text="Kalibratie zoekbalk",
                      command=lambda: self._calib_key("boot_searchbar", tr("searchbar"))).pack(fill="x", padx=10, pady=8)
        ctk.CTkCheckBox(tab_start, text="Snap verzenden op boot",
                        variable=self.startup_send_snap,
                        command=self._toggle_startup_send_snap).pack(anchor="w", padx=10, pady=8)

    def _calibrate_from_settings(self):
        mode = self.mode_var.get()
        if mode == "sender":
            self._full_calibration_sender()
        elif mode == "responder":
            self._full_calibration_responder()
        else:
            self._full_calibration_combi()

    # ----- Sender UI -----
    def _build_sender(self, root):
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)
        ttk.Label(root, text=tr("sender"), font=("Segoe UI", 18, "bold")).grid(row=0, column=0, pady=(0, 10), sticky="w")

        calib = ttk.LabelFrame(root, text=tr("recalibrate"), padding=12)
        calib.grid(row=1, column=0, sticky="nsew", pady=8)
        calib.columnconfigure(0, weight=1)

        cam_ic = None
        send_ic = None
        try:
            cam_ic = ImageTk.PhotoImage(Image.new("RGBA",(1,1)))
        except Exception:
            pass

        ttk.Button(calib, text=" Foto 1 (sender)",
                   command=lambda: self._calib_key("foto1", "Foto 1 (sender)")).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(calib, text=" Foto 2 (sender)",
                   command=lambda: self._calib_key("foto2", "Foto 2 (sender)")).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send_to"),
                   command=lambda: self._calib_key("verstuur_na_foto", tr("send_to"))).grid(row=0, column=2, padx=6, sticky="ew")
        ttk.Button(calib, text=" Personen", command=self._calib_people).grid(row=1, column=0, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send"),
                   command=lambda: self._calib_key("verzend", tr("send"))).grid(row=1, column=1, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("full_calibration"), command=self._full_calibration_sender).grid(row=1, column=2, padx=6, sticky="ew")

        pf = ttk.LabelFrame(root, text=tr("people"), padding=12)
        pf.grid(row=2, column=0, sticky="ew", pady=8)
        for c in range(4): pf.columnconfigure(c, weight=1)
        for i in range(8):
            ttk.Checkbutton(pf, text=f"Person {i+1}", variable=self.person_vars[i]).grid(row=i//4, column=i%4, padx=8, pady=6, sticky="w")

        sf = ttk.LabelFrame(root, text=tr("settings"), padding=12)
        sf.grid(row=3, column=0, sticky="ew", pady=8)
        for c in range(4): sf.columnconfigure(c, weight=1)
        ttk.Label(sf, text=tr("count")).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.count_var, width=10).grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        ttk.Checkbutton(sf, text=tr("until_closed"), variable=self.until_var).grid(row=0, column=2, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Label(sf, text=tr("delay")).grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.delay_var, width=10).grid(row=1, column=1, padx=8, pady=6, sticky="ew")

        sch = ttk.LabelFrame(root, text=tr("times_people"), padding=12)
        sch.grid(row=4, column=0, sticky="nsew", pady=8)
        for c in range(4): sch.columnconfigure(c, weight=1)
        sch.rowconfigure(1, weight=1)
        ttk.Checkbutton(sch, text=tr("schedule_enable"), variable=self.schedule_enabled).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(sch, text=tr("schedule_time")).grid(row=0, column=1, sticky="e")
        ttk.Entry(sch, textvariable=self.new_time_var, width=10).grid(row=0, column=2, padx=6, sticky="w")
        ttk.Button(sch, text=tr("add_time"), command=self._add_time).grid(row=0, column=3, padx=6, sticky="w")

        self.times_list = tk.Listbox(sch, height=6)
        self.times_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(8,6), pady=6)
        self.times_list.bind("<<ListboxSelect>>", lambda e: self._load_people_for_selected_time())
        self.times_list.bind("<Double-Button-1>", lambda e: self._show_time_people())
        ttk.Button(sch, text=tr("remove_time"), command=self._remove_time).grid(row=1, column=2, padx=6, sticky="nw")

        self.time_people_vars = [tk.BooleanVar(value=False) for _ in range(8)]
        per_frame = ttk.LabelFrame(sch, text=tr("people"), padding=10)
        per_frame.grid(row=1, column=3, sticky="nsew", padx=6, pady=6)
        for c in range(2): per_frame.columnconfigure(c, weight=1)
        for i in range(8):
            ttk.Checkbutton(per_frame, text=f"P{i+1}", variable=self.time_people_vars[i]).grid(row=i//2, column=i%2, sticky="w")

        ttk.Button(root, text=" " + tr("start"), command=self._start_sender).grid(row=5, column=0, pady=12, sticky="ew")

        # init lists
        self._refresh_times()

    # ----- Responder UI -----
    def _build_responder(self, root):
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        ttk.Label(root, text=tr("responder"), font=("Segoe UI", 18, "bold")).grid(row=0, column=0, pady=(0, 10), sticky="w")

        calib = ttk.LabelFrame(root, text=tr("recalibrate"), padding=12)
        calib.grid(row=1, column=0, sticky="nsew", pady=8); calib.columnconfigure(0, weight=1)

        ttk.Button(calib, text=" " + tr("badge_points"),
                   command=self._calib_responder_badges).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" Foto (reply)",
                   command=lambda: self._calib_key("foto_reply", "Foto (reply)")).grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send_reply"),
                   command=lambda: self._calib_key("verzend_reply", tr("send_reply"))).grid(row=2, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("close_snap"),
                   command=lambda: self._calib_key("responder_close_snap", tr("close_snap"))).grid(row=3, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("searchbar"),
                   command=lambda: self._calib_key("restart_searchbar", tr("searchbar"))).grid(row=4, column=0, padx=6, pady=6, sticky="ew")

        ttk.Button(calib, text=" " + tr("full_calibration"),
                   command=self._full_calibration_responder).grid(row=5, column=0, padx=6, pady=(6,0), sticky="ew")

        opts = ttk.LabelFrame(root, text=tr("settings"), padding=12)
        opts.grid(row=2, column=0, sticky="ew", pady=8)
        opts.columnconfigure(1, weight=1)
        ttk.Checkbutton(opts, text=tr("close_before_reply"), variable=self.close_before_reply).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(opts, text=tr("restart_after_snaps")).grid(row=1, column=0, sticky="w")
        ttk.Entry(opts, textvariable=self.restart_after_snaps).grid(row=1, column=1, sticky="ew")
        ttk.Label(opts, text=tr("restart_after_minutes")).grid(row=2, column=0, sticky="w")
        ttk.Entry(opts, textvariable=self.restart_after_minutes).grid(row=2, column=1, sticky="ew")

        btns = ttk.Frame(root); btns.grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Button(btns, text=" " + tr("start_responder"), command=self._start_responder).grid(row=0, column=0, padx=6, sticky="w")
        ttk.Button(btns, text=" " + tr("stop_responder"), command=self._stop_responder).grid(row=0, column=1, padx=6, sticky="w")

    # ----- Combi UI -----
    def _build_combi(self, root):
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)
        ttk.Label(root, text=tr("combi"), font=("Segoe UI", 18, "bold")).grid(row=0, column=0, pady=(0, 10), sticky="w")

        calib = ttk.LabelFrame(root, text=tr("recalibrate"), padding=12)
        calib.grid(row=1, column=0, sticky="nsew", pady=8)

        ttk.Button(calib, text=" " + tr("badge_points"),
                   command=self._calib_responder_badges).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" Foto 1 (sender)",
                   command=lambda: self._calib_key("foto1", "Foto 1 (sender)")).grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" Foto 2 (sender)",
                   command=lambda: self._calib_key("foto2", "Foto 2 (sender)")).grid(row=2, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" Foto (reply)",
                   command=lambda: self._calib_key("foto_reply", "Foto (reply)")).grid(row=3, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send_to"),
                   command=lambda: self._calib_key("verstuur_na_foto", tr("send_to"))).grid(row=4, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send"),
                   command=lambda: self._calib_key("verzend", tr("send"))).grid(row=5, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send_reply"),
                   command=lambda: self._calib_key("verzend_reply", tr("send_reply"))).grid(row=6, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("close_snap"),
                   command=lambda: self._calib_key("responder_close_snap", tr("close_snap"))).grid(row=7, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("restart_close"),
                   command=lambda: self._calib_key("restart_close_app", tr("restart_close"))).grid(row=8, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("restart_search"),
                   command=lambda: self._calib_key("restart_searchbar", tr("restart_search"))).grid(row=9, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("full_calibration"),
                   command=self._full_calibration_combi).grid(row=10, column=0, padx=6, pady=(6,0), sticky="ew")

        # Planner (tijden & personen)
        sch = ttk.LabelFrame(root, text=tr("times_people"), padding=12)
        sch.grid(row=2, column=0, sticky="nsew", pady=8)
        for c in range(4): sch.columnconfigure(c, weight=1)
        sch.rowconfigure(1, weight=1)
        self.combi_schedule_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(sch, text=tr("schedule_enable"), variable=self.combi_schedule_enabled).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.combi_new_time_var = tk.StringVar(value="")
        ttk.Label(sch, text=tr("schedule_time")).grid(row=0, column=1, sticky="e")
        ttk.Entry(sch, textvariable=self.combi_new_time_var, width=10).grid(row=0, column=2, padx=6, sticky="w")
        ttk.Button(sch, text=tr("add_time"), command=self._combi_add_time).grid(row=0, column=3, padx=6, sticky="w")

        self.combi_times_list = tk.Listbox(sch, height=6)
        self.combi_times_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(8,6), pady=6)
        self.combi_times_list.bind("<<ListboxSelect>>", lambda e: self._combi_load_people_for_selected_time())
        self.combi_times_list.bind("<Double-Button-1>", lambda e: self._combi_show_time_people())
        ttk.Button(sch, text=tr("remove_time"), command=self._combi_remove_time).grid(row=1, column=2, padx=6, sticky="nw")

        self.combi_people_vars = [tk.BooleanVar(value=False) for _ in range(8)]
        per_frame = ttk.LabelFrame(sch, text=tr("people"), padding=10)
        per_frame.grid(row=1, column=3, sticky="nsew", padx=6, pady=6)
        for c in range(2): per_frame.columnconfigure(c, weight=1)
        for i in range(8):
            ttk.Checkbutton(per_frame, text=f"P{i+1}", variable=self.combi_people_vars[i]).grid(row=i//2, column=i%2, sticky="w")

        # Opties
        opts = ttk.LabelFrame(root, text=tr("settings"), padding=12)
        opts.grid(row=3, column=0, sticky="ew", pady=8)
        opts.columnconfigure(1, weight=1)
        ttk.Checkbutton(opts, text=tr("close_before_reply"), variable=self.close_before_reply).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(opts, text=tr("restart_after_snaps")).grid(row=1, column=0, sticky="w")
        ttk.Entry(opts, textvariable=self.restart_after_snaps).grid(row=1, column=1, sticky="ew")
        ttk.Label(opts, text=tr("restart_after_minutes")).grid(row=2, column=0, sticky="w")
        ttk.Entry(opts, textvariable=self.restart_after_minutes).grid(row=2, column=1, sticky="ew")

        # Start/stop
        btns = ttk.Frame(root); btns.grid(row=4, column=0, sticky="ew", pady=10)
        ttk.Button(btns, text=" " + tr("start_combi"), command=self._start_combi).grid(row=0, column=0, padx=6, sticky="w")
        ttk.Button(btns, text=" " + tr("stop_combi"), command=self._stop_combi).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(btns, text=" " + tr("send_reply"), command=self._combi_send_reply).grid(row=0, column=2, padx=6, sticky="w")

        self._combi_refresh_times()

    # ---------- Sender logic ----------
    def _full_calibration_sender(self):
        seq = [("foto1","Foto 1 (sender)"), ("foto2","Foto 2 (sender)"), ("verstuur_na_foto", tr("send_to"))]
        for k, lbl in seq:
            pos = calibrate_position_snap(self, lbl)
            if not pos: return
            self.cfg[k] = pos; save_snap_config(self.cfg)
        for i in range(8):
            pos = calibrate_position_snap(self, f"Persoon {i+1}")
            if not pos: break
            self.cfg["personen"][i] = pos; save_snap_config(self.cfg)
        pos = calibrate_position_snap(self, tr("send"))
        if pos:
            self.cfg["verzend"] = pos; save_snap_config(self.cfg)
        toast(self, tr("saved"), "Volledige kalibratie opgeslagen", timeout=2000)

    def _calib_key(self, key, label_text):
        pos = calibrate_position_snap(self, label_text)
        if pos:
            self.cfg[key] = pos
            if key == "restart_close_app":
                self.cfg["responder_close_snap"] = pos
            elif key == "responder_close_snap":
                self.cfg["restart_close_app"] = pos
            save_snap_config(self.cfg)
            toast(self, tr("saved"), f"{label_text} -> {pos}", timeout=2000)

    def _calib_people(self):
        for i in range(8):
            pos = calibrate_position_snap(self, f"Persoon {i+1}")
            if not pos: break
            self.cfg["personen"][i] = pos; save_snap_config(self.cfg)
        toast(self, tr("saved"), "Personenposities opgeslagen", timeout=2000)

    def _add_time(self):
        t = parse_hhmm(self.new_time_var.get())
        if not t:
            messagebox.showerror("Time", "Invalid time format. Use HH:MM"); return
        if t not in self.times:
            self.times.append(t); self.time_people.setdefault(t, [False]*8)
            self._refresh_times()
            # persist
            self.cfg["combi_times"] = self.times; self.cfg["combi_time_people"] = self.time_people; save_snap_config(self.cfg)
            # auto-start planner indien aangezet
            if self.schedule_enabled.get():
                self._ensure_sender_scheduler()

    def _remove_time(self):
        sel = self._selected_time()
        if not sel: return
        if sel in self.times: self.times.remove(sel)
        if sel in self.time_people: del self.time_people[sel]
        self._refresh_times()
        self.cfg["combi_times"] = self.times; self.cfg["combi_time_people"] = self.time_people; save_snap_config(self.cfg)

    def _selected_time(self):
        try:
            idx = self.times_list.curselection()
            if not idx: return None
            return self.times[idx[0]]
        except Exception:
            return None

    def _refresh_times(self):
        self.times.sort(); self.times_list.delete(0, tk.END)
        for t in self.times: self.times_list.insert(tk.END, t)
        self._load_people_for_selected_time()

    def _load_people_for_selected_time(self):
        sel = self._selected_time()
        mask = self.time_people.get(sel, [False]*8)
        for i in range(8): self.time_people_vars[i].set(bool(mask[i]))

    def _save_people_for_selected_time(self):
        sel = self._selected_time()
        if not sel: return
        self.time_people[sel] = [bool(v.get()) for v in self.time_people_vars]
        self.cfg["combi_time_people"] = self.time_people; save_snap_config(self.cfg)

    def _show_time_people(self):
        sel = self._selected_time()
        if not sel: return
        mask = self.time_people.get(sel, [False]*8)
        people = [f"P{i+1}" for i, on in enumerate(mask) if on]
        text = ", ".join(people) if people else "Geen"
        messagebox.showinfo(sel, text)

    def _run_sender_once(self, persons):
        self.status_var.set(tr("status_busy"))
        try:
            with self.ui_lock:
                # Foto 1 -> wacht 3s
                x, y = self.cfg["foto1"]
                pyautogui.moveTo(x, y); pyautogui.click(); time.sleep(3.0)
                # Foto 2 -> wacht 1.5s
                x, y = self.cfg["foto2"]
                pyautogui.moveTo(x, y); pyautogui.click(); time.sleep(1.5)
                # Daarna volgens ingestelde delay
                self.move_then_click(self.cfg["verstuur_na_foto"])
                for idx in persons:
                    p = self.cfg["personen"][idx]
                    if p: self.move_then_click(p)
                time.sleep(5)
                self.move_then_click(self.cfg["verzend"])
                time.sleep(2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.status_var.set(tr("status_done"))

    def _run_sender_loop(self, persons, count, endless, delay):
        self.status_var.set(tr("status_busy"))
        try:
            while self.sender_running.is_set() and (endless or count > 0):
                self._run_sender_once(persons)
                if not endless: count -= 1
                total = max(0.0, float(delay))
                steps = int(total / 0.1) if total > 0 else 0
                for _ in range(max(1, steps)):
                    if not self.sender_running.is_set(): break
                    time.sleep(0.1)
        finally:
            self.status_var.set(tr("status_done"))
            self.after(0, self._exit_mini)

    def _ensure_sender_scheduler(self):
        if not self.times or not self.schedule_enabled.get(): return
        if self._sender_scheduler_thread and self._sender_scheduler_thread.is_alive(): return
        self._start_sender_scheduler_thread()

    def _start_sender_scheduler_thread(self):
        required = [
            ("foto1", "Foto 1 (sender)"),
            ("foto2", "Foto 2 (sender)"),
            ("verstuur_na_foto", tr("send_to")),
            ("verzend", tr("send")),
        ]
        if not self._ensure_calibrated(required):
            return
        self.sender_running.set()
        self.sender_cancel_evt.clear()
        self._enter_mini(stop_callback=self._stop_sender, banner_text=tr("mini_msg"))
        def scheduler_loop():
            try:
                self.status_var.set(tr("schedule_enable"))
                while self.sender_running.is_set():
                    self._save_people_for_selected_time()
                    upcoming = [(t, next_occurrence(t)) for t in self.times]
                    upcoming.sort(key=lambda x: x[1])
                    if not upcoming:
                        time.sleep(0.5); continue
                    t_str, when = upcoming[0]
                    self.status_var.set(tr("waiting_until", time=when.strftime("%H:%M")))
                    wait_until(when, tick=self.update, cancel_evt=self.sender_cancel_evt)
                    if not self.sender_running.is_set() or self.sender_cancel_evt.is_set(): break
                    mask = self.time_people.get(t_str, [False]*8)
                    persons = [i for i, on in enumerate(mask) if on]
                    self._run_sender_once(persons)
            finally:
                self.status_var.set(tr("status_done"))
                self.after(0, self._exit_mini)
        self._sender_scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._sender_scheduler_thread.start()

    def _start_sender(self):
        required = [
            ("foto1", "Foto 1 (sender)"),
            ("foto2", "Foto 2 (sender)"),
            ("verstuur_na_foto", tr("send_to")),
            ("verzend", tr("send")),
        ]
        if not self._ensure_calibrated(required):
            return
        self.sender_running.set()
        self.sender_cancel_evt.clear()
        self._enter_mini(stop_callback=self._stop_sender, banner_text=tr("mini_msg"))
        if self.schedule_enabled.get() and self.times:
            self._start_sender_scheduler_thread()
        else:
            persons = [i for i, v in enumerate(self.person_vars) if v.get()]
            count = self.count_var.get(); endless = self.until_var.get(); delay = self.delay_var.get()
            threading.Thread(target=self._run_sender_loop, args=(persons, count, endless, delay), daemon=True).start()

    def _stop_sender(self):
        self.sender_cancel_evt.set()
        self.sender_running.clear()
        self.status_var.set(tr("status_stopped"))

    # ---------- Responder logic ----------
    def _calib_responder_badges(self):
        pts = []
        for i in range(8):
            pos = calibrate_position_snap(self, f"Rood blokje {i+1}")
            if not pos: break
            pts.append(pos)
        while len(pts) < 8: pts.append(None)
        self.cfg["responder_badges"] = pts
        save_snap_config(self.cfg)
        toast(self, tr("saved"), "Rode blokjes opgeslagen", timeout=2000)

    def _full_calibration_responder(self):
        self._calib_responder_badges()
        self._calib_key("foto_reply", "Foto (reply)")
        self._calib_key("verzend_reply", tr("send_reply"))
        self._calib_key("responder_close_snap", tr("close_snap"))
        self._calib_key("restart_searchbar", tr("searchbar"))

    def _start_responder(self):
        required = [
            ("responder_badges", "Rode blokjes"),
            ("foto_reply", "Foto reply"),
            ("verzend_reply", tr("send_reply")),
        ]
        if self.close_before_reply.get():
            required.append(("responder_close_snap", tr("close_snap")))
        if not self._ensure_calibrated(required):
            return
        if self.responder_running.is_set(): return
        self.cfg["close_before_reply"] = bool(self.close_before_reply.get())
        self.cfg["restart_after_snaps"] = int(self.restart_after_snaps.get())
        self.cfg["restart_after_minutes"] = int(self.restart_after_minutes.get())
        save_snap_config(self.cfg)
        self.responder_running.set()
        self._enter_mini(stop_callback=self._stop_responder, banner_text=tr("mini_msg"))
        threading.Thread(target=self._responder_master_loop, daemon=True).start()
        self.status_var.set("Responder actief")

    def _stop_responder(self):
        self.responder_running.clear()
        self.status_var.set(tr("status_done"))
        self.after(0, self._exit_mini)

    def _respond_sequence(self, badge_xy):
        """Open snap, optioneel sluiten, maak foto en verstuur."""
        with self.ui_lock:
            delay = self.action_delay_var.get()
            x, y = badge_xy
            pyautogui.moveTo(x, y)
            pyautogui.click()
            if delay > 0: time.sleep(delay)
            if self.close_before_reply.get() and self.cfg.get("responder_close_snap"):
                # Sluit de geopende snap en ga meteen door naar antwoorden
                self.move_then_click(tuple(self.cfg["responder_close_snap"]))
            else:
                # Zonder sluiten: dubbelklik met vertraging tussen de twee klikken
                pyautogui.click()
                if delay > 0: time.sleep(delay)

            # foto
            foto_pos = self.cfg.get("foto_reply") or self.cfg.get("foto1")
            if not foto_pos:
                return False
            self.move_then_click(tuple(foto_pos))

            # versturen
            s2 = self.cfg.get("verzend_reply")
            if not s2:
                return False
            self.move_then_click(tuple(s2))

            return True

    def _responder_master_loop(self):
        """Scan 1..8..1, per ronde max 1 reactie per persoon."""
        reacted_count_since_restart = 0
        last_restart = time.time()
        restart_snaps = int(self.cfg.get("restart_after_snaps", 0))
        restart_minutes = int(self.cfg.get("restart_after_minutes", 0))
        idx = 0
        reacted_this_round = set()
        try:
            while self.responder_running.is_set():
                if time.time() < self._color_cooldown_until:
                    time.sleep(0.05); continue

                badges = self.cfg.get("responder_badges", [None]*8)
                if not badges: time.sleep(0.1); continue

                if idx == 0:
                    reacted_this_round.clear()

                pt = badges[idx]
                if pt:
                    x, y = pt
                    if red_in_radius(x, y, RADIUS_DEFAULT) and (idx not in reacted_this_round):
                        ok = self._respond_sequence((x, y))
                        if ok:
                            reacted_this_round.add(idx)
                            reacted_count_since_restart += 1
                            if ((restart_snaps and reacted_count_since_restart >= restart_snaps) or
                                (restart_minutes and (time.time() - last_restart) >= restart_minutes*60)):
                                reacted_count_since_restart = 0
                                last_restart = time.time()
                                self._restart_via_buttons()
                                time.sleep(0.1)

                idx = (idx + 1) % 8
                time.sleep(0.1)
        finally:
            self.status_var.set(tr("status_done"))
            self.after(0, self._exit_mini)

    def _restart_via_buttons(self):
        """Klik 'app sluiten (X)' indien gezet, schakel kleurscan 5s uit, 0.5s wachten, zoekbalk -> 'snapchat' + Enter."""
        with self.ui_lock:
            close_pos = self.cfg.get("restart_close_app") or self.cfg.get("responder_close_snap")
            if close_pos:
                self.move_then_click(tuple(close_pos))
            # 5 sec geen kleurscan
            self._color_cooldown_until = time.time() + 5.0
            time.sleep(0.5)
            search_pos = self.cfg.get("restart_searchbar")
            if search_pos:
                self.move_then_click(tuple(search_pos))
                try:
                    pyautogui.typewrite("snapchat", interval=0.01)
                    pyautogui.press("enter")
                except Exception:
                    pass
                time.sleep(2.0)  # korte wachttijd tot UI opkomt

    # ---------- Combi logic ----------
    def _full_calibration_combi(self):
        # volgorde: rode blokjes, foto's, versturen1, versturen2, app-sluiten, zoekbalk
        self._calib_responder_badges()
        for key, label in [
            ("foto1", "Foto 1 (sender)"),
            ("foto2", "Foto 2 (sender)"),
            ("foto_reply", "Foto (reply)"),
            ("verstuur_na_foto", tr("send_to")),
            ("verzend", tr("send")),
            ("verzend_reply", tr("send_reply")),
            ("responder_close_snap", tr("close_snap")),
            ("restart_close_app", tr("restart_close")),
            ("restart_searchbar", tr("restart_search")),
        ]:
            self._calib_key(key, label)

    def _combi_selected_time(self):
        try:
            idx = self.combi_times_list.curselection()
            if not idx: return None
            return self.combi_times[idx[0]]
        except Exception:
            return None

    def _combi_add_time(self):
        t = parse_hhmm(self.combi_new_time_var.get())
        if not t:
            messagebox.showerror("Time", "Invalid time format. Use HH:MM"); return
        if t not in self.combi_times:
            self.combi_times.append(t); self.combi_time_people.setdefault(t, [False]*8)
            self._combi_refresh_times()
            self.cfg["combi_times"] = self.combi_times; self.cfg["combi_time_people"] = self.combi_time_people; save_snap_config(self.cfg)

    def _combi_remove_time(self):
        sel = self._combi_selected_time()
        if not sel: return
        if sel in self.combi_times: self.combi_times.remove(sel)
        if sel in self.combi_time_people: del self.combi_time_people[sel]
        self._combi_refresh_times()
        self.cfg["combi_times"] = self.combi_times; self.cfg["combi_time_people"] = self.combi_time_people; save_snap_config(self.cfg)

    def _combi_refresh_times(self):
        self.combi_times.sort(); self.combi_times_list.delete(0, tk.END)
        for t in self.combi_times: self.combi_times_list.insert(tk.END, t)
        self._combi_load_people_for_selected_time()

    def _combi_load_people_for_selected_time(self):
        sel = self._combi_selected_time()
        mask = self.combi_time_people.get(sel, [False]*8)
        for i in range(8): self.combi_people_vars[i].set(bool(mask[i]))

    def _combi_save_people_for_selected_time(self):
        sel = self._combi_selected_time()
        if not sel: return
        self.combi_time_people[sel] = [bool(v.get()) for v in self.combi_people_vars]
        self.cfg["combi_time_people"] = self.combi_time_people; save_snap_config(self.cfg)

    def _combi_show_time_people(self):
        sel = self._combi_selected_time()
        if not sel: return
        mask = self.combi_time_people.get(sel, [False]*8)
        people = [f"P{i+1}" for i, on in enumerate(mask) if on]
        text = ", ".join(people) if people else "Geen"
        messagebox.showinfo(sel, text)

    def _start_combi(self):
        required = [
            ("responder_badges", "Rode blokjes"),
            ("foto1", "Foto 1 (sender)"),
            ("foto2", "Foto 2 (sender)"),
            ("foto_reply", "Foto reply"),
            ("verstuur_na_foto", tr("send_to")),
            ("verzend", tr("send")),
            ("verzend_reply", tr("send_reply")),
        ]
        if self.close_before_reply.get():
            required.append(("responder_close_snap", tr("close_snap")))
        if not self._ensure_calibrated(required):
            return
        if self.combi_running.is_set(): return

        self.cfg["close_before_reply"] = bool(self.close_before_reply.get())
        self.cfg["restart_after_snaps"] = int(self.restart_after_snaps.get())
        self.cfg["restart_after_minutes"] = int(self.restart_after_minutes.get())
        save_snap_config(self.cfg)

        # opslaan huidige per-tijd keuze
        self._combi_save_people_for_selected_time()
        self.combi_running.set()
        self._enter_mini(stop_callback=self._stop_combi, banner_text=tr("mini_msg"))

        # start responder-loop (volgens je nieuwe flow)
        if not self.responder_running.is_set():
            self.responder_running.set()
            threading.Thread(target=self._responder_master_loop, daemon=True).start()

        # start scheduler (dagelijks) indien tijden bestaan
        if self.combi_schedule_enabled.get() and self.combi_times:
            threading.Thread(target=self._combi_sender_scheduler, daemon=True).start()

        # optioneel elk uur herstart
        if self.hourly_restart.get():
            threading.Thread(target=self._hourly_restart_loop, daemon=True).start()

        self.status_var.set("Combi actief")

    def _stop_combi(self):
        self.combi_running.clear()
        # laat responder stoppen
        self._stop_responder()
        self.status_var.set(tr("status_done"))
        self.after(0, self._exit_mini)

    def _combi_send_reply(self):
        """Stuur een reply naar het eerste gevonden rode blokje."""
        badges = self.cfg.get("responder_badges", [None]*8)
        for pt in badges:
            if not pt:
                continue
            x, y = pt
            if red_in_radius(x, y, RADIUS_DEFAULT):
                self._respond_sequence((x, y))
                break

    def _get_current_combi_persons(self):
        sel = self._combi_selected_time()
        if sel and sel in self.combi_time_people:
            mask = self.combi_time_people.get(sel, [False]*8)
            return [i for i, on in enumerate(mask) if on]
        return [i for i, v in enumerate(self.combi_people_vars) if v.get()]

    def _combi_sender_scheduler(self):
        while self.combi_running.is_set():
            self._combi_save_people_for_selected_time()
            upcoming = [(t, next_occurrence(t)) for t in self.combi_times]
            upcoming.sort(key=lambda x: x[1])
            if not upcoming:
                time.sleep(0.5); continue
            t_str, when = upcoming[0]
            self.status_var.set(tr("waiting_until", time=when.strftime("%H:%M")))
            wait_until(when, tick=self.update)
            if not self.combi_running.is_set(): break
            mask = self.combi_time_people.get(t_str, [False]*8)
            persons = [i for i, on in enumerate(mask) if on]
            self._run_sender_once(persons)
            time.sleep(0.2)

    def _hourly_restart_loop(self):
        # eenvoudige klok: elke 60 min
        while self.combi_running.is_set():
            for _ in range(60*60):
                if not self.combi_running.is_set(): return
                time.sleep(1)
            if not self.combi_running.is_set(): return
            try:
                self._restart_via_buttons()
            except Exception:
                pass

# -----------------------------------------------------------------------------
# AutoTikTok (ongewijzigd, stabiel)
# -----------------------------------------------------------------------------
AUTOTIKTOK_CONFIG_FILE = AUTOTIKTOK_DIR / "tiktok_config.json"
DEFAULT_TT_CONFIG = {"upload": None,"select_video": None,"video_item": None,"open": None,"description": None,"send": None}

def load_tt_config():
    if AUTOTIKTOK_CONFIG_FILE.exists():
        try: return json.loads(AUTOTIKTOK_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return DEFAULT_TT_CONFIG.copy()

def save_tt_config(cfg):
    AUTOTIKTOK_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def load_combined_data(path: str | Path | None = None):
    """Laad gecombineerde instellingen uit *path* en pas toe."""
    file = Path(path) if path else EXTRA_SAVE_FILE
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        snap = data.get("autosnap")
        if isinstance(snap, dict):
            save_snap_config(snap)
        tt = data.get("autotiktok")
        if isinstance(tt, dict):
            save_tt_config(tt)
        return data
    except Exception:
        return None

class AutoTikTokWindow(ctk.CTkToplevel, MiniMixin):
    def __init__(self, master, get_lang, set_lang, save_combined):
        ctk.CTkToplevel.__init__(self, master)
        MiniMixin.__init__(self)
        self.get_lang = get_lang; self.set_lang = set_lang; self.save_combined = save_combined
        self.title(tr("autotiktok")); set_window_icon(self, APP_ICON_TT)
        self.geometry("740x780"); self.resizable(True, True); self.attributes("-topmost", True)
        self.rowconfigure(0, weight=1); self.columnconfigure(0, weight=1)

        self.cfg = load_tt_config()
        self.status_var = tk.StringVar(value="")
        self.desc_var = tk.StringVar(value="")
        self.schedule_enabled = tk.BooleanVar(value=False)
        self.new_time_var = tk.StringVar(value="")
        self.times = []
        self.tt_running = threading.Event()

        self._build_ui()

    def _build_ui(self):
        wrap = ttk.Frame(self, padding=20); wrap.grid(row=0, column=0, sticky="nsew")
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(3, weight=1)

        ttk.Label(wrap, text=tr("autotiktok"), font=("Segoe UI", 20, "bold")).grid(row=0, column=0, pady=(0, 16))

        calib = ttk.LabelFrame(wrap, text=tr("recalibrate"), padding=12)
        calib.grid(row=1, column=0, sticky="ew", pady=8); calib.columnconfigure(0, weight=1)

        ttk.Button(calib, text=" Upload", command=lambda: self._calib_key("upload", "Upload")).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("select_video"), command=lambda: self._calib_key("select_video", tr("select_video"))).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("video_item"), command=lambda: self._calib_key("video_item", tr("video_item"))).grid(row=0, column=2, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("open"), command=lambda: self._calib_key("open", tr("open"))).grid(row=0, column=3, padx=6, sticky="ew")

        ttk.Button(calib, text=" " + tr("description"), command=lambda: self._calib_key("description", tr("description"))).grid(row=1, column=0, padx=6, sticky="ew")
        ttk.Button(calib, text=" " + tr("send"), command=lambda: self._calib_key("send", tr("send"))).grid(row=1, column=1, padx=6, sticky="ew")

        ttk.Button(calib, text=" " + tr("full_calibration"), command=self._full_calibration).grid(row=2, column=0, padx=6, pady=(6,0), sticky="ew")

        desc_frame = ttk.LabelFrame(wrap, text="Beschrijving", padding=12)
        desc_frame.grid(row=2, column=0, sticky="ew", pady=8)
        ent = ttk.Entry(desc_frame, textvariable=self.desc_var); ent.grid(row=0, column=0, sticky="ew")
        desc_frame.columnconfigure(0, weight=1)

        sch = ttk.LabelFrame(wrap, text=tr("times"), padding=12); sch.grid(row=3, column=0, sticky="nsew", pady=8)
        for c in range(4): sch.columnconfigure(c, weight=1)
        sch.rowconfigure(1, weight=1)
        ttk.Checkbutton(sch, text=tr("schedule_enable"), variable=self.schedule_enabled).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(sch, text=tr("schedule_time")).grid(row=0, column=1, sticky="e")
        ttk.Entry(sch, textvariable=self.new_time_var, width=10).grid(row=0, column=2, padx=6, sticky="w")
        ttk.Button(sch, text=tr("add_time"), command=self._add_time).grid(row=0, column=3, padx=6, sticky="w")

        self.times_list = tk.Listbox(sch, height=6)
        self.times_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(8,6), pady=6)
        ttk.Button(sch, text=tr("remove_time"), command=self._remove_time).grid(row=1, column=2, padx=6, sticky="nw")

        ttk.Button(wrap, text=" " + tr("start"), command=self._start).grid(row=4, column=0, pady=12, sticky="ew")
        ttk.Button(wrap, text=tr("save_settings"), command=self.save_combined).grid(row=5, column=0, pady=(0,8), sticky="e")
        ttk.Label(wrap, textvariable=self.status_var, font=("Segoe UI", 10, "italic")).grid(row=6, column=0, sticky="w")

    def _full_calibration(self):
        sequence = [("upload", "Upload"), ("select_video", tr("select_video")),
                    ("video_item", tr("video_item")), ("open", tr("open")),
                    ("description", tr("description")), ("send", tr("send"))]
        for key, label in sequence:
            pos = calibrate_position_snap(self, label)
            if not pos: return
            self.cfg[key] = pos; save_tt_config(self.cfg)
        toast(self, tr("saved"), "Volledige kalibratie opgeslagen", timeout=2000)

    def _add_time(self):
        t = parse_hhmm(self.new_time_var.get())
        if not t:
            messagebox.showerror("Time", "Invalid time format. Use HH:MM"); return
        if t not in self.times:
            self.times.append(t); self.times.sort(); self._refresh_times()

    def _remove_time(self):
        try:
            idx = self.times_list.curselection()
            if not idx: return
            t = self.times[idx[0]]
            self.times.remove(t); self._refresh_times()
        except Exception: pass

    def _refresh_times(self):
        self.times_list.delete(0, tk.END)
        for t in sorted(self.times): self.times_list.insert(tk.END, t)

    def _calib_key(self, key, label_text):
        pos = calibrate_position_snap(self, label_text)
        if pos:
            self.cfg[key] = pos; save_tt_config(self.cfg)
            toast(self, tr("saved"), f"{label_text} -> {pos}", timeout=2000)

    def _click(self, key):
        x, y = self.cfg[key]; pyautogui.moveTo(x, y); time.sleep(0.5); pyautogui.click(); time.sleep(0.5)

    def _start(self):
        required = ["upload","select_video","video_item","open","description","send"]
        if not all(self.cfg.get(k) for k in required):
            messagebox.showerror(tr("error_calib"), tr("error_calib")); return
        self.tt_running.set()
        self._enter_mini(stop_callback=self._stop, banner_text=tr("mini_msg"))
        desc = self.desc_var.get() or ""
        if self.schedule_enabled.get() and self.times:
            def scheduler_loop():
                try:
                    self.status_var.set(tr("schedule_enable"))
                    while self.tt_running.is_set():
                        upcoming = [(t, next_occurrence(t)) for t in self.times]
                        upcoming.sort(key=lambda x: x[1])
                        if not upcoming: time.sleep(0.5); continue
                        _, when = upcoming[0]
                        self.status_var.set(tr("waiting_until", time=when.strftime("%H:%M")))
                        wait_until(when, tick=self.update)
                        if not self.tt_running.is_set(): break
                        self._run_once(desc)
                finally:
                    self.status_var.set(tr("status_done")); self.after(0, self._exit_mini)
            threading.Thread(target=scheduler_loop, daemon=True).start()
        else:
            threading.Thread(target=self._run_once, args=(desc,), daemon=True).start()

    def _stop(self):
        self.tt_running.clear()
        self.status_var.set(tr("status_stopped"))

    def _scroll_bottom(self):
        for _ in range(25):
            pyautogui.scroll(-120); time.sleep(0.03)

    def _run_once(self, desc_text):
        self.status_var.set(tr("status_busy"))
        try:
            self._click("upload")
            self._click("select_video")
            self._click("video_item")
            self._click("open")
            for _ in range(30):
                if not self.tt_running.is_set(): return
                time.sleep(0.5)
            self._click("description")
            try:
                for _ in range(100): pyautogui.press("backspace")
            except Exception: pass
            if not self.tt_running.is_set(): return
            if desc_text:
                try: pyautogui.typewrite(desc_text, interval=0.01)
                except Exception: pass
            for _ in range(6):
                if not self.tt_running.is_set(): return
                time.sleep(0.5)
            self._scroll_bottom()
            if not self.tt_running.is_set(): return
            self._click("send")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.status_var.set(tr("status_done")); self.after(0, self._exit_mini)

# -----------------------------------------------------------------------------
# AutoMouse (recorder/player)
# -----------------------------------------------------------------------------
class Recorder:
    SAMPLE_INTERVAL = 0.01
    def __init__(self):
        self.events = []; self.start_time = None; self.running = False
        self._lock = threading.Lock(); self._kl = None; self._ml = None; self._sampler = None
    def _t(self): return time.perf_counter() - self.start_time
    def _key_to_name(self, key):
        if hasattr(key, "char") and key.char is not None: return key.char, False
        name = getattr(key, "name", str(key))
        if name.startswith("Key."): name = name.split(".", 1)[1]
        return name, True
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
        next_time = time.perf_counter()
        while self.running:
            try:
                x, y = pyautogui.position()
                with self._lock:
                    self.events.append({"t": self._t(), "type": "pos", "x": int(x), "y": int(y)})
            except Exception:
                pass
            next_time += self.SAMPLE_INTERVAL
            delay = next_time - time.perf_counter()
            if delay > 0: time.sleep(delay)
            else: next_time = time.perf_counter()
    def start(self):
        if self.running: return
        self.events = []; self.start_time = time.perf_counter(); self.running = True
        self._kl = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        self._ml = mouse.Listener(on_click=self._on_click, on_scroll=self._on_scroll)
        self._kl.start(); self._ml.start()
        self._sampler = threading.Thread(target=self._sample_positions, daemon=True); self._sampler.start()
    def stop(self):
        if not self.running: return
        self.running = False
        try:
            if self._kl: self._kl.stop()
            if self._ml: self._ml.stop()
        except Exception: pass
        self._kl = None; self._ml = None
    def save(self, filepath: Path):
        self.events.sort(key=lambda e: e.get("t", 0.0))
        filepath.write_text(json.dumps(self.events, indent=2), encoding="utf-8")

class Player:
    def __init__(self, events):
        self.events = sorted(events or [], key=lambda e: e.get("t", 0.0))
        self._stop = threading.Event(); self._esc_listener = None; self._ignore_esc = False
    def stop(self): self._stop.set()
    @staticmethod
    def _key_from_name(name, special):
        if special:
            try: return getattr(Key, name)
            except Exception: return None
        return name
    def _on_esc_press(self, key):
        if key == Key.esc:
            if self._ignore_esc: return None
            self._stop.set(); return False
        return None
    def play(self, speed_scale: float = 1.0):
        if not self.events: return
        self._esc_listener = keyboard.Listener(on_press=self._on_esc_press); self._esc_listener.start()
        last_t = 0.0
        try:
            for ev in self.events:
                if self._stop.is_set(): break
                t = ev.get("t", 0.0)
                wait_for = (t - last_t)
                if wait_for > 0:
                    wait_for = wait_for / max(0.001, speed_scale)
                    if self._stop.wait(wait_for): break
                et = ev["type"]
                try:
                    if et == "pos":
                        pyautogui.moveTo(ev["x"], ev["y"])
                    elif et == "mouse_down":
                        pyautogui.mouseDown(button=ev.get("button","left"))
                    elif et == "mouse_up":
                        pyautogui.mouseUp(button=ev.get("button","left"))
                    elif et == "scroll":
                        dy = int(ev.get("dy",0)); dx = int(ev.get("dx",0))
                        if dy: pyautogui.scroll(dy)
                        if dx:
                            try: pyautogui.hscroll(dx)
                            except Exception: pass
                    elif et in ("key_down","key_up"):
                        keyname = ev.get("key"); special = ev.get("special", False)
                        keyobj = self._key_from_name(keyname, special)
                        if et == "key_down":
                            if isinstance(keyobj, str): pyautogui.keyDown(keyobj)
                            else:
                                from pynput.keyboard import Controller
                                Controller().press(keyobj)
                        else:
                            if isinstance(keyobj, str): pyautogui.keyUp(keyobj)
                            else:
                                from pynput.keyboard import Controller
                                Controller().release(keyobj)
                except Exception:
                    if et == "key_down" and isinstance(ev.get("key"), str) and len(ev.get("key"))==1:
                        try: pyautogui.typewrite(ev.get("key"))
                        except Exception: pass
                last_t = t
        finally:
            try:
                if self._esc_listener: self._esc_listener.stop()
            except Exception: pass

class AutoMouseWindow(ctk.CTkToplevel, MiniMixin):
    def __init__(self, master, get_lang, set_lang):
        ctk.CTkToplevel.__init__(self, master)
        MiniMixin.__init__(self)
        self.get_lang = get_lang; self.set_lang = set_lang
        self.title(tr("automouse")); set_window_icon(self, APP_ICON_MM)
        self.geometry("780x640"); self.resizable(True, True); self.attributes("-topmost", True)
        self.rowconfigure(0, weight=1); self.columnconfigure(0, weight=1)

        self.recorder = Recorder(); self.player = None
        self.status_var = tk.StringVar(value=tr("status_done"))
        self.count_var = tk.IntVar(value=1); self.until_var = tk.BooleanVar(value=False)
        self.play_delay_var = tk.DoubleVar(value=0.0)
        self.speed_var = tk.StringVar(value="1x")
        self.speed_map = {"0.5x": 0.4, "1x": 0.8, "2x": 1.6}
        self.schedule_enabled = tk.BooleanVar(value=False)
        self.new_time_var = tk.StringVar(value="")
        self.times = []

        self._build_ui()

    @staticmethod
    def _wait_for_global_key(target_keys=(Key.insert,), allow_esc=True, tick_ui=None):
        evt = threading.Event(); result = {"val": None}
        def on_press(k):
            try:
                if isinstance(k, Key):
                    if k in target_keys: result["val"]=k; evt.set(); return False
                    if allow_esc and k == Key.esc: result["val"]="esc"; evt.set(); return False
            except Exception: pass
            return None
        lis = keyboard.Listener(on_press=on_press); lis.start()
        try:
            while not evt.is_set():
                if tick_ui:
                    try: tick_ui()
                    except Exception: pass
                time.sleep(0.01)
        finally:
            try: lis.stop()
            except Exception: pass
        return result["val"]

    def _build_ui(self):
        wrap = ttk.Frame(self, padding=20); wrap.grid(row=0, column=0, sticky="nsew")
        wrap.columnconfigure(0, weight=1); wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(3, weight=1)

        ttk.Label(wrap, text=tr("automouse"), font=("Segoe UI", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 16), sticky="w")

        row = ttk.Frame(wrap); row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=6)
        for c in range(5): row.columnconfigure(c, weight=1)
        ttk.Button(row, text=" " + tr("record_new"), command=self._record).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(row, text=" " + tr("open_record"), command=self._open).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.play_btn = ttk.Button(row, text=" " + tr("playback"), command=self._play, state="disabled")
        self.play_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        self.stop_btn = ttk.Button(row, text=" Stop", command=self._stop_play, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        self.save_btn = ttk.Button(row, text=" " + tr("status_saved"), command=self._save, state="disabled")
        self.save_btn.grid(row=0, column=4, padx=6, pady=6, sticky="ew")

        sf = ttk.LabelFrame(wrap, text=tr("settings"), padding=12)
        sf.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        for c in range(8): sf.columnconfigure(c, weight=1)
        ttk.Label(sf, text=tr("count")).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.count_var, width=10).grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        ttk.Checkbutton(sf, text=tr("until_closed"), variable=self.until_var).grid(row=0, column=2, sticky="w", padx=8, pady=6)
        ttk.Label(sf, text=tr("play_delay")).grid(row=0, column=3, sticky="e", padx=8, pady=6)
        ttk.Entry(sf, textvariable=self.play_delay_var, width=10).grid(row=0, column=4, padx=8, pady=6, sticky="w")
        ttk.Label(sf, text=tr("speed")).grid(row=0, column=5, sticky="e", padx=8, pady=6)
        ttk.OptionMenu(sf, self.speed_var, self.speed_var.get(), "0.5x", "1x", "2x").grid(row=0, column=6, sticky="w", padx=6, pady=6)

        sch = ttk.LabelFrame(wrap, text=tr("times"), padding=12)
        sch.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=8)
        for c in range(4): sch.columnconfigure(c, weight=1)
        sch.rowconfigure(1, weight=1)
        ttk.Checkbutton(sch, text=tr("schedule_enable"), variable=self.schedule_enabled).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(sch, text=tr("schedule_time")).grid(row=0, column=1, sticky="e")
        ttk.Entry(sch, textvariable=self.new_time_var, width=10).grid(row=0, column=2, padx=6, sticky="w")
        ttk.Button(sch, text=tr("add_time"), command=self._add_time).grid(row=0, column=3, padx=6, sticky="w")
        self.times_list = tk.Listbox(sch, height=6); self.times_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(8,6), pady=6)
        ttk.Button(sch, text=tr("remove_time"), command=self._remove_time).grid(row=1, column=2, padx=6, sticky="nw")

        ttk.Label(wrap, text=tr("status_done"), textvariable=self.status_var, font=("Segoe UI", 10, "italic")).grid(row=4, column=0, columnspan=2, sticky="w")

    def _add_time(self):
        t = parse_hhmm(self.new_time_var.get())
        if not t:
            messagebox.showerror("Time", "Invalid time format. Use HH:MM"); return
        if t not in self.times:
            self.times.append(t); self.times.sort()
        self._refresh_times()

    def _remove_time(self):
        try:
            idx = self.times_list.curselection()
            if not idx: return
            t = self.times[idx[0]]
            self.times.remove(t); self._refresh_times()
        except Exception: pass

    def _refresh_times(self):
        self.times_list.delete(0, tk.END)
        for t in sorted(self.times): self.times_list.insert(tk.END, t)

    def _record(self):
        path = filedialog.asksaveasfilename(initialdir=str(AUTOMOUSE_DIR), defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path: return
        self.status_var.set(tr("waiting_for_insert"))
        key = self._wait_for_global_key(target_keys=(Key.insert,), allow_esc=True, tick_ui=self.update)
        if key == "esc":
            self.status_var.set(tr("status_done")); return
        try:
            self.recorder.start()
        except Exception as e:
            messagebox.showerror("Recorder error", str(e)); self.status_var.set(tr("status_done")); return
        self.status_var.set(tr("press_insert_or_esc_to_stop"))
        _ = self._wait_for_global_key(target_keys=(Key.insert,), allow_esc=True, tick_ui=self.update)
        self.recorder.stop()
        try:
            Path(path).write_text(json.dumps(self.recorder.events, indent=2), encoding="utf-8")
            self.status_var.set(tr("status_saved"))
        except Exception:
            self.status_var.set(tr("status_done"))
        self.play_btn.config(state="normal"); self.save_btn.config(state="normal")

    def _open(self):
        path = filedialog.askopenfilename(initialdir=str(AUTOMOUSE_DIR), filetypes=[("JSON","*.json")])
        if not path: return
        try:
            events = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(events, list): raise ValueError("Invalid file")
            self.recorder.events = events; self.status_var.set(tr("status_done"))
            self.play_btn.config(state="normal"); self.save_btn.config(state="normal")
        except Exception:
            self.recorder.events = []; self.status_var.set(tr("status_done"))

    def _save(self):
        if not self.recorder.events: return
        path = filedialog.asksaveasfilename(initialdir=str(AUTOMOUSE_DIR), defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path: return
        try:
            Path(path).write_text(json.dumps(self.recorder.events, indent=2), encoding="utf-8"); self.status_var.set(tr("status_saved"))
        except Exception:
            self.status_var.set(tr("status_done"))

    def _play(self):
        if not self.recorder.events: return
        schedule_on = self.schedule_enabled.get(); times = list(self.times)
        speed_scale = self.speed_map.get(self.speed_var.get(), 0.8)
        self._enter_mini(stop_callback=self._stop_play, banner_text=tr("mini_msg"))
        self.status_var.set(tr("status_busy")); self.play_btn.config(state="disabled"); self.stop_btn.config(state="normal")
        def loop():
            try:
                if schedule_on and times:
                    while True:
                        up = [(t, next_occurrence(t)) for t in times]; up.sort(key=lambda x:x[1])
                        if not up:
                            time.sleep(0.5); continue
                        _, when = up[0]
                        self.status_var.set(tr("waiting_until", time=when.strftime("%H:%M")))
                        wait_until(when, tick=self.update)
                        self.player = Player(self.recorder.events); self.player.play(speed_scale=speed_scale)
                        if self.player._stop.is_set(): break
                else:
                    count = self.count_var.get(); endless = self.until_var.get(); play_delay = self.play_delay_var.get()
                    while endless or count>0:
                        self.player = Player(self.recorder.events); self.player.play(speed_scale=speed_scale)
                        if self.player._stop.is_set(): break
                        if play_delay>0:
                            evt = threading.Event()
                            if evt.wait(play_delay): break
                        if not endless: count -= 1
            finally:
                self.stop_btn.config(state="disabled"); self.play_btn.config(state="normal"); self.status_var.set(tr("status_done"))
                self.after(0, self._exit_mini)
        threading.Thread(target=loop, daemon=True).start()

    def _stop_play(self):
        try:
            if self.player: self.player.stop()
        except Exception: pass
        self.status_var.set(tr("status_stopped"))

# -----------------------------------------------------------------------------
# Main window
# -----------------------------------------------------------------------------
class MultiMouseApp:
    def __init__(self):
        snap_cfg = load_snap_config()
        path = snap_cfg.get("auto_settings_file")
        data = load_combined_data(path) if snap_cfg.get("auto_load_settings") else None
        if not isinstance(data, dict):
            data = {}
        lang = data.get("language", CURRENT_LANG)
        globals()["CURRENT_LANG"] = lang
        dark_mode = bool(data.get("dark_mode", True))

        self.root = ctk.CTk(); self.style = ttk.Style()
        try: self.style.theme_use("clam")
        except Exception: pass

        self.root.title(tr("app_title"))
        self.root.geometry("900x560"); self.root.resizable(True, True)
        self.root.rowconfigure(0, weight=1); self.root.columnconfigure(0, weight=1)
        self.root.attributes("-topmost", True)
        set_window_icon(self.root, APP_ICON_MM)

        # button icons
        try:
            self.icon_mouse = ctk.CTkImage(Image.open(APP_ICON_MM), size=(20,20))
            self.icon_snap = ctk.CTkImage(Image.open(APP_ICON_SNAP), size=(20,20))
            self.icon_tiktok = ctk.CTkImage(Image.open(APP_ICON_TT), size=(20,20))
        except Exception:
            self.icon_mouse = self.icon_snap = self.icon_tiktok = None

        self.lang_var = tk.StringVar(value=lang)
        self.dark_var = tk.BooleanVar(value=dark_mode)
        self.dirty = False

        self._build_ui(); self._apply_theme(initial=True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        wrap = ctk.CTkFrame(self.root)
        wrap.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        for c in range(3): wrap.columnconfigure(c, weight=1)
        wrap.rowconfigure(5, weight=1)

        title = ctk.CTkLabel(wrap, text=tr("app_title"), font=("Segoe UI", 22, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 14))

        ctk.CTkButton(wrap, text=" " + tr("open_autosnap"), image=self.icon_snap, command=self.open_autosnap, compound="left").grid(row=1, column=0, padx=10, pady=8, sticky="ew")
        ctk.CTkButton(wrap, text=" " + tr("open_automouse"), image=self.icon_mouse, command=self.open_automouse, compound="left").grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkButton(wrap, text=" " + tr("open_autotiktok"), image=self.icon_tiktok, command=self.open_autotiktok, compound="left").grid(row=1, column=2, padx=10, pady=8, sticky="ew")

        bar = ctk.CTkFrame(wrap)
        bar.grid(row=2, column=0, columnspan=3, pady=(8, 4), sticky="ew")
        for c in range(4): bar.columnconfigure(c, weight=1)
        small_font = ("Segoe UI", 8)

        ctk.CTkLabel(bar, text=tr("language"), font=small_font).grid(row=0, column=0, padx=4, sticky="e")
        lang = ctk.CTkOptionMenu(bar, variable=self.lang_var, values=["nl", "en"], command=self._switch_lang)
        lang.grid(row=0, column=1, padx=4, sticky="w")

        ctk.CTkLabel(bar, text=tr("dark_mode"), font=small_font).grid(row=0, column=2, padx=4, sticky="e")
        chk = ctk.CTkCheckBox(bar, text="", variable=self.dark_var, command=self._apply_theme)
        chk.grid(row=0, column=3, padx=4, sticky="w")

        ctk.CTkButton(wrap, text=tr("load_settings"), command=self.load_combined_settings).grid(row=3, column=0, columnspan=3, pady=(0,4), sticky="ew")
        ctk.CTkButton(wrap, text=tr("save_settings"), command=self.save_combined_settings).grid(row=4, column=0, columnspan=3, pady=8, sticky="ew")

    def _switch_lang(self, val):
        globals()["CURRENT_LANG"] = val
        self.dirty = True
        for w in list(self.root.children.values()): w.destroy()
        self._build_ui(); self._apply_theme()

    def _apply_theme(self, initial=False, mark_dirty=True):
        is_dark = bool(self.dark_var.get())
        ctk.set_appearance_mode("dark" if is_dark else "light")
        bg = "#1e1e1e" if is_dark else "#f0f0f0"; fg = "#f5f5f5" if is_dark else "#111111"
        try:
            # use CTk's fg_color so foreground text isn't white on a white window
            self.root.configure(fg_color=bg)
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
        try:
            sel_bg = "#444444" if is_dark else "#cccccc"
            def style_listboxes(parent):
                for w in parent.winfo_children():
                    if isinstance(w, tk.Listbox):
                        w.configure(bg=bg, fg=fg, selectbackground=sel_bg, selectforeground=fg)
                    try:
                        style_listboxes(w)
                    except Exception:
                        pass
            style_listboxes(self.root)
        except Exception:
            pass
        if mark_dirty and not initial:
            self.dirty = True

    def save_combined_settings(self):
        data = {
            "language": self.lang_var.get(),
            "dark_mode": bool(self.dark_var.get()),
            "autosnap": load_snap_config(),
            "autotiktok": load_tt_config(),
        }
        file_path = filedialog.asksaveasfilename(initialdir=str(EXTRA_SAVE_DIR),
                                                defaultextension=".json",
                                                filetypes=[("JSON", "*.json")])
        if not file_path:
            return
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(data, indent=2)
            Path(file_path).write_text(text, encoding="utf-8")
            # onthoud laatst opgeslagen instellingen voor automatische scripts
            EXTRA_SAVE_FILE.write_text(text, encoding="utf-8")
            messagebox.showinfo(tr("save_settings"), tr("saved"))
            self.dirty = False
        except Exception:
            messagebox.showerror(tr("save_settings"), "Kon instellingen niet opslaan")

    def load_combined_settings(self):
        file_path = filedialog.askopenfilename(initialdir=str(EXTRA_SAVE_DIR),
                                               filetypes=[("JSON", "*.json")])
        if not file_path:
            messagebox.showerror(tr("load_settings"), "Geen opgeslagen instellingen")
            return
        try:
            text = Path(file_path).read_text(encoding="utf-8")
            data = json.loads(text)
        except Exception:
            messagebox.showerror(tr("load_settings"), "Geen opgeslagen instellingen")
            return
        self.lang_var.set(data.get("language", self.lang_var.get()))
        self.dark_var.set(bool(data.get("dark_mode", False)))
        self._switch_lang(self.lang_var.get())
        self._apply_theme()
        # bewaar als laatst geladen instellingen en werk feature-configs bij
        try:
            EXTRA_SAVE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            snap = data.get("autosnap")
            if isinstance(snap, dict):
                save_snap_config(snap)
            tt = data.get("autotiktok")
            if isinstance(tt, dict):
                save_tt_config(tt)
        except Exception:
            pass
        messagebox.showinfo(tr("load_settings"), tr("loaded"))
        self.dirty = False

    def _on_close(self):
        if self.dirty:
            msg = ("Wilt u uw data opslaan?\n" "Niet opgeslagen: kalibratie, aantal snaps, tijden & personen, TikTok beschrijving, taal, thema")
            detail = "Wordt opgeslagen: kalibratie, aantal snaps, tijden met personen, TikTok beschrijving, taal en thema"
            if messagebox.askyesno(tr("save_settings"), msg, detail=detail):
                self.save_combined_settings()
        self.root.destroy()

    def _show_child_modal(self, child_window: ctk.CTkToplevel):
        # hoofdmenu blijft op achtergrond (niet topmost)
        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass

        self.root.withdraw()

        def on_close():
            try:
                child_window.destroy()
            finally:
                self.root.deiconify()
                try:
                    self.root.lift()
                    self.root.attributes("-topmost", True)
                except Exception:
                    pass

        child_window.protocol("WM_DELETE_WINDOW", on_close)
        child_window.wait_window()
        self.root.deiconify()
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
        except Exception:
            pass

    def open_autosnap(self):
        w = AutoSnapWindow(
            self.root,
            lambda: self.lang_var.get(),
            self._switch_lang,
            self.save_combined_settings,
            self.load_combined_settings,
        )
        set_window_icon(w, APP_ICON_SNAP)
        self._apply_theme(mark_dirty=False)
        self._show_child_modal(w)
        self.dirty = True

    def open_automouse(self):
        w = AutoMouseWindow(self.root, lambda: self.lang_var.get(), self._switch_lang)
        set_window_icon(w, APP_ICON_MM)
        self._apply_theme(mark_dirty=False)
        self._show_child_modal(w)

    def open_autotiktok(self):
        w = AutoTikTokWindow(self.root, lambda: self.lang_var.get(), self._switch_lang, self.save_combined_settings)
        set_window_icon(w, APP_ICON_TT)
        self._apply_theme(mark_dirty=False)
        self._show_child_modal(w)
        self.dirty = True

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    try:
        app = MultiMouseApp()
        app.root.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        _fatal(f"Onverwachte fout: {e}")


if __name__ == "__main__":
    main()
