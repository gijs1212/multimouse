import importlib.util, pathlib, sys, os, time
from pathlib import Path

def _load_mm():
    path = pathlib.Path(__file__).with_name("multimouse.pyw")
    spec = importlib.util.spec_from_file_location("_mm", path)
    mm = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_mm", mm)
    spec.loader.exec_module(mm)  # type: ignore[attr-defined]
    return mm

mm = _load_mm()


def open_snapchat():
    cfg = mm.load_snap_config()
    link = cfg.get("snapchat_shortcut") or (Path.home() / "Desktop" / "Snapchat.lnk")
    link = Path(link)
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
    win.deiconify()
    win.lift()
    win.focus_force()
    win._start_combi()
    app.root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        mm._fatal(f"Onverwachte fout: {e}")
