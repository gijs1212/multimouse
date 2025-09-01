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
pyautogui.PAUSE = 0.5


def open_snapchat(cfg):
    search = cfg.get("restart_searchbar")
    if not search:
        return
    x, y = search
    time.sleep(5.0)
    pyautogui.moveTo(x, y)
    pyautogui.click()
    try:
        pyautogui.typewrite("snapchat", interval=0.01)
        pyautogui.press("enter")
    except Exception:
        pass
    time.sleep(3.0)


def open_unreads(win):
    cfg = win.cfg
    close_pos = cfg.get("responder_close_snap")
    unread_pts = []
    for pt in cfg.get("responder_badges", []):
        if pt and red_in_radius(pt[0], pt[1], RADIUS_DEFAULT):
            unread_pts.append(pt)
    for x, y in unread_pts:
        win.move_then_click((x, y))
        win.move_then_click((x, y))
    if unread_pts and close_pos:
        win.move_then_click(tuple(close_pos))


def send_to_all(win):
    persons = list(range(8))
    win._run_sender_once(persons)


def main():
    load_combined_data()
    cfg = load_snap_config()
    open_snapchat(cfg)
    time.sleep(0.5)
    root = ctk.CTk()
    root.withdraw()
    win = AutoSnapWindow(root, lambda: "nl", lambda _v: None, lambda: None)
    win.withdraw()
    open_unreads(win)
    time.sleep(0.5)
    send_to_all(win)
    time.sleep(0.5)
    win._start_combi()
    root.mainloop()


if __name__ == "__main__":
    main()
