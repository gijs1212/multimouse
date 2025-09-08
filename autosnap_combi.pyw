import multimouse as mm
import os, time
from pathlib import Path


def open_snapchat():
    link = Path.home() / "Desktop" / "Snapchat.lnk"
    if not link.exists():
        print(f"Shortcut niet gevonden: {link}")
        return
    os.startfile(str(link))
    time.sleep(5.0)


def main():
    open_snapchat()
    app = mm.MultiMouseApp()
    app.root.withdraw()
    win = mm.AutoSnapWindow(
        app.root,
        lambda: app.lang_var.get(),
        app._switch_lang,
        app.save_combined_settings,
        app.load_combined_settings,
    )
    mm.set_window_icon(win, mm.APP_ICON_SNAP)
    app._apply_theme(mark_dirty=False)
    # ensure window shows and then start combi automation
    win.after(0, lambda: (win.deiconify(), win.lift(), win.focus_force(), win._start_combi()))
    app.root.mainloop()


if __name__ == "__main__":
    main()
