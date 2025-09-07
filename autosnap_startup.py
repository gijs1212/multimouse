import os, sys, time, importlib
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from contextlib import contextmanager

# allow modules from roaming site-packages on Windows (incl. Windows PE)
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

# ensure we can import the project modules when running from Startup
repo = Path.home() / "Documents" / "github" / "multimouse"
if repo.exists() and str(repo) not in sys.path:
    sys.path.insert(0, str(repo))


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
    MultiMouseApp,
)

pyautogui.FAILSAFE = False


def open_snapchat(cfg):
    search = cfg.get("boot_searchbar")
    if not search:
        return
    x, y = search
    pyautogui.moveTo(x, y)
    with log_action("Klik op zoekbalk"):
        pyautogui.click()
    with log_action("Wacht 1s"):
        time.sleep(1.0)
    with log_action("Typ 'snapchat'"):
        pyautogui.typewrite("snapchat", interval=0.01)
    with log_action("Wacht 1s"):
        time.sleep(1.0)
    with log_action("Druk Enter"):
        pyautogui.press("enter")
    with log_action("Wacht tot Snapchat opent (3s)"):
        time.sleep(3.0)



def main():
    print("AutoSnap startup gestart")
    load_combined_data()
    cfg = load_snap_config()
    delay = cfg.get("action_delay", 0.5)
    print(f"Actievertraging: {delay}s")
    pyautogui.PAUSE = 0
    open_snapchat(cfg)
    with log_action("Wacht 10s"):
        time.sleep(10.0)
    app = MultiMouseApp()
    win = AutoSnapWindow(app.root, lambda: app.lang_var.get(), app._switch_lang, app.save_combined_settings)
    app._apply_theme(mark_dirty=False)
    win.mode_var.set("combi")
    win._refresh_mode()
    print("Start AutoSnap combi")
    win._start_combi()
    app.root.mainloop()


if __name__ == "__main__":
    main()
