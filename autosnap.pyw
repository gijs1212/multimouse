import importlib.util, pathlib, sys

def _load_mm():
    """Load core multimouse module from adjacent .pyw."""
    path = pathlib.Path(__file__).with_name("multimouse.pyw")
    spec = importlib.util.spec_from_file_location("_mm", path)
    mm = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_mm", mm)
    spec.loader.exec_module(mm)  # type: ignore[attr-defined]
    return mm

mm = _load_mm()


def main():
    # eenvoudige AutoSnap-launcher
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
    app.root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        mm._fatal(f"Onverwachte fout: {e}")
