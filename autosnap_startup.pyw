import time
import customtkinter as ctk
import pyautogui
from multimouse import (
    load_combined_data,
    load_snap_config,
    AutoSnapWindow,
    red_in_radius,
    RADIUS_DEFAULT,
)

pyautogui.FAILSAFE = False


def open_snapchat(cfg):
    search = cfg.get("restart_searchbar")
    if search:
        x, y = search
        pyautogui.moveTo(x, y)
        time.sleep(0.5)
        pyautogui.click()
        time.sleep(0.5)
        try:
            pyautogui.typewrite("snapchat", interval=0.01)
            pyautogui.press("enter")
        except Exception:
            pass
        time.sleep(3.0)


def open_unreads(win):
    cfg = win.cfg
    close_pos = cfg.get("responder_close_snap")
    for pt in cfg.get("responder_badges", []):
        if not pt:
            continue
        x, y = pt
        if red_in_radius(x, y, RADIUS_DEFAULT):
            win.move_then_click((x, y))
            win.move_then_click((x, y))
            if close_pos:
                win.move_then_click(tuple(close_pos))


def send_to_all(win):
    persons = [i for i, p in enumerate(win.cfg.get("personen", [])) if p]
    win._run_sender_once(persons)


def main():
    load_combined_data()
    cfg = load_snap_config()
    open_snapchat(cfg)

    root = ctk.CTk()
    root.withdraw()
    win = AutoSnapWindow(root, lambda: "nl", lambda _v: None, lambda: None)
    win.withdraw()

    open_unreads(win)
    send_to_all(win)
    win._start_combi()
    root.mainloop()


if __name__ == "__main__":
    main()
