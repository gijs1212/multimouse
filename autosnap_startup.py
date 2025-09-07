import os, sys, time, importlib
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from contextlib import contextmanager

# allow modules from roaming site-packages on Windows
if sys.platform == "win32":
    extra_site = Path(os.getenv("APPDATA", "")) / "Python" / "Python313" / "site-packages"
    if extra_site.exists() and str(extra_site) not in sys.path:
        sys.path.insert(0, str(extra_site))


def _fatal(msg: str):
    try:
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror("AutoSnap", msg)
        r.destroy()
    except Exception:
        pass
    sys.exit(1)


def _require_module(name: str, pip_hint: str):
    try:
        mod = importlib.import_module(name)
        path = getattr(mod, "__file__", "builtin")
        print(f"{name} -> {path}")
        return mod
    except Exception as e:
        _fatal(f"{pip_hint} ontbreekt: {e}\nInstalleer met: pip install {pip_hint}")

ctk = _require_module("customtkinter", "customtkinter")  # type: ignore
pyautogui = _require_module("pyautogui", "pyautogui pillow")  # type: ignore

@contextmanager
def log_action(description: str):
    print(f"{description}...", end="", flush=True)
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f" {elapsed:.2f}s")

from multimouse import (
    load_combined_data,
    load_snap_config,
    AutoSnapWindow,
    red_in_radius,
    RADIUS_DEFAULT,
    set_window_icon,
    APP_ICON_SNAP,
)

pyautogui.FAILSAFE = False

def open_snapchat(cfg, delay):
    search = cfg.get("boot_searchbar")
    if not search:
        return
    x, y = search
    with log_action("Wachten na opstart (5s)"):
        time.sleep(5.0)
    with log_action("Beweeg naar zoekbalk"):
        pyautogui.moveTo(x, y)
    with log_action("Klik op zoekbalk"):
        pyautogui.click()
    try:
        with log_action("Typ 'snapchat' en druk Enter"):
            pyautogui.typewrite("snapchat", interval=0.01)
            pyautogui.press("enter")
    except Exception:
        pass
    with log_action("Wacht tot Snapchat opent (3s)"):
        time.sleep(3.0)


def open_unreads(win):
    cfg = win.cfg
    close_pos = cfg.get("responder_close_snap")
    unread_pts = []
    for pt in cfg.get("responder_badges", []):
        if pt and red_in_radius(pt[0], pt[1], RADIUS_DEFAULT):
            unread_pts.append(pt)
    print(f"{len(unread_pts)} ongelezen snaps gevonden")
    for i, (x, y) in enumerate(unread_pts, 1):
        with log_action(f"Open snap {i}/{len(unread_pts)}"):
            win.move_then_click((x, y))
            win.move_then_click((x, y))
    if unread_pts and close_pos:
        with log_action("Sluit laatste snap"):
            win.move_then_click(tuple(close_pos))


def send_to_all(win):
    persons = list(range(8))
    with log_action(f"Stuur snap naar {len(persons)} personen"):
        win._run_sender_once(persons)


def main():
    print("AutoSnap startup gestart")
    load_combined_data()
    cfg = load_snap_config()
    delay = cfg.get("action_delay", 0.5)
    print(f"Actievertraging: {delay}s")
    pyautogui.PAUSE = delay
    open_snapchat(cfg, delay)
    time.sleep(delay)
    root = ctk.CTk()
    set_window_icon(root, APP_ICON_SNAP)
    root.withdraw()
    win = AutoSnapWindow(root, lambda: "nl", lambda _v: None, lambda: None)
    win.withdraw()
    if cfg.get("startup_send_snap"):
        send_to_all(win)
        time.sleep(delay)
    open_unreads(win)
    time.sleep(delay)
    print("Start AutoSnap combi")
    win._start_combi()
    root.mainloop()


if __name__ == "__main__":
    main()
